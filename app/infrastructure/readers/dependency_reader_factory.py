from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.exceptions.domain_exceptions import ReaderException
from app.infrastructure.readers.composer_dependency_reader import (
    ComposerDependencyReader,
)
from app.infrastructure.readers.go_dependency_reader import GoDependencyReader
from app.infrastructure.readers.gradle_dependency_reader import GradleDependencyReader
from app.infrastructure.readers.maven_dependency_reader import MavenDependencyReader
from app.infrastructure.readers.npm_dependency_reader import NpmDependencyReader
from app.infrastructure.readers.python_dependency_reader import PythonDependencyReader


class DependencyReaderFactory:
    """Factory para instanciar lectores de dependencias basados en el nombre de archivo."""

    @staticmethod
    def get_reader(file_path: Path) -> DependencyFileReaderInterface:
        filename = file_path.name

        if filename in (
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
        ):
            return NpmDependencyReader()
        elif filename in (
            "requirements.txt",
            "pyproject.toml",
            "poetry.lock",
        ) or filename.endswith(".txt"):
            return PythonDependencyReader()
        elif filename in ("composer.json", "composer.lock"):
            return ComposerDependencyReader()
        elif filename == "pom.xml":
            return MavenDependencyReader()
        elif filename in ("build.gradle", "build.gradle.kts"):
            return GradleDependencyReader()
        elif filename == "go.mod":
            return GoDependencyReader()

        raise ReaderException(
            f"No existe un lector configurado para el archivo: {filename}"
        )
