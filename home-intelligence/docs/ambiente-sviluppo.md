# Ambiente di sviluppo: avvio e test

Nessuno script installa software di sistema. Serve **una** di queste opzioni, già installata:
- Docker (consigliato su Linux), oppure
- Python 3.13 (per la modalità `venv`: Home Assistant viene installato in `dev/venv`, dentro la cartella del progetto).

Per una fedeltà completa con Green (add-on, backup) vedi la sezione VM più sotto.

## Avvio rapido

```bash
cd home-intelligence
python3 -m pip install pyyaml websockets pytest   # strumenti del progetto (oppure usa dev/venv)
python3 scripts/hi_tool.py validate               # controlla il modello della casa

scripts/dev-up.sh docker      # oppure: scripts/dev-up.sh venv
# apri http://localhost:8123 e completa l'onboarding (utente, posizione, lingua)
```

Dopo l'onboarding:

1. **Elimina o rinomina le aree predefinite** create dall'onboarding (Soggiorno, Cucina, Camera da letto), così non entrano in conflitto con quelle del modello.
2. Crea un **token di accesso a lunga durata**: Profilo → Sicurezza → Token di accesso a lunga durata.
3. Sincronizza il modello (piani, aree, etichette, associazioni):
   ```bash
   export HI_URL=http://localhost:8123 HI_TOKEN=<token>      # il token NON va salvato in file
   python3 scripts/hi_tool.py sync --profilo dev             # anteprima
   python3 scripts/hi_tool.py sync --profilo dev --apply     # applica
   ```
4. Apri la dashboard **Home Intelligence** dalla barra laterale. Per il tema: Profilo → Tema → *Home Intelligence*.

Lo stato runtime (`.storage`, database, log) sta in `dev/runtime/`, escluso da git. I file della configurazione sono collegati da `homeassistant/`: le modifiche si applicano con *Strumenti per sviluppatori → YAML → Ricarica* (template, automazioni, script) oppure con un riavvio.

## Usare la simulazione

Il pacchetto `simulations/sim_package.yaml` viene copiato in `homeassistant/packages/zz_simulazione/` (cartella esclusa da git). Crea:

- sensori di temperatura e umidità, 2 Daikin e 2 termostati simulati (`generic_thermostat`);
- luci, prese (di cui una "critica"), un sensore di movimento e un sensore finestra;
- 2 persone simulate (`script.sim_persona_entra` / `sim_persona_esce`);
- FV, batteria e rete con bilancio energetico, aggiornati ogni minuto;
- un modello fisico con inerzia del pavimento (`input_number.sim_velocita` lo accelera fino a 60×);
- l'iniezione di guasti (`input_boolean.sim_guasto_sensore_*`).

Per provare un **dispositivo reale** raggiungibile dal PC: integralo, aggiungilo a `devices.yaml` con `stato: reale`, esegui `sync` e spegni `input_boolean.sim_ambiente_simulato`. Da quel momento le logiche usano solo entità reali. Lascia l'attuazione del clima disattivata finché il comportamento non è verificato.

## Validazione e test

```bash
scripts/check_config.sh                 # controllo ufficiale HA, profili prod e dev
python3 -m pytest tests/test_static.py  # senza HA in esecuzione
HASS=dev/venv/bin/hass python3 -m pytest tests -v   # avvia un'istanza HA temporanea e testa tutto
# oppure contro un'istanza già avviata (profilo dev):
HI_URL=http://localhost:8123 HI_TOKEN=<token> python3 -m pytest tests -v
```

I report (CSV degli scenari termici, log di HA) finiscono in `tests/report/`.

## Home Assistant OS in macchina virtuale (opzionale, fedeltà massima)

1. Scarica l'immagine HAOS per il tuo hypervisor dalla documentazione ufficiale (*Installation → Windows/macOS/Linux*): VirtualBox, UTM (Apple Silicon), Hyper-V o KVM.
2. Configura la VM con 2 vCPU, 4 GB di RAM, firmware **EFI** e rete in **bridge**, così ha un IP nella LAN e vede i dispositivi.
3. Completa l'onboarding, poi installa l'add-on **Terminal & SSH** con la tua chiave pubblica.
4. Copia la configurazione: `scripts/deploy_green.sh root@<ip-vm> --apply`. Lo stesso script si userà per Green.
5. Per la simulazione nella VM, copia a mano `simulations/sim_package.yaml` in `/config/packages/zz_simulazione/`. Fallo **solo** nella VM, mai su Green.

## Cosa NON è stato possibile testare nel sandbox di sviluppo

- Dispositivi reali (Daikin, interruttori, Google Home, smartphone): nessun hardware disponibile.
- Home Assistant OS, add-on, backup e ripristino: il sandbox esegue solo HA Core.
- Avvio via Docker: il daemon funziona, ma il download dell'immagine è stato bloccato dalla rete del sandbox. Il file compose è standard ma **non è stato eseguito** qui.
- Il rendering grafico delle dashboard è stato verificato con screenshot in Chromium (vedi `docs/stato-funzioni.md`). La resa su smartphone reale va confermata.
