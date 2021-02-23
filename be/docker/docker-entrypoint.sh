#!/bin/sh
set -euo pipefail

if [[ "${DOCKER_NO_VENV:-false}" != "true" ]]; then
    source .venv/bin/activate
fi

export PYTHONPATH=/diaas/be/src/

exec "$@"
