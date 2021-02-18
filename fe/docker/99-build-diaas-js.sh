#!/bin/bash
set -euo pipefail

/docker-entrypoint.d/build-diaas-js.py > /usr/share/nginx/html/diaas.js
