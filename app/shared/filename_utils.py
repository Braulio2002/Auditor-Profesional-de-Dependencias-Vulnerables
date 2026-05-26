from pathlib import Path


def get_unique_filename(directory: Path, base_filename: str) -> Path:
    """Retorna una ruta de archivo única. Si el archivo base ya existe, agrega un sufijo incremental.

    Ejemplo:
        get_unique_filename(Path("/salida"), "reporte.xlsx")
        -> Si existe, retorna Path("/salida/reporte_1.xlsx")
    """
    path = directory / base_filename
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix

    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = directory / new_filename
        if not new_path.exists():
            return new_path
        counter += 1
