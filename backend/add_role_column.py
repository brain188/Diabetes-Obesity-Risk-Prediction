"""
Run this once to add the `role` column to healthcare_workers.
Usage:  python add_role_column.py
"""
import asyncio
import os
from pathlib import Path

# Load .env so DATABASE_URL is available
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import asyncpg

SQL = """
ALTER TABLE healthcare_workers
ADD COLUMN IF NOT EXISTS role VARCHAR(50) NOT NULL DEFAULT 'healthcare_worker';
"""

async def main():
    url = os.environ["DATABASE_URL"]
    # asyncpg needs postgresql:// not postgresql+asyncpg://
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    await conn.execute(SQL)
    await conn.close()
    print("Done — 'role' column added (or already existed).")

asyncio.run(main())
