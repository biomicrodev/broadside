#!/usr/bin/env bash

set -o errexit

conda env update --file=environment.yml --prune

<<COMMENT
  In order to force napari to use pyside2, we manually uninstall pyqt5 and its
  dependencies after installing napari. conda installs both backends, even with the
  desired backend specified.
COMMENT

pip uninstall --yes pyqt5 pyqt5-sip
