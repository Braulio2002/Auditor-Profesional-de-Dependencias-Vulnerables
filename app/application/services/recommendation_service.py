from typing import Any

from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.severity_level import SeverityLevel
from app.shared.constants import RECOMMENDED_ACTIONS


class RecommendationService:
    """Genera recomendaciones técnicas estructuradas y guías de pruebas post-actualización."""

    def generate_recommendations(self, findings: list[DependencyFinding]) -> list[dict[str, Any]]:
        recommendations: list[dict[str, Any]] = []

        # Agrupar hallazgos prioritarios (Críticos y Altos)
        critical_and_high = [f for f in findings if f.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)]

        for finding in critical_and_high:
            dep = finding.dependency

            # Guía de pruebas según el impacto y ecosistema
            testing_strategy = (
                "1. Ejecutar las pruebas unitarias del proyecto.\n"
                "2. Validar manualmente la integración de las funcionalidades que utilizan esta biblioteca.\n"
                "3. Monitorear los logs en entorno de testing/staging en búsqueda de errores de regresión."
            )

            if dep.name in ("jsonwebtoken", "jwt", "cryptography", "crypto", "pycryptodome"):
                testing_strategy += (
                    "\n⚠️ CRÍTICO: Validar la autenticación de usuarios, la expiración de tokens "
                    "y el firmado/verificación criptográfica."
                )
            elif dep.name in ("express", "django", "flask", "laravel/framework", "spring"):
                testing_strategy += (
                    "\n⚠️ FRAMEWORK: Realizar un smoke-test completo de las rutas del backend "
                    "y controladores principales."
                )

            recommendations.append(
                {
                    "proyecto": finding.project,
                    "dependencia": dep.name,
                    "ecosistema": dep.ecosystem.value,
                    "hallazgo": finding.finding_type,
                    "severidad": finding.severity.value,
                    "accion_sugerida": finding.recommendation
                    or RECOMMENDED_ACTIONS.get(finding.severity.value, "Actualizar paquete."),
                    "requiere_testing": finding.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH),
                    "plan_de_pruebas": testing_strategy,
                }
            )

        return recommendations
