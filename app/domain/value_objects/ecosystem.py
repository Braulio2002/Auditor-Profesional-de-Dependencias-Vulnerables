from enum import Enum


class Ecosystem(str, Enum):
    NPM = "npm"
    PIP = "pip"
    POETRY = "poetry"
    COMPOSER = "composer"
    MAVEN = "maven"
    GRADLE = "gradle"
    GO = "go"
