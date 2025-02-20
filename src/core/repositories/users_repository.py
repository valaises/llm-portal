import sqlite3
import re
import asyncio
from pathlib import Path

from typing import List, Dict, Optional
from functools import partial
from contextlib import contextmanager

from pydantic import BaseModel, EmailStr


class ApiKeyCreatePost(BaseModel):
    api_key: Optional[str] = None
    scope: str
    tenant: EmailStr


class ApiKeyUpdatePost(BaseModel):
    api_key: str
    scope: Optional[str] = None
    tenant: Optional[str] = None


class UsersRepository:
    def __init__(
            self,
            db_path: Path
    ):
        self.db_path = db_path
        # Run init_db synchronously since it's called only once during startup
        self._init_db()

    @contextmanager
    def _get_db_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize SQLite database and create table if not exists."""
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    tenant TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    async def _run_in_thread(self, func, *args):
        """Run a blocking function in a thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args))

    def _list_keys_sync(self) -> List[Dict]:
        """Synchronous version of list_keys."""
        with self._get_db_connection() as conn:
            cursor = conn.execute("SELECT api_key, scope, tenant, created_at FROM api_keys")
            return [
                {
                    "api_key": row[0],
                    "scope": row[1],
                    "tenant": row[2],
                    "created_at": row[3]
                }
                for row in cursor.fetchall()
            ]

    def _create_key_sync(self, post: ApiKeyCreatePost) -> bool:
        """Synchronous version of create_key."""
        with self._get_db_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO api_keys (api_key, scope, tenant) VALUES (?, ?, ?)",
                    (post.api_key, post.scope, post.tenant)
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def _delete_key_sync(self, api_key: str) -> bool:
        """Synchronous version of delete_key."""
        with self._get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM api_keys WHERE api_key = ?",
                (api_key,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def _update_key_sync(self, post: ApiKeyUpdatePost) -> bool:
        """Synchronous version of update_key."""
        if post.tenant and not re.match(r"[^@]+@[^@]+\.[^@]+", post.tenant):
            raise ValueError("Invalid tenant email")

        updates = []
        values = []
        if post.scope:
            updates.append("scope = ?")
            values.append(post.scope)
        if post.tenant:
            updates.append("tenant = ?")
            values.append(post.tenant)

        if not updates:
            raise ValueError("No updates provided")

        values.append(post.api_key)
        update_query = f"UPDATE api_keys SET {', '.join(updates)} WHERE api_key = ?"

        with self._get_db_connection() as conn:
            cursor = conn.execute(update_query, values)
            conn.commit()
            return cursor.rowcount > 0

    async def list_keys(self) -> List[Dict]:
        """Get all API keys asynchronously."""
        return await self._run_in_thread(self._list_keys_sync)

    async def create_key(self, post: ApiKeyCreatePost) -> bool:
        """Create a new API key asynchronously."""
        return await self._run_in_thread(self._create_key_sync, post)

    async def delete_key(self, api_key: str) -> bool:
        """Delete an API key asynchronously."""
        return await self._run_in_thread(self._delete_key_sync, api_key)

    async def update_key(self, post: ApiKeyUpdatePost) -> bool:
        """Update an API key's scope or tenant asynchronously."""
        return await self._run_in_thread(self._update_key_sync, post)
