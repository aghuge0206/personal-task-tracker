from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, auth

# Create the Authentication API Router with URL prefix /auth
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Default 3 life domains seeded automatically when a new user registers an account
DEFAULT_DOMAINS = [
    {"name": "Personal", "icon": "👤", "color": "#EC4899", "order": 1},
    {"name": "Coursework", "icon": "📚", "color": "#8B5CF6", "order": 2},
    {"name": "Student Organizations", "icon": "👥", "color": "#10B981", "order": 3},
]

@router.post("/register", response_model=schemas.Token, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserRegister, db: Session = Depends(get_db)):
    """User Registration API Endpoint: Registers new user, seeds default 3 domains, and returns JWT token."""
    # 1. Check if user email address already exists in the database
    existing_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # 2. Hash password securely using Bcrypt salting
    hashed_pwd = auth.hash_password(user_in.password)
    new_user = models.User(email=user_in.email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3. Seed default 3 life domains for user's workflow
    for domain in DEFAULT_DOMAINS:
        cat = models.Category(
            user_id=new_user.id,
            name=domain["name"],
            icon=domain["icon"],
            color=domain["color"],
            order=domain["order"]
        )
        db.add(cat)
    db.commit()

    # 4. Generate JWT Access Token
    access_token = auth.create_access_token(data={"sub": str(new_user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": new_user}


@router.post("/login", response_model=schemas.Token)
def login_user(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    """User Login API Endpoint: Verifies user credentials and returns JWT token."""
    user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if not user or not auth.verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email credentials or password."
        )

    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    """User Profile API Endpoint: Returns authenticated current user profile info."""
    return current_user
