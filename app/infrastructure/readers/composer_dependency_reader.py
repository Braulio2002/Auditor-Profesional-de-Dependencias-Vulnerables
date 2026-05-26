import json
from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderException
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.logger import logger
from app.shared.text_utils import clean_dependency_name


class ComposerDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema PHP (Composer)."""

    def read(self, file_path: Path) -> list[Dependency]:
        if not file_path.exists():
            raise ReaderException(f"El archivo {file_path} no existe.")

        if file_path.name != "composer.json":
            file_path = file_path.parent / "composer.json"
            if not file_path.exists():
                return []

        try:
            with open(file_path, encoding="utf-8") as f:
                composer_data = json.load(f)
        except Exception as e:
            raise ReaderException(f"Error decodificando composer.json en {file_path}: {e}")

        # Cargar composer.lock para obtener versiones instaladas y dependencias indirectas
        lock_info = self._load_lockfile_info(file_path.parent)

        dependencies: list[Dependency] = []

        # Mapeo de scopes en composer.json
        scopes_mapping = {
            "require": DependencyScope.PRODUCTION,
            "require-dev": DependencyScope.DEVELOPMENT,
        }

        for json_key, scope in scopes_mapping.items():
            deps_dict = composer_data.get(json_key, {})
            if not isinstance(deps_dict, dict):
                continue

            for name, declared_ver in deps_dict.items():
                # Ignorar especificación de versión de PHP o extensiones PHP comunes (ej: "ext-json")
                if name.lower() == "php" or name.startswith("ext-"):
                    continue

                clean_name = clean_dependency_name(name)

                # Obtener versión instalada real del lockfile si existe
                installed_ver = lock_info.get(clean_name, {}).get("version", "")
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
                        source_file=file_path.name,
                        is_direct=True,
                        is_pinned=is_pinned,
                    )
                )

        # Agregar indirectas desde composer.lock
        direct_names = {dep.name for dep in dependencies}
        for name, info in lock_info.items():
            if name not in direct_names:
                dependencies.append(
                    Dependency(
                        name=name,
                        ecosystem=Ecosystem.COMPOSER,
                        declared_version="indirect",
                        installed_version=info.get("version", "0.0.0"),
                        scope=DependencyScope.DEVELOPMENT
                        if info.get("is_dev", False)
                        else DependencyScope.PRODUCTION,
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
            logger.warning(f"No se pudo parsear composer.lock en {lock_path}: {e}")

        return packages
