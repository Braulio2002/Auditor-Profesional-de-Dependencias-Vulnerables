class DomainError(Exception):
    """Excepción base para todos los errores de dominio del auditor."""

    pass


class InvalidDependencyError(DomainError):
    """Lanzada cuando una dependencia tiene atributos inconsistentes o inválidos."""

    pass


class InvalidProjectError(DomainError):
    """Lanzada cuando un proyecto escaneado no tiene un nombre válido o su ruta no existe."""

    pass


class ReaderError(DomainError):
    """Lanzada cuando ocurre un error insalvable al leer un archivo de configuración de dependencias."""

    pass


class ProviderError(DomainError):
    """Lanzada cuando un proveedor de vulnerabilidades remoto responde con errores graves."""

    pass
