#!/bin/bash
set -e

export PORT=${PORT:-5000}

# Serve the static HTML site
exec python3 -m http.server $PORT --directory .