from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Database - Individual components (optional if DATABASE_URL is provided)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DATABASE: Optional[str] = None

    # Database URL - can be provided directly or will be auto-constructed
    DATABASE_URL: Optional[str] = None

    def get_database_url(self) -> str:
        """Get DATABASE_URL - either from env or construct from POSTGRES_* variables"""
        # If DATABASE_URL is provided, use it
        if self.DATABASE_URL:
            # Ensure it uses async driver
            if self.DATABASE_URL.startswith('postgresql://'):
                return self.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
            return self.DATABASE_URL

        # Otherwise, construct from POSTGRES_* variables
        if not all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_DATABASE]):
            raise ValueError(
                "Either DATABASE_URL or all of (POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DATABASE) must be provided"
            )

        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE}"

    # JWT Settings (dùng cho cả access token và OTP verification)
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # CORS Origins
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Default Vite port
    ]

    # Token Expiry
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    PRE_AUTH_TOKEN_EXPIRE_MINUTES: int = 5  # 5 minutes

    # Google OAuth2
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # GitHub OAuth2
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str

    # FHS Integration
    FHS_HRS_BASE_URL: str = "https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr"
    FHS_AUTH_API_URL: str = "https://www.fhs.com.tw/fhs_covid_api/token"
    FHS_COVID_API_BASE_URL: str = (
        "https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail"
    )

    # PIDKey.com Integration
    PIDKEY_API_KEY: str = ""
    PIDKEY_BASE_URL: str = "https://pidkey.com/ajax/pidms_api"

    # Frontend & Cookie Settings
    FRONTEND_URL: str = "/"
    COOKIE_SECURE: bool = True
    COOKIE_DOMAIN: str = ""  # e.g., ".tphomelab.io.vn" for subdomain sharing

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    model_config = SettingsConfigDict(
        # Load .env từ:
        # 1. ".env" ở thư mục app/
        # 2. "../.env" ở thư mục backend/
        env_file=[".env", "../.env"],
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()
