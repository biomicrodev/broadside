#!/usr/bin/env bash

set -o errexit

echo "Updating conda environment ..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate broadside
conda env update --file=environment.yml --prune

<<COMMENT
  In order to force napari to use pyside2, we manually uninstall pyqt5 and its
  dependencies after installing napari. conda installs both backends, even with the
  desired backend specified.
COMMENT

echo "Uninstalling pyqt5"
pip uninstall --yes pyqt5 pyqt5-sip

conda deactivate
