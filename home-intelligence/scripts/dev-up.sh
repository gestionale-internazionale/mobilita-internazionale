#!/usr/bin/env bash
# Avvia Home Assistant di SVILUPPO con il pacchetto di simulazione.
#   scripts/dev-up.sh docker   # Home Assistant Container (Docker), consigliato su Linux
#   scripts/dev-up.sh venv     # Home Assistant Core in un virtualenv Python 3.13
# Lo stato runtime (.storage, database, log) sta in dev/runtime/ (escluso da git).
# Nessun software di sistema viene installato: Docker o Python devono essere già presenti.
source "$(dirname "$0")/_common.sh"
MODE="${1:-docker}"
python3 "$ROOT/scripts/hi_tool.py" validate
link_runtime "$RUNTIME" dev
case "$MODE" in
  docker)
    cd "$ROOT"
    HA_VERSION="$HA_VERSION" docker compose -f docker-compose.dev.yml up -d
    echo "Home Assistant in avvio su http://localhost:8123 (primo avvio: 1-3 minuti)."
    ;;
  venv)
    if [[ ! -x "$VENV/bin/hass" ]]; then
      echo "Creo il virtualenv in $VENV (solo cartella del progetto) e installo homeassistant==$HA_VERSION"
      python3 -m venv "$VENV"
      "$VENV/bin/pip" install --upgrade pip wheel
      "$VENV/bin/pip" install "homeassistant==$HA_VERSION" websockets pyyaml pytest
    fi
    echo "Avvio Home Assistant su http://localhost:8123 (CTRL+C per fermare)"
    exec "$VENV/bin/hass" -c "$RUNTIME"
    ;;
  *) echo "Modalità sconosciuta: $MODE (docker|venv)"; exit 1 ;;
esac
