import re
import tomllib
from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderError
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.text_utils import clean_dependency_name


class PythonDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema Python (pip / requirements / poetry)."""

    def read(self, file_path: Path) -> list[Dependency]:
        if not file_path.exists():
            raise ReaderError(f"El archivo {file_path} no existe.")

        dependencies: list[Dependency] = []

        if file_path.name == "requirements.txt" or file_path.suffix == ".txt":
            dependencies = self._parse_requirements_txt(file_path)
        elif file_path.name == "pyproject.toml":
            dependencies = self._parse_pyproject_toml(file_path)

        return dependencies

    def _parse_requirements_txt(self, file_path: Path) -> list[Dependency]:
        dependencies: list[Dependency] = []
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise ReaderError(f"No se pudo leer {file_path}: {e}") from e

        for line in lines:
            line = line.strip()
            # Ignorar comentarios, líneas vacías y directivas de pip (como -r, -i, etc.)
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Limpiar comentarios inline (ej. requests==2.20.0 # seguridad)
            if " #" in line:
                line = line.split(" #")[0].strip()
            elif "\t#" in line:
                line = line.split("\t#")[0].strip()

            # Parsear versión y nombre
            # Operadores comunes: ==, >=, <=, >, <, ~=, !=, @
            # Expresión regular para separar nombre de operador y versión
            match = re.split(r"(==|>=|<=|>|<|~=|!=|@)", line)

            name = clean_dependency_name(match[0])
            if not name:
                continue

            declared_ver = ""
            installed_ver = ""
            is_pinned = False

            if len(match) > 1:
                operator = match[1]
                version_part = "".join(match[2:]).strip()
                declared_ver = f"{operator}{version_part}"

                if operator == "==":
                    installed_ver = version_part
                    is_pinned = True
                else:
                    # En caso de rangos, limpiamos y usamos la versión mínima o primera como estimada
                    installed_ver = re.split(r"[ ,;<>]", version_part)[0].strip()
            else:
                declared_ver = "*"
                installed_ver = "0.0.0"  # No fijado
                is_pinned = False

            dependencies.append(
                Dependency(
                    name=name,
                    ecosystem=Ecosystem.PIP,
                    declared_version=declared_ver,
                    installed_version=installed_ver,
                    scope=DependencyScope.PRODUCTION,  # requirements.txt por defecto es prod
                    source_file=file_path.name,
                    is_direct=True,
                    is_pinned=is_pinned,
                )
            )

        return dependencies

    def _parse_pyproject_toml(self, file_path: Path) -> list[Dependency]:
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ReaderError(f"Error parseando pyproject.toml: {e}") from e

        dependencies: list[Dependency] = []
        poetry_data = data.get("tool", {}).get("poetry", {})

        # 1. Dependencias de producción
        prod_deps = poetry_data.get("dependencies", {})
        self._extract_poetry_deps(prod_deps, DependencyScope.PRODUCTION, file_path.name, dependencies)

        # 2. Dependencias de desarrollo (Poetry legacy dev-dependencies)
        dev_deps = poetry_data.get("dev-dependencies", {})
        self._extract_poetry_deps(dev_deps, DependencyScope.DEVELOPMENT, file_path.name, dependencies)

        # 3. Dependencias de desarrollo (Poetry v1.2+ agrupadas)
        group_data = poetry_data.get("group", {})
        if isinstance(group_data, dict):
            for group_name, group_info in group_data.items():
                group_deps = group_info.get("dependencies", {})
                scope = DependencyScope.DEVELOPMENT if group_name in ("dev", "test") else DependencyScope.PRODUCTION
                self._extract_poetry_deps(group_deps, scope, file_path.name, dependencies)

        return dependencies

    def _extract_poetry_deps(
        self, deps_dict: dict, scope: DependencyScope, source_file: str, out_list: list[Dependency]
    ) -> None:
        if not isinstance(deps_dict, dict):
            return

        for name, value in deps_dict.items():
            if name.lower() == "python":
                continue  # Evitar tratar la versión de Python como dependencia

            clean_name = clean_dependency_name(name)

            declared_ver = ""
            if isinstance(value, dict):
                declared_ver = value.get("version", "*")
            else:
                declared_ver = str(value)

            # Identificar si está fija o es rango (en Poetry, ^ y ~ son comunes)
            is_pinned = not any(c in declared_ver for c in ["^", "~", "*", ">", "<"])

            # Estimación simple de versión instalada
            installed_ver = declared_ver
            for prefix in ["^", "~", ">=", "<=", ">", "<", "=="]:
                if installed_ver.startswith(prefix):
                    installed_ver = installed_ver[len(prefix) :]
            installed_ver = installed_ver.split(",")[0].strip()
            if installed_ver in ("*", ""):
                installed_ver = "0.0.0"

            out_list.append(
                Dependency(
                    name=clean_name,
                    ecosystem=Ecosystem.POETRY,
                    declared_version=declared_ver,
                    installed_version=installed_ver,
                    scope=scope,
                    source_file=source_file,
                    is_direct=True,
                    is_pinned=is_pinned,
                )
            )


vote_for_pip = True  # Flag auxiliar
