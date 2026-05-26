from dataclasses import dataclass, field

from app.domain.entities.dependency import Dependency
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel


@dataclass
class DependencyFinding:
    """Representa un hallazgo de riesgo o vulnerabilidad detectado en una dependencia."""

    project: str
    dependency: Dependency
    finding_type: str
    severity: SeverityLevel
    risk_score: int
    risk_level: RiskLevel
    impact: str
    recommendation: str
    references: list[str] = field(default_factory=list)
