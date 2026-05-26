import json
from pathlib import Path
from typing import Any

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderError
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.logger import logger
from app.shared.text_utils import clean_dependency_name


class ComposerDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema PHP (Composer)."""

    COMPOSER_JSON = "composer.json"

    def read(self, file_path: Path) -> list[Dependency]:
        composer_data = self._load_composer_json(file_path)
        if not composer_data:
            return []

        actual_composer_file = file_path
        if file_path.name != self.COMPOSER_JSON:
            actual_composer_file = file_path.parent / self.COMPOSER_JSON

        # Cargar composer.lock
        # para obtener las versiones instaladas
        # y dependencias indirectas
        lock_info = self._load_lockfile_info(actual_composer_file.parent)

        dependencies = self._parse_direct_dependencies(composer_data, lock_info, actual_composer_file.name)

        # Agregar indirectas desde composer.lock
        direct_names = {dep.name for dep in dependencies}
        indirect_deps = self._parse_indirect_dependencies(lock_info, direct_names)
        dependencies.extend(indirect_deps)

        return dependencies

    def _load_composer_json(self, file_path: Path) -> dict[str, Any]:
        """Busca y carga de forma segura el archivo composer.json."""
        if not file_path.exists():
            raise ReaderError(f"El archivo {file_path} no existe.")

        if file_path.name != self.COMPOSER_JSON:
            file_path = file_path.parent / self.COMPOSER_JSON
            if not file_path.exists():
                return {}

        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ReaderError(f"Error decodificando composer.json en {file_path}: {e}") from e

    def _parse_direct_dependencies(
        self,
        composer_data: dict[str, Any],
        lock_info: dict[str, dict],
        file_name: str,
    ) -> list[Dependency]:
        """Parsea dependencias directas declaradas en composer.json."""
        dependencies: list[Dependency] = []
        scopes_mapping = {
            "require": DependencyScope.PRODUCTION,
            "require-dev": DependencyScope.DEVELOPMENT,
        }

        for json_key, scope in scopes_mapping.items():
            deps_dict = composer_data.get(json_key, {})
            if not isinstance(deps_dict, dict):
                continue

            for name, declared_ver in deps_dict.items():
                # Omitir PHP y extensiones ext-* en composer.json
                if name.lower() == "php" or name.startswith("ext-"):
                    continue

                clean_name = clean_dependency_name(name)

                # Obtener versión instalada real del lockfile si existe
                lock_package = lock_info.get(clean_name, {})
                installed_ver = lock_package.get("version", "")
                if not installed_ver:
                    installed_ver = self._clean_declared_version(declared_ver)

                is_pinned = not any(c in declared_ver for c in ["^", "~", "*", ">", "<"])

                dependencies.append(
                    Dependency(
                        name=clean_name,
                        ecosystem=Ecosystem.COMPOSER,
                        declared_version=declared_ver,
                        installed_version=installed_ver,
                        scope=scope,
                        source_file=file_name,
                        is_direct=True,
                        is_pinned=is_pinned,
                    )
                )
        return dependencies

    def _parse_indirect_dependencies(self, lock_info: dict[str, dict], direct_names: set[str]) -> list[Dependency]:
        """Mapea dependencias indirectas desde composer.lock."""
        dependencies: list[Dependency] = []
        for name, info in lock_info.items():
            if name not in direct_names:
                scope = DependencyScope.PRODUCTION
                if info.get("is_dev", False):
                    scope = DependencyScope.DEVELOPMENT

                dependencies.append(
                    Dependency(
                        name=name,
                        ecosystem=Ecosystem.COMPOSER,
                        declared_version="indirect",
                        installed_version=info.get("version", "0.0.0"),
                        scope=scope,
                        source_file="composer.lock",
                        is_direct=False,
                        is_pinned=True,
                    )
                )
        return dependencies

    def _clean_declared_version(self, declared_ver: str) -> str:
        clean_ver = declared_ver.strip()
        for prefix in ["^", "~", ">=", "<=", ">", "<"]:
            if clean_ver.startswith(prefix):
                clean_ver = clean_ver[len(prefix) :]
        return clean_ver.split(" ")[0].strip()

    def _load_lockfile_info(self, project_dir: Path) -> dict[str, dict]:
        """Carga las dependencias del composer.lock y su tipo."""
        lock_path = project_dir / "composer.lock"
        if not lock_path.exists():
            return {}

        packages: dict[str, dict] = {}
        try:
            with open(lock_path, encoding="utf-8") as f:
                lock_data = json.load(f)

            # Procesar producción y desarrollo
            for pkg in lock_data.get("packages", []):
                name = clean_dependency_name(pkg.get("name", ""))
                version = pkg.get("version", "").lstrip("v")
                if name:
                    packages[name] = {"version": version, "is_dev": False}

            for pkg in lock_data.get("packages-dev", []):
                name = clean_dependency_name(pkg.get("name", ""))
                version = pkg.get("version", "").lstrip("v")
                if name:
                    packages[name] = {"version": version, "is_dev": True}
        except Exception as e:
            logger.warning(
                "No se pudo parsear composer.lock en %s: %s",
                lock_path,
                e,
            )

        return packages
