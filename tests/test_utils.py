"""Tests for utilities."""

import pytest

import benchcab.utils as bu


def test_get_installed_root():
    """Test get_installed_root()."""
    # Test it actually returns something. We should be able to mock this.
    assert bu.get_installed_root()


def test_load_package_data_pass():
    """Test load_package_data() passes as expected."""
    assert isinstance(bu.load_package_data("config-schema.yml"), dict)


def test_load_package_data_fail():
    """Test load_package_data() fails as expected."""
    with pytest.raises(FileNotFoundError):
        _ = bu.load_package_data("config-missing.yml")


def test_interpolate_string_template_pass():
    """Test interpolate_string_template() passes as expected."""
    result = bu.interpolate_string_template("I should {{status}}", status="pass")
    assert result == "I should pass"


def test_interpolate_string_template_fail():
    """Test interpolate_string_template() fails as expected."""
    result = bu.interpolate_string_template("I should {{status}}", status="fail")
    assert result != "I should not pass"


def test_interpolate_file_template_pass():
    """Test interpolate_file_template() passes as expected."""
    result = bu.interpolate_file_template("test/template.j2", myarg="PASS")
    assert result == "This is a template. PASS"


def test_interpolate_file_template_fail():
    """Test interpolate_file_template() fails as expected."""
    result = bu.interpolate_file_template("test/template.j2", notmyarg="PASS")
    assert result != "This is a template. PASS"


def test_get_logger_singleton_pass():
    """Test get_logger() returns a singleton object..."""
    logger1 = bu.get_logger(name="benchcab")
    logger2 = bu.get_logger(name="benchcab")

    assert logger1 is logger2


def test_get_logger_singleton_fail():
    """Test get_logger() returns a singleton object..."""
    logger1 = bu.get_logger(name="benchcab")
    logger2 = bu.get_logger(name="benchcab2")

    assert logger1 is not logger2
