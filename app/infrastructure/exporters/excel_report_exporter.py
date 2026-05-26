from pathlib import Path

import pandas as pd

from app.application.interfaces.report_exporter_interface import ReportExporterInterface
from app.domain.entities.dependency_audit_report import DependencyAuditReport
from app.shared.date_utils import get_current_local_formatted
from app.shared.filename_utils import get_unique_filename
from app.shared.logger import logger


class ExcelReportExporter(ReportExporterInterface):
    """Genera un libro de Excel con 6 pestañas estructuradas conteniendo todos los datos de auditoría."""

    def __init__(self, settings):
        self.settings = settings

    def export(self, report: DependencyAuditReport, output_dir: Path) -> Path:
        logger.info("Generando reporte Excel...")

        target_path = get_unique_filename(output_dir, self.settings.excel_report_name)

        try:
            # 1. Preparar datos para HOJA 1: Resumen por Proyecto
            summary_rows = []
            for p in report.projects:
                proj_findings = [f for f in report.findings if f.project == p.name]
                proj_deps = [
                    d
                    for d in report.dependencies
                    if d.source_file in [f.name for f in p.dependency_files]
                ]

                # Encontrar el ecosistema predominante
                ecosystems_str = ", ".join([eco.value for eco in p.detected_ecosystems])

                total_deps = len(proj_deps)
                vuln_deps_count = len(
                    {f.dependency.name for f in proj_findings if "Vulnerabilidad" in f.finding_type}
                )
                crit_count = sum(1 for f in proj_findings if f.severity.value == "CRITICAL")
                high_count = sum(1 for f in proj_findings if f.severity.value == "HIGH")
                med_count = sum(1 for f in proj_findings if f.severity.value == "MEDIUM")
                low_count = sum(1 for f in proj_findings if f.severity.value == "LOW")

                # Buscar desactualizadas y abandonadas
                outdated_count = sum(1 for f in proj_findings if "Desactualizada" in f.finding_type)
                abandoned_count = sum(1 for f in proj_findings if "Abandonada" in f.finding_type)

                # Riesgo general del proyecto (se calcula en base al hallazgo más severo)
                # O usar el riesgo calculado en report
                proj_risk = "BAJO"
                if crit_count > 0:
                    proj_risk = "CRÍTICO"
                elif high_count > 0:
                    proj_risk = "ALTO"
                elif med_count > 0:
                    proj_risk = "MEDIO"

                summary_rows.append(
                    {
                        "proyecto": p.name,
                        "ecosistema": ecosystems_str,
                        "total_dependencias": total_deps,
                        "dependencias_vulnerables": vuln_deps_count,
                        "dependencias_criticas": crit_count,
                        "dependencias_altas": high_count,
                        "dependencias_medias": med_count,
                        "dependencias_bajas": low_count,
                        "dependencias_desactualizadas": outdated_count,
                        "dependencias_abandonadas": abandoned_count,
                        "riesgo_general": proj_risk,
                        "fecha_analisis": get_current_local_formatted(),
                    }
                )
            df_summary = pd.DataFrame(summary_rows)
            if df_summary.empty:
                df_summary = pd.DataFrame(
                    columns=[
                        "proyecto",
                        "ecosistema",
                        "total_dependencias",
                        "dependencias_vulnerables",
                        "dependencias_criticas",
                        "dependencias_altas",
                        "dependencias_medias",
                        "dependencias_bajas",
                        "dependencias_desactualizadas",
                        "dependencias_abandonadas",
                        "riesgo_general",
                        "fecha_analisis",
                    ]
                )

            # 2. Preparar datos para HOJA 2: Dependencias
            deps_rows = []
            for d in report.dependencies:
                # Buscar hallazgos asociados
                dep_findings = [
                    f for f in report.findings if f.dependency.name.lower() == d.name.lower()
                ]
                has_findings = len(dep_findings) > 0
                max_finding_score = max([f.risk_score for f in dep_findings]) if has_findings else 0

                # Identificar riesgo y estado
                risk_str = "BAJO"
                if max_finding_score >= 76:
                    risk_str = "CRÍTICO"
                elif max_finding_score >= 51:
                    risk_str = "ALTO"
                elif max_finding_score >= 21:
                    risk_str = "MEDIO"

                # Estado actualizacion
                outdated_finding = next(
                    (f for f in dep_findings if "Desactualizada" in f.finding_type), None
                )
                estado_act = "Al día"
                recommended_ver = d.installed_version

                if outdated_finding:
                    # Encontrar el diccionario de recomendaciones para extraer la versión recomendada
                    rec = next(
                        (r for r in report.recommendations if r.get("dependencia") == d.name), None
                    )
                    recommended_ver = (
                        rec.get("version_recomendada", d.installed_version)
                        if rec
                        else d.installed_version
                    )
                    estado_act = "Desactualizada"

                # Buscar si está abandonada
                abandoned_finding = next(
                    (f for f in dep_findings if "Abandonada" in f.finding_type), None
                )
                obs_text = ""
                if abandoned_finding:
                    obs_text = "PAQUETE ABANDONADO/DEPRECADO."
                elif has_findings:
                    obs_text = ", ".join([f.finding_type for f in dep_findings])
                else:
                    obs_text = "Sin incidencias detectadas."

                # Proyecto origen
                proj_orig = next(
                    (
                        p.name
                        for p in report.projects
                        if d.source_file in [f.name for f in p.dependency_files]
                    ),
                    "Proyecto Desconocido",
                )

                deps_rows.append(
                    {
                        "proyecto": proj_orig,
                        "ecosistema": d.ecosystem.value,
                        "archivo_origen": d.source_file,
                        "dependencia": d.name,
                        "version_declarada": d.declared_version,
                        "version_instalada": d.installed_version,
                        "version_recomendada": recommended_ver,
                        "tipo_dependencia": d.scope.value,
                        "estado_actualizacion": estado_act,
                        "riesgo": risk_str,
                        "score": max_finding_score,
                        "observacion": obs_text,
                    }
                )
            df_deps = pd.DataFrame(deps_rows)
            if df_deps.empty:
                df_deps = pd.DataFrame(
                    columns=[
                        "proyecto",
                        "ecosistema",
                        "archivo_origen",
                        "dependencia",
                        "version_declarada",
                        "version_instalada",
                        "version_recomendada",
                        "tipo_dependencia",
                        "estado_actualizacion",
                        "riesgo",
                        "score",
                        "observacion",
                    ]
                )

            # 3. Preparar datos para HOJA 3: Vulnerabilidades
            vulns_rows = []
            for h in report.findings:
                if "Vulnerabilidad" not in h.finding_type:
                    continue

                # Intentar encontrar la vulnerabilidad correspondiente para extraer IDs específicos
                vuln_id = "Desconocido"
                cve_id = "N/A"
                ghsa_id = "N/A"
                fixed_ver = "N/A"

                # Resolver coincidencia de nombre
                match_v = next(
                    (
                        v
                        for v in report.vulnerabilities
                        if h.dependency.name.lower() in v.summary.lower()
                        or h.dependency.name.lower() in v.affected_versions
                    ),
                    None,
                )
                if match_v:
                    vuln_id = match_v.vulnerability_id
                    cve_id = match_v.cve or "N/A"
                    ghsa_id = match_v.ghsa or "N/A"
                    fixed_ver = match_v.fixed_versions or "Última estable"

                vulns_rows.append(
                    {
                        "proyecto": h.project,
                        "ecosistema": h.dependency.ecosystem.value,
                        "dependencia": h.dependency.name,
                        "version_instalada": h.dependency.installed_version,
                        "id_vulnerabilidad": vuln_id,
                        "cve": cve_id,
                        "ghsa": ghsa_id,
                        "severidad": h.severity.value,
                        "descripcion": h.impact,
                        "impacto_potencial": "Compromiso de integridad/disponibilidad.",
                        "version_corregida": fixed_ver,
                        "referencias": ", ".join(h.references) if h.references else "N/A",
                        "recomendacion": h.recommendation,
                    }
                )
            df_vulns = pd.DataFrame(vulns_rows)
            if df_vulns.empty:
                df_vulns = pd.DataFrame(
                    columns=[
                        "proyecto",
                        "ecosistema",
                        "dependencia",
                        "version_instalada",
                        "id_vulnerabilidad",
                        "cve",
                        "ghsa",
                        "severidad",
                        "descripcion",
                        "impacto_potencial",
                        "version_corregida",
                        "referencias",
                        "recomendacion",
                    ]
                )

            # 4. Preparar datos para HOJA 4: Actualizaciones Sugeridas
            updates_rows = []
            for rec in report.recommendations:
                # Obtener la dependencia correspondiente
                dep_name = rec.get("dependencia", "")
                dep_obj = next(
                    (d for d in report.dependencies if d.name.lower() == dep_name.lower()), None
                )

                # Clasificar riesgo e indicar acción
                tipo_act = "MINOR"
                if "mayor" in rec.get("accion_sugerida", "").lower():
                    tipo_act = "MAJOR"
                elif "parche" in rec.get("accion_sugerida", "").lower():
                    tipo_act = "PATCH"

                updates_rows.append(
                    {
                        "proyecto": rec.get("proyecto", ""),
                        "dependencia": dep_name,
                        "version_actual": dep_obj.installed_version if dep_obj else "0.0.0",
                        "version_recomendada": rec.get("version_recomendada", ""),
                        "tipo_actualizacion": tipo_act,
                        "riesgo_actualizacion": "HIGH"
                        if tipo_act == "MAJOR"
                        else ("MEDIUM" if tipo_act == "MINOR" else "LOW"),
                        "accion_sugerida": rec.get("accion_sugerida", ""),
                        "requiere_testing": "SÍ" if rec.get("requiere_testing", True) else "NO",
                    }
                )
            df_updates = pd.DataFrame(updates_rows)
            if df_updates.empty:
                df_updates = pd.DataFrame(
                    columns=[
                        "proyecto",
                        "dependencia",
                        "version_actual",
                        "version_recomendada",
                        "tipo_actualizacion",
                        "riesgo_actualizacion",
                        "accion_sugerida",
                        "requiere_testing",
                    ]
                )

            # 5. Preparar datos para HOJA 5: Riesgos de Configuración
            config_rows = []
            for h in report.findings:
                if "Vulnerabilidad" in h.finding_type or "Abandonada" in h.finding_type:
                    continue

                config_rows.append(
                    {
                        "proyecto": h.project,
                        "archivo": h.dependency.source_file,
                        "dependencia": h.dependency.name,
                        "problema": h.finding_type,
                        "severidad": h.severity.value,
                        "evidencia_segura": f"Versión declarada: {h.dependency.declared_version}",
                        "recomendacion": h.recommendation,
                    }
                )
            df_configs = pd.DataFrame(config_rows)
            if df_configs.empty:
                df_configs = pd.DataFrame(
                    columns=[
                        "proyecto",
                        "archivo",
                        "dependencia",
                        "problema",
                        "severidad",
                        "evidencia_segura",
                        "recomendacion",
                    ]
                )

            # 6. Preparar datos para HOJA 6: Errores
            errors_rows = []
            for err in report.errors:
                errors_rows.append(
                    {
                        "proyecto": err.get("proyecto", ""),
                        "archivo": err.get("archivo", ""),
                        "tipo_error": err.get("tipo_error", ""),
                        "mensaje_error": err.get("mensaje_error", ""),
                        "fecha_analisis": get_current_local_formatted(),
                    }
                )
            df_errors = pd.DataFrame(errors_rows)
            if df_errors.empty:
                df_errors = pd.DataFrame(
                    columns=["proyecto", "archivo", "tipo_error", "mensaje_error", "fecha_analisis"]
                )

            # Escribir las 6 hojas de forma estructurada a un libro Excel único con Pandas y openpyxl
            with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
                df_summary.to_excel(writer, sheet_name="Resumen", index=False)
                df_deps.to_excel(writer, sheet_name="Dependencias", index=False)
                df_vulns.to_excel(writer, sheet_name="Vulnerabilidades", index=False)
                df_updates.to_excel(writer, sheet_name="Actualizaciones Sugeridas", index=False)
                df_configs.to_excel(writer, sheet_name="Riesgos de Configuración", index=False)
                df_errors.to_excel(writer, sheet_name="Errores", index=False)

                # Ajustar anchos de columnas automáticamente en openpyxl para una estética visual pulida
                workbook = writer.book
                for sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    for col in sheet.columns:
                        max_len = max(len(str(cell.value or "")) for cell in col)
                        col_letter = col[0].column_letter
                        sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

            logger.info(f"Reporte Excel de múltiples hojas generado en: {target_path}")
            return target_path

        except Exception as e:
            logger.error(f"Error grave exportando reporte Excel: {e}")
            raise
