#!/usr/bin/env bash
# Render start from monorepo root (no Root Directory setting required)
set -euo pipefail
cd railvoice-backend
exec bash scripts/free_boot.sh
