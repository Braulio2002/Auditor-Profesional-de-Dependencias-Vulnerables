from app.application.services.recommendation_service import RecommendationService
from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel


def test_recommendation_service():
    service = RecommendationService()

    dep = Dependency(
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
        dependency=dep,
        finding_type="Vulnerabilidad Conocida",
        severity=SeverityLevel.CRITICAL,
        risk_score=90,
        risk_level=RiskLevel.CRITICAL,
        impact="Test impact",
        recommendation="Actualizar a v9.0.0",
    )

    recs = service.generate_recommendations([finding])
    assert len(recs) == 1
    assert recs[0]["proyecto"] == "demo"
    assert recs[0]["dependencia"] == "jsonwebtoken"
    assert recs[0]["requiere_testing"] is True
    assert "CRÍTICO: Validar la autenticación" in recs[0]["plan_de_pruebas"]
