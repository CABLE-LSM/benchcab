# Running with CABLE version 2.x

There are two differences one might need to deal with to run with an older version of CABLE in `benchcab`:

- the build script is different
- the FLUXNET data is using the new ALMA convention which may not be supported by older CABLE versions.

## Build script

`benchcab` by default assumes the source code is compiled by the build script for version 3. To use other build scripts, you will need to:

- make sure the Gadi host is known in your build script. If you do not have a `host_gadi()` section in your build script, you might be able to add the following to your build script: 
    ```bash title="build script excerpt"
    known_hosts()
    {
 	   set -A kh gadi cher pear shin jigg nXXX ces2 
 	}
 	##
 	host_gadi()
 	{
 	   . /etc/bashrc
 	   module purge
 	   module add intel-compiler/2021.1.1
 	   module add openmpi/4.1.0
 	   module add netcdf/4.7.4
 	
 	   export FC='mpif90'
 	   export NCDIR=$NETCDF_ROOT'/lib/Intel'
 	   export NCMOD=$NETCDF_ROOT'/include/Intel'
 	   export CFLAGS='-O2 -fp-model precise'
 	   if [[ $1 = 'debug' ]]; then
 	      export CFLAGS='-O0 -traceback -g -fp-model precise -ftz -fpe0'
 	   fi
 	   export LDFLAGS='-L'$NCDIR' -O0'
 	   export LD='-lnetcdf -lnetcdff'
 	   build_build
 	   cd ../
 	   build_status
 	}
    ```

- ensure your build script is using exactly the same modules as listed in the [`config.yaml` file](config_options.md#modules) of the `benchcab` work directory. For this you can either modify the modules in your build script or in the `config.yaml` file. Make sure to commit the build script with the correct modules to your branch before running `benchcab`.
- give the path to the build script for that older branch using the [`build_script` option](config_options.md#build_script) in the `config.yaml` file.
- give the path to the install directory of built executables using the [`install_dir` option](config_options.md#install_dir) in the `config.yaml`.

## FLUXNET data

`benchcab` is using [the FLUXNET data][PLUMBER2_data] published for PLUMBER2. Some of the variables in these files have different names and/or number of dimensions than previous versions of the FLUXNET data. As such, older versions of CABLE might not read the data correctly and need a patch to the source code reading in the meteorological forcing.

To patch your CABLE code to read the new format, you will need to replace the subroutines *open_met_file* and *get_met_data* in `offline/cable_input.F90`. You can use the subroutines provided here:

- [*open_met_file* subroutine][open_met_file_sub]
- [*get_met_data* subroutine][get_met_data_sub]

Make sure to commit your patched CABLE source code before running `benchcab`.

!!! danger "Compatibility with older ALMA format not guaranteed"

    The new subroutines *open_met_file* and *get_met_data* have not been tested with the older ALMA format for the FLUXNET data. We will not ensure compatibility with the older format since it is outdated. It is recommended to update to the new format for all experiments.

[PLUMBER2_data]: https://geonetwork.nci.org.au/geonetwork/srv/eng/catalog.search#/metadata/f7075_4625_2374_0846
[open_met_file_sub]: ../assets/v2_support/open_met_file_sub.F90
[get_met_data_sub]: ../assets/v2_support/get_met_data_sub.F90
