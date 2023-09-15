# config.yaml options

!!! note "Required options"
    All keys listed here are required unless stated otherwise.

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

: **Default:** _required option, no default_. :octicons-dash-24: NCI project ID to charge the simulations to.

``` yaml

project: nf33

```

## modules

: **Default:** _required option, no default_. :octicons-dash-24: NCI modules to use for compiling CABLE

``` yaml

modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]

```

## experiment

: **Default:** _required option, no default_. :octicons-dash-24: Type of experiment to run. Experiments are defined in the **benchcab-evaluation** workspace on [modelevaluation.org][meorg]. This key specifies the met forcing files used in the test suite. To choose from:

    - [`forty-two-site-test`][forty-two-me]: to run simulations using 42 FLUXNET sites
    - [`five-site-test`][five-me]: to run simulations using 5 FLUXNET sites
    - `AU-Tum`: to run simulations at the Tumbarumba (AU) site
    - `AU-How`: to run simulations at the Howard Spring (AU) site
    - `FI-Hyy`: to run simulations at the Hyytiala (FI) site
    - `US-Var`: to run simulations at the Vaira Ranch-Ione (US) site
    - `US-Whs`: to run simulations at the Walnut Gulch Lucky Hills Shrub (US) site

```yaml

experiment: "AU-How"

```

## fluxsite
Contains settings specific to fluxsite tests.

This key is _optional_. **Default** settings for the fluxsite tests will be used if it is not present

```yaml
fluxsite:
  pbs:
    ncpus: 18
    mem: 30GB
    walltime: 06:00:00
    storage: [scratch/a00, gdata/xy11]
  multiprocess: True
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

## realisations

Entries for each CABLE branch to use. Each entry is a dictionary, `{}`, that contains the following keys.

```yaml
realisations: [
  { # head of the trunk
    path: "trunk",
  },
  { # some development branch
    path: "branches/Users/foo/my_branch",
    patch: {
      cable: {
        cable_user: {
          FWSOIL_SWITCH: "Lai and Ktaul 2000"
        }
      }
    },
    patch_remove: {
      cable: {
        soilparmnew: nil
      }
    }
  }
]
```

[`path`](#+realisation.path){ #+realisation.path }

: **Default:** _required option, no default_. :octicons-dash-24: The path of the branch relative to the SVN root of the CABLE repository (`https://trac.nci.org.au/svn/cable`).

```yaml
realisations: [
  { # head of the trunk
    path: "trunk", # (1) 
  },
  { # some development branch
    path: "branches/Users/foo/my_branch", # (2)
  }
]

```

1. To checkout `https://trac.nci.org.au/svn/cable/trunk`
2. To checkout `https://trac.nci.org.au/svn/cable/branches/Users/foo/my_branch`

[`name`](#+realisation.name){ #+realisation.name }

: **Default:** base name of [path](#+realisation.path), _optional key_. :octicons-dash-24: An alias name used internally by `benchcab` for the branch. The `name` key also specifies the directory name when checking out the branch, that is, `name` is the optional `PATH` argument to `svn checkout`.

```yaml
realisations: [
  { # head of the trunk
    path: "trunk",
  },
  { # some development branch
    path: "branches/Users/foo/my_branch", 
    name: "my_feature", # (1)
  }
]

```

1. Checkout the branch in the directory `src/my_feature`

[`build_script`](#+realisation.build_script){ #+realisation.build_script }

: **Default:** unset, _optional key_. :octicons-dash-24: The path to a custom shell script to build the code in that branch, relative to the name of the branch. **Note:** any lines in the provided shell script that call the [environment modules API][environment-modules] will be ignored. To specify modules to use for the build script, please specify them using the [`modules`](#modules) key.

```yaml
realisations: [
  { # head of the trunk
    path: "trunk",
  },
  { # some development branch
    path: "branches/Users/foo/my_branch", 
    build_script: "offline/build.sh", # (1)
  }
]
```

1. Uses the build script stored by `benchcab` as `src/my_branch/offline/build.sh`

[`revision`](#+realisation.revision){ #+realisation.revision }

: **Default:** HEAD of the branch is checked out, _optional key_. :octicons-dash-24: The revision number to checkout for the branch. This option can be used to ensure the reproducibility of the tests.

```yaml
realisations: [
  { # head of the trunk
    path: "trunk",
  },
  { # some development branch
    path: "branches/Users/foo/my_branch", 
    revision: 439,
  }
]
```

[`patch`](#+realisation.patch){ #+realisation.patch }

: **Default:** unset, _optional key_. :octicons-dash-24: Branch-specific namelist settings for `cable.nml`. Settings specified in `patch` get "patched" to the base namelist settings used for both branches. Any namelist settings specified here will overwrite settings defined in the default namelist file and in the science configurations. This means these settings will be set as stipulated in the `patch` for this branch for all science configurations run by `benchcab`.
: The `patch` key must be a dictionary-like data structure that is compliant with the [`f90nml`][f90nml-github] python package.

```yaml
realisations: [
  { # head of the trunk
    path: "trunk",
  },
  { # some development branch
    path: "branches/Users/foo/my_branch",
    patch: { # (1)
      cable: {
        cable_user: {
          FWSOIL_SWITCH: "Lai and Ktaul 2000", 
        }
      }
    }
  }
]
```

1. Sets FWSOIL_SWITCH to "Lai and Ktaul 2000" for all science configurations for this branch

[`patch_remove`](#+realisation.path_remove){#+realisation.patch_remove}

: **Default:** unset, no effect, _optional key. :octicons-dash-24: Specifies branch-specific namelist settings to be removed from the `cable.nml` namelist settings. When the `patch_remove` key is specified, the specified namelists are removed from all namelist files for this branch for all science configurations run by `benchcab`. When specifying a namelist parameter in `patch_remove`, the value of the namelist parameter is ignored.
: The `patch_remove` key must be a dictionary-like data structure that is compliant with the [`f90nml`][f90nml-github] python package.

```yaml
realisations: [
  { # head of the trunk
    path: "trunk",
  },
  { # some development branch
    path: "branches/Users/foo/my_branch",
    patch_remove: {
      cable: {
        soilparmnew: nil, # (1)
      }
    }
  }
]
```

1. The value is ignored and does not have to be a possible value for the namelist option.


## science_configurations

: **Default:** unset, no impact, _optional key_. :octicons-dash-24: User defined science configurations. Science configurations that are specified here will replace [the default science configurations](default_science_configurations.md). In the output filenames, each configuration is identified with S<N\> where N is an integer starting from 0 for the first listed configuration and increasing by 1 for each subsequent configuration.

```yaml
science_configurations: [
  { # S0 configuration
    cable: {
      cable_user: {
        GS_SWITCH: "medlyn",
        FWSOIL_SWITCH: "Haverd2013"
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

[meorg]: https://modelevaluation.org/
[forty-two-me]: https://modelevaluation.org/experiment/display/urTKSXEsojdvEPwdR
[five-me]: https://modelevaluation.org/experiment/display/xNZx2hSvn4PMKAa9R
[f90nml-github]: https://github.com/marshallward/f90nml
[environment-modules]: https://modules.sourceforge.net/
[nci-pbs-directives]: https://opus.nci.org.au/display/Help/PBS+Directives+Explained