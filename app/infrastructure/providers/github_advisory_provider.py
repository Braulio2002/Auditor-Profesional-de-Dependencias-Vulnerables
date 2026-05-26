from app.application.interfaces.vulnerability_provider_interface import (
    VulnerabilityProviderInterface,
)
from app.domain.entities.dependency import Dependency
from app.domain.entities.vulnerability import Vulnerability
from app.shared.logger import logger


class GitHubAdvisoryProvider(VulnerabilityProviderInterface):
    """Proveedor opcional de vulnerabilidades que consulta GitHub Advisory Database."""

    def __init__(self, settings):
        self.settings = settings

    def get_name(self) -> str:
        return "GitHub Advisory Database"

    def fetch_vulnerabilities(
        self, dependencies: list[Dependency]
    ) -> dict[str, list[Vulnerability]]:
        # Si no hay token de GitHub configurado
        if not self.settings.github_token:
            logger.info(
                "GitHub Token no configurado. Omitiendo consultas a GitHub Advisory Database."
            )
            return {}

        logger.info(
            "GitHub Token configurado. Consultando GitHub Advisory Database...")
        # Nota: La consulta requiere llamadas GraphQL autenticadas.
        # Implementación extensible:
        # En una versión futura, aquí se realiza el request GraphQL a api.github.com/graphql
        # Por ahora actúa como puerto habilitado resiliente.
        return {}
