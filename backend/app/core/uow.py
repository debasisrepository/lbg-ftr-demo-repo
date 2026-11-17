from sqlalchemy.orm import Session


class UnitOfWork:
    def __init__(self, session: Session):
        self.session = session
        self._deferred_audit = []

    def defer_audit(self, entry):
        self._deferred_audit.append(entry)

    def commit(self):
        for entry in self._deferred_audit:
            self.session.add(entry)
        self.session.commit()
        self._deferred_audit.clear()

    def rollback(self):
        self.session.rollback()
        self._deferred_audit.clear()
