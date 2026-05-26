import sys
from pathlib import Path

# Configurar encoding utf-8 para consola en Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Añadir el directorio raíz al path para permitir ejecuciones directas sin problemas de empaquetado
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.application.services.abandoned_dependency_analyzer_service import (
    AbandonedDependencyAnalyzerService,
)
from app.application.services.dependency_normalizer_service import DependencyNormalizerService
from app.application.services.executive_summary_service import ExecutiveSummaryService
from app.application.services.insecure_version_rule_service import InsecureVersionRuleService
from app.application.services.outdated_dependency_analyzer_service import (
    OutdatedDependencyAnalyzerService,
)
from app.application.services.project_discovery_service import ProjectDiscoveryService
from app.application.services.recommendation_service import RecommendationService
from app.application.services.risk_score_calculator_service import RiskScoreCalculatorService
from app.application.services.version_parser_service import VersionParserService
from app.application.use_cases.audit_dependencies_use_case import AuditDependenciesUseCase
from app.config.settings import Settings
from app.infrastructure.exporters.excel_report_exporter import ExcelReportExporter
from app.infrastructure.exporters.json_report_exporter import JsonReportExporter
from app.infrastructure.exporters.pdf_report_exporter import PdfReportExporter
from app.infrastructure.filesystem.directory_manager import DirectoryManager
from app.infrastructure.providers.osv_vulnerability_provider import OsvVulnerabilityProvider
from app.infrastructure.providers.package_registry_provider import PackageRegistryProvider
from app.presentation.cli import CLI


def main() -> None:
    # 1. Cargar configuraciones
    settings = Settings()

    # 2. Inicializar componentes de infraestructura
    dir_manager = DirectoryManager(settings)

    osv_provider = OsvVulnerabilityProvider(settings)
    registry_provider = PackageRegistryProvider(settings)

    exporters = [
        JsonReportExporter(settings),
        ExcelReportExporter(settings),
        PdfReportExporter(settings),
    ]

    # 3. Inicializar servicios de aplicación
    discovery_service = ProjectDiscoveryService(settings)
    normalizer_service = DependencyNormalizerService()
    version_parser = VersionParserService()

    insecure_rule_service = InsecureVersionRuleService(version_parser, settings)
    outdated_analyzer = OutdatedDependencyAnalyzerService(version_parser)
    abandoned_analyzer = AbandonedDependencyAnalyzerService(settings)
    risk_calculator = RiskScoreCalculatorService(settings)
    recommendation_service = RecommendationService()
    summary_service = ExecutiveSummaryService()

    from app.application.services.vulnerability_analyzer_service import VulnerabilityAnalyzerService

    vuln_analyzer = VulnerabilityAnalyzerService(osv_provider, settings)

    # 4. Inyectar dependencias al caso de uso principal (Inversión de Dependencias)
    use_case = AuditDependenciesUseCase(
        directory_manager=dir_manager,
        discovery_service=discovery_service,
        normalizer_service=normalizer_service,
        vulnerability_analyzer=vuln_analyzer,
        insecure_version_rule_service=insecure_rule_service,
        outdated_analyzer=outdated_analyzer,
        abandoned_analyzer=abandoned_analyzer,
        risk_calculator=risk_calculator,
        recommendation_service=recommendation_service,
        executive_summary_service=summary_service,
        registry_provider=registry_provider,
        exporters=exporters,
        settings=settings,
    )

    # 5. Ejecutar la capa de presentación CLI
    cli = CLI(use_case)
    cli.run()


if __name__ == "__main__":
    main()
