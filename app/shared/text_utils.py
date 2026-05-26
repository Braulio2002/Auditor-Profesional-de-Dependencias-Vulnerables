import re


def clean_dependency_name(name: str) -> str:
    """Limpia caracteres innecesarios o espacios en el nombre de una dependencia."""
    if not name:
        return ""
    # Quitar comillas, espacios iniciales/finales y saltos de línea
    name = name.strip().replace('"', "").replace("'", "")
    # Para paquetes de Python, a veces vienen con especificaciones de extras: ej. requests[security] -> requests
    name = re.sub(r"\[.*\]", "", name)
    return name.strip()


def sanitize_description(description: str, max_length: int = 150) -> str:
    """Recorta descripciones largas de vulnerabilidades para reportes visuales."""
    if not description:
        return "Sin descripción disponible."

    # Reemplazar saltos de línea por espacios
    clean_desc = re.sub(r"\s+", " ", description).strip()

    if len(clean_desc) <= max_length:
        return clean_desc

    return clean_desc[:max_length] + "..."
