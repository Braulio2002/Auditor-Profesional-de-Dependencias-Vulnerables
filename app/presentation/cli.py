import sys

from app.application.use_cases.audit_dependencies_use_case import AuditDependenciesUseCase
from app.domain.entities.dependency_audit_report import DependencyAuditReport
from app.shared.logger import logger


class CLI:
    """Capa de Presentación encargada de interactuar con el usuario y formatear los resúmenes en consola."""

    def __init__(self, use_case: AuditDependenciesUseCase):
        self.use_case = use_case

    def display_banner(self) -> None:
        """Dibuja un banner ASCII DevSecOps premium en consola."""
        banner = """
======================================================================
     🛡️   AUDITOR PROFESIONAL DE DEPENDENCIAS VULNERABLES   🛡️
======================================================================
   Herramienta Defensiva de Seguridad de Supply Chain y DevSecOps
======================================================================
"""
        print(banner)

    def run(self) -> None:
        self.display_banner()

        try:
            # Ejecutar el caso de uso principal
            report = self.use_case.execute()

            # Mostrar resumen ejecutivo formateado en consola
            self.display_summary(report)

        except Exception as e:
            logger.critical(
                f"Ha ocurrido un error fatal durante la ejecución de la auditoría: {e}",
                exc_info=True,
            )
            sys.exit(1)

    def display_summary(self, report: DependencyAuditReport) -> None:
        """Formatea y pinta un panel de control resumen en la consola."""
        summary = report.summary

        print("\n" + "=" * 70)
        print("                 📈 PANEL RESUMEN DE SEGURIDAD")
        print("=" * 70)
        print(f" Proyectos Analizados:        {summary.get('total_proyectos', 0)}")
        print(f" Dependencias Totales:        {summary.get('total_dependencias', 0)}")
        print(f" Dependencias Vulnerables:    {summary.get('dependencias_vulnerables', 0)}")
        print(f" Dependencias Abandonadas:    {summary.get('dependencias_abandonadas', 0)}")
        print(f" Dependencias sin Pin Fijo:   {summary.get('dependencias_sin_pin', 0)}")

        print("-" * 70)
        print(" Hallazgos por Severidad:")
        counts = summary.get("conteo_hallazgos_severidad", {})
        print(f"   🔴 CRÍTICOS:  {counts.get('CRITICAL', 0)}")
        print(f"   🟠 ALTOS:     {counts.get('HIGH', 0)}")
        print(f"   🟡 MEDIOS:    {counts.get('MEDIUM', 0)}")
        print(f"   🟢 BAJOS:     {counts.get('LOW', 0) + counts.get('INFO', 0)}")

        print("-" * 70)
        risk_color = (
            "\x1b[31;1m" if summary.get("riesgo_general") in ("CRITICAL", "CRÍTICO", "HIGH", "ALTO") else "\x1b[32;1m"
        )
        reset = "\x1b[0m"
        print(f" RIESGO GENERAL DEL PROYECTO: {risk_color}{summary.get('riesgo_general', 'BAJO')}{reset}")
        print(f" Explicación: {summary.get('explicacion_riesgo', '')}")

        if report.errors:
            print("-" * 70)
            print(
                f" ⚠️  SE REGISTRARON {len(report.errors)} ERRORES DURANTE EL PROCESAMIENTO (REVISAR PESTAÑA 'Errores')."
            )

        print("=" * 70)
        print(" ✅ Reportes técnicos exportados con éxito en la carpeta: 'datos_salida/'")
        print(" Proceso finalizado satisfactoriamente.")
        print("=" * 70 + "\n")
