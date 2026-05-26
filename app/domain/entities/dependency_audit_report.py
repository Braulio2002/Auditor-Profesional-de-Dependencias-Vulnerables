from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.entities.project_scan_target import ProjectScanTarget
from app.domain.entities.vulnerability import Vulnerability


@dataclass
class DependencyAuditReport:
    """Representa el reporte global consolidado de auditoría de seguridad del ecosistema."""

    metadata: dict[str, Any] = field(default_factory=dict)
    projects: list[ProjectScanTarget] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    findings: list[DependencyFinding] = field(default_factory=list)
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    generated_at: str = ""
