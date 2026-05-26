from app.application.services.risk_score_calculator_service import RiskScoreCalculatorService
from app.config.settings import Settings
from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel


def test_risk_calculator_scoring():
    settings = Settings()
    calculator = RiskScoreCalculatorService(settings)

    dep = Dependency(
        name="lodash",
        ecosystem=Ecosystem.NPM,
        declared_version="^4.17.15",
        installed_version="4.17.15",
        scope=DependencyScope.PRODUCTION,
        source_file="package.json",
        is_direct=True,
        is_pinned=False,
    )

    finding = DependencyFinding(
        project="demo",
        dependency=dep,
        finding_type="Vulnerabilidad Conocida",
        severity=SeverityLevel.HIGH,
        risk_score=75,
        risk_level=RiskLevel.HIGH,
        impact="Test impact",
        recommendation="Test rec",
    )

    score, sev, lvl = calculator.calculate_score_and_level(dep, [finding])
    assert score == 75
    assert sev == SeverityLevel.HIGH
    assert lvl == RiskLevel.HIGH


def test_risk_calculator_elevate_sensitive():
    settings = Settings()
    calculator = RiskScoreCalculatorService(settings)

    # jwt es una dependencia marcada como sensible en constants
    dep_sensitive = Dependency(
        name="jsonwebtoken",
        ecosystem=Ecosystem.NPM,
        declared_version="8.5.1",
        installed_version="8.5.1",
        scope=DependencyScope.PRODUCTION,
        source_file="package.json",
        is_direct=True,
        is_pinned=True,
    )

    finding = DependencyFinding(
        project="demo",
        dependency=dep_sensitive,
        finding_type="Vulnerabilidad Conocida",
        severity=SeverityLevel.MEDIUM,
        risk_score=50,
        risk_level=RiskLevel.MEDIUM,
        impact="Test impact",
        recommendation="Test rec",
    )

    # Al ser sensible y vulnerable, debe elevarse el score de 50 a 65 (+15) y la severidad a HIGH
    score, sev, lvl = calculator.calculate_score_and_level(dep_sensitive, [finding])
    assert score == 65
    assert sev == SeverityLevel.HIGH
    assert lvl == RiskLevel.HIGH
