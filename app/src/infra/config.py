from pydantic import BaseModel, AnyHttpUrl, SecretStr, Field, validator
from functools import lru_cache
import os, yaml


class StripeCfg(BaseModel):
    webhook_secret: SecretStr
    api_key: SecretStr


class TwilioCfg(BaseModel):
    account_sid: SecretStr
    auth_token: SecretStr
    messaging_service_sid: SecretStr


class DbCfg(BaseModel):
    dsn: str = "postgresql+asyncpg://app:app@db:5432/medextract"


class RedisCfg(BaseModel):
    url: str = "redis://redis:6379/0"


class SecurityCfg(BaseModel):
    jwt_secret: SecretStr
    allowed_origins: list[AnyHttpUrl] = []


class AppCfg(BaseModel):
    env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    stripe: StripeCfg
    twilio: TwilioCfg
    db: DbCfg = DbCfg()
    redis: RedisCfg = RedisCfg()
    security: SecurityCfg
    enable_metrics: bool = True
    enable_tracing: bool = True


def _load_yaml(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


@lru_cache()
def get_settings() -> AppCfg:
    env = os.getenv("APP_ENV", "development")
    path = f"config/{env}.yaml"
    data = _load_yaml(path)
    # env overrides
    data.setdefault("stripe", {})
    data["stripe"]["webhook_secret"] = os.getenv("STRIPE_WEBHOOK_SECRET", data["stripe"].get("webhook_secret", ""))
    data["stripe"]["api_key"] = os.getenv("STRIPE_API_KEY", data["stripe"].get("api_key", ""))

    data.setdefault("twilio", {})
    data["twilio"]["account_sid"] = os.getenv("TWILIO_ACCOUNT_SID", data["twilio"].get("account_sid", ""))
    data["twilio"]["auth_token"] = os.getenv("TWILIO_AUTH_TOKEN", data["twilio"].get("auth_token", ""))
    data["twilio"]["messaging_service_sid"] = os.getenv("TWILIO_MSG_SERVICE_SID", data["twilio"].get("messaging_service_sid", ""))

    data.setdefault("security", {})
    data["security"]["jwt_secret"] = os.getenv("JWT_SECRET", data["security"].get("jwt_secret", ""))

    data.setdefault("db", {})
    data["db"]["dsn"] = os.getenv("DATABASE_DSN", data["db"].get("dsn", ""))

    data.setdefault("redis", {})
    data["redis"]["url"] = os.getenv("REDIS_URL", data["redis"].get("url", ""))

    return AppCfg(**data)
