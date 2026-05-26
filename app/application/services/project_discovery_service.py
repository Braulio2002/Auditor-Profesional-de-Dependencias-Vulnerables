from pathlib import Path

from app.domain.entities.project_scan_target import ProjectScanTarget
from app.domain.value_objects.ecosystem import Ecosystem
from app.shared.logger import logger


class ProjectDiscoveryService:
    """Servicio encargado de explorar datos_entrada/ para identificar proyectos y archivos de dependencias."""

    def __init__(self, settings):
        self.settings = settings

    def discover_projects(self) -> list[ProjectScanTarget]:
        logger.info(f"Buscando proyectos en: {self.settings.datos_entrada_dir}")
        projects: list[ProjectScanTarget] = []

        if not self.settings.datos_entrada_dir.exists():
            return []

        # Escanear subdirectorios directos en datos_entrada/ como proyectos individuales
        subdirs = [p for p in self.settings.datos_entrada_dir.iterdir() if p.is_dir()]

        # Si no hay subcarpetas pero hay archivos de dependencias directamente en datos_entrada/
        if not subdirs:
            root_files = self._scan_dir_for_dependency_files(self.settings.datos_entrada_dir)
            if root_files:
                target = self._build_scan_target(
                    "Proyecto Raíz", self.settings.datos_entrada_dir, root_files
                )
                projects.append(target)
                logger.info(
                    f"Proyecto detectado: Proyecto Raíz (en datos_entrada/) con {len(root_files)} archivos."
                )
        else:
            for subdir in subdirs:
                if subdir.name in self.settings.excluded_dirs:
                    continue
                files = self._scan_dir_for_dependency_files(subdir)
                if files:
                    target = self._build_scan_target(subdir.name, subdir, files)
                    projects.append(target)
                    logger.info(f"Proyecto detectado: {subdir.name} con {len(files)} archivos.")

        return projects

    def _scan_dir_for_dependency_files(self, directory: Path) -> list[Path]:
        """Escanea recursivamente un directorio buscando archivos compatibles, ignorando carpetas excluidas."""
        found_files: list[Path] = []

        try:
            for item in directory.rglob("*"):
                # Ignorar si algún componente de la ruta está en la lista de excluidos
                if any(part in self.settings.excluded_dirs for part in item.parts):
                    continue

                if item.is_file() and item.name in self.settings.supported_files:
                    found_files.append(item)
        except Exception as e:
            logger.error(f"Error explorando el directorio {directory}: {e}")

        return found_files

    def _build_scan_target(self, name: str, path: Path, files: list[Path]) -> ProjectScanTarget:
        detected_ecosystems: set[Ecosystem] = set()
        for f in files:
            eco_str = self.settings.supported_files.get(f.name)
            if eco_str:
                try:
                    detected_ecosystems.add(Ecosystem(eco_str))
                except ValueError:
                    pass

        return ProjectScanTarget(
            name=name, path=path, detected_ecosystems=detected_ecosystems, dependency_files=files
        )
