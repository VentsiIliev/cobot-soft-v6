#!/usr/bin/env bash
set -euo pipefail

WHEEL_PATH="${1:-/home/ilv/contour_editor-plugin/ContourEditor-Plugin/dist/contour_editor_plugin-1.0.0-py3-none-any.whl}"
if [ ! -f "$WHEEL_PATH" ]; then
  echo "Wheel not found: $WHEEL_PATH" >&2
  exit 1
fi

python3 -m pip uninstall -y contour_editor_plugin
python3 -m pip install "$WHEEL_PATH"
