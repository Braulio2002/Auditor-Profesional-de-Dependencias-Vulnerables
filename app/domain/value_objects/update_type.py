from enum import StrEnum


class UpdateType(StrEnum):
    PATCH = "PATCH"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    UNKNOWN = "UNKNOWN"
