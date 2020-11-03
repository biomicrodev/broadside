# Notes
We use conda for managing python versions and dependencies. Install miniconda [from here](https://docs.conda.io/en/latest/miniconda.html).

# Common commands

## Conda

| Action                        | Command                                             |
| ----------------------------- | --------------------------------------------------- |
| update conda                  | `conda update --name base --channel defaults conda` |
| init conda env                | `conda env create [--file=environment.yml]`         |
| update conda env              | `bin/conda-update.sh`                               |
| activate/deactivate conda env | `conda activate broadside; ...; conda deactivate`   |
| download bioformats           | `bin/download-bioformats.py`                        |

## Git

[See here](https://gist.github.com/c0ldlimit/4089101) for adding existing projects to github.

## Packaging

Execute `bin/build.sh`.

## Testing

Execute `pytest` in the project directory.
