from pathlib import Path

from app.domain.value_objects.dependency_scope import DependencyScope
from app.domain.value_objects.ecosystem import Ecosystem
from app.infrastructure.readers.maven_dependency_reader import MavenDependencyReader


def test_read_maven_pom(tmp_path: Path):
    pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <properties>
        <jackson.version>2.12.3</jackson.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>${jackson.version}</version>
        </dependency>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.12</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""
    pom_file = tmp_path / "pom.xml"
    with open(pom_file, "w", encoding="utf-8") as f:
        f.write(pom_content)

    reader = MavenDependencyReader()
    dependencies = reader.read(pom_file)

    assert len(dependencies) == 2

    jackson = next(d for d in dependencies if "jackson-databind" in d.name)
    assert jackson.ecosystem == Ecosystem.MAVEN
    assert jackson.declared_version == "${jackson.version}"
    assert jackson.installed_version == "2.12.3"  # Resuelta con éxito
    assert jackson.scope == DependencyScope.PRODUCTION

    junit = next(d for d in dependencies if "junit" in d.name)
    assert junit.declared_version == "4.12"
    assert junit.installed_version == "4.12"
    assert junit.scope == DependencyScope.TEST
