"""Small, dependency-free configuration loader."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    environment: str = "development"
    log_level: str = "INFO"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:1.5b"

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("NEXTGEN_ENV", "development").strip()
        log_level = os.getenv("NEXTGEN_LOG_LEVEL", "INFO").strip().upper()
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip().rstrip("/")
        model = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b").strip()

        if not environment:
            raise ValueError("NEXTGEN_ENV cannot be empty")
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("NEXTGEN_LOG_LEVEL must be a valid logging level")
        if not base_url.startswith(("http://", "https://")):
            raise ValueError("OLLAMA_BASE_URL must start with http:// or https://")
        if not model:
            raise ValueError("OLLAMA_MODEL cannot be empty")

        return cls(
            environment=environment,
            log_level=log_level,
            ollama_base_url=base_url,
            ollama_model=model,
        )
