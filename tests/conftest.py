import pytest
import os
import yaml
from pathlib import Path

from benchcab import bench_config
from benchcab import get_cable

@pytest.fixture
def testconfig():
    # Test config
    conf = {
        "use_branches":["user_branch","trunk"],
        "user_branch":{
            "name": "v3.0-YP-changes",
            "revision": -1,
            "trunk": False,
            "share_branch": False,
            },
        "trunk":{
            "name": "trunk",
            "revision": 9000,
            "trunk": True,
            "share_branch": False,
            },
        "share":{
            "name": "integration",
            "revision": -1,
            "trunk": False,
            "share_branch": True,
            },
        "user":os.environ["USER"],
        "project":os.environ["PROJECT"],
        "modules":[
            "intel-compiler/2021.1.1",
            "openmpi/4.1.0",
            "netcdf/4.7.4",
        ],
        }
    return conf

@pytest.fixture
def create_testconfig(testconfig, tmp_path):

    os.chdir(tmp_path)
    with open("config.yaml", "w") as fout:
        yaml.dump(testconfig,fout)

    TestSetup=bench_config.BenchSetup("config.yaml")
    # return the config options, compilation options and directory tree:
    # opt, compilation_opt, benchdirs
    opt, compilation_opt, benchdirs = TestSetup.setup_bench()

    return tmp_path, opt, compilation_opt, benchdirs
