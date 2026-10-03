# this file is responsible for defining the configuration settings for the FastAPI application, including application metadata, cryptographic secret key, database URL, and other relevant settings. 
# The settings are defined using Pydantic's BaseSettings class, which allows for easy management of environment variables and default values.
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application Metadata
    PROJECT_NAME: str = "Personal Task & Project Tracker"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Cryptographic Secret Key for signing JSON Web Tokens (JWT)
    # In production, this value is read from environment variables (.env file)
    SECRET_KEY: str = "antigravity_secret_key_super_secure_change_in_production_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # Tokens expire after 7 days (10,080 minutes)

    # Database Uniform Resource Locator (URL) pointing to local SQLite database file
    DATABASE_URL: str = "sqlite:///./task_tracker.db"

    class Config:
        env_file = ".env"
        case_sensitive = True

# Instantiated settings object imported across the backend application
settings = Settings()
