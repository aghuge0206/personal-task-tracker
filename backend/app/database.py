from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite database configuration setting for multi-threaded FastAPI execution
# SQLite by default blocks multi-thread access; check_same_thread=False allows FastAPI to process concurrent requests safely
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# Create the SQLAlchemy Database Engine (The core manager connection pool to the database)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True to print raw SQL commands to stdout for debugging
)

# SessionLocal is a factory class that generates temporary database session objects for transactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all database data models (User, Category, Task, etc.) inherit from
Base = declarative_base()

# FastAPI Dependency Generator function that creates a database session for each API request
# and automatically closes the connection when the request is complete
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
