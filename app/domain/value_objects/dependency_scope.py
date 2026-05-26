from enum import Enum


class DependencyScope(str, Enum):
    PRODUCTION = "PRODUCTION"
    DEVELOPMENT = "DEVELOPMENT"
    TEST = "TEST"
    OPTIONAL = "OPTIONAL"
    PEER = "PEER"
    UNKNOWN = "UNKNOWN"
