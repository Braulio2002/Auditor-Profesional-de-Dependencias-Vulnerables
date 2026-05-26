from unittest.mock import MagicMock
import pytest

from app.application.use_cases.audit_dependencies_use_case import AuditDependenciesUseCase
from app.config.settings import Settings
from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.entities.project_scan_target import ProjectScanTarget
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel



def test_use_case_empty_projects():
    # Setup mocks
    dir_manager = MagicMock()
    discovery_service = MagicMock()
    discovery_service.discover_projects.return_value = []
    
    normalizer_service = MagicMock()
    vulnerability_analyzer = MagicMock()
    insecure_rule_service = MagicMock()
    outdated_analyzer = MagicMock()
    abandoned_analyzer = MagicMock()
    risk_calculator = MagicMock()
    recommendation_service = MagicMock()
    summary_service = MagicMock()
    registry_provider = MagicMock()
    exporter = MagicMock()
    settings = Settings()

    use_case = AuditDependenciesUseCase(
        directory_manager=dir_manager,
        discovery_service=discovery_service,
        normalizer_service=normalizer_service,
        vulnerability_analyzer=vulnerability_analyzer,
        insecure_version_rule_service=insecure_rule_service,
        outdated_analyzer=outdated_analyzer,
        abandoned_analyzer=abandoned_analyzer,
        risk_calculator=risk_calculator,
        recommendation_service=recommendation_service,
        executive_summary_service=summary_service,
        registry_provider=registry_provider,
        exporters=[exporter],
        settings=settings,
    )

    report = use_case.execute()

    assert report.summary["total_proyectos"] == 0
    assert report.summary["riesgo_general"] == "BAJO"
    dir_manager.ensure_directories_exist.assert_called_once()
    discovery_service.discover_projects.assert_called_once()


def test_use_case_successful_audit_flow(tmp_path):
    # Setup mocks for project discovery
    project = ProjectScanTarget(
        name="my_test_project",
        path=tmp_path,
        detected_ecosystems={Ecosystem.PIP},
        dependency_files=[tmp_path / "requirements.txt"],
    )
    
    dir_manager = MagicMock()
    discovery_service = MagicMock()
    discovery_service.discover_projects.return_value = [project]
    
    # Mock readers and normalization
    dep = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="==2.28.1",
        installed_version="2.28.1",
        scope=DependencyScope.PRODUCTION,
        source_file="requirements.txt",
        is_direct=True,
        is_pinned=True,
    )
    
    normalizer_service = MagicMock()
    normalizer_service.normalize_and_deduplicate.return_value = [dep]
    
    vulnerability_analyzer = MagicMock()
    vulnerability_analyzer.analyze_vulnerabilities.return_value = []
    
    insecure_rule_service = MagicMock()
    insecure_rule_service.analyze_dependency_config.return_value = None
    
    abandoned_analyzer = MagicMock()
    abandoned_analyzer.analyze_abandoned.return_value = None
    
    registry_provider = MagicMock()
    registry_provider.get_latest_version.return_value = "2.31.0"
    
    outdated_analyzer = MagicMock()
    outdated_analyzer.analyze_outdated.return_value = {
        "update_risk": "MEDIUM",
        "action_suggested": "Update requests to v2.31.0",
    }
    
    risk_calculator = MagicMock()
    risk_calculator.calculate_score_and_level.return_value = (20, SeverityLevel.LOW, RiskLevel.LOW)
    risk_calculator.calculate_project_risk.return_value = RiskLevel.LOW
    
    recommendation_service = MagicMock()
    recommendation_service.generate_recommendations.return_value = ["Mock recommendation"]
    
    summary_service = MagicMock()
    summary_service.generate_summary.return_value = {"total_proyectos": 1, "riesgo_general": "BAJO"}
    
    exporter = MagicMock()
    exporter.export.return_value = "/path/to/report.pdf"
    
    settings = Settings()

    use_case = AuditDependenciesUseCase(
        directory_manager=dir_manager,
        discovery_service=discovery_service,
        normalizer_service=normalizer_service,
        vulnerability_analyzer=vulnerability_analyzer,
        insecure_version_rule_service=insecure_rule_service,
        outdated_analyzer=outdated_analyzer,
        abandoned_analyzer=abandoned_analyzer,
        risk_calculator=risk_calculator,
        recommendation_service=recommendation_service,
        executive_summary_service=summary_service,
        registry_provider=registry_provider,
        exporters=[exporter],
        settings=settings,
    )

    report = use_case.execute()

    assert len(report.projects) == 1
    assert report.projects[0].name == "my_test_project"
    assert len(report.dependencies) == 1
    assert report.dependencies[0].name == "requests"
    
    # Confirms direct dependencies check was performed
    registry_provider.get_latest_version.assert_called_once_with("requests", Ecosystem.PIP)
    outdated_analyzer.analyze_outdated.assert_called_once_with(dep, "2.31.0")
    
    # Confirms report summaries and plans were generated
    summary_service.generate_summary.assert_called_once()
    recommendation_service.generate_recommendations.assert_called_once()
    exporter.export.assert_called_once()
