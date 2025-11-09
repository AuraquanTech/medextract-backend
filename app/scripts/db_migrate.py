#!/usr/bin/env python3
"""Database migration script - creates tables from SQLAlchemy models."""
import asyncio
from src.repositories.db import Base, engine

async def migrate():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())
