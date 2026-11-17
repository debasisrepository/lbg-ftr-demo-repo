import threading
import time
import logging
from app.database import SessionLocal
from app.services.heartbeat.scanner import HeartbeatScanner

logger = logging.getLogger(__name__)


class HeartbeatScheduler:
    SCAN_INTERVAL_SECONDS = 15 * 60

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("HeartbeatScheduler started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("HeartbeatScheduler stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._scan_and_update()
            except Exception as e:
                logger.error(f"HeartbeatScheduler error: {e}")
            time.sleep(self.SCAN_INTERVAL_SECONDS)

    def _scan_and_update(self):
        db = SessionLocal()
        try:
            scanner = HeartbeatScanner(db)
            scanner.scan_silent_cases()
        finally:
            db.close()


_scheduler_instance: HeartbeatScheduler | None = None


def get_scheduler() -> HeartbeatScheduler:
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = HeartbeatScheduler()
    return _scheduler_instance
