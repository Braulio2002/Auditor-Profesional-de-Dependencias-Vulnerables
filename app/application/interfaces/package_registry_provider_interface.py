from abc import ABC, abstractmethod

from app.domain.value_objects.ecosystem import Ecosystem


class PackageRegistryProviderInterface(ABC):
    """Interfaz base (Puerto) para consultar las versiones disponibles en registros públicos de paquetes."""

    @abstractmethod
    def get_latest_version(self, name: str, ecosystem: Ecosystem) -> str | None:
        """Consulta el registro público y retorna la última versión estable recomendada.

        Args:
            name: Nombre de la biblioteca.
            ecosystem: Ecosistema tecnológico (npm, pip, composer, etc.).

        Returns:
            Optional[str]: La última versión estable en formato string, o None si falla.
        """
        pass
