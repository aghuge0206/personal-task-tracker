# this file manages the gmail inbox queue api endpoints, basically gets a list of incoming emails, sorted by received date, and updates the status of an email

import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

# Create Email Queue API Router with URL prefix /email-queue
router = APIRouter(prefix="/email-queue", tags=["Email Queue"])

SAMPLE_EMAILS = [
    {
        "gmail_message_id": "msg_001",
        "from_email": "recruiting@google.com",
        "subject": "Google Software Engineer Intern Interview Invitation",
        "body_preview": "Hi Akshat, We are excited to invite you to complete your technical interview for the Software Engineer Intern role. Please select a time slot by Friday at 11:59 PM.",
        "is_important": True
    },
    {
        "gmail_message_id": "msg_002",
        "from_email": "ta@cs.uw.edu",
        "subject": "CSE 373 Homework 4 Deadline Extension",
        "body_preview": "Hello CSE 373 Students, The deadline for Homework 4 has been extended to next Monday at 5:00 PM. Please review the updated rubric on Canvas.",
        "is_important": True
    },
    {
        "gmail_message_id": "msg_003",
        "from_email": "newsletter@techdigest.io",
        "subject": "Top 10 Tech Trends in 2026",
        "body_preview": "Check out this week's top stories in AI, cloud computing, and developer tools...",
        "is_important": False
    }
]

# gets a list of incoming emails for the current user, sorted by received date, and returns them in a structured response. if the queue is empty, it seeds sample emails for demo purposes. It hides already converted emails from the active queue.
@router.get("/", response_model=List[schemas.EmailQueueResponse])
def get_email_queue(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """GET Email Queue API Endpoint: Returns pending Gmail inbox queue items for current user."""
    # Seed sample emails if queue is empty for demo purposes
    count = db.query(models.EmailQueue).filter(models.EmailQueue.user_id == current_user.id).count()
    if count == 0:
        for sample in SAMPLE_EMAILS:
            item = models.EmailQueue(
                user_id=current_user.id,
                gmail_message_id=sample["gmail_message_id"],
                from_email=sample["from_email"],
                subject=sample["subject"],
                body_preview=sample["body_preview"],
                is_important=sample["is_important"],
                status="inbox"
            )
            db.add(item)
        db.commit()

    items = db.query(models.EmailQueue).filter(
        models.EmailQueue.user_id == current_user.id,
        models.EmailQueue.status != "converted"  # Hide already converted emails from active queue
    ).order_by(models.EmailQueue.received_at.desc()).all()

    return items

# updates the status of an email in the queue (inbox, spam, converted) for the current user. It returns the updated email item in the response.
@router.put("/{email_id}/status", response_model=schemas.EmailQueueResponse)
def update_email_status(
    email_id: int,
    status_str: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """PUT Email Status API Endpoint: Updates email status (inbox, spam, converted)."""
    item = db.query(models.EmailQueue).filter(
        models.EmailQueue.id == email_id,
        models.EmailQueue.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Email item not found")

    item.status = status_str  # "inbox", "spam", "converted"
    db.commit()
    db.refresh(item)
    return item
