#!/usr/bin/env bash
# Launch the Proxy_check web UI and open it in the browser.
set -e
cd "$(dirname "$(readlink -f "$0")")"
source .venv/bin/activate
python web.py &
SERVER_PID=$!
sleep 1
xdg-open "http://127.0.0.1:5001" >/dev/null 2>&1 || true
wait "$SERVER_PID"
