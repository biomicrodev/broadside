#!/usr/bin/env bash

set -o errexit

# enter conda env
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate broadside

python -m broadside

conda deactivate
