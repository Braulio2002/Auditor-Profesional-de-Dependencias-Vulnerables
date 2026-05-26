import json
from dataclasses import asdict
from pathlib import Path

from app.application.interfaces.report_exporter_interface import ReportExporterInterface
from app.domain.entities.dependency_audit_report import DependencyAuditReport
from app.shared.filename_utils import get_unique_filename
from app.shared.logger import logger


class JsonReportExporter(ReportExporterInterface):
    """Exporta el reporte consolidado de auditoría a formato JSON estructurado."""

    def __init__(self, settings):
        self.settings = settings

    def export(self, report: DependencyAuditReport, output_dir: Path) -> Path:
        logger.info("Generando reporte JSON...")

        # Resolver ruta única para evitar sobrescribir
        target_path = get_unique_filename(output_dir, self.settings.json_report_name)

        try:
            # Convertir las entidades a diccionarios planos estructurados
            report_dict = {
                "metadata": report.metadata,
                "generated_at": report.generated_at,
                "summary": report.summary,
                "proyectos_analizados": [
                    {
                        "nombre": p.name,
                        "ruta": str(p.path),
                        "ecosistemas": [eco.value for eco in p.detected_ecosystems],
                        "archivos_dependencias": [
                            str(f.relative_to(self.settings.base_dir))
                            if hasattr(f, "is_relative_to")
                            and f.is_relative_to(self.settings.base_dir)
                            else f.name
                            for f in p.dependency_files
                        ],
                    }
                    for p in report.projects
                ],
                "dependencias": [
                    {
                        "nombre": d.name,
                        "ecosistema": d.ecosystem.value,
                        "version_declarada": d.declared_version,
                        "version_instalada": d.installed_version,
                        "scope": d.scope.value,
                        "archivo_origen": d.source_file,
                        "es_directa": d.is_direct,
                        "esta_fijada": d.is_pinned,
                    }
                    for d in report.dependencies
                ],
                "hallazgos": [
                    {
                        "proyecto": h.project,
                        "dependencia": h.dependency.name,
                        "ecosistema": h.dependency.ecosystem.value,
                        "tipo_hallazgo": h.finding_type,
                        "severidad": h.severity.value,
                        "risk_score": h.risk_score,
                        "risk_level": h.risk_level.value,
                        "impacto": h.impact,
                        "recomendacion": h.recommendation,
                        "referencias": h.references,
                    }
                    for h in report.findings
                ],
                "vulnerabilidades": [asdict(v) for v in report.vulnerabilities],
                "recomendaciones": report.recommendations,
                "errores": report.errors,
            }

            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Reporte JSON generado correctamente: {target_path}")
            return target_path

        except Exception as e:
            logger.error(f"Error exportando reporte JSON: {e}")
            raise
