# security vault that hashes passwords to make plaintext passwords unreadable, generates digitally signed jwt (json web tokens) for user auth, and verifies the user's identity on every incoming api request

import datetime
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models

# OAuth2 Scheme extractor looking for 'Authorization: Bearer <token>' header in incoming HTTP requests
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def hash_password(password: str) -> str:
    """Hashes a plain text password using native Bcrypt with random salt."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt() # bcrypt generates random salts for each hash to make it more secure and prevent rainbow table attacks by making every hash unique even for the same password
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if a plain text password matches a stored Bcrypt hash."""
    pwd_bytes = plain_password.encode('utf-8')
    hash_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pwd_bytes, hash_bytes)

# generates digitally signed JWT containing user identity and expiration timestamp
def create_access_token(data: dict, expires_delta: datetime.timedelta = None) -> str:
    """Generates a digitally signed JSON Web Token (JWT) containing user identity and expiration timestamp."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# function that verifies the JWT signature and fetches the logged-in User database record
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """FastAPI Dependency that verifies JWT token signature and fetches the logged-in User database record."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user
