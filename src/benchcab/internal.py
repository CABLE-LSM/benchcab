# Copyright 2022 ACCESS-NRI and contributors. See the top-level COPYRIGHT file for details.
# SPDX-License-Identifier: Apache-2.0

"""internal.py: define all runtime constants in a single file."""

import os
from pathlib import Path

from benchcab.utils.pbs import PBSConfig

_, NODENAME, _, _, _ = os.uname()

CONFIG_REQUIRED_KEYS = ["realisations", "modules"]

# CMake module used for compilation:
DEFAULT_MODULES = {
    "cmake": "cmake/3.24.2",
    "intel-compiler": "intel-compiler/2021.10.0",
}

# Number of parallel jobs used when compiling with CMake:
CMAKE_BUILD_PARALLEL_LEVEL = 4

# Parameters for job script:
QSUB_FNAME = "benchmark_cable_qsub.sh"
FLUXSITE_DEFAULT_PBS: PBSConfig = {
    "ncpus": 18,
    "mem": "30GB",
    "walltime": "6:00:00",
    "storage": [],
}
FLUXSITE_DEFAULT_MULTIPROCESS = True

# DIRECTORY PATHS/STRUCTURE:

# Path to hidden state directory:
STATE_DIR = Path(".state")
STATE_PREFIX = ".state_attr_"

# Default system paths in Unix
SYSTEM_PATHS = ["/bin", "/usr/bin", "/usr/local/bin"]

# Path to the user's home directory
HOME_DIR = Path(os.environ["HOME"])

# Relative path to directory containing CABLE source codes
SRC_DIR = Path("src")

# Relative path to run directory that stores CABLE runs
RUN_DIR = Path("runs")

# Relative path to core namelist files
NAMELIST_DIR = Path("namelists")

# Path to CABLE-AUX
CABLE_AUX_DIR = Path("/g/data/wd9/BenchMarking/CABLE-AUX_v20240122")

# Path CABLE grid info file
GRID_FILE = CABLE_AUX_DIR / "offline" / "gridinfo_CSIRO_1x1.nc"

# Relative path to directory that stores codecov files
CODECOV_DIR = RUN_DIR / "coverage"

# Fluxsite directory tree
FLUXSITE_DIRS: dict[str, Path] = {}

# Relative path to root directory for CABLE fluxsite runs
FLUXSITE_DIRS["RUN"] = RUN_DIR / "fluxsite"

# Relative path to directory that stores CABLE log files
FLUXSITE_DIRS["LOG"] = FLUXSITE_DIRS["RUN"] / "logs"

# Relative path to directory that stores CABLE output files
FLUXSITE_DIRS["OUTPUT"] = FLUXSITE_DIRS["RUN"] / "outputs"

# Relative path to tasks directory where cable executables are run from
FLUXSITE_DIRS["TASKS"] = FLUXSITE_DIRS["RUN"] / "tasks"

# Relative path to directory that stores results of analysis on model output
FLUXSITE_DIRS["ANALYSIS"] = FLUXSITE_DIRS["RUN"] / "analysis"

# Relative path to directory that stores bitwise comparison results
FLUXSITE_DIRS["BITWISE_CMP"] = FLUXSITE_DIRS["ANALYSIS"] / "bitwise-comparisons"

# Relative path to root directory for CABLE spatial runs
SPATIAL_RUN_DIR = RUN_DIR / "spatial"

# Relative path to tasks directory (contains payu control directories configured
# for each spatial task)
SPATIAL_TASKS_DIR = SPATIAL_RUN_DIR / "tasks"

# A custom payu laboratory directory for payu runs
PAYU_LABORATORY_DIR = RUN_DIR / "payu-laboratory"

# Path to PLUMBER2 site forcing data directory (doi: 10.25914/5fdb0902607e1):
MET_DIR = Path("/g/data/ks32/CLEX_Data/PLUMBER2/v1-0/Met/")

# Default met forcings to use in the spatial test suite. Each met
# forcing has a corresponding payu experiment that is configured to run CABLE
# with that forcing.
SPATIAL_DEFAULT_MET_FORCINGS = {
    "crujra_access": "https://github.com/CABLE-LSM/cable_example.git",
}

# CABLE SVN root url:
CABLE_SVN_ROOT = "https://trac.nci.org.au/svn/cable"

# Relative path to temporary build directory (serial)
TMP_BUILD_DIR = Path("offline", ".tmp")

# Relative path to temporary build directory (MPI)
TMP_BUILD_DIR_MPI = Path("offline", ".mpitmp")

# CABLE GitHub URL:
CABLE_GIT_URL = "https://github.com/CABLE-LSM/CABLE.git"

# CABLE executable file name:
CABLE_EXE = "cable"

# CABLE MPI executable file name:
CABLE_MPI_EXE = "cable-mpi"

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

FLUXSITE_DEFAULT_EXPERIMENT = "forty-two-site-test"
FLUXSITE_DEFAULT_MEORG_MODEL_OUTPUT_ID = False

OPTIONAL_COMMANDS = ["fluxsite-bitwise-cmp", "gen_codecov"]


def get_met_forcing_file_names(experiment: str) -> list[str]:
    """Get a list of meteorological forcing file basenames specified by an experiment.

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


# Configuration for the client upload
MEORG_CLIENT = dict(
    num_threads=1,  # Parallel uploads over 4 cores
    cache_delay=60 * 5,  # 5mins between upload and analysis triggering
    mem="8G",
    walltime="01:00:00",
    storage=["gdata/ks32", "gdata/xp65", "gdata/wd9", "gdata/rp23"],
)
