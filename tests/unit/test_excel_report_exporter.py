from pathlib import Path

import pandas as pd

from app.config.settings import Settings
from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_audit_report import DependencyAuditReport
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.entities.project_scan_target import ProjectScanTarget
from app.domain.entities.vulnerability import Vulnerability
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel
from app.infrastructure.exporters.excel_report_exporter import ExcelReportExporter


def test_excel_export_success(tmp_path):
    settings = Settings()
    settings.excel_report_name = "test_audit_report.xlsx"

    exporter = ExcelReportExporter(settings)

    # 1. Mock entity data
    project = ProjectScanTarget(
        name="test_proj",
        path=tmp_path,
        detected_ecosystems={Ecosystem.PIP},
        dependency_files=[Path("requirements.txt")],
    )

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

    vuln = Vulnerability(
        vulnerability_id="CVE-2023-1234",
        cve="CVE-2023-1234",
        ghsa="GHSA-1234",
        severity=SeverityLevel.HIGH,
        summary="A fake vulnerability in requests",
        affected_versions="<2.31.0",
        fixed_versions="2.31.0",
        references=["https://cve.mitre.org"],
    )

    finding = DependencyFinding(
        project="test_proj",
        dependency=dep,
        finding_type="Vulnerabilidad Conocida (CVE-2023-1234)",
        severity=SeverityLevel.HIGH,
        risk_score=75,
        risk_level=RiskLevel.HIGH,
        impact="High severity impact",
        recommendation="Update requests to v2.31.0",
        references=["https://cve.mitre.org"],
    )

    finding_outdated = DependencyFinding(
        project="test_proj",
        dependency=dep,
        finding_type="Dependencia Desactualizada",
        severity=SeverityLevel.LOW,
        risk_score=20,
        risk_level=RiskLevel.LOW,
        impact="Outdated package requests",
        recommendation="Update requests to v2.31.0",
        references=[],
    )

    recommendation = {
        "proyecto": "test_proj",
        "dependencia": "requests",
        "version_recomendada": "2.31.0",
        "accion_sugerida": "Update requests major version",
        "requiere_testing": True,
    }

    error = {
        "proyecto": "test_proj",
        "archivo": "requirements.txt",
        "tipo_error": "SyntaxError",
        "mensaje_error": "Mocked syntax error during parsing",
    }

    report = DependencyAuditReport(
        metadata={"status": "success"},
        projects=[project],
        dependencies=[dep],
        findings=[finding, finding_outdated],
        vulnerabilities=[vuln],
        errors=[error],
        generated_at="2026-05-26T00:00:00Z",
    )
    report.recommendations = [recommendation]

    # 2. Export
    output_path = exporter.export(report, tmp_path)

    assert output_path.exists()
    assert output_path.suffix == ".xlsx"

    # 3. Read sheet names using Pandas ExcelFile
    excel_file = pd.ExcelFile(output_path)
    expected_sheets = {
        "Resumen",
        "Dependencias",
        "Vulnerabilidades",
        "Actualizaciones Sugeridas",
        "Riesgos de Configuración",
        "Errores",
    }
    assert set(excel_file.sheet_names) == expected_sheets

    # 4. Validate contents of one of the sheets
    df_summary = excel_file.parse("Resumen")
    assert len(df_summary) == 1
    assert df_summary.loc[0, "proyecto"] == "test_proj"
    assert df_summary.loc[0, "riesgo_general"] == "ALTO"

    df_deps = excel_file.parse("Dependencias")
    assert len(df_deps) == 1
    assert df_deps.loc[0, "dependencia"] == "requests"
    assert df_deps.loc[0, "version_recomendada"] == "2.31.0"
