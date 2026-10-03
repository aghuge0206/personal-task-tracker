# defines the voice input and NLP parsing API endpoints
# when a user speaks a task, this module should send the transcript to the backend, which will parse it for title, duration estimate, datetime, category auto-matching
# and then it should return a structured response for the frontend to pre-fill the task creation form, which the user can then edit and submit to create a new task

import re
import datetime
import dateparser
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

# Create Voice NLP API Router with URL prefix /voice
router = APIRouter(prefix="/voice", tags=["Voice Input & NLP"])

@router.post("/parse", response_model=schemas.VoiceParseResponse)
def parse_voice_transcript(
    payload: schemas.VoiceParseRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """POST Voice Parse API Endpoint: Extracts title, date, time, duration estimate, and category matches from transcript."""
    transcript = payload.transcript.strip()
    
    # 1. Extract Time Estimate (e.g. "for 45 minutes", "takes 30 mins", "for 2 hours")
    time_estimate_mins = 30 # default 30 mins
    dur_match = re.search(r'(?:for|takes?)\s+(\d+)\s+(minute|min|hour|hr)s?', transcript, re.IGNORECASE)
    if dur_match:
        val = int(dur_match.group(1))
        unit = dur_match.group(2).lower()
        if 'hour' in unit or 'hr' in unit:
            time_estimate_mins = val * 60
        else:
            time_estimate_mins = val

    # 2. Extract Date & Time using dateparser NLP library
    parsed_date = None
    parsed_time = None
    
    # Clean duration phrases before date parsing to avoid dateparser confusion
    clean_text = re.sub(r'(?:for|takes?)\s+\d+\s+(?:minute|min|hour|hr)s?', '', transcript, flags=re.IGNORECASE)

    parsed_datetime = dateparser.parse(
        clean_text,
        settings={'PREFER_DATES_FROM': 'future', 'RELATIVE_BASE': datetime.datetime.now()}
    )

    if parsed_datetime:
        parsed_date = parsed_datetime.date()
        parsed_time = parsed_datetime.time()

    # 3. Smart Category Keyword Matching
    user_cats = db.query(models.Category).filter(models.Category.user_id == current_user.id).all()
    suggested_cat_id = None
    suggested_cat_name = None

    transcript_lower = transcript.lower()
    best_match_len = 0
    for cat in user_cats:
        cat_name_lower = cat.name.lower()
        if cat_name_lower in transcript_lower and len(cat_name_lower) > best_match_len:
            best_match_len = len(cat_name_lower)
            suggested_cat_id = cat.id
            suggested_cat_name = cat.name

    # 4. Clean up Title (remove extracted date/time keywords)
    title = transcript
    for phrase in ["by ", "due ", "at ", "on "]:
        if phrase in title.lower():
            parts = re.split(r'\b(?:by|due|on)\b', title, flags=re.IGNORECASE)
            if parts and parts[0].strip():
                title = parts[0].strip()
                break

    return schemas.VoiceParseResponse(
        title=title,
        due_date=parsed_date,
        due_time=parsed_time,
        time_estimate_mins=time_estimate_mins,
        suggested_category_id=suggested_cat_id,
        suggested_category_name=suggested_cat_name
    )
