#!/usr/bin/env bash
# Valida la configurazione con il controllo ufficiale di Home Assistant
# (hass --script check_config) in due profili:
#   prod = configurazione destinata a Green (senza simulazione)
#   dev  = configurazione con il pacchetto di simulazione
# Richiede homeassistant installato (scripts/dev-up.sh venv lo installa in dev/venv).
source "$(dirname "$0")/_common.sh"
HASS="${HASS:-$VENV/bin/hass}"
[[ -x "$HASS" ]] || HASS="$(command -v hass || true)"
[[ -n "$HASS" ]] || { echo "hass non trovato: esegui prima scripts/dev-up.sh venv oppure imposta HASS"; exit 2; }
python3 "$ROOT/scripts/hi_tool.py" validate
rc=0
for profilo in prod dev; do
  tmp="$(mktemp -d)"
  link_runtime "$tmp" "$profilo"
  echo "=== check_config profilo $profilo ==="
  out="$("$HASS" --script check_config -c "$tmp" 2>&1)" || true
  echo "$out" | tail -n 30
  if echo "$out" | grep -qE "Failed config|Invalid config|ERROR"; then rc=1; fi
  rm -rf "$tmp"
done
link_runtime "$RUNTIME" dev >/dev/null 2>&1 || true
exit $rc
