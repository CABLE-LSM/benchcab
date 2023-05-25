# User Guide

In this guide, we will describe:

- how to install the package
- how to use the software, including any requirements
- the different modes supported by the software

`benchcab` has been designed to work on NCI machine exclusively. It might be extended later on to other systems.

## Pre-requisites

To use `benchcab`, you need to join the following projects at NCI:

- [ks32][ks32_mynci]
- [hh5][hh5_mynci]

## Installation

The package is already installed for you in the Conda environments under the hh5 project. You simply need to load the module for the conda environment:

```bash
   module use /g/data/hh5/public/modules
   module load conda/analysis3-unstable
```

You need to load the module on each new session at NCI on login or compute nodes.

!!! Tip "Save the module location"

    You should not put any `module load` or `module add` commands in your `$HOME/.bashrc` file. But you can safely store the `module use /g/data/hh5/public/modules` command in your `$HOME/.bashrc` file. This means you won't have to type this line again in other sessions you open on Gadi.

## Usage

`benchcab` will run the exact same configurations on two CABLE branches specified by the user, e.g. a user branch (with personal changes) against the head of the trunk. The results should be attached with all new [tickets](https://trac.nci.org.au/trac/cable/report/1).

The code will: (i) check out and (ii) build the code branches. Then it will run each executable across N standard science configurations for a given number of sites. It is possible to produce some plots locally from the output produced. But [the modelevaluation website][meorg] can be used for further benchmarking and evaluation.

### Create a work directory

#### Choose a location

You can run the benchmark from any directory you want under `/scratch` or `/g/data`. `/scratch` is preferred as the data in the run directory does not need to be preserved for a long time. The code will create sub-directories as needed. Please ensure you have enough space to store the CABLE outputs in your directory, at least temporary, until you upload them to [modelevaluation.org][meorg]. You will need about 33GB for the outputs for the `forty-two-site` experiment (with 8 different science configurations).

!!! Warning "The HOME directory is unsuitable"
    
    Do not use your $HOME directory to contain the work directory as it does not have enough space to contain the outputs.

#### Setup the work directory

The simplest is to clone an existing work directory with git and then adapt it to your case. Such [an example work directory][bench_example] is available on GitHub under the CABLE-LSM organisation.
```bash
git clone git@github.com:CABLE-LSM/bench_example.git
```

Once the work directory is cloned, you will need to adapt the `config.yaml` file to your case. Refer to [the description of the options][config_options] for this file.

## Run the simulations

Change directory into the cloned example work directory
```bash
cd bench_example
```

!!! warning
    `benchcab` will yell at you if it cannot find files in the current working directory.


Currently, `benchcab` can only run CABLE for flux sites. To run the flux site tests, run

```bash
benchcab -f
```

The benchmarking will follow the steps:

1. Checkout both branches. The codes will be stored under `src/` directory in your work directory. The sub-directories are created automatically.
2. Compile the source code from both branches
3. Setup and launch a PBS job to run the simulations in parallel. When `benchcab` launches the PBS job, it will print out the job ID to the terminal. You can check the status of the job with `qstat`.

For help on the available options for `benchcab`:

```bash
benchcab -h
```

## Directory structure and files

The following files and directories are created when `benchcab -f` executes successfully:
```
.
├── benchmark_cable_qsub.sh
├── benchmark_cable_qsub.sh.o<jobid>
├── rev_number-1.log
├── runs
│   └── site
│       ├── logs
│       │   ├── <task>_log.txt
│       │   └── ...
│       ├── outputs
│       │   ├── <task>_out.nc
│       │   └── ...
│       └── tasks
│           ├── <task>
│           │   ├── cable (executable)
│           │   ├── cable.nml
│           │   ├── cable_soilparm.nml
│           │   └── pft_params.nml
│           └── ...
└── src
    ├── CABLE-AUX
    ├── <realisation-0>
    └── <realisation-1>
```

The `benchmark_cable_qsub.sh` file is the job script submitted to run the test suite and `benchmark_cable_qsub.sh.o<jobid>` contains the job's standard output/error stream.

The `rev_number-*.log` file keeps a record of the revision numbers used for each realisation specified in the config file.

The `src` directory contains the source code checked out from SVN for each branch specified in the config file (labelled `realisation-*` above) and the CABLE-AUX branch.

The `runs/site` directory contains the log files, output files, and tasks for running CABLE. CABLE runs are organised into tasks where a task consists of a branch (realisation), a meteorological forcing, and a science configuration. In the above directory structure, `<task>` uses the following naming convention:
```
<met_file_basename>_R<realisation_key>_S<science_config_key>
```
where `met_file_base_name` is the base file name of the meteorological forcing file in the FLUXNET dataset, `realisation_key` is the branch key specified in the config file, and `science_config_key` identifies the science configuration used.

The `runs/site/tasks/<task>` directory contains the executable and input files for each task.

The output files and log files for all tasks are stored in the `runs/site/outputs` and `runs/site/logs` directories respectively.

!!! warning "Re-running `benchcab` multiple times in the same working directory"
    We recommend the user to manually delete the generated files when re-running `benchcab`. Re-running `benchcab` multiple times in the same working directory is currently not yet supported (see issue [CABLE-LSM/benchcab#20](https://github.com/CABLE-LSM/benchcab/issues/20)). To clean the current working directory, run the following command in the working directory
    ```bash
    rm benchmark_cable_qsub.sh* rev_number-*; rm -rf runs/ src/
    ```

## Analyse the output with [modelevaluation.org][meorg]

<!-- **Prerequisite**: To run the model evaluation step, you will need to create an account on [modelevaluation.org][meorg]. -->

Once the benchmarking has finished running all the simulations, you need to upload the output files to [modelevaluation.org][meorg] via the web interface. To do this:

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
    1. Transfer model outputs from the `runs/site/outputs/` directory to your local computer so that they can be uploaded via the web interface.
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
        - **Five site test** and **Forty two site test**: a benchmark is required to run the analysis for the `Five site test` experiment. You can use [this model profile][benchmark_eg] as a benchmark for this experiment.
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

Alternatively, you can also post discussions or questions on [the ACCESS-Hive forum][hive-forum].

[hh5_mynci]: https://my.nci.org.au/mancini/project/hh5
[ks32_mynci]: https://my.nci.org.au/mancini/project/ks32
[bench_example]: https://github.com/CABLE-LSM/bench_example.git
[config_options]: config_options.md
[hive-forum]: https://forum.access-hive.org.au
[issues-benchcab]: https://github.com/CABLE-LSM/benchcab/issues
[meorg]: https://modelevaluation.org/
[model_profile_eg]: https://modelevaluation.org/model/display/fd5GFaJGYu7H4JpP5
[model_output_eg]: https://modelevaluation.org/modelOutput/display/GnDhhmaehoxcF2nEd
