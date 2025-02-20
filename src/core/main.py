import asyncio
import threading
from queue import Queue
import signal

import uvloop
import uvicorn

from core.args import parse_args
from core.logger import init_logger, info, error, warn
from core.models import get_assets_models
from core.globals import BASE_DIR, SECRET_KEY
from core.app import App
from core.repositories.stats_repository import StatsRepository
from core.repositories.users_repository import UsersRepository
from core.stats import spawn_stats_worker


class Server(uvicorn.Server):
    """Custom uvicorn Server with graceful shutdown"""

    def __init__(self, app, host: str, port: int, stats_stop: threading.Event, stats_thread: threading.Thread):
        self.stats_stop = stats_stop
        self.stats_thread = stats_thread
        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            timeout_keep_alive=600,
            log_config=None
        )
        super().__init__(config)

    async def shutdown(self, sockets=None):
        """Graceful shutdown with stats worker cleanup"""

        # Stop stats worker
        if self.stats_stop and self.stats_thread:
            self.stats_stop.set()
            self.stats_thread.join(timeout=30)
            if self.stats_thread.is_alive():
                warn("Stats worker didn't finish in time - some stats might be lost")

        # Shutdown uvicorn
        await super().shutdown(sockets=sockets)


def setup_signal_handlers(server: Server):
    """Setup handlers for signals"""
    def handle_exit(signum, frame):
        info(f"Received exit signal {signal.Signals(signum).name}")
        asyncio.create_task(server.shutdown())

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


def main():
    if not SECRET_KEY:
        error("LLM_PROXY_SECRET is not set")
        return 1

    args = parse_args()
    init_logger(args.DEBUG)
    info("Logger initialized")

    a_models = get_assets_models(BASE_DIR)
    if not a_models.model_list:
        error("No models available. Exiting...")
        return 1

    db_dir = BASE_DIR / "db"
    db_dir.mkdir(parents=True, exist_ok=True)

    users_repository = UsersRepository(db_dir / "users.db")
    stats_repository = StatsRepository(db_dir / "stats.db")

    stats_queue = Queue()
    stats_stop, stats_thread = spawn_stats_worker(stats_queue, stats_repository)

    app = App(
        a_models,
        stats_queue,
        users_repository,
        docs_url=None,
        redoc_url=None
    )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    server = Server(
        app=app,
        host=args.host,
        port=args.port,
        stats_stop=stats_stop,
        stats_thread=stats_thread
    )

    setup_signal_handlers(server)

    server.run()
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
