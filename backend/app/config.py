from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / 'backend'
DATA_DIR = BACKEND_DIR / 'data'
EXPORT_DIR = BASE_DIR / 'exports' / 'generated'
SAMPLE_DIR = BASE_DIR / 'sample_data'


class Settings(BaseSettings):
    app_name: str = 'Pharmacy Stock Sync'
    database_url: str = f"sqlite:///{(DATA_DIR / 'pharmacy_stock_sync.db').as_posix()}"
    primary_shopify_location_pattern: str = '310A'
    auto_accept_threshold: int = 85
    review_threshold: int = 50
    reserve_stock_buffer: int = 0
    ai_enabled: bool = False
    ai_provider: str = 'disabled'
    ai_model: str = 'disabled'

    model_config = SettingsConfigDict(env_file='.env', extra='ignore')


settings = Settings()
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
