"""Environment-driven configuration for the API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    parquet_path: Path
    manifest_path: Path
    model_dir: Path
    allowed_origins: tuple[str, ...]
    environment: str

    @classmethod
    def from_env(cls) -> "Settings":
        parquet = Path(
            os.environ.get(
                "DETENTIONS_PARQUET", str(ROOT / "data" / "processed" / "detentions.parquet")
            )
        )
        manifest = Path(
            os.environ.get(
                "MANIFEST_PATH", str(ROOT / "data" / "processed" / "manifest.json")
            )
        )
        model_dir = Path(
            os.environ.get("MODEL_DIR", str(ROOT / "artifacts" / "models"))
        )
        origins = tuple(
            origin.strip()
            for origin in os.environ.get(
                "ALLOWED_ORIGINS", "http://localhost:3000"
            ).split(",")
            if origin.strip()
        )
        return cls(
            parquet_path=parquet,
            manifest_path=manifest,
            model_dir=model_dir,
            allowed_origins=origins,
            environment=os.environ.get("APP_ENV", "development"),
        )


settings = Settings.from_env()
