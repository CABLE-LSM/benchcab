# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""internal.py: define all runtime constants in a single file."""

import os
from pathlib import Path
from typing import Any


_, NODENAME, _, _, _ = os.uname()

CONFIG_REQUIRED_KEYS = ["realisations", "project", "modules", "experiment"]

# Parameters for job script:
QSUB_FNAME = "benchmark_cable_qsub.sh"
FLUXSITE_DEFAULT_PBS: Any = {
    "ncpus": 18,
    "mem": "30GB",
    "walltime": "6:00:00",
    "storage": [],
}
MPI = False
FLUXSITE_DEFAULT_MULTIPROCESS = True

# DIRECTORY PATHS/STRUCTURE:

# Path to the user's current working directory
CWD = Path.cwd()

# Path to the user's home directory
HOME_DIR = Path(os.environ["HOME"])

# Relative path to directory containing CABLE source codes
SRC_DIR = Path("src")

# Relative path to run directory that stores CABLE runs
RUN_DIR = Path("runs")

# Relative path to core namelist files
NAMELIST_DIR = Path("namelists")

# Relative path to CABLE Auxiliary repository
CABLE_AUX_DIR = SRC_DIR / "CABLE-AUX"

# Relative URL path to CABLE Auxiliary repository on SVN
CABLE_AUX_RELATIVE_SVN_PATH = "branches/Share/CABLE-AUX"

# TODO(Sean): hard coding paths assets in CABLE_AUX is brittle, these should
# be promoted to config parameters, especially since we no longer throw exceptions
# when the assets cannot be found.

# Relative path to CABLE grid info file
GRID_FILE = CABLE_AUX_DIR / "offline" / "gridinfo_CSIRO_1x1.nc"

# Relative path to modis_phenology_csiro.txt
PHEN_FILE = CABLE_AUX_DIR / "core" / "biogeochem" / "modis_phenology_csiro.txt"

# Relative path to pftlookup_csiro_v16_17tiles.csv
CNPBIOME_FILE = (
    CABLE_AUX_DIR / "core" / "biogeochem" / "pftlookup_csiro_v16_17tiles.csv"
)

# Relative path to root directory for CABLE fluxsite runs
FLUXSITE_RUN_DIR = RUN_DIR / "fluxsite"

# Relative path to directory that stores CABLE log files
FLUXSITE_LOG_DIR = FLUXSITE_RUN_DIR / "logs"

# Relative path to directory that stores CABLE output files
FLUXSITE_OUTPUT_DIR = FLUXSITE_RUN_DIR / "outputs"

# Relative path to tasks directory where cable executables are run from
FLUXSITE_TASKS_DIR = FLUXSITE_RUN_DIR / "tasks"

# Relative path to directory that stores results of analysis on model output
FLUXSITE_ANALYSIS_DIR = FLUXSITE_RUN_DIR / "analysis"

# Relative path to directory that stores bitwise comparison results
FLUXSITE_BITWISE_CMP_DIR = FLUXSITE_ANALYSIS_DIR / "bitwise-comparisons"

# Path to met files:
MET_DIR = Path("/g/data/ks32/CLEX_Data/PLUMBER2/v1-0/Met/")

# CABLE SVN root url:
CABLE_SVN_ROOT = "https://trac.nci.org.au/svn/cable"

# CABLE executable file name:
CABLE_EXE = "cable-mpi" if MPI else "cable"

# CABLE namelist file name:
CABLE_NML = "cable.nml"

# CABLE vegetation namelist file:
CABLE_VEGETATION_NML = "pft_params.nml"

# CABLE soil namelist file:
CABLE_SOIL_NML = "cable_soilparm.nml"

# CABLE fixed C02 concentration
CABLE_FIXED_CO2_CONC = 400.0

# CABLE standard output filename
CABLE_STDOUT_FILENAME = "out.txt"

OFFLINE_SOURCE_FILES = [
    "science/albedo/*90",
    "science/radiation/*90",
    "science/canopy/*90",
    "science/casa-cnp/*90",
    "science/gw_hydro/*90",
    "science/misc/*90",
    "science/roughness/*90",
    "science/soilsnow/*90",
    "science/landuse/*90",
    "offline/*90",
    "util/*90",
    "params/*90",
    "science/sli/*90",
    "science/pop/*90",
]

# Contains the default science configurations used to run the CABLE test suite
# (when a science config file is not provided by the user)
DEFAULT_SCIENCE_CONFIGURATIONS = [
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "medlyn",
                "FWSOIL_SWITCH": "Haverd2013",
            }
        }
    },
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "leuning",
                "FWSOIL_SWITCH": "Haverd2013",
            }
        }
    },
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "medlyn",
                "FWSOIL_SWITCH": "standard",
            }
        }
    },
    {
        "cable": {
            "cable_user": {
                "GS_SWITCH": "leuning",
                "FWSOIL_SWITCH": "standard",
            }
        }
    },
]

# Contains the FLUXNET site ids for each met forcing file associated with an experiment
# on modelevaluation.org
MEORG_EXPERIMENTS = {
    # List of FLUXNET site ids associated with the 'Five site test'
    # experiment (workspace: benchcab-evaluation), see:
    # https://modelevaluation.org/experiment/display/xNZx2hSvn4PMKAa9R
    "five-site-test": [
        "AU-Tum",
        "AU-How",
        "FI-Hyy",
        "US-Var",
        "US-Whs",
    ],
    # List of FLUXNET site ids associated with the 'Forty two site test'
    # experiment (workspace: benchcab-evaluation), see:
    # https://modelevaluation.org/experiment/display/urTKSXEsojdvEPwdR
    "forty-two-site-test": [
        "AU-Tum",
        "AU-How",
        "AU-Cum",
        "AU-ASM",
        "AU-GWW",
        "AU-Ctr",
        "AU-Stp",
        "BR-Sa3",
        "CA-Qfo",
        "CH-Dav",
        "CN-Cha",
        "CN-Din",
        "DE-Geb",
        "DE-Gri",
        "DE-Hai",
        "DE-Tha",
        "DK-Sor",
        "FI-Hyy",
        "FR-Gri",
        "FR-Pue",
        "GF-Guy",
        "IT-Lav",
        "IT-MBo",
        "IT-Noe",
        "NL-Loo",
        "RU-Fyo",
        "US-Blo",
        "US-GLE",
        "US-Ha1",
        "US-Me2",
        "US-MMS",
        "US-Myb",
        "US-NR1",
        "US-PFa",
        "US-FPe",
        "US-SRM",
        "US-SRG",
        "US-Ton",
        "US-UMB",
        "US-Var",
        "US-Whs",
        "US-Wkg",
    ],
}

OPTIONAL_COMMANDS = ["fluxsite-bitwise-cmp"]


def get_met_forcing_file_names(experiment: str) -> list[str]:
    """Get a list of meteorological forcing file basenames specified by an experiment

    The `experiment` argument either specifies a key in `MEORG_EXPERIMENTS` or a site id
    within the five-site-test experiment.

    Assume all site ids map uniquely to a met file in MET_DIR.
    """

    if experiment in MEORG_EXPERIMENTS["five-site-test"]:
        # the user is specifying a single met site
        return [next(MET_DIR.glob(f"{experiment}*")).name]

    file_names = [
        next(MET_DIR.glob(f"{site_id}*")).name
        for site_id in MEORG_EXPERIMENTS[experiment]
    ]

    return file_names
