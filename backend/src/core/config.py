from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LinkForge URL Shortener"

    # --- PostgreSQL (Neon / Supabase / local Docker) ---
    DATABASE_URL: Optional[str] = None   # Full URL takes priority if set
    POSTGRES_USER: str = "linkforge_user"
    POSTGRES_PASSWORD: str = "linkforge_password"
    POSTGRES_DB: str = "linkforge_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @computed_field
    @property
    def ASYNC_DATABASE_URI(self) -> str:
        # If a full DATABASE_URL is provided (e.g. Neon/Supabase), use it directly
        if self.DATABASE_URL:
            # asyncpg does not support ?sslmode= or ?channel_binding= query params
            # Strip them and re-add SSL via the asyncpg-native ?ssl=require form
            base = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            # Remove incompatible params and keep only the base URL
            base = base.split("?")[0]
            return f"{base}?ssl=require"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # --- MongoDB (Atlas / Aiven) ---
    MONGODB_URI: str = "mongodb://admin:adminpassword@localhost:27017"
    MONGODB_DB: str = "linkforge_analytics"

    # --- Redis (Upstash / Aiven / local Docker) ---
    REDIS_URL: str = "redis://localhost:6379"
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None

    # --- Rate Limiting Tiers ---
    RATE_LIMIT_IP_CAPACITY: int = 60
    RATE_LIMIT_IP_REFILL: float = 1.0
    RATE_LIMIT_USER_FREE_CAPACITY: int = 100
    RATE_LIMIT_USER_FREE_REFILL: float = 1.67
    RATE_LIMIT_USER_PREMIUM_CAPACITY: int = 1000
    RATE_LIMIT_USER_PREMIUM_REFILL: float = 16.67

    # --- Kafka (Aiven with SSL, or local Docker plain-text) ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:29092"
    KAFKA_SASL_USERNAME: Optional[str] = None
    KAFKA_SASL_PASSWORD: Optional[str] = None
    # Path to the Aiven CA certificate (download from Aiven dashboard)
    KAFKA_SSL_CA_PATH: Optional[str] = None
    SCHEMA_REGISTRY_URL: Optional[str] = None

    @computed_field
    @property
    def KAFKA_SECURITY_PROTOCOL(self) -> str:
        """Returns SASL_SSL when Aiven credentials are set, PLAINTEXT for local Docker."""
        return "SASL_SSL" if self.KAFKA_SASL_USERNAME else "PLAINTEXT"

    @computed_field
    @property
    def KAFKA_SASL_MECHANISM(self) -> str:
        return "PLAIN" if self.KAFKA_SASL_USERNAME else "GSSAPI"

    # --- SMTP (Email) ---
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@linkforge.dev"
    FROM_NAME: str = "LinkForge"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://127.0.0.1:8000"

    # --- JWT ---
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Google OAuth 2.0 ---
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"

    # --- GitHub OAuth 2.0 ---
    GITHUB_OAUTH_CLIENT_ID: Optional[str] = None
    GITHUB_OAUTH_CLIENT_SECRET: Optional[str] = None
    GITHUB_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/oauth/github/callback"

    # --- Observability (OpenTelemetry, Prometheus, Loki, Tempo) ---
    ENVIRONMENT: str = "production"
    JAEGER_ENABLED: bool = False
    JAEGER_HOST: str = "localhost"
    JAEGER_PORT: int = 6831
    PROMETHEUS_ENABLED: bool = True
    LOKI_ENABLED: bool = True
    LOKI_URL: str = "https://logs-prod-028.grafana.net/loki/api/v1/push"
    LOKI_USERNAME: str = "1683438"
    LOKI_PASSWORD: Optional[str] = None
    OTEL_TRACES_EXPORTER: str = "otlp"
    OTEL_METRICS_EXPORTER: str = "prometheus"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_EXPORTER_OTLP_HEADERS: Optional[str] = None
    PROMETHEUS_REMOTE_WRITE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
