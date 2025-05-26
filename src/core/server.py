import signal
import asyncio
from typing import List

import uvicorn

from core.logger import warn, info
from core.workers.w_abstract import Worker


class Server(uvicorn.Server):
    """Custom uvicorn Server with graceful shutdown"""

    def __init__(
            self,
            app,
            host: str,
            port: int,
            workers: List[Worker] = None,
    ):
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            timeout_keep_alive=600,
            log_config=None
        )
        super().__init__(config)
        self.workers = workers or []

    async def shutdown(self, sockets=None):
        """Graceful shutdown with stats worker cleanup"""

        for worker in self.workers:
            if worker.stop_event and worker.thread:
                worker.stop_event.set()
                worker.thread.join(timeout=5)
                if worker.thread.is_alive():
                    warn(f"{worker.name} didn't finish in time")

        # Shutdown uvicorn
        await super().shutdown(sockets=sockets)


def setup_signal_handlers(server: Server):
    """Setup handlers for signals"""
    def handle_exit(signum, frame):
        info(f"Received exit signal {signal.Signals(signum).name}")
        asyncio.create_task(server.shutdown())

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
