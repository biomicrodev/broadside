# Broadside
Digital pathology for local _in vivo_ multiplex drug delivery.

Created by the Laboratory for Bio-Micro Devices at Brigham & Women's Hospital.

# Commands

| Action                        | Command                                             |
| ----------------------------- | --------------------------------------------------- |
| update conda                  | `conda update --name base --channel defaults conda` |
| init conda env                | `conda env create [--file=environment.yml]`         |
| update conda env              | `bin/conda-update.sh`                               |
| activate/deactivate conda env | `conda activate broadside; ...; conda deactivate`   |
| package into executable       | `bin/build.sh`                                      |
| test                          | `pytest`                                            |
