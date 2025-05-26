import asyncio

from queue import Queue

import uvloop

from core.logger import init_logger, info
from core.globals import BASE_DIR
from core.app import App
from core.repositories.stats_repository import StatsRepository
from core.repositories.users_repository import UsersRepository
from core.server import Server
from core.workers.w_stats import spawn_worker as spawn_stats_worker


def main():
    init_logger(False)
    info("Logger initialized")

    db_dir = BASE_DIR / "db"
    db_dir.mkdir(parents=True, exist_ok=True)

    users_repository = UsersRepository(db_dir / "users.db")
    stats_repository = StatsRepository(db_dir / "stats.db")

    stats_queue = Queue()
    stats_worker = spawn_stats_worker(stats_queue, stats_repository)

    app = App(
        stats_queue,
        users_repository,
        docs_url=None,
        redoc_url=None
    )

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    server = Server(
        app=app,
        host="0.0.0.0",
        port=7012,
        workers=[
            stats_worker,
        ]
    )

    server.run()
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
