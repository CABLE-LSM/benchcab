# User Guide

In this guide, we will describe:

- how to install the package
- how to use the software, including any requirements
- the different running modes supported by the software

`benchcab` has been designed to work on NCI machine exclusively. It might be extended later on to other systems.

## Pre-requisites

To use `benchcab`, you need to join the following projects at NCI:

- [ks32][ks32_mynci]
- [xp65][xp65_mynci]
- [wd9][wd9_mynci] if not part of the [cable][cable_mynci] project

## Quick-start

To launch a `benchcab` run, execute the following in the command line:

```sh
module use /g/data/xp65/public/modules
module load conda/benchcab
cd /scratch/$PROJECT/$USER
git clone https://github.com/CABLE-LSM/bench_example.git
cd bench_example
# Edit config.yaml to your liking
vim config.yaml
benchcab run
```

## Installation

The package is already installed for you in the Conda environments under the xp65 project. You simply need to load the module for the conda environment:

```bash
   module use /g/data/xp65/public/modules
   module load conda/benchcab
```

You need to load the module on each new session at NCI on login or compute nodes.

!!! Tip "Save the module location"

    You should not put any `module load` or `module add` commands in your `$HOME/.bashrc` file. But you can safely store the `module use /g/data/xp65/public/modules` command in your `$HOME/.bashrc` file. This means you won't have to type this line again in other sessions you open on Gadi.

## Usage

`benchcab` allows you to run an ensemble of configurations for CABLE using any number of code versions. `benchcab` can be used along 3 major modes:

- *Regression test:* running two versions of CABLE with the same standard set of science configurations.
- *New feature:* running two versions of CABLE with the same standard set of science configurations except one version is patched to use a new feature.
- *Ensemble run:* running any number of versions of CABLE with the same set of customised science configurations.

The regression and new feature run modes should be used as necessary when evaluating new developments in CABLE.

### Create a work directory

#### Choose a location

You can run the benchmark from any directory you want under `/scratch` or `/g/data`. `/scratch` is preferred as the data in the run directory does not need to be preserved for a long time. The code will create sub-directories as needed. Please ensure you have enough space to store the CABLE outputs in your directory, at least temporarily until you upload them to [modelevaluation.org][meorg]. 

The full test suite will require about 22GB of storage space.

!!! Warning "The HOME directory is unsuitable"

    Do not use your $HOME directory to contain the work directory as it does not have enough space to contain the outputs.

#### Setup the work directory

The simplest is to clone an existing work directory with git and then adapt it to your case. Such [an example work directory][bench_example] is available on GitHub under the CABLE-LSM organisation.

```bash
git clone git@github.com:CABLE-LSM/bench_example.git
```

Once the work directory is cloned, you will need to adapt the `config.yaml` file to your case. Refer to [the description of the options][config_options] for this file.

!!! info "Running with CABLE v2.x"

    Defaults in `benchcab` are set to run version 3 of CABLE. To run with version 2, check the ["running with CABLE version 2.x"][run_CABLE_v2] page for information on specific setup required. 

## Run the simulations

Change directory into the cloned example work directory

```bash
cd bench_example
```

!!! warning
    `benchcab` will stop if it is not run within a work directory with the proper structure.

Currently, `benchcab` can only run CABLE for flux site and offline spatial configurations. **To run the whole workflow**, run

```bash
benchcab run
```

The tool will follow the steps:

1. Checkout the code branches. The codes will be stored under `src/` directory in your work directory. The sub-directories are created automatically.
2. Compile the source code from all branches
3. Setup and launch a PBS job to run the flux site simulations in parallel. When `benchcab` launches the PBS job, it will print out the job ID to the terminal. You can check the status of the job with `qstat`. `benchcab` will not warn you when the simulations are over.
4. Setup and run an ensemble of offline spatial runs using the [`payu`][payu-github] framework.

!!! info
    In case the code branches are already checked out before running Step (1) - `benchcab` will fail. This could happen on re-runs of `benchcab`. In that case, run `benchcab clean realisations` before the `checkout` step.

!!! warning
    It is dangerous to delete `src/` via `rm -rf`, since `src/` may contain symlinks to local directories that could also be affected. Use `benchcab clean realisations` instead. 

!!! tip "Expected output"

    You can see [an example of the expected output](expected_output.md) printed out to the screen by `benchcab run` to check if the tool has worked as expected.

For help on the **available options** for `benchcab`:

```bash
benchcab -h
benchcab <command> -h
```

!!! Tip "Running parts of the workflow"
    It is possible to run each step of the workflow separately using sub-commands for `benchcab`. Refer to the help message to learn more.

## Directory structure and files

The following files and directories are created when `benchcab run` executes successfully:

```
.
├── benchmark_cable_qsub.sh
├── benchmark_cable_qsub.sh.o<jobid>
├── rev_number-1.log
├── runs
│   ├── fluxsite
│   │   ├── logs
│   │   │   ├── <task>_log.txt
│   │   │   └── ...
│   │   ├── outputs
│   │   │   ├── <task>_out.nc
│   │   │   └── ...
│   │   ├── analysis
│   │   │   └── bitwise-comparisons
│   │   └── tasks
│   │       ├── <task>
│   │       │   ├── cable (executable)
│   │       │   ├── cable.nml
│   │       │   ├── cable_soilparm.nml
│   │       │   └── pft_params.nml
│   │       └── ...
│   ├── spatial
│   │   └── tasks
│   │       ├── <task> (a payu control / experiment directory)
│   │       └── ...
│   └── payu-laboratory
└── src
    ├── CABLE-AUX
    ├── <realisation-0>
    └── <realisation-1>
```

`benchmark_cable_qsub.sh`

:   the job script submitted to run the test suite and `benchmark_cable_qsub.sh.o<jobid>` contains the job's standard output/error stream.

`rev_number-*.log`

:   file to keep a record of the revision numbers used for each realisation specified in the config file.

`src/`

:   directory that contains the source code checked out from SVN for each branch specified in the config file (labelled `realisation-*` above) and the CABLE-AUX branch.

`runs/fluxsite/`

:   directory that contains the log files, output files, and tasks for running CABLE in the fluxsite configuration. 

`runs/fluxsite/tasks`

:   directory that contains fluxsite task directories. A task consists of a CABLE run for a branch (realisation), a meteorological forcing, and a science configuration. In the above directory structure, `<task>` uses the following naming convention:

```
<met_file_basename>_R<realisation_key>_S<science_config_key>
```

:   where `met_file_base_name` is the base file name of the meteorological forcing file in the FLUXNET dataset, `realisation_key` is the branch key specified in the config file, and `science_config_key` identifies the science configuration used.

`runs/fluxsite/tasks/<task>/`

:   directory that contains the executable, the input files for each task and the recorded standard output from the CABLE model run.

`runs/fluxsite/outputs/`

:   directory that contains the netCDF output files for all tasks

`runs/fluxsite/logs/`

:   directory that contains the log files produced by all tasks

`runs/fluxsite/analysis/bitwise-comparisons`

:   directory that contains the standard output produced by the bitwise comparison command: `benchcab fluxsite-bitwise-cmp`. Standard output is only saved when the netcdf files being compared differ from each other

`runs/spatial/`

:   directory that contains task directories for running CABLE in the offline spatial configuration.

`runs/spatial/tasks`

:   directory that contains payu control directories (or experiments) configured for each spatial task. A task consists of a CABLE run for a branch (realisation), a meteorological forcing, and a science configuration. In the above directory structure, `<task>` uses the following naming convention:

```
<met_forcing_name>_R<realisation_key>_S<science_config_key>
```

:   where `met_forcing_name` is the name of the spatial met forcing, `realisation_key` is the branch key specified in the config file, and `science_config_key` identifies the science configuration used. See the [`met_forcings`](config_options.md#met_forcings) option for more information on how to configure the met forcings used.


`runs/spatial/tasks/<task>/`

:   a payu control directory (or experiment). See [Configuring your experiment](https://payu.readthedocs.io/en/latest/config.html) for more information on payu experiments.

`runs/payu-laboratory/`

:   a custom payu laboratory directory. See [Laboratory Structure](https://payu.readthedocs.io/en/latest/design.html#laboratory-structure) for more information on the payu laboratory directory.

!!! warning "Re-running `benchcab` multiple times in the same working directory"
    We recommend the user to delete the generated files when re-running `benchcab` after running simulations and saving the necessary output files elsewhere. Re-running `benchcab` multiple times in the same working directory is currently not yet supported (see issue [CABLE-LSM/benchcab#20](https://github.com/CABLE-LSM/benchcab/issues/20)). To clean the current working directory, run the following command in the working directory

    ```bash
    benchcab clean all
    ```

## Analyse the output with [modelevaluation.org][meorg]

Once the benchmarking has finished running all the simulations, you need to upload the output files to [modelevaluation.org][meorg] via the web interface. To do this:

!!! warning "Limitations"
    Model evaluation for offline spatial outputs is not yet available (see issue [CABLE-LSM/benchcab#193](https://github.com/CABLE-LSM/benchcab/issues/193)).

1. Go to [modelevaluation.org][meorg] and login or create a new account.
2. Navigate to the `benchcab-evaluation` workspace. To do this, click the **Current Workspace** button at the top of the page, and select `benchcab-evaluation` under "Workspaces Shared With Me".
    <figure markdown>
      ![Workspace Button](../assets/model_evaluation/Current%20Workspace%20button.png){ width="500" }
      <figcaption>Button to choose workspace</figcaption>
    </figure>
    <figure markdown>
      ![Workspace Choice](../assets/model_evaluation/Choose%20workspace.png){ width="500" }
      <figcaption>Workspaces available to you</figcaption>
    </figure>

3. Create a model profile for your set of model outputs. You can see [this example][model_profile_eg] to get started. To create your own, select the **Model Profiles** tab and click **Create Model Profile**.
    <figure markdown>
      ![Model profile](../assets/model_evaluation/Create%20model%20profile.png){ width="500" }
      <figcaption>Create model profile</figcaption>
    </figure>

    The model profile should describe the versions of CABLE used to generate the model outputs and the URLs to the repository pointing to the code versions. You are free to set the name as you like.

4. Upload model outputs created by `benchcab` by doing the following:
    1. Transfer model outputs from the `runs/fluxsite/outputs/` directory to your local computer so that they can be uploaded via the web interface.
    2. Create a new model output form. You can see [this example][model_output_eg] to get started. To create your own, select the **Model Outputs** tab on [modelevaluation.org][meorg] and click **Upload Model Output**.
        <figure markdown>
          ![Model output](../assets/model_evaluation/New%20model%20output.png){ width="500" }
          <figcaption>Create model output</figcaption>
        </figure>

    3. Fill out the fields for "Name", "Experiment" and "Model" ("State Selection", "Parameter Selection" and "Comments" are optional):
        - **The experiment** should correspond to the experiment specified in the [configuration file][config_options] used to run `benchcab`. 
        - **The model** should correspond to the Model Profile created in the previous step.
        - Optionally, in **the comments**, you may also want to include the URL to the Github repository containing the benchcab configuration file used to run `benchcab` and any other information needed to reproduce the outputs.

    4. Under "Model Output Files", click **Upload Files**. This should prompt you to select the model outputs you want to upload from your file system. We recommend users to make their model outputs public to download by checking **Downloadable by other users**.
        <figure markdown>
          ![Public output](../assets/model_evaluation/Public%20output.png){ width="300" }
          <figcaption>Make model output public</figcaption>
        </figure>

    5. Under "Benchmarks", you may need to add a benchmark depending on the experiment chosen. This is an error and will be fixed soon.
        - **Five site test** and **Forty two site test**: a benchmark is required to run the analysis for the `Five site test` experiment. You can use:
            - [this model profile][benchmark_5] as a benchmark for the **five site experiment**.
            - [this model profile][benchmark_42] as a benchmark for the **forty-two site experiment**.
        - **single site experiments**: No benchmark is required. You can add your own if you would like to. You can use [this example][benchmark_eg] to know how to set up your own model output as a benchmark.

    6. **Save** your model output!

5. Once the model outputs have been uploaded you can then start the analysis by clicking the **Run Analysis** button at the top of the page. The same button is also found at the bottom of the page.
    <figure markdown>
      ![Run analysis](../assets/model_evaluation/Run%20analysis.png){ width="700" }
      <figcaption>Run analysis button</figcaption>
    </figure>

6. Once the analysis has completed, view the generated plots by clicking **view plots** under "Analyses".
    <figure markdown>
      ![View plots](../assets/model_evaluation/View%20plot.png){ width="500" }
      <figcaption>Link to plots</figcaption>
    </figure>

## Contacts

Please enter your questions as issues on [the benchcab repository][issues-benchcab].

Alternatively, you can also access the ACCESS-NRI User support via [the ACCESS-Hive forum][forum-support].

[xp65_mynci]: https://my.nci.org.au/mancini/project/xp65
[ks32_mynci]: https://my.nci.org.au/mancini/project/ks32
[wd9_mynci]: https://my.nci.org.au/mancini/project/wd9
[cable_mynci]: https://my.nci.org.au/mancini/project/cable
[bench_example]: https://github.com/CABLE-LSM/bench_example.git
[config_options]: config_options.md
[forum-support]: https://forum.access-hive.org.au/t/access-help-and-support/908
[issues-benchcab]: https://github.com/CABLE-LSM/benchcab/issues
[meorg]: https://modelevaluation.org/
[model_profile_eg]: https://modelevaluation.org/model/display/fd5GFaJGYu7H4JpP5
[model_output_eg]: https://modelevaluation.org/modelOutput/display/GnDhhmaehoxcF2nEd
[benchmark_5]: https://modelevaluation.org/modelOutput/display/diLdf49PfpEwZemTz
[benchmark_42]: https://modelevaluation.org/modelOutput/display/pvkuY5gpR2n4FKZw3
[run_CABLE_v2]: running_CABLE_v2.md
[payu-github]: https://github.com/payu-org/payu
