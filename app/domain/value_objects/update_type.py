from enum import Enum


class UpdateType(str, Enum):
    PATCH = "PATCH"
    MINOR = "MINOR"
    MAJOR = "MAJOR"
    UNKNOWN = "UNKNOWN"
