import sqlite3
import asyncio
from pathlib import Path
from typing import List, Optional, Iterable
from functools import partial
from contextlib import contextmanager
from more_itertools import chunked
from pydantic import BaseModel


# Each record has 9 fields, SQLite has 999 var limit
# 999/9 ≈ 111, round down to 100 for safety
MAX_BATCH_SIZE = 100


class UsageStatRecord(BaseModel):
    user_id: int
    api_key: str
    model: str
    tokens_in: int
    tokens_out: int
    dollars_in: float
    dollars_out: float
    messages_cnt: int
    finish_reason: Optional[str] = None


class StatsRepository:
    def __init__(
            self,
            db_path: Path
    ):
        self.db_path = db_path
        # Run init_db synchronously since it's called only once during startup
        self._init_db()

    @contextmanager
    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        """Initialize SQLite database and create table if not exists."""
        with self._get_db_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_usage_stats (
                    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    api_key TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tokens_in INTEGER NOT NULL,
                    tokens_out INTEGER NOT NULL,
                    dollars_in REAL NOT NULL,
                    dollars_out REAL NOT NULL,
                    messages_cnt INTEGER NOT NULL,
                    finish_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    async def _run_in_thread(self, func, *args):
        """Run a blocking function in a thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args))

    def _insert_chunk_sync(self, records: List[UsageStatRecord]) -> bool:
        if not records:
            return True

        with self._get_db_connection() as conn:
            try:
                conn.executemany(
                    """
                    INSERT INTO llm_usage_stats (
                        user_id, api_key, model, tokens_in, tokens_out,
                        dollars_in, dollars_out, messages_cnt, finish_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            record.user_id,
                            record.api_key,
                            record.model,
                            record.tokens_in,
                            record.tokens_out,
                            record.dollars_in,
                            record.dollars_out,
                            record.messages_cnt,
                            record.finish_reason
                        )
                        for record in records
                    ]
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False

    async def insert_batch(self, records: Iterable[UsageStatRecord]) -> bool:
        if not records:
            return True

        for chunk in chunked(records, MAX_BATCH_SIZE):
            success = await self._run_in_thread(self._insert_chunk_sync, chunk)
            if not success:
                return False
        return True


    async def get_user_stats(self):
        """Get aggregated statistics per user."""

        def _get_stats_sync():
            with self._get_db_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        user_id,
                        COUNT(*) as total_requests,
                        SUM(tokens_in) as total_tokens_in,
                        SUM(tokens_out) as total_tokens_out,
                        SUM(dollars_in) as total_dollars_in,
                        SUM(dollars_out) as total_dollars_out,
                        SUM(messages_cnt) as total_messages,
                        GROUP_CONCAT(DISTINCT model) as models_used
                    FROM llm_usage_stats
                    GROUP BY user_id
                    ORDER BY total_dollars_out DESC
                """)
                return cursor.fetchall()

        return await self._run_in_thread(_get_stats_sync)
