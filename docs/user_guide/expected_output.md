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
