from pathlib import Path
import tempfile
import os
import yaml

from benchcab import benchtree
from benchcab import bench_config
from benchcab import get_cable


def checkout_branch(branch_id:str, opt:dict,tb:benchtree.BenchTree):

    # Check if the branch_id exists in file?
    locbranch = opt[branch_id]
    tr = get_cable.GetCable(src_dir=tb.src_dir, user=opt["user"])
    tr.main(**locbranch)

    print(Path.cwd())
    assert Path(f"src/{locbranch['name']}").is_dir(), "Directory does not exist"
    assert len(list(Path(f"src/{locbranch['name']}").iterdir())) > 0, "Directory is empty"

def test_create_minbenchtree(create_testconfig):
    """Test the min. directory tree is created"""

    td = create_testconfig[0]
    # Get into the temporary directory to test creating the directory structure
    os.chdir(td)

    tb = benchtree.BenchTree(Path(td))
    tb.create_minbenchtree()

    paths_to_create=[
        (td/"src").is_dir(),
        (td/"runs").is_dir(),
    ]
    assert all(paths_to_create)

    
def test_read_config(create_testconfig, testconfig):
    
    os.chdir(create_testconfig[0])
    TestSetup=bench_config.BenchSetup("config.yaml")
    # Get the branch information from the testconfig
    opt = TestSetup.read_config()

    assert opt == testconfig

def test_checkout_trunk(create_testconfig):

    td = create_testconfig[0]
    os.chdir(td)
    # Setup the benchmarking
    opt, _, tb = create_testconfig[1:]

    checkout_branch("trunk", opt, tb)

def test_checkout_user(create_testconfig):

    td = create_testconfig[0]
    os.chdir(td)
    # Setup the benchmarking
    opt, _, tb = create_testconfig[1:]

    checkout_branch("user_branch", opt, tb)
 
def test_checkout_share(create_testconfig):

    td = create_testconfig[0]
    os.chdir(td)
    # Setup the benchmarking
    opt, _, tb = create_testconfig[1:]

    checkout_branch("share", opt, tb)


