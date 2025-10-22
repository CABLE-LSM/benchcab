# config.yaml options

The different running modes of `benchcab` are solely dependent on the options used in `config.yaml`. The following gives some typical ways to configure `benchcab` for each mode, but the tool is not restricted to these choices of options:

=== "Regression test"

    For this test, you want to:

    * Specify the details of two branches of CABLE
    * Do not specify a [`patch`](#+realisation.patch)
    * Use the default set of science options, i.e. do not specify [`science_configurations`](#`science_configurations`) in `config.yaml`
    * Choose the [`experiment`](#`experiment`) suitable for your stage of development. A run with the `forty-two-site-test` will be required for submissions of new development to CABLE.

=== "New feature test"

    For this test, you want to:

    * Specify the details of two branches of CABLE
    * Specify a [`patch`](#+realisation.patch) for **one** of the branches
    * Use the default set of science options, i.e. do not specify [`science_configurations`](#`science_configurations`) in `config.yaml`
    * Choose the [`experiment`](#`experiment`) suitable for your stage of development. A run with the `forty-two-site-test` will be required for submissions of new development to CABLE.


=== "Ensemble mode"

    This running mode is quite open to customisations:

    * Specify the number of CABLE's branches you need
    * Use [`patch`](#+realisation.patch) on branches as required
    * Specify the [science configurations](#`science_configurations`) you want to run. [`patch`](#+realsation.patch) will be applied on top of the science configurations listed.


## project

: **Default:** user's default project, _optional key_. :octicons-dash-24: NCI project ID to charge the simulations to. The user's default project defined in the $PROJECT environment variable is used by default.

``` yaml

project: nf33

```

## modules

: **Default:** _required key, no default_. :octicons-dash-24: NCI modules to use for compiling CABLE

``` yaml

modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]

```

## fluxsite
Contains settings specific to fluxsite tests.

This key is _optional_. **Default** settings for the fluxsite tests will be used if it is not present

```yaml
fluxsite:
  experiment: AU-How
  pbs:
    ncpus: 18
    mem: 30GB
    walltime: 06:00:00
    storage: [scratch/a00, gdata/xy11]
  multiprocess: True
```

### [experiment](#experiment)

: **Default:** `forty-two-site-test`, _optional key_. :octicons-dash-24: Type of fluxsite experiment to run. Experiments are defined in the **benchcab-evaluation** workspace on [modelevaluation.org][meorg]. This key specifies the met forcing files used in the test suite. To choose from:

: | Key value | Experiment description |
|-----------|------------------------|
| [`forty-two-site-test`][forty-two-me] | Run simulations for 42 FLUXNET sites |
| [`five-site-test`][five-me] | Run simulations for 5 FLUXNET sites |
| `AU-Tum` | Run simulations at the Tumbarumba (AU) site |
| `AU-How` | Run simulations at the Howard Spring (AU) site |
| `FI-Hyy` | Run simulations at the Hyytiala (FI) site |
| `US-Var` | Run simulations at the Vaira Ranch-Ione (US) site |
| `US-Whs` | Run simulations at the Walnut Gulch Lucky Hills Shrub (US) site |

```yaml
fluxsite:
  experiment: AU-How

```

### [pbs](#pbs)

Contains settings specific to the PBS scheduler at NCI for the PBS script running the CABLE simulations at FLUXNET sites and the bitwise comparison for these simulations.

This key is _optional_. **Default** values for the PBS settings will apply if it is not specified.

```yaml
fluxsite:
  pbs:
    ncpus: 18
    mem: 30GB
    walltime: 06:00:00
    storage: [scratch/a00, gdata/xy11]
```

[`ncpus`](#+pbs.ncpus){ #+pbs.ncpus }

: **Default:** 18, _optional key_. :octicons-dash-24: The number of CPU cores to allocate for the PBS job, i.e. the `-l ncpus=<4>` PBS flag in [PBS Directives Explained][nci-pbs-directives].

```yaml

fluxsite:
  pbs:
    ncpus: 18

```

[`mem`](#+pbs.mem){ #+pbs.mem }

: **Default:** 30GB, _optional key_. :octicons-dash-24: The total memory limit for the PBS job, i.e. the `-l mem=<10GB>` PBS flag in [PBS Directives Explained][nci-pbs-directives].

```yaml

fluxsite:
  pbs:
    mem: 30GB

```

[`walltime`](#+pbs.walltime){ #+pbs.walltime }

: **Default:** `6:00:00`, _optional key_. :octicons-dash-24: The wall clock time limit for the PBS job, i.e. `-l walltime=<HH:MM:SS>` PBS flag in [PBS Directives Explained][nci-pbs-directives].

```yaml

fluxsite:
  pbs:
    walltime: 6:00:00

```
[`storage`](#+pbs.storage){ #+pbs.storage }

: **Default:** [], _optional key_. :octicons-dash-24: List of extra storage flags required for the PBS job, i.e. `-l storage=<scratch/a00>` in [PBS Directives Explained][nci-pbs-directives].

```yaml

fluxsite:
  pbs:
    storage: [scratch/a00, gdata/xy11]

```

### [multiprocess](#multiprocess)

: **Default:** True, _optional key_. :octicons-dash-24: Enables or disables multiprocessing for executing embarrassingly parallel tasks.

```yaml

fluxsites:
  multiprocess: True

```

## spatial

Contains settings specific to spatial tests.

This key is _optional_. **Default** settings for the spatial tests will be used if it is not present.

```yaml
spatial:
  met_forcings:
    crujra_access: https://github.com/CABLE-LSM/cable_example.git
  payu:
    config:
      walltime: 1:00:00
    args: -n 2
```

### [met_forcings](#met_forcings)

Specify one or more spatial met forcings to use in the spatial test suite. Each entry is a key-value pair where the key is the name of the met forcing and the value is a URL to a payu experiment that is configured to run CABLE with that forcing.

This key is _optional_. **Default** values for the `met_forcings` key is as follows:

```yaml
spatial:
  met_forcings:
    crujra_access: https://github.com/CABLE-LSM/cable_example.git
```

### [payu](#payu)

Contains settings specific to the payu workflow manager.

This key is _optional_. **Default** values for the payu settings will apply if not specified.

```yaml
spatial:
  payu:
    config:
      walltime: 1:00:00
    args: -n 2
```

[`config`](#+payu.config){ #+payu.config }

: **Default:** unset, _optional key_. :octicons-dash-24: Specify global configuration options for running payu. Settings specified here are passed into to the payu configuration file for each experiment.

```yaml
spatial:
  payu:
    config:
      walltime: 1:00:00
```

[`args`](#+payu.args){ #+payu.args }

: **Default:** unset, _optional key_. :octicons-dash-24: Specify command line arguments to the `payu run` command in the form of a string. Arguments are used for all spatial payu runs.

```yaml
spatial:
  payu:
    args: -n 2
```

## realisations

Entries for each CABLE branch to use. Each entry is a key-value pair and are listed as follows:

```yaml
realisations:
  # head of main branch
  - repo:
      git:
        branch: main
  # some development branch
  - repo:
      git:
        branch: my_branch
    patch:
      cable:
        cable_user:
          FWSOIL_SWITCH: "Lai and Ktaul 2000"
    patch_remove:
      cable:
        soilparmnew: nil
```

### [repo](#repo)

Contains settings to specify the CABLE branch to test against. 

This key is _required_. The `repo` key must specify the [`svn`](#+repo.svn), the [`git`](#+repo.git) or the [`local`](#+repo.local) key.

```yaml
realisations:
  - repo:
      svn:
        branch_path: trunk
  - repo:
      git:
        branch: main
  - repo:
      local:
        path: /home/ab1234/cable_local
```

#### [`svn`](#+repo.svn){ #+repo.svn}

Contains settings to specify a branch from the CABLE SVN repository (`https://trac.nci.org.au/svn/cable`).

This key is _optional_. No default.

```yaml
realisations:
  - repo:
      svn:
        branch_path: branches/Users/foo/my_branch
        revision: 1234
```

[`branch_path`](#+repo.svn.branch_path){ #+repo.svn.branch_path}

: **Default:** _required key, no default_. :octicons-dash-24: Specify the branch path relative to the SVN root of the CABLE repository (`https://trac.nci.org.au/svn/cable`).

```yaml
realisations:
  # head of the trunk
  - repo:
      svn:
        branch_path: trunk # (1)
  # some development branch
  - repo:
      svn:
        branch_path: branches/Users/foo/my_branch # (2)
```

1. To checkout `https://trac.nci.org.au/svn/cable/trunk`
2. To checkout `https://trac.nci.org.au/svn/cable/branches/Users/foo/my_branch`

[`revision`](#+repo.svn.revision){ #+repo.svn.revision}

: **Default:** HEAD of the branch is checked out, _optional key_. :octicons-dash-24: Specify the revision number to checkout for the branch. This option can be used to ensure the reproducibility of the tests.

```yaml
realisations:
  - repo:
      svn:
        branch_path: branches/Users/foo/my_branch
        revision: 1234
```

#### [`git`](#+repo.git){ #+repo.git}

Contains settings to specify a branch on the GitHub repository. By default, the [CABLE GitHub repository][cable-github] will be cloned (see [`url`](#+repo.git.url) to specify another GitHub repository).

This key is _optional_. No default.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
        commit: 067b1f4a570385fce01552fdf96ced0adbbe17eb
        url: https://github.com/SeanBryan51/CABLE.git
```

[`branch`](#+repo.git.branch){ #+repo.git.branch}

: **Default:** _required key, no default_. :octicons-dash-24: Specify the GitHub branch name to be checked out.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
```

[`commit`](#+repo.git.commit){ #+repo.git.commit}

: **Default:** unset, _optional key_. :octicons-dash-24: Specify a specific commit to use for the branch.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
        commit: 067b1f4a570385fce01552fdf96ced0adbbe17eb
```

[`url`](#+repo.git.url){ #+repo.git.url}

: **Default:** URL of the [CABLE GitHub repository][cable-github], _optional key_. :octicons-dash-24: Specify the GitHub repository url to clone from when checking out the branch.

#### [`local`](#+repo.local){ #+repo.local}

Contains settings to specify CABLE checkouts on a local repository.

This key is _optional_. No default.

```yaml
realisations:
  - repo:
      local:
        path: /scratch/tm70/ab1234/CABLE
```

[`path`](#+repo.local.path){ #+repo.local.path}

: **Default:** _required key, no default_. :octicons-dash-24: Specify the local checkout path of CABLE branch.

### [meorg_output_name](#meorg_output_name)


: **Default:** unset, _optional key_. :octicons-dash-24: Chosen as the model name for one of the realisations, if the user wants to upload the Model Output to me.org for further analysis. The following workflow is executed:
1. A new model output name is created based on the selected realisation. A `base32` format hash derived from `realisations`, `model_profile_id` and `$USER` is also appended. This minimises collision between different use-cases for different users. In case the `model_output_name` already exists, the files within that model output are deleted, for fresh set of benchmarking results to be sent for analysis.
2. The following settings are taken by default for the model output
  - Model Profile - `CABLE`
  - State Selection - `default`
  - Parameter Selection - `automated`
  - Bundled experiments - `true`
  - Comments - `none`
3. Depending on the fluxsite [`experiment`](#`experiment`), `benchcab` will do the following:
  - Add them experiments in model output.
  - Associate the experiment with base benchmark (already stored in `me.org`), and other listed realisations. 
4. Run the analysis, and provide a link to the user to check status.

Note: It is the user's responsbility to ensure the model output name does not clash with existing names belonging to other users on modelevaluation.org. The realisation name is set via `name` if provided, otherwise the default realisation name of the `Repo`. 

The model output name should also follow the Github issue branch format (i.e. it should start with a digit, with words separated by dashes). Finally, the maximum number of characters allowed for `meorg_output_name` is 50.

This key is _optional_. No default.

```yaml
realisations:
  - repo:
      git:
        branch: 123-my-branch
        meorg_output_name: True
  - repo:
      git:
        branch: 456-my-branch
```

### [name](#name)

: **Default:** base name of [branch_path](#+repo.svn.branch_path) if an SVN repository is given; the branch name if a git repository is given; the folder name if a local path is given, _optional key_. :octicons-dash-24: An alias name used internally by `benchcab` for the branch. The `name` key also specifies the directory name of the source code when retrieving from SVN, GitHub or local.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
    name: my_feature # (1)
```

1. Checkout the branch in the directory `src/my_feature`

### [build_script](#build_script)

: **Default:** unset, _optional key_. :octicons-dash-24: The path to a custom shell script to build the code in that branch, relative to the repository root directory. **Note:** any lines in the provided shell script that call the [environment modules API][environment-modules] will be ignored. To specify modules to use for the build script, please specify them using the [`modules`](#modules) key.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
    build_script: offline/build.sh
```

### [install_dir](#install-dir)

: **Default:** unset, _optional key_. :octicons-dash-24: The path to the directory containing the installed executables relative to the project root directory of the CABLE repository. If specified, `benchcab` will look for executables in this directory when building up the run directories.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
    install_dir: path/to/bin/directory
```

### [patch](#patch)

: **Default:** unset, _optional key_. :octicons-dash-24: Branch-specific namelist settings for `cable.nml`. Settings specified in `patch` get "patched" to the base namelist settings used for both branches. Any namelist settings specified here will overwrite settings defined in the default namelist file and in the science configurations. This means these settings will be set as stipulated in the `patch` for this branch for all science configurations run by `benchcab`.
: The `patch` key must be a dictionary-like data structure that is compliant with the [`f90nml`][f90nml-github] python package.
: To specify a boolean namelist option, one needs to use the Python booleans, True and False, **not the Fortran booleans**

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
    patch:  # (1)
      cable:
        cable_user:
          FWSOIL_SWITCH: "Lai and Ktaul 2000"
          litter: True # (2)
```

1. Sets FWSOIL_SWITCH to "Lai and Ktaul 2000" for all science configurations for this branch
2. The Python boolean will be translated to a Fortran boolean when writing to the namelist file
   
### [patch_remove](#patch_remove)

: **Default:** unset, _optional key. :octicons-dash-24: Specifies branch-specific namelist settings to be removed from the `cable.nml` namelist settings. When the `patch_remove` key is specified, the specified namelists are removed from all namelist files for this branch for all science configurations run by `benchcab`. When specifying a namelist parameter in `patch_remove`, the value of the namelist parameter is ignored.
: The `patch_remove` key must be a dictionary-like data structure that is compliant with the [`f90nml`][f90nml-github] python package.

```yaml
realisations:
  - repo:
      git:
        branch: my_branch
    patch_remove:
      cable:
        soilparmnew: nil # (1)
```

1. The value is ignored and does not have to be a possible value for the namelist option.


## science_configurations

: **Default:** unset, _optional key_. :octicons-dash-24: User defined science configurations. Science configurations that are specified here will replace [the default science configurations](default_science_configurations.md). In the output filenames, each configuration is identified with S<N\> where N is an integer starting from 0 for the first listed configuration and increasing by 1 for each subsequent configuration.
: To specify a boolean namelist option, one needs to use the Python booleans, True and False, **not the Fortran booleans**

```yaml
science_configurations: [
  { # S0 configuration
    cable: {
      cable_user: {
        GS_SWITCH: "medlyn",
        FWSOIL_SWITCH: "Haverd2013",
        litter: True # (1)
      }
    }
  },
  { # S1 configuration
    cable: {
      cable_user: {
        GS_SWITCH: "leuning",
        FWSOIL_SWITCH: "Haverd2013"
      }
    }
  }
]
```

1. The Python boolean will be translated to a Fortran boolean when writing the namelist file.

## codecov

: **Default:** False, _optional key. :octicons-dash-24: Specifies whether to build `benchcab` with code-coverage flags, which can then be used in post-run analysis (`benchcab gen_codecov`).

```yaml
codecov:
  true
```

[meorg]: https://modelevaluation.org/
[forty-two-me]: https://modelevaluation.org/experiment/display/s6k22L3WajmiS9uGv
[five-me]: https://modelevaluation.org/experiment/display/Nb37QxkAz3FczWDd7
[f90nml-github]: https://github.com/marshallward/f90nml
[environment-modules]: https://modules.sourceforge.net/
[nci-pbs-directives]: https://opus.nci.org.au/display/Help/PBS+Directives+Explained
[cable-github]: https://github.com/CABLE-LSM/CABLE

## meorg_bin

: **Default:** False, _optional key. :octicons-dash-24: Specifies the absolute system path to the ME.org client executable. In the absence of this key it will be inferred from the same directory as benchcab should `meorg_output_name` be set in `realisations` above.

``` yaml

meorg_bin: /path/to/meorg

```
