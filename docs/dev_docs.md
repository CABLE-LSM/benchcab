# Developer Guide
## Building
### Dependencies
- conda env
```sh
module load conda
conda env create --name benchcab-dev --file .conda/benchcab-dev.yaml
conda activate benchcab-dev
pip install --user -e .
```

### Dev-Dependencies
- `black`, `ruff`, `autoformatter`

!!! tip
    Add a docstring using numpy style. (autodocstring extension in VS Code can pre-populate for you, make sure to select numpy style on settings first).

### Documentation
- mkdocs

```sh
pip install -r mkdocs-requirements.txt
```

!!! tip 
    Using `mkdocs` on Gadi 
    Use ssh port forwarding
    ```sh
    ssh -L 8000:localhost:8000 <username>@gadi.nci.org.au
    ```

```sh
mkdocs serve
```

## Running

Follow the user guide

## Testing
- Static Type Checking  `mypy`
- Unit tests `pytest`
- Integration tests
```sh
/bin/bash benchcab/data/test/integration.sh
```

### Comparing Models

```sh
module load <name>
```

Outputs are stored in `$SRC_DIR/runs/outputs/`

- `netcdf`

```sh
ncdump -h
```

- `nccmp`/`cdo` - Bitwise comparison

```sh
cdo </path/to/output1> </path/to/output2> 
```

!!! tip
    Generally, try to keep a separate copy of `output2` from the `main` branch and `output1` from the feature branch to compare the ouputs, thus checking the validity of integration testing.