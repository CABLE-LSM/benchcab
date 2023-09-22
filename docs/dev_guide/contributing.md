# Contributors Guide

## Ways to contribute

We welcome a range of contributions to this open-source software:

- open or contribute to [a GitHub issue][benchcab_issues] to convey a problem or send a bug report or propose an enhancement
- update the documentation to fix a typo, improve the clarity or the readability, add missing sections, etc.
- contribute to the code to fix an open issue.

_Before_ contributing to the documentation or the code-base, consider becoming a member of the CABLE-LSM GitHub organisation. Doing so allows you to create a branch within the `benchcab` repository instead of working from a fork which simplifies the contribution process. To request an invitation to the organisation please [open an issue][new_issue] on the `benchcab` repository.

## Contributing documentation

The documentation is written in Markdown using [Material for Mkdocs][Material] and distributed through [ReadTheDocs][ReadTheDocs].
The `benchcab` repository has continuous integration set up to build a preview of the documentation for all pull requests which means you are not required to build the documentation locally.

If you would like to build the documentation locally, you can use the [`pip` requirements file][mkdocs-requirements] to install all the required packages. Once the packages are installed, you can use `mkdocs serve` from the top level of the `benchcab` repository to build a local version.

## Contributing code

`benchcab` is written in python 3. It is using the following packages and standards for formatting:

- [flake8][flake8] for linting
- [black][black] for code formatting

`benchcab` supports the stable Python versions. It should not contain features from pre-release versions. All contributions to `benchcab` should follow the ACCESS-NRI [Coding guidelines for Python][code_guidelines].

### Testing
You can use this [conda environment file][benchcab-dev] to install a development environment to test your changes locally.

`benchcab` comes with a suite of unit tests written in the [`pytest`][pytest] framework. New contributions to the code base are expected to update the tests as required.

[Material]: https://squidfunk.github.io/mkdocs-material/
[ReadTheDocs]: https://about.readthedocs.com/
[mkdocs-requirements]: https://github.com/CABLE-LSM/benchcab/blob/master/mkdocs-requirements.txt
[new_issue]: https://github.com/CABLE-LSM/benchcab/issues/new
[benchcab_issues]: https://github.com/CABLE-LSM/benchcab/issues/
[benchcab-dev]: https://github.com/CABLE-LSM/benchcab/blob/master/.conda/benchcab-dev.yaml
[flake8]: https://flake8.pycqa.org/en/latest/
[black]: https://pypi.org/project/black/
[code_guidelines]: https://github.com/ACCESS-NRI/dev-docs/wiki/Code-guidelines#python
[pytest]: https://docs.pytest.org/en/7.3.x/