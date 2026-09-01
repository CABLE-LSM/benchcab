# Expected output from benchcab

Below you will find examples of the expected output printed by `benchcab` to the screen when running the full workflow, with `benchcab run`. 

Other sub-commands should print out part of this output.

```
$ benchcab run
Creating src directory
Checking out repositories...
Successfully checked out trunk at revision 9672
Successfully checked out test-branch at revision 9672
Successfully checked out CABLE-AUX at revision 9672
Writing revision number info to rev_number-1.log

Compiling CABLE serially for realisation trunk...
Successfully compiled CABLE for realisation trunk
Compiling CABLE serially for realisation test-branch...
Successfully compiled CABLE for realisation test-branch

Compiling CABLE with MPI for realisation trunk...
Successfully compiled CABLE for realisation trunk
Compiling CABLE with MPI for realisation test-branch...
Successfully compiled CABLE for realisation test-branch

Setting up run directory tree for fluxsite tests...
Setting up tasks...
Successfully setup fluxsite tasks

Setting up run directory tree for spatial tests...
Setting up tasks...
Successfully setup spatial tasks

Creating PBS job script to run fluxsite tasks on compute nodes: benchmark_cable_qsub.sh
PBS job submitted: 100563227.gadi-pbs
The CABLE log file for each task is written to runs/fluxsite/logs/<task_name>_log.txt
The CABLE standard output for each task is written to runs/fluxsite/tasks/<task_name>/out.txt
The NetCDF output for each task is written to runs/fluxsite/outputs/<task_name>_out.nc

Running spatial tasks...
Successfully dispatched payu jobs

```

The benchmark_cable_qsub.sh PBS job should print out the following to the job log file:
```
Running fluxsite tasks...
Successfully ran fluxsite tasks

Running comparison tasks...
Success: files AU-Tum_2002-2017_OzFlux_Met_R0_S0_out.nc AU-Tum_2002-2017_OzFlux_Met_R1_S0_out.nc are identical
Success: files AU-Tum_2002-2017_OzFlux_Met_R0_S1_out.nc AU-Tum_2002-2017_OzFlux_Met_R1_S1_out.nc are identical
Success: files AU-Tum_2002-2017_OzFlux_Met_R0_S2_out.nc AU-Tum_2002-2017_OzFlux_Met_R1_S2_out.nc are identical
Success: files AU-Tum_2002-2017_OzFlux_Met_R0_S3_out.nc AU-Tum_2002-2017_OzFlux_Met_R1_S3_out.nc are identical
Successfully ran comparison tasks
```

# Directory structure and files

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
