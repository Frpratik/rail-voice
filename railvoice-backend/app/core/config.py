from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RailVoice"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    database_url: str = "postgresql+asyncpg://railvoice:railvoice@localhost:5432/railvoice"
    database_url_sync: str = "postgresql://railvoice:railvoice@localhost:5432/railvoice"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    celery_enabled: bool = True

    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    duplicate_similarity_threshold: float = 0.82
    local_duplicate_similarity_threshold: float = 0.45
    spam_auto_hold_threshold: float = 0.85
    ai_sync_on_create: bool = True

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    otp_mock_mode: bool = True
    otp_mock_code: str = "123456"

    google_client_id: str = ""
    google_oauth_mock_mode: bool = True

    storage_backend: str = "local"  # local | s3
    local_storage_path: str = "storage/uploads"
    public_base_url: str = "http://localhost:8000"
    s3_endpoint: str = ""
    s3_bucket: str = "railvoice"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "ap-south-1"

    rate_limit_enabled: bool = True
    rate_limit_otp_per_minute: int = 5
    rate_limit_write_per_minute: int = 30
    rate_limit_default_per_minute: int = 120

    anonymous_daily_issue_limit: int = 3
    issue_edit_window_minutes: int = 15
    max_photos_per_issue: int = 5

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if not self.is_production:
            defaults = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3001",
            ]
            for origin in defaults:
                if origin not in origins:
                    origins.append(origin)
        return origins

    def validate_for_runtime(self) -> list[str]:
        """Return blocking configuration errors for the current environment."""
        errors: list[str] = []
        if not self.is_production:
            return errors

        weak_secrets = {"", "change-me", "change-me-to-a-long-random-string-in-production"}
        if self.secret_key.strip() in weak_secrets or len(self.secret_key) < 32:
            errors.append("SECRET_KEY must be a strong random string (32+ chars) in production")
        if self.otp_mock_mode:
            errors.append("OTP_MOCK_MODE must be false in production")
        if self.google_oauth_mock_mode:
            errors.append("GOOGLE_OAUTH_MOCK_MODE must be false in production")
        if not self.cors_origins.strip():
            errors.append("CORS_ORIGINS must be set in production")
        return errors


settings = Settings()
