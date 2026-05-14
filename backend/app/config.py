from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "JD Compass Agent")
    frontend_origin: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")

    search_max_results: int = int(os.getenv("SEARCH_MAX_RESULTS", "3"))
    search_region: str = os.getenv("SEARCH_REGION", "wt-wt")
    search_safe_search: str = os.getenv("SEARCH_SAFE_SEARCH", "off")
    search_backend: str = os.getenv("SEARCH_BACKEND", "lite")
    search_timeout_seconds: int = int(os.getenv("SEARCH_TIMEOUT_SECONDS", "4"))


settings = Settings()
