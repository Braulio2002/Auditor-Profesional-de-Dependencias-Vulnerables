import json
from pathlib import Path

from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.infrastructure.readers.composer_dependency_reader import ComposerDependencyReader


def test_read_composer_dependencies(tmp_path: Path):
    composer_data = {
        "require": {"laravel/framework": "^8.0"},
        "require-dev": {"phpunit/phpunit": "^9.0"},
    }
    composer_file = tmp_path / "composer.json"
    with open(composer_file, "w", encoding="utf-8") as f:
        json.dump(composer_data, f)

    lock_data = {
        "packages": [{"name": "laravel/framework", "version": "8.50.0"}],
        "packages-dev": [{"name": "phpunit/phpunit", "version": "9.5.2"}],
    }
    lock_file = tmp_path / "composer.lock"
    with open(lock_file, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)

    reader = ComposerDependencyReader()
    dependencies = reader.read(composer_file)

    assert len(dependencies) >= 2

    laravel = next(d for d in dependencies if d.name == "laravel/framework")
    assert laravel.ecosystem == Ecosystem.COMPOSER
    assert laravel.declared_version == "^8.0"
    assert laravel.installed_version == "8.50.0"
    assert laravel.scope == DependencyScope.PRODUCTION

    phpunit = next(d for d in dependencies if d.name == "phpunit/phpunit")
    assert phpunit.declared_version == "^9.0"
    assert phpunit.installed_version == "9.5.2"
    assert phpunit.scope == DependencyScope.DEVELOPMENT
