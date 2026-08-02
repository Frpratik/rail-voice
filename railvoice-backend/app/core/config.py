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
    otp_ttl_seconds: int = 300
    otp_length: int = 6
    sms_provider: str = "console"  # console | twilio | msg91
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    msg91_auth_key: str = ""
    msg91_template_id: str = ""
    msg91_sender_id: str = "RAILVC"

    google_client_id: str = ""
    google_oauth_mock_mode: bool = True
    google_auth_enabled: bool = True

    storage_backend: str = "local"  # local | s3
    local_storage_path: str = "storage/uploads"
    public_base_url: str = "http://localhost:8000"
    s3_endpoint: str = ""
    s3_bucket: str = "railvoice"
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_region: str = "ap-south-1"

    whatsapp_enabled: bool = True
    whatsapp_verify_token: str = "railvoice_whatsapp_token_2026"
    whatsapp_api_key: str = ""
    whatsapp_phone_number_id: str = ""

    rate_limit_enabled: bool = True
    rate_limit_backend: str = "auto"  # auto | memory | redis
    rate_limit_otp_per_minute: int = 5
    rate_limit_write_per_minute: int = 30
    rate_limit_default_per_minute: int = 120
    rate_limit_otp_per_mobile_per_hour: int = 5
    rate_limit_require_redis_in_production: bool = True

    @property
    def effective_otp_per_minute(self) -> int:
        # Mock OTP is for demos — don't brick persona switching with tight IP limits.
        if self.otp_mock_mode and not self.is_production:
            return max(self.rate_limit_otp_per_minute, 60)
        return self.rate_limit_otp_per_minute

    @property
    def effective_otp_per_mobile_per_hour(self) -> int:
        if self.otp_mock_mode and not self.is_production:
            return max(self.rate_limit_otp_per_mobile_per_hour, 120)
        return self.rate_limit_otp_per_mobile_per_hour

    anonymous_daily_issue_limit: int = 3
    issue_edit_window_minutes: int = 15
    max_photos_per_issue: int = 5

    s3_public_base_url: str = ""
    sla_hours_severity_1: int = 4
    sla_hours_severity_2: int = 12
    sla_hours_severity_3: int = 24
    sla_hours_severity_4: int = 48
    sla_hours_severity_5: int = 72

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def sla_hours_for_severity(self, severity: int) -> int:
        mapping = {
            1: self.sla_hours_severity_1,
            2: self.sla_hours_severity_2,
            3: self.sla_hours_severity_3,
            4: self.sla_hours_severity_4,
            5: self.sla_hours_severity_5,
        }
        return mapping.get(max(1, min(5, severity)), self.sla_hours_severity_3)

    @property
    def redis_url_effective(self) -> str | None:
        url = (self.redis_url or "").strip()
        return url or None

    @property
    def use_redis_rate_limit(self) -> bool:
        backend = self.rate_limit_backend.lower().strip()
        if backend == "memory":
            return False
        if backend == "redis":
            return True
        return bool(self.redis_url_effective)

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
        if not self.otp_mock_mode:
            provider = self.sms_provider.lower().strip()
            if provider == "console":
                errors.append("SMS_PROVIDER=console is not allowed in production")
            elif provider == "twilio":
                if not (self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number):
                    errors.append("Twilio credentials required when SMS_PROVIDER=twilio")
            elif provider == "msg91":
                if not (self.msg91_auth_key and self.msg91_template_id):
                    errors.append("MSG91 credentials required when SMS_PROVIDER=msg91")
            else:
                errors.append(f"Unknown SMS_PROVIDER={self.sms_provider}")
        if self.google_auth_enabled and not self.google_client_id.strip():
            errors.append("GOOGLE_CLIENT_ID required when GOOGLE_AUTH_ENABLED=true in production")
        if self.rate_limit_require_redis_in_production and not self.redis_url_effective:
            errors.append("REDIS_URL required in production when RATE_LIMIT_REQUIRE_REDIS_IN_PRODUCTION=true")
        return errors


settings = Settings()
