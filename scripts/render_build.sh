#!/usr/bin/env bash
# Render build from monorepo root (no Root Directory setting required)
set -euo pipefail
cd railvoice-backend
pip install -r requirements.txt
