# this file handles full crud operations for tasks, calculates urgency heatmap status, performs category roll up queries, sorts quick wins, and manages multi-select bulk delete and clear done operations

import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app import models, schemas, auth

# Create Task API Router with URL prefix /tasks
router = APIRouter(prefix="/tasks", tags=["Tasks"])

# recursively collects a category ID and all nested child subcategory IDs to roll them up
def get_descendant_category_ids(category_id: int, user_id: int, db: Session) -> List[int]:
    """Recursively collects a category ID and all nested child subcategory IDs (Category Roll-up logic)."""
    ids = [category_id]
    children = db.query(models.Category.id).filter(
        models.Category.parent_id == category_id,
        models.Category.user_id == user_id
    ).all()
    for child in children:
        ids.extend(get_descendant_category_ids(child.id, user_id, db))
    return ids

# heatmap urgency status computation based on due date and time, returning a string for visual badge
def compute_urgency_status(due_date: Optional[datetime.date], due_time: Optional[datetime.time]) -> str:
    """Computes visual urgency heatmap badge status (Yellow -> Amber -> Red -> Overdue)."""
    if not due_date:
        return "normal"

    now = datetime.datetime.now()
    due_datetime = datetime.datetime.combine(due_date, due_time or datetime.time(23, 59, 59))
    time_diff = due_datetime - now

    if time_diff.total_seconds() < 0:
        return "overdue" # Past deadline
    elif time_diff.total_seconds() <= 86400: # Within 24 hours (86,400 seconds)
        return "red"
    elif time_diff.total_seconds() <= 172800: # Within 2 days (172,800 seconds)
        return "amber"
    elif time_diff.total_seconds() <= 432000: # Within 5 days (432,000 seconds)
        return "yellow"
    return "normal"

# enriches the task response with computed urgency status and category metadata for the frontend
def enrich_task_response(task: models.Task) -> schemas.TaskResponse:
    """Attaches computed urgency heatmap status and category styling metadata to response payload."""
    resp = schemas.TaskResponse.from_orm(task)
    resp.urgency_status = compute_urgency_status(task.due_date, task.due_time)
    if task.category:
        resp.category_name = task.category.name
        resp.category_color = task.category.color
        resp.category_icon = task.category.icon
    return resp


class BulkDeleteRequest(BaseModel):
    task_ids: List[int]


@router.get("/", response_model=List[schemas.TaskResponse]) 
# get tasks filtered by category, status, and quick-win duration, sorted by earliest deadline
def get_tasks(
    category_id: Optional[int] = None,
    status_filter: Optional[str] = "pending", # "pending", "completed", "all"
    max_mins: Optional[int] = None, # For Quick-Win duration filtering (< 15m, < 30m, < 60m)
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """GET Tasks API Endpoint: Handles category roll-up queries, status filters, and quick wins sorted by earliest deadline."""
    query = db.query(models.Task).filter(models.Task.user_id == current_user.id)

    # 1. Roll-up Category Filtering
    if category_id is not None:
        cat_ids = get_descendant_category_ids(category_id, current_user.id, db)
        query = query.filter(models.Task.category_id.in_(cat_ids))

    # 2. Status Filtering
    if status_filter != "all":
        query = query.filter(models.Task.status == status_filter)

    # 3. Quick-Win Time Estimate Filtering
    if max_mins is not None:
        query = query.filter(models.Task.time_estimate_mins <= max_mins)

    # 4. order strictly by earliest due date, then due time, then newest task ID for consistent ordering. nulls pushed to last
    tasks = query.order_by(
        models.Task.due_date.asc().nullslast(),
        models.Task.due_time.asc().nullslast(),
        models.Task.id.desc()
    ).all()

    return [enrich_task_response(t) for t in tasks]

@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """POST Task API Endpoint: Creates a new task record."""
    if task_in.category_id:
        cat = db.query(models.Category).filter(
            models.Category.id == task_in.category_id,
            models.Category.user_id == current_user.id
        ).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

    new_task = models.Task(
        user_id=current_user.id,
        category_id=task_in.category_id,
        title=task_in.title,
        description=task_in.description,
        due_date=task_in.due_date,
        due_time=task_in.due_time,
        time_estimate_mins=task_in.time_estimate_mins,
        status=task_in.status or "pending"
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return enrich_task_response(new_task)


@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """PUT Task API Endpoint: Updates task title, due date, status, or category."""
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    update_data = task_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return enrich_task_response(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """DELETE Task API Endpoint: Permanently deletes a single task."""
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return None


# deletes multiple selected task IDs at once, scoped to the current user, and returns 204 No Content
@router.post("/bulk-delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_tasks(
    body: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """POST Bulk Delete API Endpoint: Deletes multiple selected task IDs at once."""
    db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.id.in_(body.task_ids)
    ).delete(synchronize_session=False) # quick bulk delete without loading objects into memory
    db.commit()
    return None

# clears all completed tasks for the current user, returning 204 No Content
@router.post("/clear-done", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_done_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """POST Clear Done API Endpoint: Purges all completed tasks for current user."""
    db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.status == "completed"
    ).delete(synchronize_session=False)
    db.commit()
    return None
