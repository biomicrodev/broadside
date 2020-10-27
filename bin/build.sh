#!/usr/bin/env bash

set -o errexit

# For MacOS, `realpath` needs to be installed using `brew install coreutils`.
PROJECTPATH=$(realpath "$(dirname "$(realpath $0)")/../")

# enter conda env
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate broadside

pyinstaller \
  --onefile \
  --windowed \
  --distpath "${PROJECTPATH}/dist/" \
  --workpath "${PROJECTPATH}/build/" \
  "${PROJECTPATH}/app.spec"

conda deactivate
