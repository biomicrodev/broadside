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
conda env create --file environment.yml
```

To update the conda environment:

```bash
conda env update --file environment.yml --prune
```

Activate and de-activate accordingly:

```bash
conda activate broadside
...
conda deactivate
```

## Git

[See here](https://docs.github.com/en/free-pro-team@latest/github/importing-your-projects-to-github/adding-an-existing-project-to-github-using-the-command-line) for adding existing projects to github.
