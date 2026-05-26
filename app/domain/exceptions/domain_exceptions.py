class DomainException(Exception):
    """Excepción base para todos los errores de dominio del auditor."""

    pass


class InvalidDependencyException(DomainException):
    """Lanzada cuando una dependencia tiene atributos inconsistentes o inválidos."""

    pass


class InvalidProjectException(DomainException):
    """Lanzada cuando un proyecto escaneado no tiene un nombre válido o su ruta no existe."""

    pass


class ReaderException(DomainException):
    """Lanzada cuando ocurre un error insalvable al leer un archivo de configuración de dependencias."""

    pass


class ProviderException(DomainException):
    """Lanzada cuando un proveedor de vulnerabilidades remoto responde con errores graves."""

    pass
