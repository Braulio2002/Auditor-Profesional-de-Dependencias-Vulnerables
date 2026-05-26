import re
from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderException
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.text_utils import clean_dependency_name


class GradleDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema Java/Kotlin (Gradle build.gradle / build.gradle.kts)."""

    def read(self, file_path: Path) -> list[Dependency]:
        if not file_path.exists():
            raise ReaderException(f"El archivo {file_path} no existe.")

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise ReaderException(f"Error leyendo archivo Gradle {file_path}: {e}")

        dependencies: list[Dependency] = []

        # 1. Regex para el formato compacto: configuration 'group:name:version' o configuration("group:name:version")
        # Ejemplo: implementation 'com.google.guava:guava:30.1-jre'
        compact_pattern = re.compile(
            r"^\s*([a-zA-Z0-9]+)\s*\(?\s*['\"]([^'\":]+):([^'\":]+):([^'\"]+)['\"]\s*\)?",
            re.MULTILINE,
        )

        # 2. Regex para formato de pares clave-valor: configuration group: '...', name: '...', version: '...'
        # Ejemplo: testImplementation group: 'junit', name: 'junit', version: '4.12'
        verbose_pattern = re.compile(
            r"^\s*([a-zA-Z0-9]+)\s*\(?\s*group\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*name\s*:\s*['\"]([^'\"]+)['\"]\s*,\s*version\s*:\s*['\"]([^'\"]+)['\"]\s*\)?",
            re.MULTILINE,
        )

        # Procesar coincidenas compactas
        for match in compact_pattern.finditer(content):
            config, group, name, version = match.groups()
            dependencies.append(
                self._build_dependency(config, group, name, version, file_path.name)
            )

        # Procesar coincidencias verbosas
        for match in verbose_pattern.finditer(content):
            config, group, name, version = match.groups()
            dependencies.append(
                self._build_dependency(config, group, name, version, file_path.name)
            )

        return dependencies

    def _build_dependency(
        self, config: str, group: str, name: str, version: str, source_file: str
    ) -> Dependency:
        dep_name = f"{group}:{name}"
        clean_name = clean_dependency_name(dep_name)

        # Mapear configuración de Gradle a Scope del Dominio
        config_lower = config.lower()
        scope = DependencyScope.PRODUCTION

        if "test" in config_lower:
            scope = DependencyScope.TEST
        elif "only" in config_lower:
            scope = DependencyScope.OPTIONAL

        is_pinned = not any(c in version for c in ["+", "LATEST", "RELEASE", "SNAPSHOT", "$"])

        return Dependency(
            name=clean_name,
            ecosystem=Ecosystem.GRADLE,
            declared_version=version,
            installed_version=version,
            scope=scope,
            source_file=source_file,
            is_direct=True,
            is_pinned=is_pinned,
        )
