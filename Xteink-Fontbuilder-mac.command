#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
if [ ! -d ".venv" ]; then
    bash setup_mac.sh
fi
exec .venv/bin/python main.py
