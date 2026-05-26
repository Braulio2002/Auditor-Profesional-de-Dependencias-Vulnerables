from app.application.services.version_parser_service import VersionParserService


def test_version_parser_pinned():
    parser = VersionParserService()

    assert parser.is_pinned_version("1.2.3") is True
    assert parser.is_pinned_version("==1.2.3") is True
    assert parser.is_pinned_version("v1.2.3") is True

    assert parser.is_pinned_version("^1.2.3") is False
    assert parser.is_pinned_version("~1.2.3") is False
    assert parser.is_pinned_version("*") is False
    assert parser.is_pinned_version("latest") is False
    assert parser.is_pinned_version(">=1.2.3") is False


def test_version_parser_wildcards():
    parser = VersionParserService()

    assert parser.has_wildcards("1.*") is True
    assert parser.has_wildcards("latest") is True
    assert parser.has_wildcards("1.2.3") is False


def test_version_parser_open_ranges():
    parser = VersionParserService()

    assert parser.is_open_range(">=1.0.0") is True
    assert parser.is_open_range(">1.0.0") is True
    assert parser.is_open_range("*") is True

    assert parser.is_open_range(">=1.0.0,<2.0.0") is False
    assert parser.is_open_range("^1.0.0") is False


def test_parse_version_parts():
    parser = VersionParserService()

    major, minor, patch, tag = parser.parse_version_parts("1.2.3-beta.1")
    assert major == 1
    assert minor == 2
    assert patch == 3
    assert tag == "beta.1"

    major, minor, patch, tag = parser.parse_version_parts("==5.4")
    assert major == 5
    assert minor == 4
    assert patch == 0
    assert tag == ""
