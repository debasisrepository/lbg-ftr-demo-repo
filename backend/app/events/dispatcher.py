import threading
import time
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.events.repository import EventRepository
from app.events.registry import get_event_registry

logger = logging.getLogger(__name__)


class OutboxDispatcher:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("OutboxDispatcher started")

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("OutboxDispatcher stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._dispatch_batch()
            except Exception as e:
                logger.error(f"OutboxDispatcher error: {e}")
            time.sleep(2)

    def _dispatch_batch(self):
        db = SessionLocal()
        try:
            repo = EventRepository(db)
            entries = repo.get_pending_outbox_entries(limit=100)
            registry = get_event_registry()

            for outbox in entries:
                outbox_id = outbox.id
                event_id = outbox.event_id
                try:
                    event = repo.get_event_by_id(event_id)
                    if not event:
                        db.rollback()
                        db_session = SessionLocal()
                        try:
                            repo_fail = EventRepository(db_session)
                            repo_fail.mark_outbox_failed(outbox_id, "Event not found")
                            db_session.commit()
                        finally:
                            db_session.close()
                        continue

                    handlers = registry.get_handlers(event.event_type)
                    handler_errors = []
                    for handler in handlers:
                        try:
                            handler(event.id, event.payload)
                        except Exception as e:
                            logger.error(f"Handler error for event {event.id}: {e}")
                            handler_errors.append(str(e))

                    if handler_errors:
                        raise Exception("; ".join(handler_errors))

                    repo.mark_outbox_published(outbox_id)
                    db.commit()
                except Exception as e:
                    db.rollback()
                    db_session = SessionLocal()
                    try:
                        repo_fail = EventRepository(db_session)
                        repo_fail.mark_outbox_failed(outbox_id, str(e))
                        db_session.commit()
                    finally:
                        db_session.close()
        finally:
            db.close()


_dispatcher_instance: OutboxDispatcher | None = None


def get_dispatcher() -> OutboxDispatcher:
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = OutboxDispatcher()
    return _dispatcher_instance
