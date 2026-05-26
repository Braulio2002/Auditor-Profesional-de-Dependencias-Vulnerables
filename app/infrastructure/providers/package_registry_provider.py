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
                    # Registro de npm
                    url = f"https://registry.npmjs.org/{name}/latest"
                    res = client.get(url)
                    if res.status_code == 200:
                        latest_ver = res.json().get("version")

                elif ecosystem in (Ecosystem.PIP, Ecosystem.POETRY):
                    # Registro de PyPI
                    url = f"https://pypi.org/pypi/{name}/json"
                    res = client.get(url)
                    if res.status_code == 200:
                        latest_ver = res.json().get("info", {}).get("version")

                elif ecosystem == Ecosystem.COMPOSER:
                    # Registro de Packagist
                    url = f"https://packagist.org/packages/{name}.json"
                    res = client.get(url)
                    if res.status_code == 200:
                        # Packagist retorna una lista ordenada por fecha de releases
                        versions_data = res.json().get("package", {}).get("versions", {})
                        # Obtener la primera versión que no sea de desarrollo (no contenga -dev, alpha, beta)
                        for ver_str in versions_data.keys():
                            if not any(
                                x in ver_str.lower() for x in ["dev", "alpha", "beta", "rc"]
                            ):
                                latest_ver = ver_str.lstrip("v")
                                break
        except Exception as e:
            logger.warning(
                f"No se pudo consultar el registro de paquetes para {name} ({ecosystem.value}): {e}"
            )

        if latest_ver:
            self.cache[cache_key] = latest_ver

        return latest_ver
