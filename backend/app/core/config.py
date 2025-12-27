from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

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

    # FHS Integration
    FHS_HRS_BASE_URL: str = "https://www.fhs.com.tw/ads/api/Furnace/rest/json/hr"
    FHS_AUTH_API_URL: str = "https://www.fhs.com.tw/fhs_covid_api/token"
    FHS_COVID_API_BASE_URL: str = (
        "https://www.fhs.com.tw/fhs_covid_api/api/reportVaccines/detail"
    )

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
