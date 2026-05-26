import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    # Directorios base
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    datos_entrada_dir: Path = base_dir / "datos_entrada"
    datos_salida_dir: Path = base_dir / "datos_salida"

    # Modos de ejecución
    offline_mode: bool = False
    timeout_seconds: int = 10

    # Ecosistemas habilitados
    enabled_ecosystems: set[str] = field(
        default_factory=lambda: {
            "npm",
            "yarn",
            "pnpm",
            "pip",
            "poetry",
            "composer",
            "maven",
            "gradle",
            "go",
        }
    )

    # Archivos soportados por ecosistema
    supported_files: dict[str, str] = field(
        default_factory=lambda: {
            "package.json": "npm",
            "package-lock.json": "npm",
            "yarn.lock": "npm",
            "pnpm-lock.yaml": "npm",
            "requirements.txt": "pip",
            "pyproject.toml": "poetry",
            "poetry.lock": "poetry",
            "composer.json": "composer",
            "composer.lock": "composer",
            "pom.xml": "maven",
            "build.gradle": "gradle",
            "build.gradle.kts": "gradle",
            "go.mod": "go",
        }
    )

    # Carpetas excluidas del escaneo para evitar procesar dependencias de terceros o temporales
    excluded_dirs: set[str] = field(
        default_factory=lambda: {
            "node_modules",
            "vendor",
            "target",
            "dist",
            "build",
            ".git",
            ".idea",
            ".vscode",
            "venv",
            ".venv",
        }
    )

    # APIs externas de vulnerabilidades
    osv_api_url: str = "https://api.osv.dev/v1/query"
    nvd_api_key: str = os.getenv("NVD_API_KEY", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "")

    # Nombres base para reportes
    excel_report_name: str = "dependency_audit_report.xlsx"
    json_report_name: str = "dependency_audit_report.json"
    pdf_report_name: str = "dependency_audit_report.pdf"

    # Pesos de scoring (de 0 a 100)
    score_weights: dict[str, int] = field(
        default_factory=lambda: {
            "vulnerability_critical_exploitable": 100,
            "vulnerability_critical": 90,
            "vulnerability_high": 75,
            "vulnerability_medium": 50,
            "vulnerability_low": 25,
            "dependency_abandoned": 60,
            "version_very_outdated": 45,
            "version_unpinned": 30,
            "open_range": 25,
            "dependency_duplicate": 15,
            "no_findings": 0,
        }
    )

    def __post_init__(self):
        # Asegurar lectura de variables de entorno para offline_mode si aplica
        env_offline = os.getenv("OFFLINE_MODE", "").lower()
        if env_offline in ("true", "1", "yes"):
            self.offline_mode = True
