from typing import Any

from app.application.services.version_parser_service import VersionParserService
from app.domain.entities.dependency import Dependency
from app.domain.value_objects.update_type import UpdateType


class OutdatedDependencyAnalyzerService:
    """Detecta dependencias desactualizadas y evalúa la dificultad y el riesgo de actualización."""

    def __init__(self, version_parser: VersionParserService):
        self.version_parser = version_parser

    def analyze_outdated(self, dependency: Dependency, latest_version: str | None) -> dict[str, Any] | None:
        """Compara la versión instalada con la última versión recomendada."""
        if not latest_version or latest_version == "0.0.0" or dependency.installed_version == "0.0.0":
            return None

        installed = dependency.installed_version.strip()
        latest = latest_version.strip()

        if installed == latest:
            return None

        # Parsear ambas versiones
        inst_major, inst_minor, inst_patch, _ = self.version_parser.parse_version_parts(installed)
        lat_major, lat_minor, lat_patch, _ = self.version_parser.parse_version_parts(latest)

        # Comprobar si efectivamente la última versión es más nueva
        is_newer = (
            lat_major > inst_major
            or (lat_major == inst_major and lat_minor > inst_minor)
            or (lat_major == inst_major and lat_minor == inst_minor and lat_patch > inst_patch)
        )

        if not is_newer:
            return None

        # Clasificar la distancia de actualización
        if lat_major > inst_major:
            update_type = UpdateType.MAJOR
            update_risk = "HIGH"
            action = (
                f"Actualización mayor de v{installed} a v{latest}. Puede contener breaking changes. "
                "Requiere revisión exhaustiva y pruebas completas de integración."
            )
        elif lat_minor > inst_minor:
            update_type = UpdateType.MINOR
            update_risk = "MEDIUM"
            action = (
                f"Actualización menor de v{installed} a v{latest}. Típicamente añade funcionalidad "
                "sin romper compatibilidad. Se recomienda probar en entorno local/staging antes."
            )
        elif lat_patch > inst_patch:
            update_type = UpdateType.PATCH
            update_risk = "LOW"
            action = (
                f"Actualización de parche de v{installed} a v{latest}. Corrige errores o problemas "
                "menores. Bajo riesgo. Recomendado aplicar a la brevedad."
            )
        else:
            update_type = UpdateType.UNKNOWN
            update_risk = "LOW"
            action = f"Actualizar a la versión recomendada v{latest}."

        return {
            "dependency": dependency.name,
            "installed_version": installed,
            "recommended_version": latest,
            "update_type": update_type,
            "update_risk": update_risk,
            "action_suggested": action,
            "requires_testing": update_risk in ("HIGH", "MEDIUM"),
        }
