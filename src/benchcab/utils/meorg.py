"""Utility methods for interacting with the ME.org client."""

import os
from datetime import datetime, timezone
from pathlib import Path

from hpcpy import get_client
from meorg_client.client import Client as MeorgClient


import benchcab.utils as bu
from benchcab import internal
from benchcab.internal import MEORG_CLIENT, MEORG_PROFILE, MEORG_EXPERIMENT_ID_MAP
from benchcab.utils import interpolate_file_template
from benchcab.utils.fs import mkdir


def do_meorg(
    config: dict,
    upload_dir: str,
    benchcab_bin: str,
    benchcab_job_id: str = None,
    *,
    gadi: bool = None,
    dry_run: bool = False,
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
    benchcab_job_id : str, optional
        Job id the first job waits on with `afterok`, by default None
    gadi : bool, optional
        Run the analysis on Gadi (the inputs, analysis and result jobs) instead
        of on the me.org worker, by default `fluxsite.meorg_analysis.enabled`
    dry_run : bool, optional
        Render the Gadi job scripts without submitting them, by default False

    Returns
    -------
    bool
        True if successful, False otherwise

    """
    logger = bu.get_logger()

    meorg_output_name = config.get("meorg_output_name")
    num_threads = MEORG_CLIENT["num_threads"]
    if gadi is None:
        gadi = config["fluxsite"]["meorg_analysis"]["enabled"]

    # Check if a model output id has been assigned
    if meorg_output_name is None:
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

        upload_job = dict(
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

        if gadi:
            jobs = submit_gadi_analysis(config, upload_job, benchcab_job_id, dry_run)
            action = "rendered, not submitted" if dry_run else "submitted"
            for name, job in zip(["Inputs", "Analysis", "Result"], jobs):
                logger.info(f"{name} job {action}: {job}")
            return True

        # Submit the outputs
        client = get_client()
        meorg_jobid = client.submit(
            bu.get_installed_root() / "data" / "meorg_jobscript.j2",
            render=True,
            dry_run=False,
            depends_on=benchcab_job_id,
            **upload_job,
        )

        logger.info(f"Upload job submitted: {meorg_jobid}")
        return True


def get_run_id(experiment: str) -> str:
    """Return the id of an analysis run, fixed when the jobs are submitted."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"benchcab-{experiment}-{Path.cwd().name}-{timestamp}"


def get_analysis_cache(project: str) -> tuple:
    """Return the cache of the analysis inputs and the storage it needs.

    The shared cache is used when the user can write to it, as a member of its
    project. Otherwise the inputs go to a cache in the user's scratch.

    Parameters
    ----------
    project : str
        The NCI project of the benchcab run

    Returns
    -------
    tuple
        The cache directory, and the storage flags the jobs that read it need

    """
    analysis = internal.MEORG_ANALYSIS
    if os.access(analysis["shared_cache"], os.W_OK | os.X_OK):
        return analysis["shared_cache"], analysis["shared_cache_storage"]
    user_cache = analysis["cache"].format(project=project, user=os.environ.get("USER"))
    return user_cache, []


def submit_gadi_analysis(
    config: dict, upload_job: dict, depends_on: str = None, dry_run: bool = False
) -> list:
    """Submit the analysis on Gadi as three jobs chained with `afterok`.

    The inputs job (copyq) creates the model output on me.org, or reuses the one
    with this name without changing its files, and fetches the analysis inputs.
    The analysis job (normal) runs `meorg-run`. The result job (copyq) deletes
    the files of an earlier run, submits the result, then uploads the model
    output files.

    Parameters
    ----------
    config : dict
        The master config dictionary
    upload_job : dict
        The job script context of the upload job, used for the inputs job
    depends_on : str, optional
        Job id the inputs job waits on, by default None
    dry_run : bool, optional
        Render the job scripts and return the qsub commands, by default False

    Returns
    -------
    list
        The three submitted jobs, or their qsub commands when `dry_run` is True

    """
    settings = config["fluxsite"]["meorg_analysis"]
    analysis = internal.MEORG_ANALYSIS
    run_dir = (internal.FLUXSITE_DIRS["ANALYSIS"] / "meorg").absolute()
    mkdir(run_dir, parents=True, exist_ok=True)

    common = dict(
        project=config["project"],
        run_dir=str(run_dir),
        run_id=get_run_id(config["fluxsite"]["experiment"]),
    )
    # Every job also needs the storage of the benchcab work directory. The
    # inputs and analysis jobs also need the storage of the cache.
    fluxsite_storage = config["fluxsite"]["pbs"]["storage"]
    copyq_storage = list(dict.fromkeys(upload_job["storage"] + fluxsite_storage))
    cache, cache_storage = get_analysis_cache(config["project"])
    bu.get_logger().info(f"Analysis inputs cache: {cache}")
    jobs = {
        "meorg_jobscript.j2": dict(
            upload_job,
            storage=list(dict.fromkeys(copyq_storage + cache_storage)),
            gadi=True,
            cache=cache,
        ),
        "meorg_analysis_jobscript.j2": dict(
            queue="normal",
            ncpus=settings["ncpus"],
            mem=settings["mem"],
            walltime=settings["walltime"],
            storage=list(
                dict.fromkeys(analysis["storage"] + cache_storage + fluxsite_storage)
            ),
            # Prefixed to avoid the `module_use` and `modules` arguments that
            # newer hpcpy versions consume before the template context.
            meorg_module_use=analysis["module_use"],
            meorg_module=settings["module"],
        ),
        "meorg_result_jobscript.j2": dict(
            num_threads=upload_job["num_threads"],
            mem=upload_job["mem"],
            walltime=upload_job["walltime"],
            storage=copyq_storage,
            meorg_bin=upload_job["meorg_bin"],
            data_dir=upload_job["data_dir"],
            experiment_id=upload_job["model_exp_ids"][0],
        ),
    }

    client = get_client()
    submitted = []
    for template, context in jobs.items():
        job = client.submit(
            bu.get_installed_root() / "data" / template,
            render=True,
            dry_run=dry_run,
            depends_on=depends_on,
            **(context | common),
        )
        submitted.append(job)
        # A dry run has no job ids, so chain on a placeholder
        depends_on = f"<job {len(submitted)}>" if dry_run else job

    return submitted
