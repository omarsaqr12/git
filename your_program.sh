#!/bin/sh
# CodeCrafters-compatible entry point. Run from the target working directory.
set -e
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m app.main "$@"
