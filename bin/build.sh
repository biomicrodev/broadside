#!/usr/bin/env bash

set -o errexit

# For MacOS, `realpath` needs to be installed using `brew install coreutils`.
PROJECT_ROOT=$(realpath "$(dirname "$(realpath $0)")/../")

# enter conda env
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate broadside

pyinstaller \
  --onedir \
  --windowed \
  --noconfirm \
  --distpath "${PROJECT_ROOT}/dist/" \
  --workpath "${PROJECT_ROOT}/build/" \
  "${PROJECT_ROOT}/app.spec"

conda deactivate
