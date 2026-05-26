from typing import Any

from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.entities.project_scan_target import ProjectScanTarget
from app.domain.value_objects.risk_level import RiskLevel


class ExecutiveSummaryService:
    """Genera resúmenes ejecutivos comprensibles orientados a responsables de seguridad y líderes técnicos."""

    def generate_summary(
        self,
        projects: list[ProjectScanTarget],
        dependencies: list[Dependency],
        findings: list[DependencyFinding],
        errors: list[dict[str, Any]],
        overall_risk: RiskLevel,
    ) -> dict[str, Any]:

        # Conteo de vulnerabilidades por severidad
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        vulnerable_deps = set()
        abandoned_deps = set()
        unpinned_deps = set()

        for f in findings:
            severity_counts[f.severity.value] = severity_counts.get(f.severity.value, 0) + 1

            if "Vulnerabilidad" in f.finding_type:
                vulnerable_deps.add(f.dependency.name)
            elif "Abandonada" in f.finding_type:
                abandoned_deps.add(f.dependency.name)
            elif "No Fijada" in f.finding_type:
                unpinned_deps.add(f.dependency.name)

        # Explicación de negocio del riesgo
        risk_explanations = {
            RiskLevel.CRITICAL: (
                "CRÍTICO: El proyecto contiene al menos una vulnerabilidad crítica explotable "
                "en una biblioteca central. Se recomienda encarecidamente corregirla inmediatamente "
                "para evitar posibles intrusiones o robo de información."
            ),
            RiskLevel.HIGH: (
                "ALTO: Se identificaron riesgos significativos o múltiples vulnerabilidades severas "
                "que exponen el entorno. Requiere remediación prioritaria en el ciclo actual "
                "de desarrollo."
            ),
            RiskLevel.MEDIUM: (
                "MEDIO: Hay dependencias desactualizadas o configuraciones de versiones inseguras. "
                "Planificar mitigación en las próximas ventanas de mantenimiento."
            ),
            RiskLevel.LOW: (
                "BAJO: El ecosistema se encuentra mayormente estable y seguro. Mantener vigilancia "
                "habitual y realizar actualizaciones de mantenimiento ordinarias."
            ),
        }

        return {
            "total_proyectos": len(projects),
            "total_dependencias": len(dependencies),
            "dependencias_unicas": len({d.name for d in dependencies}),
            "dependencias_vulnerables": len(vulnerable_deps),
            "dependencias_abandonadas": len(abandoned_deps),
            "dependencias_sin_pin": len(unpinned_deps),
            "conteo_hallazgos_severidad": severity_counts,
            "total_errores": len(errors),
            "riesgo_general": overall_risk.value,
            "explicacion_riesgo": risk_explanations.get(overall_risk, "Riesgo no definido."),
            "proyectos_detalles": [
                {
                    "nombre": p.name,
                    "ecosistemas": [eco.value for eco in p.detected_ecosystems],
                    "archivos_detectados": len(p.dependency_files),
                }
                for p in projects
            ],
        }
