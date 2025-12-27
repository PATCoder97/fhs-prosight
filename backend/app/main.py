from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.routers import auth

app = FastAPI(
    title="FHS Pro Sight Backend",
    description="Backend service for FHS HR management system - Synchronize and manage employee data from HRS",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    # Security scheme for Swagger UI
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    },
)

# Configure OpenAPI security scheme (JWT Bearer token)
app.openapi_schema = None  # Reset schema cache


@app.get("/openapi.json", include_in_schema=False)
async def get_openapi():
    """Generate OpenAPI schema with security definitions"""
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    
    openapi_schema = get_openapi(
        title="FHS Pro Sight Backend API",
        version="1.0.0",
        description="Backend service for FHS HR management system with Role-Based Access Control",
        routes=app.routes,
    )
    
    # Add JWT Bearer security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from OAuth login. Include in Authorization header: `Authorization: Bearer <token>`",
        }
    }
    
    # Add role-based security scopes
    openapi_schema["info"]["x-security"] = {
        "user": "Regular user access",
        "mod": "Moderator access - can manage other users",
        "admin": "Administrator access - full system access",
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

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

# Import protected router after creating app instance
from app.routers import protected, users
app.include_router(protected.router, prefix="/api")
app.include_router(users.router, prefix="/api")
