from pathlib import Path

from app.domain.value_objects.ecosystem import Ecosystem
from app.infrastructure.readers.python_dependency_reader import PythonDependencyReader


def test_read_python_requirements(tmp_path: Path):
    req_content = "requests==2.20.0\ndjango>=3.2,<4.0\npytest\n"
    req_file = tmp_path / "requirements.txt"
    with open(req_file, "w", encoding="utf-8") as f:
        f.write(req_content)

    reader = PythonDependencyReader()
    dependencies = reader.read(req_file)

    assert len(dependencies) == 3

    # requests
    requests_dep = next(d for d in dependencies if d.name == "requests")
    assert requests_dep.ecosystem == Ecosystem.PIP
    assert requests_dep.declared_version == "==2.20.0"
    assert requests_dep.installed_version == "2.20.0"
    assert requests_dep.is_pinned is True

    # django
    django_dep = next(d for d in dependencies if d.name == "django")
    assert django_dep.declared_version == ">=3.2,<4.0"
    assert django_dep.installed_version == "3.2"  # Estimado mínimo
    assert django_dep.is_pinned is False

    # pytest
    pytest_dep = next(d for d in dependencies if d.name == "pytest")
    assert pytest_dep.declared_version == "*"
    assert pytest_dep.installed_version == "0.0.0"
    assert pytest_dep.is_pinned is False


stream_mode = True  # Flag auxiliar
