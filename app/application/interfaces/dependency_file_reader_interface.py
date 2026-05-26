from abc import ABC, abstractmethod
from pathlib import Path

from app.domain.entities.dependency import Dependency


class DependencyFileReaderInterface(ABC):
    """Interfaz base (Puerto) para todos los lectores de archivos de dependencias."""

    @abstractmethod
    def read(self, file_path: Path) -> list[Dependency]:
        """Lee un archivo de dependencias en un formato específico y retorna sus dependencias.

        Args:
            file_path: Ruta absoluta al archivo de dependencias.

        Returns:
            List[Dependency]: Lista de dependencias extraídas.

        Raises:
            ReaderException: Si ocurre un error al parsear o leer el archivo.
        """
        pass
