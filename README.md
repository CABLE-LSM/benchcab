# benchcab

[![Documentation status][readthedocs_badge]][docs] [![Test coverage][codecov_badge]][codecov_summary] [![Conda package status][conda_badge]][conda] [![GitHub License][license_badge]][license]

<!-- --8<-- [start:contents] -->
`benchcab` is a testing framework that tests the CABLE land surface model across a range of model configurations and model versions. The tool:

- checks out the model versions specified by the user
- builds the required executables
- runs each model version across N standard science configurations for a variety of meteorological forcings
- performs bitwise comparison checks on model outputs across model versions

The user can then pipe the model outputs into a benchmark analysis via [modelevaluation.org][meorg] to assess model performance.

The full documentation is available at [benchcab.readthedocs.io][docs].

## Supported configurations

`benchcab` currently tests the following model configurations for CABLE:

- **Flux site simulations (offline)** - running CABLE forced with observed eddy covariance data at a single site
- **Global/regional simulations (offline)** - running CABLE forced with meteorological fields over a region (global or regional)

## License

`benchcab` is distributed under [an Apache License v2.0][apache-license].

## Acknowledgements

`benchcab` is a continuation of the efforts made by Martin De Kauwe ([@mdekauwe](https://github.com/mdekauwe)) and Gab Abramowitz ([@gabsun](https://github.com/gabsun)) in developing a CABLE benchmarking framework - we thank them for their contribution.

[conda_badge]: https://img.shields.io/conda/v/accessnri/benchcab
[codecov_badge]: https://codecov.io/gh/CABLE-LSM/benchcab/branch/main/graph/badge.svg?token=JJYE1YZDXQ
[readthedocs_badge]: https://readthedocs.org/projects/benchcab/badge/?version=stable
[license_badge]: https://img.shields.io/github/license/CABLE-LSM/benchcab
[conda]: https://anaconda.org/accessnri/benchcab
[codecov_summary]: https://codecov.io/gh/CABLE-LSM/benchcab
[docs]: https://benchcab.readthedocs.io
[license]: https://github.com/CABLE-LSM/benchcab/blob/main/LICENSE
[meorg]: https://modelevaluation.org
[apache-license]: https://www.apache.org/licenses/LICENSE-2.0
<!-- --8<-- [end:contents] -->