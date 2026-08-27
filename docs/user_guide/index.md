# User Guide

!!! Tip "Quick-start instructions (if you have done this before)"

    ```sh
    module use /g/data/xp65/public/modules
    module load conda/benchcab
    cd /scratch/$PROJECT/$USER
    git clone https://github.com/CABLE-LSM/bench_example.git
    cd bench_example
    vim config.yaml # Edit config.yaml
    benchcab run
    ```

In this guide, we will describe:

- how to use the software on NCI Gadi, including any requirements
- the different running modes supported by the software

`benchcab` has been designed to work on NCI machine exclusively. It might be extended later on to other systems.

## Pre-requisites

To use `benchcab`, you need:

1. **An NCI account:** If you do not have an account, you can sign up [here][nci-signup]. You will need an NCI project with an existing compute allocation. Once you have an account, please join the following additional projects:

    - [ks32][ks32_mynci] (Required to access to flux tower driving data)
    - [xp65][xp65_mynci] (Required to access `benchcab` tool)
    - [wd9][wd9_mynci] if not part of the [cable][cable_mynci] project (Required to access CABLE ancillaries)
    - [rp23][rp23_mynci] (Required to access ancillary and driving data for spatial CABLE configurations)

    Please reach out to the lead CI for the above projects stating your affiliation and purpose. This may take a few days for the request to be approved.

2. **An account on [modelevaluation.org][meorg]**: See [registration][meorg-registration] to create an account. After creating an account, please join the benchcab-evaluation workspace (see [workspaces][meorg-workspaces]).

## Usage

### Connecting to Gadi

To get started with using benchcab, we recommend users to connect to Gadi via the terminal which is the native environment for running the benchcab command line tool. For more information on how to do this, see [Connecting to Gadi via terminal][nci-opus-connecting-to-gadi].

### Loading the software

The package is already installed for you in the Conda environments under the xp65 project. You simply need to load the module for the conda environment:

```bash
module use /g/data/xp65/public/modules
module load conda/benchcab
```

You need to load the module on each new session at NCI on login or compute nodes.

!!! Tip "Save the module location"

    You should not put any `module load` or `module add` commands in your `$HOME/.bashrc` file. But you can safely store the `module use /g/data/xp65/public/modules` command in your `$HOME/.bashrc` file. This means you won't have to type this line again in other sessions you open on Gadi.

### Authenticate your credentials with `meorg_client`

`benchcab` uses the [**meorg_client**][meorg_client] package to interact with [modelevaluation.org][meorg] (see [Configuring benchcab for use with modelevaluation.org](#configuring-benchcab-for-use-with-modelevaluationorg)). The **meorg_client** package is installed with `benchcab` and is available in the environment. Please follow [these instructions][meorg_client-setup-credentials] to authenticate your credentials.

### Create a work directory

#### Choose a location

Benchcab will automatically setup and run the requested CABLE simulations for you under a common directory of your choice. This directory can belong under `/scratch` or `/g/data`, however, `/scratch` is preferred as the data in the run directory does not need to be preserved for a long time. The code will create sub-directories as needed. Please ensure you have enough space to store the CABLE outputs in your directory. The full test suite will require about 22GB of storage space.

```bash
cd /scratch/$PROJECT/$USER  # or cd /g/data/$PROJECT/$USER
```

!!! Warning "The `$HOME` directory is unsuitable"

    Do not use your `$HOME` directory to contain the work directory as it does not have enough space to contain the outputs.

#### Setup the work directory

Once you have identified a common directory to run the benchcab simulations, you can now download [the example work directory][bench_example] with git and then adapt it to your case.

```bash
git clone https://github.com/CABLE-LSM/bench_example.git
```

### Modify the configuration file

Once the work directory is cloned, change directory into the cloned example work directory

```bash
cd bench_example
```

You will then need to adapt the `config.yaml` file to your case. This file should look similar to the following:

```yaml
--8<-- "https://raw.githubusercontent.com/CABLE-LSM/bench_example/refs/heads/main/config.yaml"
```

Here the [`realisations`](config_options.md#realisations) section specifies to run CABLE executables built from the `main` branch of CABLE repository for the default ensemble of CABLE model configurations. The model configurations consist of various flux towers and gridded simulations (see [`fluxsite`](config_options.md#fluxsite) and [`spatial`](config_options.md#spatial)), with each driving data set simulated using one or more CABLE science configurations (see [`science_configurations`](config_options.md#science_configurations)).

The `realisations` list can be expanded to compare behaviour across multiple branches (see [Example Configurations](#example-configurations)).

We also specify the environment modules required for building the CABLE executable in the [`modules`](config_options.md#modules) section. These modules will be loaded before invoking the CABLE build system.

For more information on the available options in the `config.yaml` file, please refer to [config.yaml options](config_options.md#configyaml-options).

!!! info "Running with CABLE v2.x"

    Defaults in `benchcab` are set to run version 3 of CABLE. To run with version 2, check the ["running with CABLE version 2.x"][run_CABLE_v2] page for information on specific setup required.

!!! warning
    `benchcab` will stop if it is not run within a work directory with the proper structure.

#### Configuring benchcab for use with [modelevaluation.org][meorg]

!!! warning "Limitations"
    Model evaluation for offline spatial outputs is not yet available (see issue [CABLE-LSM/benchcab#193](https://github.com/CABLE-LSM/benchcab/issues/193)).

`benchcab` communicates with `meorg` using `meorg_client` package (available on `xp65` conda environment in Gadi). The benchmarking results are uploaded to `modelevaluation.org` for further analysis, which can be seen via the web interface. By default this feature is not enabled. To enable support:

1. Go to [modelevaluation.org][meorg] and login or create a new account.
2. To view analysis in the web interface, one needs to enable `benchcab-evaluation` workspace. To do this, click the **Current Workspace** button at the top of the page, and select `benchcab-evaluation` under "Workspaces Shared With Me".
    <figure markdown>
      ![Workspace Button](../assets/model_evaluation/Current%20Workspace%20button.png){ width="500" }
      <figcaption>Button to choose workspace</figcaption>
    </figure>
    <figure markdown>
      ![Workspace Choice](../assets/model_evaluation/Choose%20workspace.png){ width="500" }
      <figcaption>Workspaces available to you</figcaption>
    </figure>
3. `benchcab` requires access to the necessary permissions for interfacing with `meorg`. Use `meorg initialise` to create the credentials file.
    <figure markdown>
      ![View plots](../assets/model_evaluation/meorg%20initialise.png){ width="500" }
      <figcaption>Initialising `meorg_client`</figcaption>
    </figure>
4. Set the [`meorg_output_name`](config_options.md#meorg_output_name) as `true` for one of the realisations to enable the analysis workflow (run as a PBS jobscript). Please note that the CABLE branch name must satisfy the appropriate naming convention. The CABLE branch name will then be used as the model output name which is uploaded to [modelevaluation.org][meorg].

### Run the simulations

Currently, `benchcab` can only run CABLE in offline mode for flux site and spatial configurations. **To run the whole workflow**, run

```bash
benchcab run
```

The tool will follow the steps:

1. Checkout the code branches. The codes will be stored under `src/` directory in your work directory. The sub-directories are created automatically.
2. Compile the source code from all branches
3. Setup and launch a PBS job to run the flux site simulations in parallel. When `benchcab` launches the PBS job, it will print out the job ID to the terminal. You can check the status of the job with `qstat`. `benchcab` will not warn you when the simulations are over.
4. Setup and run an ensemble of offline spatial runs using the [`payu`][payu-github] framework.
5. Launch a PBS job to trigger the evaluation on [modelevaluation.org][meorg] if enabled. This will be run after the PBS job for flux site simulations has completed.

!!! info
    In case the code branches are already checked out before running Step (1) - `benchcab` will fail. This could happen on re-runs of `benchcab`. In that case, run `benchcab clean realisations` before the `checkout` step.

!!! warning
    It is dangerous to delete `src/` via `rm -rf`, since `src/` may contain symlinks to local directories that could also be affected. Use `benchcab clean realisations` instead. 

!!! tip "Expected output"

    You can see [an example of the expected output](expected_output.md#expected-output-from-benchcab) printed out to the screen by `benchcab run` to check if the tool has worked as expected. A description of the directory structure generated by a successful benchcab run can be found [here](expected_output.md#directory-structure-and-files).

For help on the **available options** for `benchcab`:

```bash
benchcab -h
benchcab <command> -h
```

!!! Tip "Running parts of the workflow"
    It is possible to run each step of the workflow separately using sub-commands for `benchcab`. Refer to the help message to learn more.

!!! warning "Re-running `benchcab` multiple times in the same working directory"
    We recommend the user to delete the generated files when re-running `benchcab` after running simulations and saving the necessary output files elsewhere. Re-running `benchcab` multiple times in the same working directory is currently not yet supported (see issue [CABLE-LSM/benchcab#20](https://github.com/CABLE-LSM/benchcab/issues/20)). To clean the current working directory, run the following command in the working directory

    ```bash
    benchcab clean all
    ```

### Accessing the evaluation on [modelevaluation.org][meorg]

Upon successful submission of the files and starting the analysis, the model output will available at [Model Outputs][meorg-model-outputs] in the **benchcab-evaluation** workspace.

After identifying the uploaded output, one can view the generated plots by clicking **view plots** under "Analyses".
    <figure markdown>
      ![View plots](../assets/model_evaluation/View%20plot.png){ width="500" }
      <figcaption>Link to plots</figcaption>
    </figure>

## Different running modes supported by benchcab

One of the powerful features of `benchcab` is the ability to run an ensemble of CABLE configurations using any number of code versions and compare how each configuration performs in the final evaluation. `benchcab` can be used along 3 major modes:

- *Regression test:* running two versions of CABLE with the same standard set of science configurations.
- *New feature:* running two versions of CABLE with the same standard set of science configurations except one version is patched to use a new feature.
- *Ensemble run:* running any number of versions of CABLE with the same set of customised science configurations.

The regression and new feature run modes should be used as necessary when evaluating new developments in CABLE. For more information on setting up these use cases, please see [config.yaml options](config_options.md#configyaml-options).

## Example Configurations

For the `main` branch and another branch named `123-benchcab-demo`, run the benchcab flux tower tests for:

**1. The `five-site-test` experiment with the [modelevaluation.org][meorg] analysis**

??? note "Solution"

    ```yaml
    --8<-- "https://raw.githubusercontent.com/CABLE-LSM/bench_example/refs/heads/examples-main-vs-demo-branch/config.yaml"
    ```

**2. The `five-site-test` experiment with the [modelevaluation.org][meorg] analysis, except now test the impact of a new option by setting `cable_user%new_option = .true.` in the CABLE namelist file for all simulations involving `123-benchcab-demo`**

!!! tip "See the [`patch`](config_options.md#patch) option"

??? note "Solution"

    ```yaml
    --8<-- "https://raw.githubusercontent.com/CABLE-LSM/bench_example/refs/heads/examples-main-vs-demo-branch-patch/config.yaml"
    ```

Please also see [Configuration examples for various use cases](use_cases.md#configuration-examples-for-various-use-cases).

## Contacts

Please enter your questions as issues on [the benchcab repository][issues-benchcab].

Alternatively, you can also access the ACCESS-NRI User support via [the ACCESS-Hive forum][forum-support].

[xp65_mynci]: https://my.nci.org.au/mancini/project/xp65
[ks32_mynci]: https://my.nci.org.au/mancini/project/ks32
[wd9_mynci]: https://my.nci.org.au/mancini/project/wd9
[rp23_mynci]: https://my.nci.org.au/mancini/project/rp23
[cable_mynci]: https://my.nci.org.au/mancini/project/cable
[bench_example]: https://github.com/CABLE-LSM/bench_example.git
[forum-support]: https://forum.access-hive.org.au/t/access-help-and-support/908
[issues-benchcab]: https://github.com/CABLE-LSM/benchcab/issues
[meorg]: https://modelevaluation.org/
[meorg-registration]: https://modelevaluation.org/registration
[meorg-workspaces]: https://modelevaluation.org/workspaces
[meorg_client]: https://meorg-client.readthedocs.io/en/latest
[meorg_client-setup-credentials]: https://meorg-client.readthedocs.io/en/latest/cli/#set-up-credentials
[meorg-model-outputs]: https://modelevaluation.org/modelOutputs/workspace
[model_profile_eg]: https://modelevaluation.org/model/display/fd5GFaJGYu7H4JpP5
[model_output_eg]: https://modelevaluation.org/modelOutput/display/GnDhhmaehoxcF2nEd
[benchmark_5]: https://modelevaluation.org/modelOutput/display/diLdf49PfpEwZemTz
[benchmark_42]: https://modelevaluation.org/modelOutput/display/pvkuY5gpR2n4FKZw3
[run_CABLE_v2]: running_CABLE_v2.md
[payu-github]: https://github.com/payu-org/payu
[nci-signup]: https://my.nci.org.au/mancini/signup/0
[nci-opus-connecting-to-gadi]: https://opus.nci.org.au/spaces/Help/pages/230491359/Connecting+to+Gadi...#ConnectingtoGadi...-ConnectingtoGadiviaterminal
