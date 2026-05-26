from typing import Any

from app.application.interfaces.package_registry_provider_interface import (
    PackageRegistryProviderInterface,
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
from app.application.services.vulnerability_analyzer_service import VulnerabilityAnalyzerService
from app.domain.entities.dependency_audit_report import DependencyAuditReport
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel
from app.infrastructure.filesystem.directory_manager import DirectoryManager
from app.infrastructure.readers.dependency_reader_factory import DependencyReaderFactory
from app.shared.date_utils import get_current_utc_iso
from app.shared.logger import logger


class AuditDependenciesUseCase:
    """Caso de uso principal (Orquestador de Aplicación) que ejecuta el flujo completo de auditoría."""

    def __init__(
        self,
        directory_manager: DirectoryManager,
        discovery_service: ProjectDiscoveryService,
        normalizer_service: DependencyNormalizerService,
        vulnerability_analyzer: VulnerabilityAnalyzerService,
        insecure_version_rule_service: InsecureVersionRuleService,
        outdated_analyzer: OutdatedDependencyAnalyzerService,
        abandoned_analyzer: AbandonedDependencyAnalyzerService,
        risk_calculator: RiskScoreCalculatorService,
        recommendation_service: RecommendationService,
        executive_summary_service: ExecutiveSummaryService,
        registry_provider: PackageRegistryProviderInterface,
        exporters: list[Any],
        settings,
    ):
        self.directory_manager = directory_manager
        self.discovery_service = discovery_service
        self.normalizer_service = normalizer_service
        self.vulnerability_analyzer = vulnerability_analyzer
        self.insecure_version_rule_service = insecure_version_rule_service
        self.outdated_analyzer = outdated_analyzer
        self.abandoned_analyzer = abandoned_analyzer
        self.risk_calculator = risk_calculator
        self.recommendation_service = recommendation_service
        self.executive_summary_service = executive_summary_service
        self.registry_provider = registry_provider
        self.exporters = exporters
        self.settings = settings

    def execute(self) -> DependencyAuditReport:
        logger.info("Iniciando auditoría técnica de seguridad...")

        # 1. Asegurar la existencia de directorios de entrada/salida y demos
        self.directory_manager.ensure_directories_exist()

        # 2. Descubrir proyectos en datos_entrada/
        projects = self.discovery_service.discover_projects()

        if not projects:
            return self._build_empty_report()

        all_dependencies: list[Any] = []
        all_findings: list[DependencyFinding] = []
        all_vulnerabilities = []
        errors = []

        # 3. Analizar cada proyecto
        for proj in projects:
            logger.info(f"Procesando proyecto: {proj.name}...")

            # Leer dependencias de los archivos del proyecto
            proj_deps = self._read_project_dependencies(proj, errors)

            # Normalizar y consolidar duplicaciones
            proj_deps_normalized = self.normalizer_service.normalize_and_deduplicate(proj_deps)
            all_dependencies.extend(proj_deps_normalized)

            # Consultar vulnerabilidades externas de red (con manejo de red offline)
            proj_vuln_findings = self.vulnerability_analyzer.analyze_vulnerabilities(
                proj.name, proj_deps_normalized, errors, all_vulnerabilities
            )
            all_findings.extend(proj_vuln_findings)

            # Analizar reglas internas (Offline y online)
            self._analyze_project_dependency_rules(proj.name, proj_deps_normalized, all_findings)

            # Calcular scoring numérico 0-100 por dependencias
            self._calculate_scoring_for_project(proj.name, proj_deps_normalized, all_findings)

        # 4. Calcular nivel de riesgo general consolidado
        overall_risk = self.risk_calculator.calculate_project_risk(all_findings)

        # 5. Estructurar reporte de auditoría completo
        report = DependencyAuditReport(
            metadata={
                "version": "1.0.0",
                "ambiente": "Auditoría de Supply Chain",
                "status": "success",
            },
            projects=projects,
            dependencies=all_dependencies,
            findings=all_findings,
            errors=errors,
            generated_at=get_current_utc_iso(),
        )

        # 6. Generar resúmenes y planes de mitigación
        report.summary = self.executive_summary_service.generate_summary(
            projects, all_dependencies, all_findings, errors, overall_risk
        )
        report.recommendations = self.recommendation_service.generate_recommendations(all_findings)

        # 7. Exportar reportes físicos en la carpeta datos_salida/
        self._export_reports(report, errors)

        return report

    def _build_empty_report(self) -> DependencyAuditReport:
        """Construye un reporte vacío cuando no se encuentran proyectos."""
        logger.info("No se encontraron proyectos ni archivos de dependencias compatibles para analizar.")
        report = DependencyAuditReport(metadata={"status": "empty"}, generated_at=get_current_utc_iso())
        report.summary = {
            "total_proyectos": 0,
            "total_dependencias": 0,
            "riesgo_general": "BAJO",
            "explicacion_riesgo": "No se encontraron dependencias para analizar.",
        }
        return report

    def _read_project_dependencies(self, proj, errors: list[dict[str, Any]]) -> list[Any]:
        """Lee y agrupa todas las dependencias declaradas en los archivos del proyecto."""
        proj_deps = []
        for file_path in proj.dependency_files:
            logger.info(f"Leyendo archivo de dependencias: {file_path.name}...")
            try:
                reader = DependencyReaderFactory.get_reader(file_path)
                raw_deps = reader.read(file_path)
                proj_deps.extend(raw_deps)
            except Exception as e:
                logger.error(f"Error procesando el archivo {file_path.name}: {e}")
                errors.append(
                    {
                        "proyecto": proj.name,
                        "archivo": file_path.name,
                        "tipo_error": e.__class__.__name__,
                        "mensaje_error": str(e),
                    }
                )
        return proj_deps

    def _analyze_project_dependency_rules(
        self, project_name: str, dependencies: list[Any], all_findings: list[DependencyFinding]
    ) -> None:
        """Audita cada dependencia respecto a reglas de configuración, versiones obsoletas y estado del registro."""
        for dep in dependencies:
            # A. Analizar reglas de versión insegura (ej. unpinned)
            insecure_finding = self.insecure_version_rule_service.analyze_dependency_config(project_name, dep)
            if insecure_finding:
                all_findings.append(insecure_finding)

            # B. Analizar estado obsoletas/abandonadas
            abandoned_finding = self.abandoned_analyzer.analyze_abandoned(project_name, dep)
            if abandoned_finding:
                all_findings.append(abandoned_finding)

            # C. Analizar desactualizadas contra registros públicos en línea
            if dep.is_direct:
                self._analyze_outdated_dependency(project_name, dep, all_findings)

    def _analyze_outdated_dependency(self, project_name: str, dep: Any, all_findings: list[DependencyFinding]) -> None:
        """Verifica si la versión directa de la dependencia está desactualizada y registra hallazgos."""
        latest_ver = self.registry_provider.get_latest_version(dep.name, dep.ecosystem)
        outdated_info = self.outdated_analyzer.analyze_outdated(dep, latest_ver)
        if outdated_info:
            score = (
                self.settings.score_weights.get("version_very_outdated", 45)
                if outdated_info["update_risk"] == "HIGH"
                else 20
            )
            all_findings.append(
                DependencyFinding(
                    project=project_name,
                    dependency=dep,
                    finding_type="Dependencia Desactualizada",
                    severity=SeverityLevel.LOW,
                    risk_score=score,
                    risk_level=RiskLevel.LOW,
                    impact=f"El paquete está desactualizado respecto a la versión recomendada v{latest_ver}.",
                    recommendation=outdated_info["action_suggested"],
                    references=[],
                )
            )

    def _calculate_scoring_for_project(
        self, project_name: str, dependencies: list[Any], all_findings: list[DependencyFinding]
    ) -> None:
        """Calcula el puntaje de riesgo para cada dependencia basada en sus hallazgos asociados."""
        for dep in dependencies:
            dep_findings = [
                f for f in all_findings if f.dependency.name.lower() == dep.name.lower() and f.project == project_name
            ]
            self.risk_calculator.calculate_score_and_level(dep, dep_findings)

    def _export_reports(self, report: DependencyAuditReport, errors: list[dict[str, Any]]) -> None:
        """Exporta el reporte consolidado a todos los formatos registrados."""
        generated_paths = []
        for exporter in self.exporters:
            try:
                path = exporter.export(report, self.settings.datos_salida_dir)
                generated_paths.append(path)
            except Exception as e:
                logger.error(f"Fallo al exportar reporte con {exporter.__class__.__name__}: {e}")
                errors.append(
                    {
                        "proyecto": "Global",
                        "archivo": "Exportador",
                        "tipo_error": e.__class__.__name__,
                        "mensaje_error": f"Fallo al escribir reporte: {e}",
                    }
                )
        logger.info(f"Auditoría completada. Se generaron {len(generated_paths)} archivos de reportes técnicos.")
