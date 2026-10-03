# This file defines the database table schema blueprint, defining the 5 tables stored inside the relational db 

import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users" # initialize the table name

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships (One User has Many Categories, Tasks, and Email Queue items)
    # cascade="all, delete-orphan" ensures that when a User is deleted, all their associated Categories, Tasks, and EmailQueue items are also deleted from the database
    categories = relationship("Category", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    email_items = relationship("EmailQueue", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    
    # Self-referencing Foreign Key pointing to another Category ID in the SAME table
    # Allows infinite nesting: e.g. "Recruiting" (id=1) -> "Google" (id=2, parent_id=1) -> "Recorded Interview" (id=3, parent_id=2)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    icon = Column(String, default="📁")
    color = Column(String, default="#3B82F6")
    order = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="categories")
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="category", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    due_time = Column(Time, nullable=True)
    time_estimate_mins = Column(Integer, default=30)
    status = Column(String, default="pending")  # "pending", "completed", "archived"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan")


class EmailQueue(Base):
    __tablename__ = "email_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gmail_message_id = Column(String, unique=True, index=True, nullable=True)
    from_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body_preview = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="inbox")  # "inbox", "spam", "converted"
    is_important = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="email_items")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    reminder_type = Column(String, nullable=False)  # "5_days_before", "daily", "final_2_hours"
    scheduled_time = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)

    # Relationships
    task = relationship("Task", back_populates="reminders")
