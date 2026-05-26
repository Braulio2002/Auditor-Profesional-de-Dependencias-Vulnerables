import re
from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderError
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.text_utils import clean_dependency_name


class GoDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema Go (go.mod)."""

    def read(self, file_path: Path) -> list[Dependency]:
        if not file_path.exists():
            raise ReaderError(f"El archivo {file_path} no existe.")

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise ReaderError(f"Error leyendo go.mod en {file_path}: {e}") from e

        dependencies: list[Dependency] = []

        # Regex para capturar dependencias de Go
        # Formato: module_name vX.Y.Z-modifier // indirect o sin comentario
        # Ejemplos:
        # github.com/gin-gonic/gin v1.7.2
        # github.com/mattn/go-isatty v0.0.12 // indirect
        dep_pattern = re.compile(r"^\s*([a-zA-Z0-9.\-_/]+)\s+(v[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9.\-_]*)(.*)")

        for line in lines:
            line = line.strip()
            # Ignorar definición de módulo principal o versión de Go
            if line.startswith("module") or line.startswith("go ") or line.startswith("require (") or line == ")":
                continue

            match = dep_pattern.match(line)
            if match:
                module_name, version, rest = match.groups()
                clean_name = clean_dependency_name(module_name)

                is_indirect = " // indirect" in rest or "//indirect" in rest

                is_pinned = not any(c in version for c in ["+incompatible", "latest"])

                dependencies.append(
                    Dependency(
                        name=clean_name,
                        ecosystem=Ecosystem.GO,
                        declared_version=version,
                        installed_version=version,
                        # Go no tiene clasificación de dev nativa en go.mod
                        scope=DependencyScope.PRODUCTION,
                        source_file=file_path.name,
                        is_direct=not is_indirect,
                        is_pinned=is_pinned,
                    )
                )

        return dependencies
