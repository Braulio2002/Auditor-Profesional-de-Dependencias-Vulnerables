import json
from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderException
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.text_utils import clean_dependency_name
from app.shared.logger import logger


class NpmDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema Node.js (NPM/Yarn/PNPM)."""

    def read(self, file_path: Path) -> list[Dependency]:
        if not file_path.exists():
            raise ReaderException(f"El archivo {file_path} no existe.")

        if file_path.name != "package.json":
            # Si nos pasan un lockfile, intentamos procesar el package.json correspondiente
            file_path = file_path.parent / "package.json"
            if not file_path.exists():
                return []

        try:
            with open(file_path, encoding="utf-8") as f:
                pkg_data = json.load(f)
        except Exception as e:
            raise ReaderException(f"Error decodificando package.json en {file_path}: {e}")

        # Intentar cargar package-lock.json para obtener las versiones reales instaladas
        lock_versions = self._load_lockfile_versions(file_path.parent)

        dependencies: list[Dependency] = []

        # Mapeo de campos de dependencias en package.json a scopes
        scopes_mapping = {
            "dependencies": DependencyScope.PRODUCTION,
            "devDependencies": DependencyScope.DEVELOPMENT,
            "peerDependencies": DependencyScope.PEER,
            "optionalDependencies": DependencyScope.OPTIONAL,
        }

        for json_key, scope in scopes_mapping.items():
            deps_dict = pkg_data.get(json_key, {})
            if not isinstance(deps_dict, dict):
                continue

            for name, declared_ver in deps_dict.items():
                clean_name = clean_dependency_name(name)
                # La versión instalada se extrae de package-lock.json si existe, o usamos la declarada limpia de comodines
                installed_ver = lock_versions.get(clean_name, "")
                if not installed_ver:
                    installed_ver = self._clean_declared_version(declared_ver)

                is_pinned = not any(c in declared_ver for c in ["^", "~", "*", ">", "<", "latest"])

                dependencies.append(
                    Dependency(
                        name=clean_name,
                        ecosystem=Ecosystem.NPM,
                        declared_version=declared_ver,
                        installed_version=installed_ver,
                        scope=scope,
                        source_file=file_path.name,
                        is_direct=True,
                        is_pinned=is_pinned,
                    )
                )

        # Agregar también dependencias indirectas desde package-lock.json que no estén en package.json
        direct_names = {dep.name for dep in dependencies}
        for name, inst_ver in lock_versions.items():
            if name not in direct_names:
                dependencies.append(
                    Dependency(
                        name=name,
                        ecosystem=Ecosystem.NPM,
                        declared_version="indirect",
                        installed_version=inst_ver,
                        scope=DependencyScope.PRODUCTION,  # Por defecto
                        source_file="package-lock.json",
                        is_direct=False,
                        is_pinned=True,
                    )
                )

        return dependencies

    def _clean_declared_version(self, declared_ver: str) -> str:
        """Remueve prefijos comunes de rango para dejar una versión limpia."""
        clean_ver = declared_ver.strip()
        for prefix in ["^", "~", ">=", "<=", ">", "<"]:
            if clean_ver.startswith(prefix):
                clean_ver = clean_ver[len(prefix) :]
        return clean_ver.split(" ")[0].strip()

    def _load_lockfile_versions(self, project_dir: Path) -> dict[str, str]:
        """Carga las versiones instaladas desde package-lock.json si existe."""
        lock_path = project_dir / "package-lock.json"
        if not lock_path.exists():
            return {}

        versions: dict[str, str] = {}
        try:
            with open(lock_path, encoding="utf-8") as f:
                lock_data = json.load(f)

            # Soporte para lockfile v2 y v3 (tienen sección 'packages')
            if "packages" in lock_data:
                for pkg_path, pkg_info in lock_data["packages"].items():
                    if not pkg_path:  # Ruta vacía es el proyecto raíz
                        continue
                    # Extraer el nombre del paquete (ej. "node_modules/lodash" -> "lodash")
                    name = pkg_path.replace("node_modules/", "")
                    # Manejar sub-carpetas en paquetes con scope
                    if "/" in name and not name.startswith("@"):
                        parts = name.split("node_modules/")
                        name = parts[-1]
                    version = pkg_info.get("version")
                    if name and version:
                        versions[clean_dependency_name(name)] = version
            # Soporte para lockfile v1 (sección 'dependencies')
            elif "dependencies" in lock_data:
                for name, info in lock_data["dependencies"].items():
                    version = info.get("version")
                    if name and version:
                        versions[clean_dependency_name(name)] = version
        except Exception as e:
            logger.warning(f"No se pudo parsear package-lock.json en {lock_path}: {e}")

        return versions
