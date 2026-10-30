#!/bin/sh
# Run the extractor with the virtual environment next to this script (macOS and Linux).
DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$DIR/venv/bin/python" "$DIR/extract_order.py" "$@"
