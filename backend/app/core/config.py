from cryptography.fernet import Fernet
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRETS = {"change-me-in-production", "change-this-to-a-long-random-string", "replace-with-a-long-random-string", ""}


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # development | test | production
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/serviceflow"
    SECRET_KEY: str = "change-me-in-production"  # signs JWTs
    ENCRYPTION_KEY: str = ""  # Fernet key; encrypts ID document numbers at rest
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:8000"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    RATE_LIMIT_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @model_validator(mode="after")
    def validate_security(self):
        if self.ENCRYPTION_KEY:
            Fernet(self.ENCRYPTION_KEY.encode())  # raises ValueError if malformed
        if self.is_production:
            problems = []
            if self.SECRET_KEY in _INSECURE_SECRETS or len(self.SECRET_KEY) < 32:
                problems.append("SECRET_KEY must be a random string of at least 32 characters")
            if not self.ENCRYPTION_KEY:
                problems.append("ENCRYPTION_KEY is required (generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")")
            if "*" in self.cors_origins_list:
                problems.append("CORS_ORIGINS must not contain '*'")
            if problems:
                raise ValueError("Insecure production configuration: " + "; ".join(problems))
        return self


settings = Settings()
