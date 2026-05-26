from app.domain.entities.dependency import Dependency
from app.shared.text_utils import clean_dependency_name


class DependencyNormalizerService:
    """Normaliza nombres de dependencias y remueve duplicados dentro de un proyecto."""

    def normalize_and_deduplicate(self, dependencies: list[Dependency]) -> list[Dependency]:
        if not dependencies:
            return []

        normalized: dict[tuple[str, str], Dependency] = {}

        for dep in dependencies:
            name_normalized = clean_dependency_name(dep.name).lower()
            key = (name_normalized, dep.scope.value)

            if key not in normalized:
                # Normalizar el nombre de la propia entidad
                dep.name = name_normalized
                normalized[key] = dep
            else:
                existing = normalized[key]
                # Si la versión declarada o la instalada es más completa en la nueva dependencia, actualizarla.
                # Priorizar los datos obtenidos de lockfiles (que típicamente tienen is_direct=False o declared_version='indirect' pero tienen versión exacta)
                # O si la actual es indirecta y la nueva es directa (tiene declared_version de verdad).

                if existing.declared_version in (
                    "indirect",
                    "",
                    "*",
                ) and dep.declared_version not in ("indirect", "", "*"):
                    existing.declared_version = dep.declared_version
                    existing.is_direct = True

                if not existing.installed_version or existing.installed_version == "0.0.0":
                    if dep.installed_version and dep.installed_version != "0.0.0":
                        existing.installed_version = dep.installed_version

                # Mantener la información del archivo de origen más informativo
                if existing.source_file.endswith("lock") and not dep.source_file.endswith("lock"):
                    existing.source_file = dep.source_file

        return list(normalized.values())
