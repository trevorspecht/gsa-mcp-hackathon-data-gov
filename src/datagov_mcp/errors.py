"""Stable errors contain no upstream response bodies or credential values."""


class ServiceError(Exception):
    def __init__(self, code: str, message: str, hint: str):
        super().__init__(message)
        self.code = code
        self.hint = hint

    def as_dict(self) -> dict:
        return {"error": {"code": self.code, "message": str(self), "hint": self.hint}}
