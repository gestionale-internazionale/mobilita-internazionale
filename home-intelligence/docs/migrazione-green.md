# Migrazione su Home Assistant Green

Green esce dalla fabbrica con **Home Assistant OS**. La configurazione di questo progetto viaggia tramite Git e i file YAML. Le integrazioni con credenziali (Daikin, Google, inverter) si configurano **sul Green** dall'interfaccia: non conviene migrare `.storage` da un Container.

> Se prima hai usato **HAOS in VM**, puoi anche ripristinare su Green un backup completo della VM (Impostazioni → Sistema → Backup → Carica backup durante l'onboarding). Così arrivano anche integrazioni, utenti e dashboard UI. Un backup di un Container o venv **non** è ripristinabile su HAOS.

## Procedura

1. **Avvio:** collega Green alla rete via cavo e all'alimentazione, poi apri `http://homeassistant.local:8123`.
2. **Onboarding:** crea l'utente amministratore, imposta posizione, fuso orario (Europe/Rome), unità metriche e valuta EUR. In alternativa ripristina il backup della VM e salta al punto 5.
3. **Aggiornamenti:** Impostazioni → Sistema → Aggiornamenti. Porta HA almeno alla versione verificata (2026.2.3 o successiva) e controlla le note di rilascio.
4. **Trasferimento della configurazione:**
   - installa l'add-on **Terminal & SSH** e aggiungi la tua chiave pubblica;
   - da PC: `scripts/deploy_green.sh root@homeassistant.local` (anteprima), poi con `--apply`;
   - Strumenti per sviluppatori → YAML → **Verifica configurazione** → **Riavvia**;
   - elimina o rinomina le aree predefinite dell'onboarding (Soggiorno, Cucina, …);
   - crea un token a lunga durata ed esegui `HI_URL=http://homeassistant.local:8123 HI_TOKEN=… python3 scripts/hi_tool.py sync --profilo prod --apply`. Il profilo **prod** esclude i dispositivi simulati.
   - Verifica che **non** esista `/config/packages/zz_simulazione` (lo script lo controlla).
5. **Dispositivi reali**, uno per categoria (vedi `analisi-tecnica.md`):
   - Matter: condivisione da Google Home → integrazione Matter (il Matter Server è disponibile su HAOS);
   - integrazioni dei produttori di interruttori e prese;
   - Daikin: integrazione locale `daikin` se l'adattatore è supportato, altrimenti valutare Onecta;
   - Companion App sui telefoni → associazione alle persone.
6. **Associazione delle entità:** per ogni dispositivo aggiorna `inventory/devices.yaml` (entità, area, etichette, `stato: reale`) → `hi_tool.py validate` → `sync --apply` → `hi_tool.py generate` (card dei termostati) → `deploy_green.sh --apply`. Commit su Git.
7. **Verifica:**
   - vista Diagnostica: nessuna entità non disponibile e ruoli associati corretti;
   - vista Clima: temperature reali e decisioni sensate per qualche giorno, con **attuazione spenta**;
   - prova di presenza: uscita e rientro reali;
   - notifica di prova.
8. **Attivazione graduale delle automazioni:**
   1. modalità e presenza (già attive) → verifica per una settimana;
   2. attuazione Daikin per zona;
   3. termostati del pavimento (dopo la verifica dell'impianto);
   4. controllo combinato.
9. **Integrazioni successive:** termostati (Priorità 4), FV e accumulo (Priorità 5): ruoli energetici, Energy Dashboard, prezzi.

## Backup, versionamento e ripristino

| Cosa | Dove | Come |
|---|---|---|
| Configurazione YAML, modello, dashboard, test | repository Git | commit dopo ogni modifica; tag per ogni rilascio (`v0.1.0`, …) |
| Integrazioni, utenti, registri, storico | backup HAOS | Impostazioni → Sistema → Backup → **backup automatici** giornalieri con copia esterna (Home Assistant Cloud, NAS/Samba o Google Drive tramite integrazione dedicata) |
| Segreti | `secrets.yaml` (non versionato) e `.storage` (nei backup, cifrati) | conservare la **chiave di cifratura dei backup** in un password manager |

**Ripristino:**
- su un nuovo Green, ripristina l'ultimo backup durante l'onboarding;
- per tornare indietro solo con la configurazione: `git checkout <tag>` + `deploy_green.sh --apply` + riavvio.
