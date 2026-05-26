# Constantes del Auditor de Dependencias

# Palabras clave para dependencias sensibles (Criptografía, Auth, Web, etc.)
SENSITIVE_KEYWORDS: set[str] = {
    # Autenticación y Autorización
    "auth",
    "login",
    "oauth",
    "jwt",
    "session",
    "passport",
    "keycloak",
    "security",
    "identity",
    # Criptografía
    "crypto",
    "cryptography",
    "hash",
    "bcrypt",
    "scrypt",
    "argon2",
    "ssl",
    "tls",
    "cipher",
    "pycrypto",
    "pycryptodome",
    # Bases de datos y ORMs
    "db",
    "database",
    "orm",
    "sqlalchemy",
    "prisma",
    "hibernate",
    "mongoose",
    "sequelize",
    "mysql",
    "postgres",
    "postgresql",
    "sqlite",
    "mongodb",
    "redis",
    "driver",
    # Subida de archivos y parseo
    "upload",
    "multer",
    "xml",
    "etree",
    "expat",
    "yaml",
    "toml",
    "json",
    "serializer",
    "pickle",
    "protobuf",
    # Frameworks Web
    "express",
    "koa",
    "django",
    "flask",
    "fastapi",
    "laravel",
    "spring",
    "struts",
    "next",
    "react",
    "vue",
    "angular",
}

# Acciones de recomendación por nivel de riesgo
RECOMMENDED_ACTIONS: dict[str, str] = {
    "CRITICAL": "Actualización inmediata obligatoria. Detener despliegues hasta aplicar el parche en producción.",
    "HIGH": "Actualizar de forma prioritaria en el próximo sprint. Requiere validación y pruebas de regresión.",
    "MEDIUM": "Planificar actualización a medio plazo. Probar compatibilidad en entorno de staging.",
    "LOW": "Actualizar durante tareas de mantenimiento ordinario. Mantener bajo observación.",
}

# Tipos de Hallazgos
FINDING_VULNERABILITY = "Vulnerabilidad Conocida"
FINDING_OUTDATED = "Dependencia Desactualizada"
FINDING_ABANDONED = "Dependencia Abandonada"
FINDING_UNPINNED = "Versión No Fijada"
FINDING_OPEN_RANGE = "Rango de Versión Inseguro"
FINDING_DUPLICATE = "Dependencia Duplicada"
