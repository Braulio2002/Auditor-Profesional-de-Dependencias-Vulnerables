from app.domain.entities.dependency import Dependency
from app.domain.entities.dependency_finding import DependencyFinding
from app.domain.value_objects.risk_level import RiskLevel
from app.domain.value_objects.severity_level import SeverityLevel
from app.shared.constants import SENSITIVE_KEYWORDS
from app.shared.logger import logger


class RiskScoreCalculatorService:
    """Calcula el score de riesgo por dependencia y clasifica el riesgo general del proyecto."""

    def __init__(self, settings):
        self.settings = settings

    def is_sensitive_dependency(self, name: str) -> bool:
        """Determina si el nombre de la dependencia está relacionado con bibliotecas críticas de seguridad."""
        name_lower = name.lower()
        # Verificar si alguna palabra clave sensible está contenida en el nombre del paquete
        return any(kw in name_lower for kw in SENSITIVE_KEYWORDS)

    def calculate_score_and_level(
        self, dependency: Dependency, findings: list[DependencyFinding]
    ) -> tuple[int, SeverityLevel, RiskLevel]:
        """Calcula el score numérico final (0-100) de riesgo para una dependencia y su nivel correspondiente."""
        if not findings:
            return 0, SeverityLevel.INFO, RiskLevel.LOW

        # El score máximo de cualquier hallazgo individual para esta dependencia
        max_score = 0
        highest_severity = SeverityLevel.INFO

        # Encontrar el hallazgo con mayor impacto
        for finding in findings:
            if finding.risk_score > max_score:
                max_score = finding.risk_score
                highest_severity = finding.severity

        # ELEVACIÓN DE PRIORIDAD POR DEPENDENCIA SENSIBLE
        # Si es un componente sensible (criptografía, autenticación, base de datos) y tiene vulnerabilidades
        has_vulnerabilities = any(
            "Vulnerabilidad" in f.finding_type for f in findings)
        if has_vulnerabilities and self.is_sensitive_dependency(dependency.name):
            # Penalización por componente sensible: subir +15 puntos (máximo 100)
            original_score = max_score
            max_score = min(max_score + 15, 100)
            logger.warning(
                f"[DevSecOps Elevación] Dependencia sensible vulnerable detectada: {dependency.name}. "
                f"Elevando score de {original_score} a {max_score}."
            )
            # Elevar la severidad si es menor que HIGH
            if highest_severity in (SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.INFO):
                highest_severity = SeverityLevel.HIGH

        # Clasificación del nivel de riesgo basado en el score (0-100)
        # 0 a 20: Bajo | 21 a 50: Medio | 51 a 75: Alto | 76 a 100: Crítico
        if max_score >= 76:
            risk_level = RiskLevel.CRITICAL
        elif max_score >= 51:
            risk_level = RiskLevel.HIGH
        elif max_score >= 21:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return max_score, highest_severity, risk_level

    def calculate_project_risk(self, findings: list[DependencyFinding]) -> RiskLevel:
        """Determina el nivel de riesgo general del proyecto basado en sus hallazgos."""
        if not findings:
            return RiskLevel.LOW  # Sin riesgo relevante

        # Extraer severidades y scores
        scores = [f.risk_score for f in findings]
        max_score = max(scores) if scores else 0

        # Clasificar según el hallazgo más grave
        if any(f.severity == SeverityLevel.CRITICAL for f in findings) or max_score >= 76:
            return RiskLevel.CRITICAL

        # Si hay varios hallazgos de severidad ALTA
        high_findings_count = sum(
            1 for f in findings if f.severity == SeverityLevel.HIGH)
        if high_findings_count >= 2 or max_score >= 51:
            return RiskLevel.HIGH

        # Si predominan hallazgos de severidad MEDIA
        medium_findings_count = sum(
            1 for f in findings if f.severity == SeverityLevel.MEDIUM)
        if medium_findings_count >= 1 or max_score >= 21:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW
