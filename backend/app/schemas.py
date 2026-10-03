# if models defined how data is saved in the tables, schemas defines the data contract - the format of data coming into the server from the frontend and leaving the server back to the browser
# this defines the API and how the backend communicates with the frontend and vice versa

import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field

# --- AUTHENTICATION SCHEMAS ---
# checks that user registration and login requests have the correct data format
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- CATEGORY SCHEMAS ---
class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None
    icon: Optional[str] = "📁"
    color: Optional[str] = "#3B82F6"
    order: Optional[int] = 0

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    order: Optional[int] = None

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    children: List['CategoryResponse'] = []

    class Config:
        from_attributes = True


# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    due_date: Optional[datetime.date] = None
    due_time: Optional[datetime.time] = None
    time_estimate_mins: Optional[int] = 30
    status: Optional[str] = "pending"  # "pending", "completed", "archived"

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    due_date: Optional[datetime.date] = None
    due_time: Optional[datetime.time] = None
    time_estimate_mins: Optional[int] = None
    status: Optional[str] = None

# sends a response payload with the task data and additional computed fields like urgency_status and category details to the react frontend
class TaskResponse(TaskBase):
    id: int
    user_id: int
    created_at: datetime.datetime
    urgency_status: Optional[str] = "normal"  # "yellow" (5 days), "amber" (4-2 days), "red" (<24h), "overdue"
    category_name: Optional[str] = None
    category_color: Optional[str] = None
    category_icon: Optional[str] = None

    class Config:
        from_attributes = True # converts object attributes into json format for the response payload to the frontend to read easy


# --- EMAIL QUEUE SCHEMAS ---
class EmailQueueBase(BaseModel):
    gmail_message_id: Optional[str] = None
    from_email: str
    subject: str
    body_preview: Optional[str] = None
    received_at: Optional[datetime.datetime] = None
    status: Optional[str] = "inbox"
    is_important: Optional[bool] = False

class EmailQueueResponse(EmailQueueBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# --- VOICE / NLP PARSER SCHEMAS ---
class VoiceParseRequest(BaseModel):
    transcript: str

class VoiceParseResponse(BaseModel):
    title: str
    due_date: Optional[datetime.date] = None
    due_time: Optional[datetime.time] = None
    time_estimate_mins: Optional[int] = 30
    suggested_category_id: Optional[int] = None
    suggested_category_name: Optional[str] = None
