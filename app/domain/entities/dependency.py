from dataclasses import dataclass

from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem


@dataclass
class Dependency:
    """Representa una biblioteca o dependencia de software declarada o instalada."""

    name: str
    ecosystem: Ecosystem
    declared_version: str
    installed_version: str
    scope: DependencyScope
    source_file: str
    is_direct: bool
    is_pinned: bool
