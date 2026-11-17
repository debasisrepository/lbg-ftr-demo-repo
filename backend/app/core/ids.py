import uuid


class IdGenerator:
    @staticmethod
    def uuid4() -> uuid.UUID:
        return uuid.uuid4()

    @staticmethod
    def uuid_from_int(val: int) -> uuid.UUID:
        return uuid.UUID(int=val)
