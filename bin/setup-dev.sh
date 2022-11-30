#!/usr/bin/env bash
set -euxo pipefail
IFS=$'\n\t'

eval "$(conda shell.bash hook)"
conda activate broadside
python -m pip install .[dev] .[before-annotate] .[annotate] .[after-annotate]
conda deactivate
