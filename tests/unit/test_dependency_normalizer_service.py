from app.application.services.dependency_normalizer_service import DependencyNormalizerService
from app.domain.entities.dependency import Dependency
from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem


def test_normalize_and_deduplicate_empty():
    service = DependencyNormalizerService()
    assert service.normalize_and_deduplicate([]) == []


def test_normalize_and_deduplicate_lowercase_and_clean():
    service = DependencyNormalizerService()
    dep1 = Dependency(
        name="  My-Awesome-Pkg  ",
        ecosystem=Ecosystem.PIP,
        declared_version="==1.0.0",
        installed_version="1.0.0",
        scope=DependencyScope.PRODUCTION,
        source_file="requirements.txt",
        is_direct=True,
        is_pinned=True,
    )
    res = service.normalize_and_deduplicate([dep1])
    assert len(res) == 1
    assert res[0].name == "my-awesome-pkg"


def test_normalize_and_deduplicate_declared_version_update():
    service = DependencyNormalizerService()
    dep_indirect = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="indirect",
        installed_version="2.28.1",
        scope=DependencyScope.PRODUCTION,
        source_file="poetry.lock",
        is_direct=False,
        is_pinned=True,
    )
    dep_direct = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="^2.28.0",
        installed_version="2.28.1",
        scope=DependencyScope.PRODUCTION,
        source_file="pyproject.toml",
        is_direct=True,
        is_pinned=False,
    )
    
    # Passing indirect then direct: declared_version should become "^2.28.0" and is_direct should become True
    res = service.normalize_and_deduplicate([dep_indirect, dep_direct])
    assert len(res) == 1
    assert res[0].declared_version == "^2.28.0"
    assert res[0].is_direct is True


def test_normalize_and_deduplicate_installed_version_update():
    service = DependencyNormalizerService()
    dep_no_install = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="^2.28.0",
        installed_version="0.0.0",
        scope=DependencyScope.PRODUCTION,
        source_file="pyproject.toml",
        is_direct=True,
        is_pinned=False,
    )
    dep_installed = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="^2.28.0",
        installed_version="2.28.1",
        scope=DependencyScope.PRODUCTION,
        source_file="poetry.lock",
        is_direct=False,
        is_pinned=True,
    )
    
    res = service.normalize_and_deduplicate([dep_no_install, dep_installed])
    assert len(res) == 1
    assert res[0].installed_version == "2.28.1"


def test_normalize_and_deduplicate_source_file_update():
    service = DependencyNormalizerService()
    dep_lock = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="indirect",
        installed_version="2.28.1",
        scope=DependencyScope.PRODUCTION,
        source_file="poetry.lock",
        is_direct=False,
        is_pinned=True,
    )
    dep_toml = Dependency(
        name="requests",
        ecosystem=Ecosystem.PIP,
        declared_version="^2.28.0",
        installed_version="2.28.1",
        scope=DependencyScope.PRODUCTION,
        source_file="pyproject.toml",
        is_direct=True,
        is_pinned=False,
    )
    
    # When both exist, if existing has lock and new has non-lock, update source_file to non-lock
    res = service.normalize_and_deduplicate([dep_lock, dep_toml])
    assert len(res) == 1
    assert res[0].source_file == "pyproject.toml"
