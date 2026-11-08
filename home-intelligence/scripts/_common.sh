#!/usr/bin/env bash
# Variabili comuni agli script di sviluppo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CFG="$ROOT/homeassistant"
RUNTIME="${HI_RUNTIME:-$ROOT/dev/runtime}"
HA_VERSION="${HA_VERSION:-2026.2.3}"   # versione su cui il progetto è stato verificato
VENV="${HI_VENV:-$ROOT/dev/venv}"
# Elementi della configurazione versionata collegati nella cartella runtime.
LINKED=(configuration.yaml automations.yaml scripts.yaml scenes.yaml packages dashboards themes www custom_templates)

link_runtime() {
  # $1 = cartella runtime, $2 = "dev" (con simulazione) | "prod" (senza)
  local dir="$1" profilo="$2"
  mkdir -p "$dir"
  for item in "${LINKED[@]}"; do
    rm -rf "${dir:?}/$item"
    ln -s "$CFG/$item" "$dir/$item"
  done
  if [[ "$profilo" == "dev" ]]; then
    mkdir -p "$CFG/packages/zz_simulazione"
    cp "$ROOT/simulations/sim_package.yaml" "$CFG/packages/zz_simulazione/sim_package.yaml"
  else
    rm -rf "$CFG/packages/zz_simulazione"
  fi
  [[ -f "$dir/secrets.yaml" ]] || cp "$CFG/secrets.yaml.example" "$dir/secrets.yaml"
}
