from app.application.services.insecure_version_rule_service import InsecureVersionRuleService
from app.application.services.version_parser_service import VersionParserService
from app.config.settings import Settings
from app.domain.entities.dependency import Dependency
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem


def test_analyze_insecure_version():
    settings = Settings()
    parser = VersionParserService()
    service = InsecureVersionRuleService(parser, settings)

    # 1. Caso Seguro (Fijado)
    dep_safe = Dependency(
        name="lodash",
        ecosystem=Ecosystem.NPM,
        declared_version="4.17.15",
        installed_version="4.17.15",
        scope=DependencyScope.PRODUCTION,
        source_file="package.json",
        is_direct=True,
        is_pinned=True,
    )
    finding_safe = service.analyze_dependency_config("demo", dep_safe)
    assert finding_safe is None

    # 2. Caso Inseguro (Comodín)
    dep_unpinned = Dependency(
        name="lodash",
        ecosystem=Ecosystem.NPM,
        declared_version="*",
        installed_version="4.17.15",
        scope=DependencyScope.PRODUCTION,
        source_file="package.json",
        is_direct=True,
        is_pinned=False,
    )
    finding_unpinned = service.analyze_dependency_config("demo", dep_unpinned)
    assert finding_unpinned is not None
    assert "No Fijada" in finding_unpinned.finding_type
    assert finding_unpinned.risk_score == 30

    # 3. Caso Rango Abierto
    dep_open = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version=">=2.0.0",
        installed_version="2.25.0",
        scope=DependencyScope.PRODUCTION,
        source_file="requirements.txt",
        is_direct=True,
        is_pinned=False,
    )
    finding_open = service.analyze_dependency_config("demo", dep_open)
    assert finding_open is not None
    assert "Rango de Versión Inseguro" in finding_open.finding_type
    assert finding_open.risk_score == 25
