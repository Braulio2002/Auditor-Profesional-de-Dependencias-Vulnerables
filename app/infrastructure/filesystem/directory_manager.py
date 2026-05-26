import json

from app.shared.logger import logger


class DirectoryManager:
    """Administra las carpetas físicas de entrada y salida, aprovisionando datos de prueba."""

    def __init__(self, settings):
        self.settings = settings

    def ensure_directories_exist(self) -> None:
        """Crea las carpetas de datos_entrada/ y datos_salida/ y sus archivos de demostración si están vacíos."""
        logger.info("Verificando carpetas de trabajo...")

        # Crear carpetas si no existen
        self.settings.datos_entrada_dir.mkdir(parents=True, exist_ok=True)
        self.settings.datos_salida_dir.mkdir(parents=True, exist_ok=True)

        # Crear .gitkeep en datos_salida/
        (self.settings.datos_salida_dir / ".gitkeep").touch()

        # Aprovisionar demos si datos_entrada/ está vacío (o solo tiene un .gitkeep)
        entrada_files = list(self.settings.datos_entrada_dir.iterdir())
        has_projects = any(f.is_dir() for f in entrada_files)

        if not has_projects:
            logger.info(
                "La carpeta 'datos_entrada/' está vacía. Generando proyectos de demostración para auditoría..."
            )
            self._create_demo_node_project()
            self._create_demo_python_project()
            self._create_demo_php_project()
            (self.settings.datos_entrada_dir / ".gitkeep").touch()
            logger.info(
                "Proyectos demo creados con éxito en 'datos_entrada/'.")

    def _create_demo_node_project(self) -> None:
        proj_dir = self.settings.datos_entrada_dir / "proyecto_demo_node"
        proj_dir.mkdir(parents=True, exist_ok=True)

        # Crear package.json
        pkg_data = {
            "name": "proyecto-demo-node",
            "version": "1.0.0",
            "description": "Proyecto de demostración vulnerable Node.js",
            "main": "index.js",
            "dependencies": {
                "lodash": "^4.17.15",
                "express": "~4.16.0",
                "axios": "*",
                "jsonwebtoken": "8.5.1",
            },
            "devDependencies": {"jest": "^29.0.0", "eslint": "latest"},
        }
        with open(proj_dir / "package.json", "w", encoding="utf-8") as f:
            json.dump(pkg_data, f, indent=2)

        # Crear package-lock.json simulado básico
        lock_data = {
            "name": "proyecto-demo-node",
            "version": "1.0.0",
            "lockfileVersion": 2,
            "requires": True,
            "dependencies": {
                "lodash": {
                    "version": "4.17.15",
                    "resolved": "https://registry.npmjs.org/lodash/-/lodash-4.17.15.tgz",
                },
                "express": {
                    "version": "4.16.4",
                    "resolved": "https://registry.npmjs.org/express/-/express-4.16.4.tgz",
                },
                "axios": {
                    "version": "0.21.1",
                    "resolved": "https://registry.npmjs.org/axios/-/axios-0.21.1.tgz",
                },
                "jsonwebtoken": {
                    "version": "8.5.1",
                    "resolved": "https://registry.npmjs.org/jsonwebtoken/-/jsonwebtoken-8.5.1.tgz",
                },
            },
        }
        with open(proj_dir / "package-lock.json", "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)

    def _create_demo_python_project(self) -> None:
        proj_dir = self.settings.datos_entrada_dir / "proyecto_demo_python"
        proj_dir.mkdir(parents=True, exist_ok=True)

        # requirements.txt
        req_content = (
            "# Requerimientos de Producción\n"
            "requests==2.20.0\n"
            "django>=3.2,<4.0\n"
            "urllib3==1.26.5\n"
            "cryptography\n"
            "pyyaml>=5.4\n"
            "\n"
            "# Requerimientos de Desarrollo\n"
            "pytest\n"
            "black==*\n"
        )
        with open(proj_dir / "requirements.txt", "w", encoding="utf-8") as f:
            f.write(req_content)

    def _create_demo_php_project(self) -> None:
        proj_dir = self.settings.datos_entrada_dir / "proyecto_demo_php"
        proj_dir.mkdir(parents=True, exist_ok=True)

        # composer.json
        composer_data = {
            "name": "demo/proyecto-php",
            "description": "Proyecto PHP de demostración",
            "require": {"php": ">=7.4", "laravel/framework": "^8.0", "guzzlehttp/guzzle": "^6.3"},
            "require-dev": {"phpunit/phpunit": "^9.0"},
        }
        with open(proj_dir / "composer.json", "w", encoding="utf-8") as f:
            json.dump(composer_data, f, indent=2)

        # composer.lock básico simulado
        lock_data = {
            "_readme": [],
            "packages": [
                {"name": "laravel/framework", "version": "8.50.0", "source": {}},
                {"name": "guzzlehttp/guzzle", "version": "6.5.5", "source": {}},
            ],
            "packages-dev": [{"name": "phpunit/phpunit", "version": "9.5.2", "source": {}}],
        }
        with open(proj_dir / "composer.lock", "w", encoding="utf-8") as f:
            json.dump(lock_data, f, indent=2)
