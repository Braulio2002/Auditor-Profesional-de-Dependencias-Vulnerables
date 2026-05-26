from pathlib import Path

from app.domain.entities.dependency_audit_report import DependencyAuditReport
from app.domain.value_objects.severity_level import SeverityLevel
from app.shared.date_utils import get_current_local_formatted
from app.shared.filename_utils import get_unique_filename
from app.shared.logger import logger

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PdfReportExporter:
    """Exporta el reporte consolidado de auditoría a formato PDF ejecutivo altamente estético y estructurado."""

    def __init__(self, settings):
        self.settings = settings

    def export(self, report: DependencyAuditReport, output_dir: Path) -> Path:
        target_path = get_unique_filename(output_dir, self.settings.pdf_report_name)

        if not REPORTLAB_AVAILABLE:
            logger.warning("reportlab no está instalado. Omitiendo la generación del reporte PDF.")
            # Crear un archivo de log/texto indicando la falta de librería para que no rompa el flujo
            with open(target_path.with_suffix(".txt"), "w", encoding="utf-8") as f:
                f.write(
                    "Instale 'reportlab' para habilitar la exportación del reporte ejecutivo PDF."
                )
            return target_path.with_suffix(".txt")

        logger.info("Generando reporte ejecutivo PDF...")

        try:
            # Configurar el documento
            doc = SimpleDocTemplate(
                str(target_path),
                pagesize=letter,
                rightMargin=54,
                leftMargin=54,
                topMargin=54,
                bottomMargin=54,
            )

            styles = getSampleStyleSheet()

            # Colores corporativos premium (DevSecOps)
            primary_color = colors.HexColor("#1A365D")  # Azul Oscuro
            accent_color = colors.HexColor("#E53E3E")  # Rojo Alerta
            text_dark = colors.HexColor("#2D3748")  # Gris Carbón
            bg_light = colors.HexColor("#F7FAFC")  # Gris Claro

            # Estilos personalizados
            title_style = ParagraphStyle(
                "CoverTitle",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=28,
                leading=34,
                textColor=primary_color,
                alignment=TA_CENTER,
            )

            subtitle_style = ParagraphStyle(
                "CoverSubtitle",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=14,
                leading=18,
                textColor=colors.HexColor("#718096"),
                alignment=TA_CENTER,
            )

            h1_style = ParagraphStyle(
                "SectionHeading",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=20,
                leading=24,
                textColor=primary_color,
                spaceAfter=15,
                keepWithNext=True,
            )

            body_style = ParagraphStyle(
                "CustomBody",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=10,
                leading=14,
                textColor=text_dark,
            )

            bold_body_style = ParagraphStyle(
                "BoldBody", parent=body_style, fontName="Helvetica-Bold"
            )

            table_header_style = ParagraphStyle(
                "TableHeader",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=9,
                leading=11,
                textColor=colors.white,
            )

            table_cell_style = ParagraphStyle(
                "TableCell",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=8,
                leading=10,
                textColor=text_dark,
            )

            critical_style = ParagraphStyle(
                "CriticalCell",
                parent=table_cell_style,
                fontName="Helvetica-Bold",
                textColor=accent_color,
            )

            story = []

            # ================= PAGINA 1: PORTADA =================
            story.append(Spacer(1, 1.5 * inch))
            # Icono representativo en texto
            story.append(Paragraph("🛡️", ParagraphStyle("Shield", fontSize=60, alignment=TA_CENTER)))
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("Auditor Profesional de Dependencias Vulnerables", title_style))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph("Reporte Ejecutivo de Seguridad y Supply Chain", subtitle_style))
            story.append(Spacer(1, 2 * inch))

            # Tabla de metadatos de portada
            meta_data = [
                [
                    Paragraph("Fecha del Análisis:", bold_body_style),
                    Paragraph(get_current_local_formatted(), body_style),
                ],
                [
                    Paragraph("Nivel de Riesgo General:", bold_body_style),
                    Paragraph(
                        report.summary.get("riesgo_general", "BAJO"),
                        critical_style
                        if report.summary.get("riesgo_general")
                        in ("CRITICAL", "CRÍTICO", "HIGH", "ALTO")
                        else body_style,
                    ),
                ],
                [
                    Paragraph("Total Proyectos Escaneados:", bold_body_style),
                    Paragraph(str(report.summary.get("total_proyectos", 0)), body_style),
                ],
                [
                    Paragraph("Total Dependencias Analizadas:", bold_body_style),
                    Paragraph(str(report.summary.get("total_dependencias", 0)), body_style),
                ],
            ]
            t_meta = Table(meta_data, colWidths=[2.2 * inch, 4 * inch])
            t_meta.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
                        ("PADDING", (0, 0), (-1, -1), 10),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )
            story.append(t_meta)
            story.append(PageBreak())

            # ================= PAGINA 2: RESUMEN EJECUTIVO =================
            story.append(Paragraph("Resumen Ejecutivo de Seguridad", h1_style))
            summary_text = (
                f"Este reporte técnico recopila los resultados de la auditoría de seguridad defensiva de dependencias "
                f"realizada en <b>{report.summary.get('total_proyectos', 0)} proyectos</b> del ecosistema. El análisis identifica "
                f"vulnerabilidades conocidas (CVE/GHSA), configuraciones de versiones inseguras, bibliotecas abandonadas o deprecadas "
                f"y duplicaciones que comprometen la cadena de suministro del software (supply chain security)."
            )
            story.append(Paragraph(summary_text, body_style))
            story.append(Spacer(1, 0.2 * inch))

            # Explicación del riesgo
            risk_desc = report.summary.get("explicacion_riesgo", "Sin explicación disponible.")
            story.append(Paragraph("<b>Evaluación de Riesgo de Negocio:</b>", bold_body_style))
            story.append(Spacer(1, 0.05 * inch))
            story.append(
                Paragraph(
                    risk_desc,
                    ParagraphStyle(
                        "RiskDesc",
                        parent=body_style,
                        backColor=bg_light,
                        borderColor=primary_color,
                        borderWidth=1,
                        borderPadding=8,
                    ),
                )
            )
            story.append(Spacer(1, 0.3 * inch))

            # Métricas rápidas en tabla
            story.append(
                Paragraph(
                    "Métricas de Vulnerabilidades Encontradas",
                    ParagraphStyle("Sub", parent=h1_style, fontSize=12, spaceAfter=8),
                )
            )

            counts = report.summary.get("conteo_hallazgos_severidad", {})
            metrics_data = [
                [
                    Paragraph("Severidad del Hallazgo", table_header_style),
                    Paragraph("Total Detectado", table_header_style),
                ],
                [
                    Paragraph("🔴 Crítico", bold_body_style),
                    Paragraph(str(counts.get("CRITICAL", 0)), body_style),
                ],
                [
                    Paragraph("🟠 Alto", bold_body_style),
                    Paragraph(str(counts.get("HIGH", 0)), body_style),
                ],
                [
                    Paragraph("🟡 Medio", bold_body_style),
                    Paragraph(str(counts.get("MEDIUM", 0)), body_style),
                ],
                [
                    Paragraph("🟢 Bajo / Informativo", bold_body_style),
                    Paragraph(str(counts.get("LOW", 0) + counts.get("INFO", 0)), body_style),
                ],
            ]
            t_metrics = Table(metrics_data, colWidths=[3 * inch, 3.2 * inch])
            t_metrics.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(t_metrics)
            story.append(Spacer(1, 0.4 * inch))

            # ================= TOP RIESGOS / CONTEXTO =================
            story.append(
                Paragraph(
                    "Top Riesgos y Dependencias Sensibles",
                    ParagraphStyle("Sub2", parent=h1_style, fontSize=12, spaceAfter=8),
                )
            )
            sensitive_text = (
                "Nuestra auditoría presta especial atención a componentes de seguridad crítica como "
                "autenticación (JWT, cookies, OAuth), criptografía (cifrado, contraseñas), bases de datos y ORMs. "
                "Cualquier vulnerabilidad en estas capas se prioriza con un score incrementado para llamar a la "
                "atención inmediata de los ingenieros de DevSecOps."
            )
            story.append(Paragraph(sensitive_text, body_style))
            story.append(PageBreak())

            # ================= PAGINA 3: DETALLE TÉCNICO DE VULNERABILIDADES =================
            story.append(Paragraph("Detalle de Vulnerabilidades Críticas y Altas", h1_style))

            crit_high_findings = [
                f
                for f in report.findings
                if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
            ]

            if not crit_high_findings:
                story.append(
                    Paragraph(
                        "✅ Excelente: No se han detectado vulnerabilidades de severidad Crítica o Alta en los proyectos analizados.",
                        body_style,
                    )
                )
            else:
                table_data = [
                    [
                        Paragraph("Proyecto", table_header_style),
                        Paragraph("Dependencia", table_header_style),
                        Paragraph("Versión", table_header_style),
                        Paragraph("Severidad", table_header_style),
                        Paragraph("Hallazgo", table_header_style),
                    ]
                ]

                for f in crit_high_findings[:15]:  # Mostrar los primeros 15 para mantenerlo limpio
                    table_data.append(
                        [
                            Paragraph(f.project, table_cell_style),
                            Paragraph(f.dependency.name, table_cell_style),
                            Paragraph(f.dependency.installed_version, table_cell_style),
                            Paragraph(
                                f.severity.value,
                                critical_style
                                if f.severity == SeverityLevel.CRITICAL
                                else table_cell_style,
                            ),
                            Paragraph(f.finding_type, table_cell_style),
                        ]
                    )

                t_vulns = Table(
                    table_data,
                    colWidths=[1.2 * inch, 1.5 * inch, 0.9 * inch, 0.9 * inch, 2.2 * inch],
                )
                t_vulns.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                            ("PADDING", (0, 0), (-1, -1), 5),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.append(t_vulns)

            story.append(Spacer(1, 0.3 * inch))

            # ================= ACCIONES RECOMENDADAS =================
            story.append(
                Paragraph(
                    "Plan de Remediación Sugerido",
                    ParagraphStyle("Sub3", parent=h1_style, fontSize=12, spaceAfter=8),
                )
            )

            if not report.recommendations:
                story.append(
                    Paragraph(
                        "No se requieren acciones urgentes de remediación. Mantener el software actualizado periódicamente.",
                        body_style,
                    )
                )
            else:
                rec_text = "Se aconseja seguir las siguientes directrices técnicas para corregir los riesgos descubiertos:\n"
                story.append(Paragraph(rec_text, body_style))
                story.append(Spacer(1, 0.1 * inch))

                for idx, rec in enumerate(report.recommendations[:5]):  # Mostrar top 5
                    bullet = f"<b>{idx + 1}. {rec.get('dependencia')} ({rec.get('proyecto')}):</b> {rec.get('accion_sugerida')}"
                    story.append(
                        Paragraph(
                            bullet,
                            ParagraphStyle(
                                "Bullet", parent=body_style, leftIndent=20, bulletIndent=10
                            ),
                        )
                    )
                    story.append(Spacer(1, 0.05 * inch))

            story.append(Spacer(1, 0.4 * inch))

            # Conclusiones finales
            story.append(
                Paragraph(
                    "Conclusión del Auditor",
                    ParagraphStyle("Sub4", parent=h1_style, fontSize=12, spaceAfter=8),
                )
            )
            concl = (
                "La seguridad en el supply chain es un esfuerzo continuo. Mantener dependencias actualizadas "
                "de forma recurrente mediante canalizaciones automáticas de CI/CD (DevSecOps) previene activamente "
                "la exposición a exploits de vulnerabilidades conocidas. Este reporte debe ser utilizado como un baseline "
                "de hardening técnico para robustecer el ecosistema."
            )
            story.append(Paragraph(concl, body_style))

            # Compilar el PDF
            doc.build(story)
            logger.info(f"Reporte ejecutivo PDF generado correctamente en: {target_path}")
            return target_path

        except Exception as e:
            logger.error(f"Error inesperado al generar PDF con reportlab: {e}")
            raise
