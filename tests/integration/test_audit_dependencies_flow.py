from pathlib import Path

from app.application.interfaces.package_registry_provider_interface import (
    PackageRegistryProviderInterface,
)
from app.application.interfaces.vulnerability_provider_interface import (
    VulnerabilityProviderInterface,
)
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
from app.application.services.vulnerability_analyzer_service import VulnerabilityAnalyzerService
from app.application.use_cases.audit_dependencies_use_case import AuditDependenciesUseCase
from app.config.settings import Settings
from app.domain.entities.dependency import Dependency
from app.domain.entities.vulnerability import Vulnerability
from app.domain.value_objects.ecosystem import Ecosystem
from app.domain.value_objects.severity_level import SeverityLevel
from app.infrastructure.exporters.excel_report_exporter import ExcelReportExporter
from app.infrastructure.exporters.json_report_exporter import JsonReportExporter
from app.infrastructure.exporters.pdf_report_exporter import PdfReportExporter
from app.infrastructure.filesystem.directory_manager import DirectoryManager


class MockVulnerabilityProvider(VulnerabilityProviderInterface):
    def get_name(self) -> str:
        return "Mock Provider"

    def fetch_vulnerabilities(self, dependencies: list[Dependency]) -> dict[str, list[Vulnerability]]:
        # Si consultan lodash, retornar una vulnerabilidad crítica simulada
        results = {}
        for dep in dependencies:
            if dep.name.lower() == "lodash":
                results[dep.name.lower()] = [
                    Vulnerability(
                        vulnerability_id="CVE-2020-8203",
                        cve="CVE-2020-8203",
                        ghsa="GHSA-p6mc-m468-83gw",
                        severity=SeverityLevel.CRITICAL,
                        summary="Prototype pollution in lodash",
                        affected_versions="<4.17.21",
                        fixed_versions="4.17.21",
                        references=["https://nvd.nist.gov/vuln/detail/CVE-2020-8203"],
                    )
                ]
        return results


class MockRegistryProvider(PackageRegistryProviderInterface):
    def get_latest_version(self, name: str, ecosystem: Ecosystem) -> str:
        if name.lower() == "lodash":
            return "4.17.21"
        elif name.lower() == "requests":
            return "2.28.0"
        return "1.0.0"


def test_audit_dependencies_use_case_flow(tmp_path: Path):
    # Configurar directorios temporales de test
    settings = Settings()
    settings.datos_entrada_dir = tmp_path / "datos_entrada"
    settings.datos_salida_dir = tmp_path / "datos_salida"

    # 1. Componentes
    dir_manager = DirectoryManager(settings)
    discovery_service = ProjectDiscoveryService(settings)
    normalizer_service = DependencyNormalizerService()
    version_parser = VersionParserService()

    insecure_rule_service = InsecureVersionRuleService(version_parser, settings)
    outdated_analyzer = OutdatedDependencyAnalyzerService(version_parser)
    abandoned_analyzer = AbandonedDependencyAnalyzerService(settings)
    risk_calculator = RiskScoreCalculatorService(settings)
    recommendation_service = RecommendationService()
    summary_service = ExecutiveSummaryService()

    mock_provider = MockVulnerabilityProvider()
    mock_registry = MockRegistryProvider()

    vuln_analyzer = VulnerabilityAnalyzerService(mock_provider, settings)

    exporters = [
        JsonReportExporter(settings),
        ExcelReportExporter(settings),
        PdfReportExporter(settings),
    ]

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
        registry_provider=mock_registry,
        exporters=exporters,
        settings=settings,
    )

    # 2. Ejecutar Caso de Uso (Genera automáticamente los demos en la carpeta datos_entrada temporal de test)
    report = use_case.execute()

    # 3. Validaciones de Dominio
    assert len(report.projects) >= 3  # Node, Python, PHP demos
    assert len(report.dependencies) > 0
    assert len(report.findings) > 0
    assert report.summary["total_proyectos"] >= 3

    # Verificar que se reportó la vulnerabilidad de lodash
    lodash_vuln = [f for f in report.findings if f.dependency.name == "lodash" and "Vulnerabilidad" in f.finding_type]
    assert len(lodash_vuln) > 0
    assert lodash_vuln[0].severity == SeverityLevel.CRITICAL

    # 4. Validar archivos físicos generados en datos_salida/
    json_reports = list(settings.datos_salida_dir.glob("*.json"))
    xlsx_reports = list(settings.datos_salida_dir.glob("*.xlsx"))
    pdf_reports = list(settings.datos_salida_dir.glob("*.pdf")) or list(settings.datos_salida_dir.glob("*.txt"))

    assert len(json_reports) == 1
    assert len(xlsx_reports) == 1
    assert len(pdf_reports) == 1
