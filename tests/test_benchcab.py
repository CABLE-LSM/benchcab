"""`pytest` tests for `benchcab.py`."""

import re
from contextlib import nullcontext as does_not_raise
from unittest import mock

import pytest

from benchcab.benchcab import Benchcab


@pytest.fixture(scope="module", autouse=True)
def _set_user_projects():
    with mock.patch("grp.getgrgid") as mocked_getgrid, mock.patch(
        "os.getgroups"
    ) as mocked_groups:
        type(mocked_getgrid.return_value).gr_name = mock.PropertyMock(
            return_value="hh5"
        )
        mocked_groups.return_value = [1]
        yield


@pytest.fixture(scope="module", params=["hh5", "invalid_project_name"])
def config_project(request):
    """Get config project name."""
    return request.param


# Error message if config project name cannot be resolved.
no_project_name_msg = re.escape(
    """Couldn't resolve project: check 'project' in config.yaml
       and/or $PROJECT set in ~/.config/gadi-login.conf
    """
)

# For testing whether user is member of necessary projects to run benchcab, we need to simulate the environment of Gadi
# TODO: Simulate Gadi environment for running tests for validating environment


@pytest.mark.skip()
@pytest.mark.parametrize(
    ("config_project", "pytest_error"),
    [
        ("hh5", does_not_raise()),
        (None, pytest.raises(AttributeError, match=no_project_name_msg)),
    ],
)
def test_project_name(config_project, pytest_error):
    """Tests whether config project name is suitable to run in Gadi environment."""
    app = Benchcab(benchcab_exe_path=None)
    with pytest_error:
        app._validate_environment(project=config_project, modules=[])


@pytest.mark.skip()
@pytest.mark.parametrize(
    ("config_project", "pytest_error"),
    [
        ("hh5", does_not_raise()),
        ("invalid_project_name", pytest.raises(PermissionError)),
    ],
)
def test_user_project_group(config_project, pytest_error):
    """Test _validate_environment for if current user's groups does not contain the project name."""
    app = Benchcab(benchcab_exe_path=None)
    with pytest_error:
        app._validate_environment(project=config_project, modules=[])
