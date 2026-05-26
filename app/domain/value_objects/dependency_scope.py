from enum import StrEnum


class DependencyScope(StrEnum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    OPTIONAL = "OPTIONAL"
    PEER = "PEER"
    UNKNOWN = "UNKNOWN"
