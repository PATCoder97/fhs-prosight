from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.routers import auth, users, employees, hrs_data, evaluations, dormitory_bills

app = FastAPI(
    title="FHS Pro Sight Backend",
    description="Backend service for FHS HR management system - Synchronize and manage employee data from HRS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add middleware - order matters! SessionMiddleware must be added first (but will be the last in the chain)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(hrs_data.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(dormitory_bills.router, prefix="/api")
