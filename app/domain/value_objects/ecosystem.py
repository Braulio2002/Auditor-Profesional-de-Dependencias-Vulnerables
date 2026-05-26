from enum import StrEnum


class Ecosystem(StrEnum):
    NPM = "npm"
    PIP = "pip"
    POETRY = "poetry"
    COMPOSER = "composer"
    MAVEN = "maven"
    GRADLE = "gradle"
    GO = "go"
