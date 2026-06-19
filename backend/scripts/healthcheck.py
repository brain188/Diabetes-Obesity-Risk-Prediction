#!/usr/bin/env python3
"""
Health check script for Docker containers.
"""

import sys
import requests

try:
    response = requests.get(
        "http://localhost:8000/health",
        timeout=5
    )
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "healthy":
            sys.exit(0)
except Exception as e:
    print(f"Health check failed: {e}")

sys.exit(1)