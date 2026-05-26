from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities.dependency_audit_report import DependencyAuditReport


class ReportExporterInterface(ABC):
    """Interfaz base (Puerto) para exportadores de reportes del auditor."""

    @abstractmethod
    def export(self, report: DependencyAuditReport, output_dir: Path) -> Path:
        """Exporta el reporte consolidado a un archivo físico.

        Args:
            report: El reporte consolidado de auditoría.
            output_dir: Carpeta de destino.

        Returns:
            Path: Ruta del archivo generado.
        """
        pass


class ReportExporterPDFInterface(ABC):
    """Interfaz opcional para exportadores de reportes PDF."""

    @abstractmethod
    def export_pdf(self, report: DependencyAuditReport, output_path: Path) -> Path:
        """Exporta el reporte consolidado a un archivo PDF."""
        pass
