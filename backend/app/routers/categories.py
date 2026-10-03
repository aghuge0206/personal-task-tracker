# defines the category management api router, which basically means it handles all CRUD operations for categories and subcategories. 

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

# Create Category API Router with URL prefix /categories
router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[schemas.CategoryResponse]) # get all categories for the current user, including nested subcategories
def get_categories(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """GET Categories API Endpoint: Returns top-level categories and nested subcategories for current user."""
    # only return categories and data associated with current user so that user A cant look at user B's categories
    top_categories = db.query(models.Category).filter(
        models.Category.user_id == current_user.id,
        models.Category.parent_id == None
    ).order_by(models.Category.order, models.Category.id).all()
    
    return top_categories


@router.post("/", response_model=schemas.CategoryResponse, status_code=status.HTTP_201_CREATED) # post a new category or subcategory for current user
def create_category(
    category_in: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """POST Category API Endpoint: Creates a new top-level domain or nested subcategory."""
    # verified if parent id exists and belongs to the current user
    if category_in.parent_id:
        parent = db.query(models.Category).filter(
            models.Category.id == category_in.parent_id,
            models.Category.user_id == current_user.id
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        # raises exception to avoid creating a child under a non existent parent

    new_cat = models.Category(
        user_id=current_user.id,
        name=category_in.name,
        parent_id=category_in.parent_id,
        icon=category_in.icon,
        color=category_in.color,
        order=category_in.order
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


@router.put("/{category_id}", response_model=schemas.CategoryResponse) # updates an existing category or subcategory for current user (put is the same as update)
def update_category(
    category_id: int,
    category_in: schemas.CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """PUT Category API Endpoint: Updates category name, icon, color, or parent ID."""
    cat = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(cat, field, value)

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT) # delete a category or subcategory for current user and all subcategories
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """DELETE Category API Endpoint: Deletes category and cascades to subcategories and tasks."""
    cat = db.query(models.Category).filter(
        models.Category.id == category_id,
        models.Category.user_id == current_user.id
    ).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    db.delete(cat)
    db.commit()
    return None
