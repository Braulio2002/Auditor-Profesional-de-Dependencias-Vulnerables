import xml.etree.ElementTree as ET
from pathlib import Path

from app.application.interfaces.dependency_file_reader_interface import (
    DependencyFileReaderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.exceptions.domain_exceptions import ReaderException
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.text_utils import clean_dependency_name


class MavenDependencyReader(DependencyFileReaderInterface):
    """Lector de dependencias para el ecosistema Java (Maven pom.xml)."""

    def read(self, file_path: Path) -> list[Dependency]:
        if not file_path.exists():
            raise ReaderException(f"El archivo {file_path} no existe.")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except Exception as e:
            raise ReaderException(f"Error parseando XML en {file_path}: {e}")

        # El espacio de nombres (namespace) de Maven es común en los pom.xml
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        # 1. Extraer propiedades definidas en <properties> para poder resolver variables
        properties: dict[str, str] = {}
        properties_el = root.find(f"{ns}properties")
        if properties_el is not None:
            for prop in properties_el:
                prop_tag = prop.tag.replace(ns, "") if ns else prop.tag
                if prop.text:
                    properties[prop_tag] = prop.text.strip()

        # Agregar propiedades integradas básicas del proyecto
        project_version_el = root.find(f"{ns}version")
        if project_version_el is not None and project_version_el.text:
            properties["project.version"] = project_version_el.text.strip()

        dependencies: list[Dependency] = []

        # Encontrar el bloque <dependencies>
        dependencies_el = root.find(f"{ns}dependencies")
        if dependencies_el is not None:
            for dep in dependencies_el.findall(f"{ns}dependency"):
                group_id_el = dep.find(f"{ns}groupId")
                artifact_id_el = dep.find(f"{ns}artifactId")
                version_el = dep.find(f"{ns}version")
                scope_el = dep.find(f"{ns}scope")

                if group_id_el is None or artifact_id_el is None:
                    continue

                group_id = group_id_el.text.strip() if group_id_el.text else ""
                artifact_id = artifact_id_el.text.strip() if artifact_id_el.text else ""

                # Nombre unificado para Maven: groupId:artifactId
                dep_name = f"{group_id}:{artifact_id}"
                clean_name = clean_dependency_name(dep_name)

                declared_ver = (
                    version_el.text.strip() if (version_el is not None and version_el.text) else ""
                )

                # Resolver variable si está definida (ej: ${jackson.version})
                resolved_ver = declared_ver
                if declared_ver.startswith("${") and declared_ver.endswith("}"):
                    prop_key = declared_ver[2:-1]
                    resolved_ver = properties.get(prop_key, declared_ver)

                if not resolved_ver:
                    resolved_ver = "0.0.0"  # Versión heredada o no especificada en pom directo (ej: de parent bom)

                scope_text = (
                    scope_el.text.strip().upper()
                    if (scope_el is not None and scope_el.text)
                    else "COMPILE"
                )

                # Mapeo de scopes Maven a Domain scopes
                scope = DependencyScope.PRODUCTION
                if scope_text == "TEST":
                    scope = DependencyScope.TEST
                elif scope_text in ("PROVIDED", "SYSTEM"):
                    scope = DependencyScope.OPTIONAL
                elif scope_text == "RUNTIME":
                    scope = DependencyScope.PRODUCTION

                is_pinned = not any(
                    c in resolved_ver for c in ["[", "]", "(", ")", "LATEST", "RELEASE", "SNAPSHOT"]
                )

                dependencies.append(
                    Dependency(
                        name=clean_name,
                        ecosystem=Ecosystem.MAVEN,
                        declared_version=declared_ver or "unspecified",
                        installed_version=resolved_ver,
                        scope=scope,
                        source_file=file_path.name,
                        is_direct=True,
                        is_pinned=is_pinned,
                    )
                )

        return dependencies
