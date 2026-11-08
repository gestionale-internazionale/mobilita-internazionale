#!/usr/bin/env bash
# Copia la configurazione di PRODUZIONE su Home Assistant Green via SSH/rsync.
# Prerequisiti su Green: add-on "Terminal & SSH" (o "Advanced SSH & Web Terminal")
# con chiave pubblica configurata. Default: simulazione (--dry-run).
#   scripts/deploy_green.sh root@homeassistant.local          # dry-run
#   scripts/deploy_green.sh root@homeassistant.local --apply  # copia davvero
# NON copia mai: .storage, database, secrets.yaml, pacchetto di simulazione.
source "$(dirname "$0")/_common.sh"
DEST="${1:?Uso: deploy_green.sh utente@host [--apply]}"
APPLY="${2:-}"
python3 "$ROOT/scripts/hi_tool.py" validate
DRY="--dry-run"; [[ "$APPLY" == "--apply" ]] && DRY=""
rsync -av $DRY --delete-after \
  --exclude 'packages/zz_simulazione/' --exclude '.storage/' --exclude 'secrets.yaml' \
  --exclude '*.db*' --exclude '*.log*' --exclude 'automations.yaml' --exclude 'scripts.yaml' --exclude 'scenes.yaml' \
  "$CFG/packages" "$CFG/dashboards" "$CFG/themes" "$CFG/www" "$CFG/custom_templates" \
  "$DEST:/config/"
rsync -av $DRY "$CFG/configuration.yaml" "$DEST:/config/configuration.yaml"
ssh "$DEST" 'test ! -e /config/packages/zz_simulazione' || { echo "ERRORE: pacchetto simulazione presente su Green!"; exit 1; }
[[ -z "$DRY" ]] && echo "Copiato. Verifica: Strumenti per sviluppatori → YAML → Verifica configurazione, poi Riavvia." || echo "Dry-run completato (usa --apply per copiare)."
