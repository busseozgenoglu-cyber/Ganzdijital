#!/bin/bash
set -e
export PORT=${PORT:-5000}
exec python3 server.py --port $PORT
