import yaml
from pathlib import Path
import os
from benchcab.set_default_paths import set_paths
from benchcab.benchtree import BenchTree

class BenchSetup(object):
    def __init__(self, myconfig:str):
        """
        myconfig: str, Name of the config file to use for setup."""

        self.myconfig = myconfig

    @staticmethod
    def check_config(opt:dict):
        """Run some checks on the config file to ensure the data is coherent.
        check1: make sure the names in use_branches are keys in the dictionary.
        check2: make sure all required entries are listed
        check3: add revision pointing to HEAD of branch if missing for one branch
        """

        assert all([x in opt for x in opt["use_branches"][0:2]]), "At least one of the first 2 aliases " \
            " listed in 'use_branches' is not an entry in the config file to define a CABLE branch."

        assert all([x in opt for x in [
            "use_branches",
            "project",
            "user",
            "modules",
            ]]), "The config file does not list all required entries. "\
                "Those are 'use_branches', 'project', 'user', 'modules'"
        
        assert len(opt["use_branches"]) >= 2, "You need to list 2 branches in 'use_branches'"
        if len(opt["use_branches"]) > 2:
            print("------------------------------------------------------")
            print("Warning: more than 2 branches listed in 'use_branches'")
            print("Only the first 2 branches will be used.")
            print("------------------------------------------------------")
            
        # Add "revision" to each branch description if not provided with default value -1, i.e. HEAD of branch   
        for req_branch in opt["use_branches"][:2]:
            opt[req_branch].setdefault("revision",-1)

    def read_config(self):
        """Read config file for the CABLE benchmarking"""

        assert Path(self.myconfig).is_file(), f"{self.myconfig} was not found"

        with open(Path(self.myconfig), "r") as fin:
            opt = yaml.safe_load(fin)
        
        self.check_config(opt)
        return opt

    @staticmethod
    def compilation_setup(ModToLoad:list):
        """Load the modules and define the paths to libraries 
        depending on the machine name as needed for CABLE compilation.
        
        ModToLoad: list, list of modules to load for Gadi. Empty list for other cases"""

        (_, nodename, _, _, _) = os.uname()

        compilation_opt = set_paths(nodename, ModToLoad)

        return compilation_opt

    def setup_bench(self):
        """Main function to setup a CABLE benchmarking run"""

        opt = self.read_config()
        compilation_opt = self.compilation_setup(opt["modules"])

        # Setup the minimal benchmarking directory tree
        myworkdir=Path.cwd()
        benchdirs=BenchTree(myworkdir)
        benchdirs.create_minbenchtree()

        return (opt, compilation_opt, benchdirs)



