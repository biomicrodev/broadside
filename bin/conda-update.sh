#!/usr/bin/env bash

set -o errexit

conda env update --file=environment.yml --prune

<<COMMENT
  In order to force napari to use pyside2, we manually uninstall pyqt5 and its
  dependencies after installing napari. conda does not do this automatically, even with
  the backend specified.
COMMENT

pip uninstall --yes pyqt5 pyqt5-sip
