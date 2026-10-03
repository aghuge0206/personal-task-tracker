# binds all 5 api routers into a single application, configures security headers, automatically creates database tables if they don't exist, and configures and launches the web server. This is the main entrypoint for the backend server

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import auth, categories, tasks, voice, email_queue

# create all database tables if they don't already exist, based on the SQLAlchemy models defined in app/models.py
Base.metadata.create_all(bind=engine)

# create the master fastapi app instance that manages all web requests
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",  # Interactive Swagger API documentation UI
    redoc_url="/redoc" # Alternative ReDoc API documentation UI
)

# Configure Cross-Origin Resource Sharing (CORS) Middleware, a mandatory browser security mechanism
# Allows the React frontend running on port 5173 to safely make API calls to this backend server on port 8000
# allows for cross port communication basically
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins during local development
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET, POST, PUT, DELETE HTTP verbs
    allow_headers=["*"],
)

# bind all api routers to the main app instance, with the URL prefix /api/v1 for all endpoints
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(categories.router, prefix=settings.API_V1_STR)
app.include_router(tasks.router, prefix=settings.API_V1_STR)
app.include_router(voice.router, prefix=settings.API_V1_STR)
app.include_router(email_queue.router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    """Root Server Status Endpoint: Returns welcome message and link to interactive API documentation."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API!",
        "version": settings.VERSION,
        "docs": "/docs" # provide a link to the interactive Swagger API documentation UI, on here i can test all the endpoints and see the request/response formats
    }
