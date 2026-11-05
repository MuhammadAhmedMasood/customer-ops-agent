"""Settings read from environment variables (and the .env file, if present)."""

import os

from dotenv import load_dotenv

load_dotenv()

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:8000")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# How many proxies in front of the app append to X-Forwarded-For.
# 1 = Cloud Run only. 2 = Vercel in front of Cloud Run.
TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "1"))
