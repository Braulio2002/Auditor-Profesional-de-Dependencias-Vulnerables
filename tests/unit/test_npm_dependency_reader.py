import json
from pathlib import Path

from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.infrastructure.readers.npm_dependency_reader import NpmDependencyReader


def test_read_npm_dependencies(tmp_path: Path):
    # Crear un package.json simulado
    pkg_data = {
        "name": "test-project",
        "dependencies": {"lodash": "^4.17.15"},
        "devDependencies": {"jest": "29.0.0"},
    }
    pkg_file = tmp_path / "package.json"
    with open(pkg_file, "w", encoding="utf-8") as f:
        json.dump(pkg_data, f)

    # Crear un package-lock.json simulado
    lock_data = {"packages": {"node_modules/lodash": {"version": "4.17.21"}}}
    lock_file = tmp_path / "package-lock.json"
    with open(lock_file, "w", encoding="utf-8") as f:
        json.dump(lock_data, f)

    reader = NpmDependencyReader()
    dependencies = reader.read(pkg_file)

    assert len(dependencies) >= 2

    # lodash
    lodash = next(d for d in dependencies if d.name == "lodash")
    assert lodash.ecosystem == Ecosystem.NPM
    assert lodash.declared_version == "^4.17.15"
    assert lodash.installed_version == "4.17.21"
    assert lodash.scope == DependencyScope.PRODUCTION
    assert lodash.is_direct is True
    assert lodash.is_pinned is False

    # jest
    jest = next(d for d in dependencies if d.name == "jest")
    assert jest.declared_version == "29.0.0"
    assert jest.installed_version == "29.0.0"
    assert jest.scope == DependencyScope.DEVELOPMENT
    assert jest.is_pinned is True
