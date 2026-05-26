from dataclasses import dataclass, field
from pathlib import Path

from app.domain.value_objects.ecosystem import Ecosystem


@dataclass
class ProjectScanTarget:
    """Representa una carpeta o proyecto identificado para auditoría de seguridad."""

    name: str
    path: Path
    detected_ecosystems: set[Ecosystem] = field(default_factory=set)
    dependency_files: list[Path] = field(default_factory=list)
