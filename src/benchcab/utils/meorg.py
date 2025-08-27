"""Utility methods for interacting with the ME.org client."""

import os

from hpcpy import get_client
from meorg_client.client import Client as MeorgClient

import benchcab.utils as bu
from benchcab.internal import MEORG_CLIENT, MEORG_PROFILE, MEORG_EXPERIMENT_ID_MAP
from benchcab.utils import interpolate_file_template


def do_meorg(
    config: dict, upload_dir: str, benchcab_bin: str, benchcab_job_id: str = None
):
    """Perform the upload of model outputs to modelevaluation.org.

    Parameters
    ----------
    config : dict
        The master config dictionary
    upload_dir : str
        Absolute path to the data dir for upload
    benchcab_bin : str
        Path to the benchcab bin, from which to infer the client bin

    Returns
    -------
    bool
        True if successful, False otherwise

    """
    logger = bu.get_logger()

    meorg_output_name = config["meorg_output_name"]
    num_threads = MEORG_CLIENT["num_threads"]

    # Check if a model output id has been assigned
    if config.get("meorg_output_name") is None:
        logger.info("No meorg_output_name resolved in configuration.")
        logger.info("NOT uploading to modelevaluation.org")
        return False

    # Allow the user to specify an absolute path to the meorg bin in config
    meorg_bin = config.get("meorg_bin", False)

    # Otherwise infer the path from the benchcab installation
    if meorg_bin == False:
        logger.debug(f"Inferring meorg bin from {benchcab_bin}")
        bin_segments = benchcab_bin.split("/")
        bin_segments[-1] = "meorg"
        meorg_bin = "/".join(bin_segments)

    logger.debug(f"meorg_bin = {meorg_bin}")

    # Now, check if that actually exists
    if os.path.isfile(meorg_bin) == False:
        logger.error(f"No meorg_client executable found at {meorg_bin}")
        logger.error("NOT uploading to modelevaluation.org")
        return False

    # Also only run if the client is initialised
    if MeorgClient().is_initialised() == False:

        logger.warn(
            "A meorg_output_name has been supplied, but the meorg_client is not initialised."
        )
        logger.warn(
            "To initialise, run `meorg initialise` in the installation environment."
        )
        logger.warn(
            "Once initialised, the outputs from this run can be uploaded with the following command:"
        )
        logger.warn(
            f"meorg file upload {upload_dir}/*.nc -n {num_threads} --attach_to {meorg_output_name}"
        )
        logger.warn("Then the analysis can be triggered with:")
        logger.warn(f"meorg analysis start {meorg_output_name}")
        return False

    # Finally, attempt the upload!
    else:

        experiment = config["fluxsite"]["experiment"]
        logger.info("Uploading outputs to modelevaluation.org")

        mo = {
            "state_selection": "default",
            "parameter_selection": "automated",
            "is_bundle": True,
            "name": config["meorg_output_name"],
        }
        model_exp_id = MEORG_EXPERIMENT_ID_MAP[experiment]["experiment"]
        model_benchmark_ids = MEORG_EXPERIMENT_ID_MAP[experiment]["benchmarks"]

        # Submit the outputs
        client = get_client()
        meorg_jobid = client.submit(
            bu.get_installed_root() / "data" / "meorg_jobscript.j2",
            render=True,
            dry_run=False,
            depends_on=benchcab_job_id,
            # Interpolate into the job script
            mo=mo,
            model_prof_id=MEORG_PROFILE["id"],
            model_exp_ids=[model_exp_id],
            model_benchmark_ids=model_benchmark_ids,
            data_dir=upload_dir,
            cache_delay=MEORG_CLIENT["cache_delay"],
            mem=MEORG_CLIENT["mem"],
            num_threads=MEORG_CLIENT["num_threads"],
            walltime=MEORG_CLIENT["walltime"],
            storage=MEORG_CLIENT["storage"],
            project=config["project"],
            modules=config["modules"],
            purge_outputs=True,
            meorg_bin=meorg_bin,
        )

        logger.info(f"Upload job submitted: {meorg_jobid}")
        return True
