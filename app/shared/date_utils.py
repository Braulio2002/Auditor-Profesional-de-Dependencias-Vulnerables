from datetime import UTC, datetime


def get_current_utc_iso() -> str:
    """Retorna la fecha y hora actual en UTC con formato ISO 8601."""
    return datetime.now(UTC).isoformat()


def get_current_local_formatted() -> str:
    """Retorna la fecha y hora local formateada de forma legible."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
