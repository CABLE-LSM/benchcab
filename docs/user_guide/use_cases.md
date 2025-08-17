# Configuration examples for various use cases

In all examples replace strings like XXXXX, YYYYY, etc. with the appropriate values for your case.

## Check bitwise comparability

```yaml
realisations:
  - repo:
      git:
        branch: main
  - repo:
      git:
        branch: XXXXX
  
modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```

The results of the bitwise comparison will be in the log file from the flux site run.


## Evaluate the effect of a new feature

If you are developing a new feature and want to check the effect compared to the main version, you need to run:

- the main version as is
- the development branch with the new feature turned on for all science configurations

```yaml
realisations:
  - repo:
      git:
        branch: main
    model_output_name: True # (1)
  - repo:
      git:
        branch: XXXXX
    patch: # (2)
        cable:
            cable_user:
                existing_feature: YYYY

modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```

1. You need to setup your environment for meorg_client before using this feature. 
2. Use the option names and values as implemented in the cable namelist file.

The evaluation results will be on modelevaluation.org accessible from the Model Output page you've specified

## Evaluate the effect of a modified feature

If you are modifying an *existing* feature of CABLE (bug fix or other development) and want to check the effect of your changes compared to the main version, with that feature turned on, you need to run:

- the main branch with the new feature turned on for all science configurations
- the development branch with the new feature turned on for all science configurations

```yaml
realisations:
  - repo:
      git:
        branch: main
    patch: # (1)
        cable:
            cable_user:
                existing_feature: YYYY
    model_output_name: True # (2)
  - repo:
      git:
        branch: XXXXX
    patch: # (3)
        cable:
            cable_user:
                existing_feature: YYYY

modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```

1. Use the option names and values as implemented in the cable namelist file.
2. You need to setup your environment for meorg_client before using this feature. 
3. Use the option names and values as implemented in the cable namelist file.

The evaluation results will be on modelevaluation.org accessible from the Model Output page you've specified

## Evaluation of a bug fix affecting all science options

If you have a bug fix that affects all CABLE simulations, you need to run:

- the main branch as is
- the development branch as is

```yaml
realisations:
  - repo:
      git:
        branch: main
    model_output_name: True # (2)
  - repo:
      git:
        branch: XXXXX

modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```

1. You need to setup your environment for meorg_client before using this feature. 

The evaluation results will be on modelevaluation.org accessible from the Model Output page you've specified

## Early test of development using a local repository 

Do a quick test at one site only to compare a new feature on and off together and with the main branch.

To run only the fluxsite experiment, execute `benchcab fluxsite` with the following config.yaml file.

```yaml
experiment: AU-Tum # (1)

realisations:
  - repo:
      git:
        branch: main
    model_output_name: True # (2)
  - repo:
      name: my-feature-off # (3)
      local:
        path: XXXXX # (4)
  - repo:
      name: my-feature-on
      local:
        path: XXXXX
    patch: # (5)
        cable:
            cable_user:
                new_feature: YYYY

fluxsite:
    pbs: # (6)
      ncpus: 8
      mem: 16GB
      walltime: "0:15:00"
  
modules: [
  intel-compiler/2021.1.1,
  netcdf/4.7.4,
  openmpi/4.1.0
]
```

1. Testing at one flux site only to save time and resources.
2. You need to setup your environment for meorg_client before using this feature.
3. We are using the same branch twice so we need to name each occurrence differently.
4. Give the full path to your local CABLE repository with your code changes.
5. Use the option names and values as implemented in the cable namelist file.
6. You can reduce the requested resources to reduce the cost of the test.

Comparisons of R0 and R1 should show bitwise agreement. R2 and R0 (and R1) comparison on modelevaluation.org shows the impact of the changes.