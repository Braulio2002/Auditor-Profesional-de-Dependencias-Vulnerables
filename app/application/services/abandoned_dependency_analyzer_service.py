from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.ecosystem import Ecosystem
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel
from app.shared.constants import FINDING_ABANDONED


class AbandonedDependencyAnalyzerService:
    """Detecta bibliotecas obsoletas, deprecadas o abandonadas por sus autores."""

    def __init__(self, settings):
        self.settings = settings
        # Base de datos local/estática de dependencias obsoletas populares
        self.abandoned_db: dict[Ecosystem, dict[str, str]] = {
            Ecosystem.NPM: {
                "request": "El paquete 'request' fue formalmente deprecado en 2020. Use 'axios', 'got' o el nativo 'fetch'.",
                "node-sass": "Deprecado. Use 'sass' (Dart Sass) en su lugar.",
                "moment": "En modo de mantenimiento. Considere usar 'date-fns', 'dayjs' o el API temporal nativo.",
                "express-jwt": "Versiones antiguas obsoletas. Considere migrar a 'jose' o la última versión de express-oauth2-jwt-bearer.",
            },
            Ecosystem.PIP: {
                "pycrypto": "Totalmente abandonado. Contiene vulnerabilidades críticas sin resolver. Use 'pycryptodome' en su lugar.",
                "flask-jwt": "Deprecado y sin mantenimiento. Migre a 'flask-jwt-extended'.",
                "requests-oauthlib": "Bajo mantenimiento. Evalúe usar 'authlib'.",
            },
            Ecosystem.COMPOSER: {
                "mhash": "Abandonado y obsoleto. Use la extensión hash integrada en PHP.",
                "php-tuf/composer-metadata-manipulator": "Deprecado. No se recomienda su uso.",
                "doctrine/cache": "Doctrine/cache está deprecado en favor de PSR-6 o PSR-16.",
            },
        }

    def analyze_abandoned(
        self, project_name: str, dependency: Dependency
    ) -> DependencyFinding | None:
        """Comprueba si la dependencia está registrada como abandonada o deprecada."""
        eco_db = self.abandoned_db.get(dependency.ecosystem, {})
        reason = eco_db.get(dependency.name.lower())

        if reason:
            score = self.settings.score_weights.get("dependency_abandoned", 60)
            return DependencyFinding(
                project=project_name,
                dependency=dependency,
                finding_type=FINDING_ABANDONED,
                severity=SeverityLevel.HIGH,
                risk_score=score,
                risk_level=RiskLevel.HIGH,
                impact="El paquete no recibe actualizaciones de seguridad ni parches de compatibilidad por parte de sus autores, lo cual expone la infraestructura a futuros exploits de zero-days sin resolución.",
                recommendation=reason,
                references=[
                    "https://github.com/request/request/issues/3142",
                    "https://pypi.org/project/pycrypto/",
                ],
            )

        return None
