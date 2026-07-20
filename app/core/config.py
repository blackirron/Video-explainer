"""
Central place for all configuration.

Why this file exists:
- Every app you build will need API keys / secrets (Claude API key, etc).
- Hardcoding them in your code is how keys end up leaked on GitHub.
- This file reads them from environment variables (which come from a
  .env file locally, and from your host's dashboard when deployed).

You will basically NEVER need to touch this file when building new apps —
you just add new fields here if a new app needs a new secret/setting.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App identity ---
    app_name: str = "my-app"
    environment: str = "development"  # "development" | "production"

    # --- LLM provider switch ---
    # "groq"      -> free tier, no card required, used by default
    # "anthropic" -> switch to this once you have a paid Claude key
    llm_provider: str = "groq"

    # --- Secrets / API keys ---
    anthropic_api_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # --- Simple auth for your own API (see core/security.py) ---
    api_auth_token: str = "change-me-locally"

    # --- CORS: which frontends are allowed to call this backend ---
    allowed_origins: str = "*"  # comma-separated in .env, e.g. "http://localhost:3000,https://myapp.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Import this single object anywhere you need a setting:
#   from app.core.config import settings
#   settings.anthropic_api_key
settings = Settings()
