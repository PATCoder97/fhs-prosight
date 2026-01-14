from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from app.core.config import settings
from app.routers import auth, users, employees, hrs_data, evaluations, dormitory_bills, pidms

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

# Register API routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(employees.router, prefix="/api")
app.include_router(hrs_data.router, prefix="/api")
app.include_router(evaluations.router, prefix="/api")
app.include_router(dormitory_bills.router, prefix="/api")
app.include_router(pidms.router, prefix="/api")

# Serve frontend static files
static_dir = Path("/app/static")
if static_dir.exists():
    # Mount static files (CSS, JS, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """
        Serve frontend SPA for all routes except /api, /docs, /redoc
        This allows Vue Router to handle client-side routing
        """
        # Don't intercept API routes, docs, or static assets
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "assets/")):
            return {"error": "Not found"}

        # Serve index.html for all other routes
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))

        return {"error": "Frontend not built. Run 'npm run build' in frontend directory."}
