#!/usr/bin/env python
"""Scribe backend runner for production deployment."""

import os
import sys

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
WORKERS = int(os.getenv("WORKERS", "2"))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        workers=WORKERS,
        log_level="info",
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
