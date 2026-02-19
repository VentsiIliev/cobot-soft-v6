#!/usr/bin/env bash
set -euo pipefail

WHEEL_PATH="${1:-/home/ilv/contour_editor-plugin/ContourEditor-Plugin/dist/contour_editor_plugin-1.0.0-py3-none-any.whl}"
WHEEL_NAME="$(basename "$WHEEL_PATH")"
REMOTE_BASE_URL="${SVN_BASE_URL:-https://server:8443/svn/25067_FARINO_Cobot_Glue_Noozle/trunk/contour_editor_plugin/ContourEditor-Plugin/dist}"

if [ ! -f "$WHEEL_PATH" ]; then
  if ! command -v curl >/dev/null 2>&1; then
    echo "Wheel not found: $WHEEL_PATH" >&2
    echo "curl is required to fetch from SVN" >&2
    exit 1
  fi
  TMP_DIR="$(mktemp -d)"
  REMOTE_WHEEL="${REMOTE_BASE_URL%/}/$WHEEL_NAME"
  if [ -n "${SVN_USERNAME:-}" ] || [ -n "${SVN_PASSWORD:-}" ]; then
    curl -fL -u "${SVN_USERNAME:-}:${SVN_PASSWORD:-}" -o "$TMP_DIR/$WHEEL_NAME" "$REMOTE_WHEEL"
  else
    curl -fL -o "$TMP_DIR/$WHEEL_NAME" "$REMOTE_WHEEL"
  fi
  WHEEL_PATH="$TMP_DIR/$WHEEL_NAME"
fi

if [ ! -f "$WHEEL_PATH" ]; then
  echo "Wheel not found: $WHEEL_PATH" >&2
  exit 1
fi

python3 -m pip uninstall -y contour_editor_plugin
python3 -m pip install "$WHEEL_PATH"
