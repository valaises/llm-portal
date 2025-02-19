import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent.parent
API_KEY = os.environ.get('LLM_PROXY_API_KEY')