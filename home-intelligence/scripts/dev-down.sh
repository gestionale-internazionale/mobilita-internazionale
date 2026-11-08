#!/usr/bin/env bash
# Ferma l'istanza Docker di sviluppo (lo stato in dev/runtime resta).
source "$(dirname "$0")/_common.sh"
cd "$ROOT" && docker compose -f docker-compose.dev.yml down
