from app.application.services.version_parser_service import VersionParserService
from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel
from app.shared.constants import FINDING_OPEN_RANGE, FINDING_UNPINNED


class InsecureVersionRuleService:
    """Evalúa las dependencias contra reglas de seguridad de configuración y versiones."""

    def __init__(self, version_parser: VersionParserService, settings):
        self.version_parser = version_parser
        self.settings = settings

    def analyze_dependency_config(
        self, project_name: str, dependency: Dependency
    ) -> DependencyFinding | None:
        """Analiza la versión declarada de una dependencia directa y retorna un Finding si es insegura."""
        # Las indirectas no se declaran en el archivo de configuración directo, no aplica esta regla
        if not dependency.is_direct:
            return None

        declared = dependency.declared_version

        # 1. Comprobar si no está fijada (unpinned)
        if declared in ("*", "latest", "any", ""):
            score = self.settings.score_weights.get("version_unpinned", 30)
            return DependencyFinding(
                project=project_name,
                dependency=dependency,
                finding_type=FINDING_UNPINNED,
                severity=SeverityLevel.MEDIUM,
                risk_score=score,
                risk_level=RiskLevel.MEDIUM,
                impact="El uso de comodines permite la descarga automática de cualquier versión futura del paquete, lo cual incrementa exponencialmente el riesgo de supply chain si la biblioteca es comprometida o introduce breaking changes.",
                recommendation=f"Especificar una versión exacta (pin) para {dependency.name} en el archivo {dependency.source_file}.",
                references=[],
            )

        # 2. Comprobar si tiene comodines parciales o rangos demasiado abiertos (ej. >=1.0.0 sin límite superior)
        if self.version_parser.is_open_range(declared):
            score = self.settings.score_weights.get("open_range", 25)
            return DependencyFinding(
                project=project_name,
                dependency=dependency,
                finding_type=FINDING_OPEN_RANGE,
                severity=SeverityLevel.LOW,
                risk_score=score,
                risk_level=RiskLevel.LOW,
                impact="Un rango demasiado abierto o sin límite superior permite que actualizaciones mayores o menores con breaking changes o fallos de seguridad no testeados se instalen automáticamente.",
                recommendation=f"Fijar la versión con un operador más seguro (ej: ~= o pin exacto) y definir límites superiores claros en {dependency.source_file}.",
                references=[],
            )

        return None
