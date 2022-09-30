from pathlib import Path
import os
import shutil
class BenchTree(object):
    """Manage the directory tree to run the benchmarking for CABLE"""

    def __init__(self, curdir:Path):
        
        self.src_dir = curdir/"src"
        self.aux_dir = curdir/"src/CABLE-AUX"
        self.plot_dir = curdir/"plots"
        # Run directory and its sub-directories
        self.runroot_dir = curdir/"runs"
        self.site_run = {
            "site_dir": self.runroot_dir/"site",
            "log_dir": self.runroot_dir/"site/logs",
            "output_dir": self.runroot_dir/"site/outputs",
            "restart_dir": self.runroot_dir/"site/restart_files",
            "namelist_dir": self.runroot_dir/"site/namelists",
        }

        self.clean_previous()

    def clean_previous(self):
        """Clean previous benchmarking runs as needed. 
        Archives previous rev_number.log"""

        revision_file=Path("rev_number.log")
        if revision_file.exists():
            revision_file.replace(self.next_path("rev_number-*.log"))

        return

    @staticmethod
    def next_path(path_pattern, sep="-"):
        """
        Finds the next free path in a sequentially named list of files with the following pattern:
            path_pattern = 'file{sep}*.suf':

        file-1.txt
        file-2.txt
        file-3.txt
        """

        loc_pattern=Path(path_pattern)
        new_file_index = 1
        common_filename, _ = loc_pattern.stem.split(sep)

        pattern_files_sorted = sorted(Path('.').glob(path_pattern))
        if len(pattern_files_sorted):
            common_filename, last_file_index = pattern_files_sorted[-1].stem.split(sep)
            new_file_index = int(last_file_index) + 1

        return f"{common_filename}{sep}{new_file_index}{loc_pattern.suffix}"

    def create_minbenchtree(self):
        """Create the minimum directory tree needed to run the CABLE benchmarking.
        At least, we need:
           - a source directory to checkout and compile the repository branches
           - a run directory to run the testcases."""

        dir_to_create= [ 
            self.src_dir, 
            self.runroot_dir,
            ]
        for mydir in dir_to_create:
            if not Path.is_dir(mydir):
                os.makedirs(mydir)

    def create_sitebenchtree(self):
        """Create directory tree for site benchmark"""

        # Make sure the default directories are created
        self.create_minbenchtree()

        # Create the sub-directories in the run directory
        for mydir in self.site_run.values():
            if not mydir.is_dir():
                os.makedirs(mydir)

        # Copy namelists from the namelists/ directory
        nml_dir = Path.cwd()/"namelists"
        try:
            shutil.copytree(nml_dir,self.site_run["site_dir"],dirs_exist_ok=True)
        except:
            raise


    
