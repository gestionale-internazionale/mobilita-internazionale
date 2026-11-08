# Fase 1 – Analisi tecnica

Data analisi: novembre 2026. La configurazione è verificata su **Home Assistant Core 2026.2.3**.
Le integrazioni di terze parti evolvono in fretta: prima di installarle va ricontrollata la loro documentazione.

## 1. Scelte architetturali

| Tema | Alternative valutate | Scelta | Motivo |
|---|---|---|---|
| Piattaforma | App web separata, Node-RED, AppDaemon/pyscript, HA nativo | **HA nativo** (YAML packages, helper, template, script, automazioni) | Funziona così com'è su Green e sopravvive agli aggiornamenti. Non servono add-on né runtime aggiuntivi. |
| Organizzazione | Un solo `configuration.yaml`, split per dominio, **packages** | **Packages per modulo** (`hi_core`, `hi_presenza`, `hi_clima`, `hi_energia`, `hi_scenari`, `hi_diagnostica`) | Ogni modulo è autonomo e versionabile, si può abilitare o rimuovere da solo. |
| Associazione dispositivi ↔ funzioni | entity_id nelle automazioni, gruppi, `input_text` di mappatura, **labels** | **Etichette (labels) native** + aree/piani nativi | Le logiche cercano "chi ha l'etichetta X": per aggiungere un dispositivo basta un'etichetta. Si gestisce da `devices.yaml` + `hi_tool.py sync` oppure dall'interfaccia. |
| Logica del supervisore termico | PID, Python (pyscript/AppDaemon), integrazione custom, **macro Jinja** | **Macro Jinja pure** (`custom_templates/hi_clima.jinja`) | Sono native e girano su Green senza add-on. Si testano eseguendole nel motore di HA tramite `/api/template`. Sono leggibili e restano separate dall'attuazione. |
| Dashboard | HACS (button-card, mushroom, auto-entities), **card native** | **Card native** (sections view, tile, area, picture-elements, heading) | Niente dipendenze da HACS, e nessuna card che si rompe a ogni aggiornamento. Le card *area* mostrano da sole i dispositivi aggiunti a un ambiente. |
| Planimetria | Immagine raster, SVG generato | **SVG schematico generato** da `house.yaml` (marcato "PROVVISORIA") | Si sostituisce con una planimetria reale indicando `immagine:` nel modello. |
| Simulazione | Mescolare entità finte e vere, **pacchetto separato** | **Pacchetto `zz_simulazione` solo in sviluppo** (escluso da git, mai su Green) | Le entità simulate hanno prefisso `sim_`, nome "[SIM]" ed etichetta `hi_simulazione`. Un interruttore stabilisce se le logiche usano entità simulate o reali, mai entrambe. |

## 2. Ambiente di sviluppo prima di Green

| Opzione | Fedeltà verso Green | Pro | Contro |
|---|---|---|---|
| **Home Assistant OS in VM** (VirtualBox/UTM/Hyper-V/Proxmox) | ★★★ identico (Supervisor, add-on, backup) | Il backup `.tar` si ripristina su Green. Ha add-on, Matter server e Bluetooth (con passthrough). | VM da installare. La rete deve essere in *bridge* per raggiungere i dispositivi LAN. |
| **Home Assistant Container** (Docker) | ★★ stesso core, niente Supervisor | Avvio in un minuto, comodo per iterare e testare. È lo stack usato dai test. | Niente add-on e niente backup ripristinabili su HAOS. Su macOS/Windows la rete host è limitata (mDNS/discovery). |
| Core in virtualenv | ★ stesso core | È quello che usano i test automatici di questo repository | Stessi limiti del Container, più le dipendenze di sistema |

**Raccomandazione:**

1. Per lo sviluppo quotidiano e i test: **Container** (`scripts/dev-up.sh docker`) oppure **venv** (`scripts/dev-up.sh venv`).
2. Prima dell'arrivo di Green, se vuoi provare dispositivi reali, add-on (Matter Server) e backup: **HAOS in VM** con rete in bridge. La configurazione YAML si copia con `scripts/deploy_green.sh`, che funziona identico verso la VM e verso Green.

Limiti del Container rispetto a HAOS:
- niente Supervisor: niente add-on (Matter Server, Terminal & SSH, Samba) né aggiornamenti gestiti;
- i backup del Container **non si ripristinano** su HAOS: si migra tramite repository Git (configurazione YAML) più la riconfigurazione delle integrazioni da interfaccia;
- la scoperta dei dispositivi funziona solo con `network_mode: host`, cioè solo su Linux.

**Nel sandbox in cui è stato sviluppato il progetto** il Docker daemon era avviabile, ma il download dell'immagine da `ghcr.io` è stato bloccato dal proxy di rete. Home Assistant è stato quindi eseguito come **Core 2026.2.3 in virtualenv**: stesso codice, stesse integrazioni native, nessuna differenza per la configurazione di questo progetto.

## 3. Google Home: percorsi di integrazione

Google Home **non esporta** i propri dispositivi verso Home Assistant: non esiste un'API ufficiale per "importarli" in blocco. Va scelto un percorso per ciascuna categoria.

| Categoria di dispositivo | Percorso consigliato | Note |
|---|---|---|
| Dispositivi **Matter** (o aggiornabili a Matter) | **Matter multi-admin**: dall'app Google Home → dispositivo → *App e servizi collegati Matter* → *Collega app* → codice di condivisione, da inserire in HA (integrazione Matter) | Il dispositivo resta controllabile **sia** da Google **sia** da HA, in locale. Su HAOS serve l'add-on Matter Server (incluso su Green). Il codice di condivisione dura pochi minuti. |
| Dispositivi con **integrazione HA del produttore** (es. Shelly, TP-Link Tapo/Kasa, Tuya, Philips Hue, Sonoff/eWeLink, Meross…) | **Integrazione diretta del produttore**, preferibilmente locale | È il percorso più affidabile e completo. Va verificato modello per modello. |
| Dispositivi dietro un **hub/bridge** (Zigbee, Hue Bridge, gateway proprietari) | **Integrazione del bridge** (es. Hue) oppure migrazione su un coordinatore Zigbee di HA (ZHA) | Il bridge resta utilizzabile anche da Google |
| Dispositivi **solo-cloud** senza integrazione HA | **Google Assistant SDK** (integrazione ufficiale) solo come ultima risorsa: invia a Google comandi testuali ("spegni la luce cucina") | **Solo comando, nessuno stato letto.** Le routine non funzionano e un solo account Google è supportato. Non adatto ad automazioni affidabili. |
| **Controllo vocale** da Google verso HA | Integrazione **Google Assistant** (manuale, via Google Cloud project; richiede HA raggiungibile in HTTPS) oppure **Home Assistant Cloud (Nabu Casa)** | Nabu Casa è la via più semplice e sicura: non apre porte del router. In alternativa resta il vocale di Google sui dispositivi condivisi via Matter. |

Non si usano API non documentate né l'estrazione di token o credenziali dall'app Google Home.

## 4. Daikin

| Integrazione | Tipo | Modelli | Note |
|---|---|---|---|
| **Daikin AC** (`daikin`, ufficiale core) | **Locale** (polling LAN) | Adattatori BRP069A/B, BRP072A/B/C, SKYFi, AirBase | Da preferire: locale, nessun limite di chiamate. Espone `climate` con modalità, setpoint, temperatura interna (ed esterna su molti modelli), ventola, swing e sensori di energia su alcuni modelli. |
| **Daikin Onecta** (HACS, community, es. `jwillemsen/daikin_onecta`) | **Cloud** (API ufficiale Daikin Onecta, OAuth tramite developer portal Daikin) | Unità recenti con adattatori Wi-Fi solo-cloud (BRP069C/BRP084…) | Nel 2026 non risulta un'integrazione core ufficiale. L'API cloud Daikin ha un **limite di chiamate giornaliere** e aggiornamenti lenti (minuti). Nella community sono segnalati problemi di autenticazione OAuth: verificare la versione corrente prima di usarla. |
| Altro (Madoka BLE, Altherma via Modbus/ESPHome) | Locale | Modelli specifici | Da valutare solo dopo aver identificato i modelli |

Conseguenze sul progetto:
- **nessuna funzione viene presunta**: il modulo clima legge `hvac_modes`, `min_temp` e `max_temp` dell'entità reale e comanda solo ciò che è supportato;
- con un'integrazione cloud il rilevamento degli interventi manuali aspetta 15 minuti, per assorbire la latenza del polling, e i comandi si inviano solo quando la decisione cambia, così da rispettare il limite di chiamate;
- consumi, temperatura esterna e modalità speciali compaiono solo se il modello li espone.

## 5. Cosa è realizzabile subito e cosa richiede hardware o informazioni

| Funzione | Subito | Serve |
|---|---|---|
| Ambiente HA avviabile, dashboard, modello casa, helper, modalità, scenari, notifiche, diagnostica | ✅ | — |
| Supervisore termico (decisioni) | ✅ in simulazione | Sensori di temperatura reali per decidere sulla casa vera |
| Presenza | ✅ (struttura + simulazione) | Companion App sugli smartphone |
| Integrazione Google Home | Procedura documentata | Elenco dispositivi e modelli |
| Daikin | Predisposto (etichette, attuazione protetta) | Modelli e adattatori → scelta dell'integrazione |
| Termostati pavimento | Predisposto | Modello e protocollo + architettura dell'impianto |
| Fotovoltaico/accumulo | Predisposto + simulazione | Marca inverter/batteria e integrazione |
| Controllo combinato delle due fonti | Logica testata | Termostati installati + verifica del comportamento dell'impianto |
| Ottimizzazione predittiva | Solo predisposizione | Dati storici reali |
