# Configuration examples for various use cases

In all examples replace strings like XXXXX, YYYYY, etc. with the appropriate values for your case.

## Required run when developing a new feature for CABLE

!!! note Separate runs can be faster

    We show an uniq configuration to get all the results needed but it isn't necessarily the fastest way. Splitting in 2 occurrences of benchcab running at the same time (one for each configuration of the feature branch) can be faster since the benchcab occurrences run in parallel of each other. It requires to setup 2 work directories for benchcab but that is a small amount of work.

When developing a new feature for CABLE (or adapting an existing feature), you need to show 2 things in the pull request:

- the results have not changed compared to the main branch when the feature is off
- the modelevaluation.org analysis results when the feature is on compared to the main branch

This can be done with one benchcab occurrence:

```yaml
realisations:
  - repo:
      git:
        branch: main
  - repo:
      name: my-feature-off (1)
      git:
        branch: XXXXX
  - repo:
      name: my-feature-on
      git:
        branch: XXXXX
    patch: (2)
        cable:
            cable_user:
                new_feature: YYYY

fluxsite:
    meorg_model_output_id: ZZZZ (3)
  
modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```
1. We are using the same branch twice so we need to name each occurrence differently.
2. One should use the same option names and values as implemented in the cable namelist file.
3. You need to setup your environment for meorg_client before using this feature. If splitting in two occurrences for benchcab, this option should only appear with the "my-feature-on" `repo` option.

With this setup, the output of R0 and R1 should be bitwise comparable.
The analysis of R0 and R2 in modelevaluation.org gives the effect of the new feature on the results.

### Modification when changing an existing feature instead of developing a new one.

In that case, you may want to show the comparison between your branch with the feature on and main *with the feature on as well*.

```yaml
realisations: (1)
  - repo:
      git:
        branch: main
    patch: (2)
        cable:
            cable_user:
                existing_feature: YYYY

  - repo:
      git:
        branch: XXXXX
    patch: (2)
        cable:
            cable_user:
                existing_feature: YYYY

fluxsite:
    meorg_model_output_id: ZZZZ (3)
  
modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```
1. We only show the configuration for the feature on case since the configuration for the feature off is the same as previously.
2. One should use the same option names and values as implemented in the cable namelist file.
3. You need to setup your environment for meorg_client before using this feature. 

## Smaller tests during development

### Comparison to one site for local development

During development, one might want to check their results before committing and pushing to CABLE's GitHub repository. It is possible to run benchcab using a local directory. 
The configuration here test both a new feature on and off but it is valid to only run one or the other case.

```yaml
experiment: AU-Tum

realisations:
  - repo:
      git:
        branch: main
  - repo:
      name: my-feature-off (1)
      local:
        path: XXXXX (2)
  - repo:
      name: my-feature-on
      local:
        path: XXXXX
    patch: (3)
        cable:
            cable_user:
                new_feature: YYYY

fluxsite:
    meorg_model_output_id: ZZZZ (4)
    pbs: (5)
      ncpus: 8
      mem: 16GB
      walltime: "0:15:00"
  
modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```
1. We are using the same branch twice so we need to name each occurrence differently.
2. Gives the full path to your local CABLE repository with your code changes.
3. One should use the same option names and values as implemented in the cable namelist file.
4. You need to setup your environment for meorg_client before using this feature. This option should only appear with the "my-feature-on" `repo` option.
5. You can reduce the requested resources to reduce the cost of the test.
