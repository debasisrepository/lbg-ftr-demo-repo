"""Unit of work pattern for transactional consistency."""
from typing import Callable

from sqlalchemy.orm import Session


class UnitOfWork:
    """Encapsulates database session and after-commit callbacks."""

    def __init__(self, session: Session):
        self.session = session
        self._after_commit_callbacks: list[Callable] = []

    def after_commit(self, callback: Callable) -> None:
        """Register a callback to run after successful commit."""
        self._after_commit_callbacks.append(callback)

    def commit(self) -> None:
        """Commit transaction and run callbacks."""
        self.session.commit()
        for callback in self._after_commit_callbacks:
            try:
                callback()
            except Exception as e:
                # Log but don't re-raise - transaction already committed
                print(f"Error in after-commit callback: {e}")
        self._after_commit_callbacks.clear()

    def rollback(self) -> None:
        """Rollback transaction and clear callbacks."""
        self.session.rollback()
        self._after_commit_callbacks.clear()

    def flush(self) -> None:
        """Flush changes to database without committing."""
        self.session.flush()
