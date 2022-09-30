#!/usr/bin/env python

"""
Run CABLE either for a single site, a subset, or all the flux sites pointed to
in the met directory

- Only intended for biophysics
- Set mpi = True if doing a number of flux sites

That's all folks.
"""
__author__ = "Martin De Kauwe"
__version__ = "1.0 (16.06.2020)"
__email__ = "mdekauwe@gmail.com"

import os
import sys
import glob
import shutil
import subprocess
import multiprocessing as mp
import numpy as np
from pathlib import Path

from benchcab.cable_utils import adjust_nml_file
from benchcab.cable_utils import get_svn_info
from benchcab.cable_utils import change_LAI
from benchcab.cable_utils import add_attributes_to_output_file
from benchcab.setup.pbs_fluxsites import *


class RunCableSite(object):
    def __init__(
        self,
        met_dir="",
        log_dir="",
        output_dir="",
        restart_dir="",
        aux_dir="",
        namelist_dir="",
        nml_fname="cable.nml",
        veg_nml="pft_params.nml",
        soil_nml="cable_soilparm.nml",
        veg_fname="def_veg_params_zr_clitt_albedo_fix.txt",
        soil_fname="def_soil_params.txt",
        grid_fname="gridinfo_CSIRO_1x1.nc",
        phen_fname="modis_phenology_csiro.txt",
        cnpbiome_fname="pftlookup_csiro_v16_17tiles.csv",
        elev_fname="GSWP3_gwmodel_parameters.nc",
        lai_dir="",
        fixed_lai=None,
        co2_conc=400.0,
        met_subset=[],
        cable_src="",
        cable_exe="cable",
        num_cores=None,
        multiprocess=False,
        verbose=False,
    ):

        self.met_dir = met_dir
        self.met_subset = met_subset
        self.log_dir = log_dir
        self.output_dir = output_dir
        self.restart_dir = restart_dir
        self.aux_dir = aux_dir
        self.namelist_dir = namelist_dir
        self.nml_fname = nml_fname
        self.biogeophys_dir = os.path.join(self.aux_dir, "core/biogeophys")
        self.grid_dir = os.path.join(self.aux_dir, "offline")
        self.biogeochem_dir = os.path.join(self.aux_dir, "core/biogeochem/")
        self.veg_fname = os.path.join(self.biogeophys_dir, veg_fname)
        self.soil_fname = os.path.join(self.biogeophys_dir, soil_fname)
        self.grid_fname = os.path.join(self.grid_dir, grid_fname)
        self.phen_fname = os.path.join(self.biogeochem_dir, phen_fname)
        self.cnpbiome_fname = os.path.join(self.biogeochem_dir, cnpbiome_fname)
        self.elev_fname = elev_fname
        self.co2_conc = co2_conc
        self.cable_src = cable_src
        self.cable_exe = os.path.join(cable_src, "offline/%s" % (cable_exe))
        self.veg_nml = Path(cable_src, f"offline/{veg_nml}")
        self.soil_nml = Path(cable_src, f"offline/{soil_nml}")
        self.verbose = verbose
        self.lai_dir = lai_dir
        self.fixed_lai = fixed_lai
        self.num_cores = num_cores
        self.multiprocess = multiprocess

        self.setup_from_source()

    def main(self, sci_config, repo_id, sci_id):

        (met_files, url, rev) = self.initialise_stuff()

        # Setup multi-processor jobs
        if self.multiprocess:
            if self.num_cores is None:  # use them all!
                self.num_cores = mp.cpu_count()
            chunk_size = int(np.ceil(len(met_files) / float(self.num_cores)))
            # if self.num_cores > len(met_files):
            #    self.num_cores = len(met_files)

            pool = mp.Pool(processes=self.num_cores)
            jobs = []

            for i in range(self.num_cores):
                start = chunk_size * i
                end = chunk_size * (i + 1)
                if end > len(met_files):
                    end = len(met_files)

                # setup a list of processes that we want to run
                p = mp.Process(
                    target=self.worker,
                    args=(
                        met_files[start:end],
                        url,
                        rev,
                        sci_config,
                        repo_id,
                        sci_id,
                    ),
                )
                p.start()
                jobs.append(p)

            # wait for all multiprocessing processes to finish
            for j in jobs:
                j.join()

        else:
            self.worker(
                met_files,
                url,
                rev,
                sci_config,
                repo_id,
                sci_id,
            )

    def worker(self, met_files, url, rev, sci_config, repo_id, sci_id):
        cwd = os.getcwd()

        for fname in met_files:
            site = os.path.basename(fname).split(".")[0]

            base_nml_fn = os.path.join(self.grid_dir, "%s" % (self.nml_fname))
            nml_fname = "cable_%s_R%s_S%s.nml" % (site, repo_id, sci_id)
            shutil.copy(base_nml_fn, nml_fname)
            # nml_fname = os.path.join(cwd, nml_fname)

            (out_fname, out_log_fname) = self.clean_up_old_files(site, repo_id, sci_id)

            # Add LAI to met file?
            if self.fixed_lai is not None or self.lai_dir != "":
                fname = change_LAI(
                    fname, site, fixed=self.fixed_lai, lai_dir=self.lai_dir
                )

            replace_dict = {
                "filename%met": "'%s'" % (fname),
                "filename%out": "'%s'" % (out_fname),
                "filename%log": "'%s'" % (out_log_fname),
                "filename%restart_out": "' '",
                "filename%type": "'%s'" % (self.grid_fname),
                "filename%veg": "'%s'" % (self.veg_fname),
                "filename%soil": "'%s'" % (self.soil_fname),
                "output%restart": ".FALSE.",
                "fixedCO2": "%.2f" % (self.co2_conc),
                "casafile%phen": "'%s'" % (self.phen_fname),
                "casafile%cnpbiome": "'%s'" % (self.cnpbiome_fname),
                "spinup": ".FALSE.",
            }

            # Make sure the dict isn't empty
            if bool(sci_config):
                replace_dict = merge_two_dicts(replace_dict, sci_config)
            adjust_nml_file(nml_fname, replace_dict)

            self.run_me(nml_fname)

            add_attributes_to_output_file(nml_fname, out_fname, sci_config, url, rev)
            shutil.move(nml_fname, os.path.join(self.namelist_dir, nml_fname))

            if self.fixed_lai is not None or self.lai_dir != "":
                os.remove("%s_tmp.nc" % (site))

    @staticmethod
    def copy_files(copies):
        # Copy file src to dst if src exist
        # copies: Dict, mapping from source path to dest. path
        for src, dst in copies.items():
            if Path(src).is_file():
                shutil.copy(src, dst)

    def setup_from_source(self):
        # copy files needed to run cable in the run directory:
        # - cable executable
        # - veg. parameters namelist
        # - soil parameters namelist
        copies = {
            self.cable_exe: "cable",
            self.veg_nml: Path(self.veg_nml).name,
            self.soil_nml: Path(self.soil_nml).name,
        }
        self.copy_files(copies)
        self.cable_exe = copies[self.cable_exe]

    def initialise_stuff(self):

        if not os.path.exists(self.restart_dir):
            os.makedirs(self.restart_dir)

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        if not os.path.exists(self.namelist_dir):
            os.makedirs(self.namelist_dir)

        # Run all the met files in the directory
        if len(self.met_subset) == 0:
            met_files = glob.glob(os.path.join(self.met_dir, "*.nc"))
        else:
            met_files = [os.path.join(self.met_dir, i) for i in self.met_subset]

        cwd = os.getcwd()
        (url, rev) = get_svn_info(cwd, self.cable_src)

        return (met_files, url, rev)

    def clean_up_old_files(self, site, repo_id, sci_id):
        out_fname = os.path.join(
            self.output_dir, "%s_R%s_S%s_out.nc" % (site, repo_id, sci_id)
        )
        if os.path.isfile(out_fname):
            os.remove(out_fname)

        out_log_fname = os.path.join(
            self.log_dir, "%s_R%s_S%s_log.txt" % (site, repo_id, sci_id)
        )
        if os.path.isfile(out_log_fname):
            os.remove(out_log_fname)

        return (out_fname, out_log_fname)

    def run_me(self, nml_fname):

        # run the model
        if self.verbose:
            cmd = "./%s %s" % (self.cable_exe, nml_fname)
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print("Job failed to submit: ", e.cmd)

        else:
            # No outputs to the screen: stout and stderr to dev/null
            cmd = "./%s %s > /dev/null 2>&1" % (self.cable_exe, nml_fname)
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print("Job failed to submit: ", e.cmd)

    @staticmethod
    def create_qsub_script(project, user, config, science_config):

        email_address = f"{user}@nci.org.au"

        # Add the local directory to the storage flag for PBS
        curdir = Path.cwd().parts
        if "scratch" in curdir:
            curdir_root = "scratch"
            curdir_proj = curdir[2]
        elif "g" in curdir and "data" in curdir:
            curdir_root = "gdata"
            curdir_proj = curdir[3]
        else:
            print("Current directory structure unknown on Gadi")
            sys.exit(1)

        f = open(qsub_fname, "w")

        f.write("#!/bin/bash\n")
        f.write("\n")
        f.write("#PBS -l wd\n")
        f.write("#PBS -l ncpus=%d\n" % (ncpus))
        f.write("#PBS -l mem=%s\n" % (mem))
        f.write("#PBS -l walltime=%s\n" % (wall_time))
        f.write("#PBS -q normal\n")
        f.write("#PBS -P %s\n" % (project))
        f.write("#PBS -j oe\n")
        f.write("#PBS -M %s\n" % (email_address))
        f.write(
            f"#PBS -l storage=gdata/ks32+gdata/wd9+gdata/hh5+gdata/{project}+{curdir_root}/{curdir_proj}\n"
        )
        f.write("\n")
        f.write("\n")
        f.write("\n")
        f.write("\n")
        f.write("module purge\n")
        f.write("module use /g/data/hh5/public/modules\n")
        f.write("module load conda/analysis3-unstable\n")
        f.write("module add netcdf/4.7.1\n")
        f.write(f"benchsiterun --config={config} --science_config={science_config}\n")
        f.write("\n")

        f.close()

        os.chmod(qsub_fname, 0o755)


def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z


if __name__ == "__main__":

    # ------------- Change stuff ------------- #
    met_dir = "../../met_data/plumber_met"
    log_dir = "logs"
    output_dir = "outputs"
    restart_dir = "restart_files"
    namelist_dir = "namelists"
    aux_dir = "../../src/CMIP6-MOSRS/CABLE-AUX/"
    cable_src = "../../src/CMIP6-MOSRS/CMIP6-MOSRS"
    mpi = False
    num_cores = 4  # set to a number, if None it will use all cores...!
    # if empty...run all the files in the met_dir
    met_subset = ["TumbaFluxnet.1.4_met.nc"]
    sci_config = {}
    # ------------------------------------------- #

    C = RunCableSite(
        met_dir=met_dir,
        log_dir=log_dir,
        output_dir=output_dir,
        restart_dir=restart_dir,
        aux_dir=aux_dir,
        namelist_dir=namelist_dir,
        met_subset=met_subset,
        cable_src=cable_src,
        mpi=mpi,
        num_cores=num_cores,
    )
    C.main(sci_config)
