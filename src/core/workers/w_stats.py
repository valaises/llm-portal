import threading

from asyncio import Queue
from queue import Empty
from typing import Iterable

from core.logger import info, warn
from core.repositories.stats_repository import StatsRepository, UsageStatRecord
from core.workers.w_abstract import Worker


def drain_queue(q: Queue) -> Iterable[UsageStatRecord]:
    try:
        while True:
            record = q.get_nowait()
            yield record
            q.task_done()
    except Empty:
        pass


def worker(
        queue: Queue,
        stop_event: threading.Event,
        stats_repository: StatsRepository
):
    """Worker that processes stats from queue and saves to database"""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        while not stop_event.is_set():
            records = []
            # Collect all available items from queue
            try:
                while True:
                    record = queue.get_nowait()
                    records.append(record)
                    queue.task_done()
            except Empty:
                pass

            # Save collected records
            if records:
                try:
                    loop.run_until_complete(
                        stats_repository.insert_batch(records)
                    )
                except Exception as e:
                    warn(f"Error saving stats batch: {e}")
                    for record in records:
                        queue.put(record)

            # Wait for more records or stop event
            stop_event.wait(1)

        try:
            info(f"Processing stats records before shutdown...")
            loop.run_until_complete(
                stats_repository.insert_batch(drain_queue(queue))
            )
            info("OK -- processed remaining records")
        except Exception as e:
            warn(f"Failed to save final batch: {e}")
    finally:
        loop.close()


def spawn_worker(
        queue: Queue,
        stats_repository: StatsRepository
) -> Worker:
    """
    Spawn a stats worker thread

    Returns:
        Tuple of (stop_event, thread)
    """
    stop_event = threading.Event()
    worker_thread = threading.Thread(
        target=worker,
        args=(queue, stop_event, stats_repository),
        daemon=True
    )
    worker_thread.start()

    return Worker("worker_stats", worker_thread, stop_event)
