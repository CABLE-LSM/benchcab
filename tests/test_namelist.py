"""`pytest` tests for namelist.py."""

from pathlib import Path

import f90nml
import pytest

from benchcab.utils.namelist import patch_namelist, patch_remove_namelist


class TestPatchNamelist:
    """Tests for `patch_namelist()`."""

    @pytest.fixture()
    def nml_path(self):
        """Return a path to a namelist file used for testing."""
        return Path("test.nml")

    def test_patch_on_non_existing_namelist_file(self, nml_path):
        """Success case: patch non-existing namelist file."""
        patch = {"cable": {"file": "/path/to/file", "bar": 123}}
        patch_namelist(nml_path, patch)
        assert f90nml.read(nml_path) == patch

    def test_patch_on_non_empty_namelist_file(self, nml_path):
        """Success case: patch non-empty namelist file."""
        f90nml.write({"cable": {"file": "/path/to/file", "bar": 123}}, nml_path)
        patch_namelist(nml_path, {"cable": {"some": {"parameter": True}, "bar": 456}})
        assert f90nml.read(nml_path) == {
            "cable": {
                "file": "/path/to/file",
                "bar": 456,
                "some": {"parameter": True},
            }
        }

    def test_empty_patch_does_nothing(self, nml_path):
        """Success case: empty patch does nothing."""
        f90nml.write({"cable": {"file": "/path/to/file", "bar": 123}}, nml_path)
        prev = f90nml.read(nml_path)
        patch_namelist(nml_path, {})
        assert f90nml.read(nml_path) == prev


class TestPatchRemoveNamelist:
    """Tests for `patch_remove_namelist()`."""

    @pytest.fixture()
    def nml(self):
        """Return a namelist dictionary used for testing."""
        return {
            "cable": {
                "cable_user": {
                    "some_parameter": True,
                    "new_feature": True,
                },
            },
        }

    @pytest.fixture()
    def nml_path(self, nml):
        """Create a namelist file and return its path."""
        _nml_path = Path("test.nml")
        f90nml.write(nml, _nml_path)
        return _nml_path

    def test_remove_namelist_parameter_from_derived_type(self, nml_path):
        """Success case: remove a namelist parameter from derrived type."""
        patch_remove_namelist(
            nml_path, {"cable": {"cable_user": {"new_feature": True}}}
        )
        assert f90nml.read(nml_path) == {
            "cable": {"cable_user": {"some_parameter": True}}
        }

    def test_empty_patch_remove_does_nothing(self, nml_path, nml):
        """Success case: empty patch_remove does nothing."""
        patch_remove_namelist(nml_path, {})
        assert f90nml.read(nml_path) == nml

    def test_key_error_raised_for_non_existent_namelist_parameter(self, nml_path):
        """Failure case: test patch_remove KeyError exeption."""
        with pytest.raises(
            KeyError,
            match=f"Namelist parameters specified in `patch_remove` do not exist in {nml_path.name}.",
        ):
            patch_remove_namelist(nml_path, {"cable": {"foo": {"bar": True}}})
