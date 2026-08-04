from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_root: Path = Path(__file__).resolve().parents[1]
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_exp_hours: int = 72
    cors_origins: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"
    business_outputs_root: Path | None = None
    opportunity_workspace_root: Path | None = None

    @property
    def outputs_root(self) -> Path:
        return self.business_outputs_root or (self.app_root / "business_build_outputs")

    @property
    def workspaces_root(self) -> Path:
        return self.opportunity_workspace_root or (self.app_root / "opportunity_workspaces")

    @property
    def local_users_path(self) -> Path:
        return self.outputs_root / "local_users.json"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()


def _render_public_url() -> str:
    # Prefer custom domain so OAuth redirects never use localhost / wrong host.
    return (
        os.getenv("PUBLIC_APP_URL")
        or os.getenv("FRONTEND_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or ""
    ).strip().rstrip("/")


_public = _render_public_url()
if _public:
    settings.frontend_url = (os.getenv("FRONTEND_URL") or _public).strip().rstrip("/") or _public
    if not (os.getenv("CORS_ORIGINS") or "").strip():
        settings.cors_origins = _public
    elif "iidatech.biz" in _public and "iidatech.biz" not in settings.cors_origins:
        settings.cors_origins = f"{settings.cors_origins},{_public}"

settings.outputs_root.mkdir(parents=True, exist_ok=True)
settings.workspaces_root.mkdir(parents=True, exist_ok=True)
