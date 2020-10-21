# Notes
We use conda for managing python versions and dependencies. Install miniconda [from here](https://docs.conda.io/en/latest/miniconda.html).

# Common commands

## Conda

To update conda itself:

```bash
conda update --name base --channel defaults conda
```

To initialize the conda environment:

```bash
conda env create [--file=environment.yml]
```

To update the conda environment, set `conda-update.sh` to be executable and then

```bash
bin/conda-update.sh
```

Activate and de-activate accordingly:

```bash
conda activate broadside
...
conda deactivate
```

## Git

[See here](https://gist.github.com/c0ldlimit/4089101) for adding existing projects to github.
