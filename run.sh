#!/usr/bin/env bash
# One-command launcher for Linux / macOS
cd "$(dirname "$0")"
if [ ! -d venv ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
python -m pip install -q -r requirements.txt
( sleep 2; (command -v xdg-open >/dev/null && xdg-open http://127.0.0.1:5000) || (command -v open >/dev/null && open http://127.0.0.1:5000) ) >/dev/null 2>&1 &
python app.py
