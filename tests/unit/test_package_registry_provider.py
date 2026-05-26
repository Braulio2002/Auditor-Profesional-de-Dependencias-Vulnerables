from unittest.mock import MagicMock, patch

import httpx

from app.config.settings import Settings
from app.domain.value_objects.ecosystem import Ecosystem
from app.infrastructure.providers.package_registry_provider import PackageRegistryProvider


def test_registry_offline_mode():
    settings = Settings(offline_mode=True)
    provider = PackageRegistryProvider(settings)

    # Should immediately return None
    assert provider.get_latest_version("requests", Ecosystem.PIP) is None


def test_registry_cache_hit():
    settings = Settings()
    provider = PackageRegistryProvider(settings)
    provider.cache["pip:requests"] = "2.31.0"

    with patch("httpx.Client") as mock_client_cls:
        assert provider.get_latest_version("requests", Ecosystem.PIP) == "2.31.0"
        mock_client_cls.assert_not_called()


def test_registry_npm_success():
    settings = Settings()
    provider = PackageRegistryProvider(settings)

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"version": "18.2.0"}

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = mock_res
        assert provider.get_latest_version("react", Ecosystem.NPM) == "18.2.0"

        # Verify cache was populated
        assert provider.cache["npm:react"] == "18.2.0"


def test_registry_pypi_success():
    settings = Settings()
    provider = PackageRegistryProvider(settings)

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"info": {"version": "2.31.0"}}

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = mock_res
        assert provider.get_latest_version("requests", Ecosystem.PIP) == "2.31.0"


def test_registry_packagist_ignores_dev_versions():
    settings = Settings()
    provider = PackageRegistryProvider(settings)

    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {
        "package": {
            "versions": {
                "v2.0.0-dev": {},
                "v2.0.0-beta1": {},
                "v1.9.5-rc2": {},
                "v1.9.4": {},
                "v1.9.3": {},
            }
        }
    }

    with patch("httpx.Client.get") as mock_get:
        mock_get.return_value = mock_res
        # Should skip development, beta, and rc versions, stripping 'v' from 1.9.4
        assert provider.get_latest_version("monolog/monolog", Ecosystem.COMPOSER) == "1.9.4"


def test_registry_exception_handling():
    settings = Settings()
    provider = PackageRegistryProvider(settings)

    with patch("httpx.Client.get") as mock_get:
        mock_get.side_effect = httpx.NetworkError("Registry Connection Timed Out")
        # Should gracefully return None
        assert provider.get_latest_version("requests", Ecosystem.PIP) is None
