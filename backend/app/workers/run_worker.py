import asyncio
import signal
from app.core.config import settings
from app.core.logging_config import setup_logging, logger
from app.db.mongo import DatabaseManager
from app.workers.job_worker import JobWorker


async def run():
    setup_logging()
    logger.info("Starting standalone Background Job Worker...")
    await DatabaseManager.connect_to_database()
    worker = JobWorker()

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received termination signal, shutting down worker...")
        worker.stop()
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            pass  # Windows signal handling

    worker_task = asyncio.create_task(worker.start())
    await stop_event.wait()
    await worker_task
    await DatabaseManager.close_database_connection()
    logger.info("Worker shutdown cleanly.")


if __name__ == "__main__":
    asyncio.run(run())
