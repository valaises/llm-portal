import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("LLM_PROXY_SECRET")
assert SECRET_KEY, "LLM_PROXY_SECRET is not set"