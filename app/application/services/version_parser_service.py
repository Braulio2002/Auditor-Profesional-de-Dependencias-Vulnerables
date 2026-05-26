import re


class VersionParserService:
    """Interpreta formatos de versiones y evalúa si son seguros o demasiado abiertos."""

    def is_pinned_version(self, version: str) -> bool:
        """Determina si una especificación de versión representa un pin exacto (ej. 1.2.3 o ==1.2.3)."""
        if not version:
            return False

        version = version.strip()

        # Si tiene operadores de rango o comodines, no está fija
        if any(c in version for c in ["^", "~", "*", ">", "<", "latest", "any"]):
            return False

        # Para pip: django>=3.0 no está fija, django==3.0 sí
        if ">=" in version or "<=" in version or "!=" in version or ">" in version or "<" in version:
            return False

        # Si es un comodín completo
        if version in ("*", ""):
            return False

        return True

    def has_wildcards(self, version: str) -> bool:
        """Determina si la versión contiene comodines como * o la palabra 'latest'."""
        if not version:
            return False
        version_lower = version.lower()
        return "*" in version or "latest" in version or "any" in version or version_lower == ""

    def is_open_range(self, version: str) -> bool:
        """Determina si el rango de versión es demasiado abierto o inseguro (ej. >=1.0.0 sin límite superior)."""
        if not version:
            return False

        # >= o > sin límite superior (no hay un && o < o <= en la misma cadena)
        version_clean = version.replace(" ", "")
        if (">=" in version_clean or ">" in version_clean) and not (
            "<" in version_clean or "<=" in version_clean or "," in version_clean or "&&" in version_clean
        ):
            return True

        # Comodines y latest también califican como rango abierto
        if self.has_wildcards(version):
            return True

        return False

    def parse_version_parts(self, version: str) -> tuple[int, int, int, str]:
        """Intenta separar una versión en sus partes (Major, Minor, Patch, Pre-release).

        Retorna Tuple[Major, Minor, Patch, Tag]
        """
        # Limpiar prefijos de operador comunes
        clean_ver = version.strip()
        for prefix in ["v", "==", "^", "~", ">=", "<=", ">", "<"]:
            if clean_ver.startswith(prefix):
                clean_ver = clean_ver[len(prefix) :]

        # Expresión regular para Semantic Versioning básico
        match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:-([a-zA-Z0-9.]+))?", clean_ver)
        if match:
            major = int(match.group(1))
            minor = int(match.group(2)) if match.group(2) else 0
            patch = int(match.group(3)) if match.group(3) else 0
            tag = match.group(4) if match.group(4) else ""
            return major, minor, patch, tag

        return 0, 0, 0, ""
