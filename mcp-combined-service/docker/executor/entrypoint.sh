#!/bin/sh
# MCP Code Executor Container Entrypoint
#
# Sets up the sandboxed execution environment and starts the server.

set -e

# Log startup
echo "Starting MCP Code Executor"
echo "Port: ${DENO_PORT:-3000}"
echo "Backend: ${PYTHON_BACKEND_URL:-http://host.docker.internal:8000}"

# Verify we're not running as root
if [ "$(id -u)" = "0" ]; then
    echo "Error: Container should not run as root"
    exit 1
fi

# Start the server
exec node dist/server.js
