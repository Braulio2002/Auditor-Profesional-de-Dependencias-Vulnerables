import httpx

from app.application.interfaces.package_registry_provider_interface import (
    PackageRegistryProviderInterface,
)
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.logger import logger


class PackageRegistryProvider(PackageRegistryProviderInterface):
    """Consulta los registros oficiales públicos de paquetes (NPM, PyPI, Packagist) para obtener versiones recomendadas."""

    def __init__(self, settings):
        self.settings = settings
        self.cache: dict[str, str] = {}

    def get_latest_version(self, name: str, ecosystem: Ecosystem) -> str | None:
        if self.settings.offline_mode:
            return None

        cache_key = f"{ecosystem.value}:{name.lower()}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        latest_ver = None

        try:
            with httpx.Client(timeout=3.0) as client:
                if ecosystem == Ecosystem.NPM:
                    latest_ver = self._fetch_npm_latest(client, name)
                elif ecosystem in (Ecosystem.PIP, Ecosystem.POETRY):
                    latest_ver = self._fetch_pypi_latest(client, name)
                elif ecosystem == Ecosystem.COMPOSER:
                    latest_ver = self._fetch_packagist_latest(client, name)
        except Exception as e:
            logger.warning(
                f"No se pudo consultar el registro de paquetes para {name} ({ecosystem.value}): {e}"
            )

        if latest_ver:
            self.cache[cache_key] = latest_ver

        return latest_ver

    def _fetch_npm_latest(self, client: httpx.Client, name: str) -> str | None:
        """Consulta el registro público de NPM para obtener la última versión."""
        url = f"https://registry.npmjs.org/{name}/latest"
        res = client.get(url)
        if res.status_code == 200:
            return res.json().get("version")
        return None

    def _fetch_pypi_latest(self, client: httpx.Client, name: str) -> str | None:
        """Consulta el registro público de PyPI para obtener la última versión."""
        url = f"https://pypi.org/pypi/{name}/json"
        res = client.get(url)
        if res.status_code == 200:
            return res.json().get("info", {}).get("version")
        return None

    def _fetch_packagist_latest(self, client: httpx.Client, name: str) -> str | None:
        """Consulta el registro público de Packagist para obtener la última versión estable."""
        url = f"https://packagist.org/packages/{name}.json"
        res = client.get(url)
        if res.status_code != 200:
            return None

        versions_data = res.json().get("package", {}).get("versions", {})
        # Obtener la primera versión que no sea de desarrollo (no contenga -dev, alpha, beta)
        for ver_str in versions_data.keys():
            if not any(
                x in ver_str.lower() for x in ["dev", "alpha", "beta", "rc"]
            ):
                return ver_str.lstrip("v")
        return None
