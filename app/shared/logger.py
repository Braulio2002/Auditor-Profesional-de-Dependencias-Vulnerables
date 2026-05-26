import logging
import sys


class ColorFormatter(logging.Formatter):
    """Formateador de logs profesional con soporte de color para terminal."""

    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    GREEN = "\x1b[32;20m"
    CYAN = "\x1b[36;20m"
    RESET = "\x1b[0m"

    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: GREEN + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMAT)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(name: str = "DependencyAuditor", level: int = logging.INFO) -> logging.Logger:
    """Configura y retorna el logger centralizado de la aplicación."""
    logger = logging.getLogger(name)

    # Evitar duplicar handlers si ya se ha configurado previamente
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Handler de consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColorFormatter())

    logger.addHandler(console_handler)
    return logger


# Instancia global por defecto
logger = setup_logger()
