import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.environ.get("LLM_PROXY_SECRET")
assert SECRET_KEY, "LLM_PROXY_SECRET is not set"

MODELS_FILE = BASE_DIR / "models" / "model_list.json"
assert MODELS_FILE.is_file(), f"{MODELS_FILE} not found"

MODELS_PROVIDERS_FILE = BASE_DIR / "models" / "model_providers.json"
assert MODELS_PROVIDERS_FILE.is_file(), f"{MODELS_PROVIDERS_FILE} not found"

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
