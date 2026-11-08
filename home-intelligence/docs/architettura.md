# Architettura

```
inventory/house.yaml ──► hi_tool.py generate ──► packages/generated/   (aree, zone termiche)
inventory/devices.yaml                          dashboards/generated/ (Casa, piani, Clima, Persone)
        │                                       www/floorplans/*.svg  (planimetrie provvisorie)
        └──────────► hi_tool.py sync ─────────► HA: floors, areas, labels, area+label sulle entità

            ┌───────────────────── Home Assistant ─────────────────────┐
 dispositivi│  entità reali / [SIM]  ──(etichette hi_*)──►  proxy hi_*   │
            │                                              │            │
            │  hi_core      modalità casa, notifiche, avvio sicuro      │
            │  hi_presenza  occupazione → Casa/Assente/Notte            │
            │  hi_clima + generated/hi_zone   setpoint → supervisore    │
            │                 → attuazione (consensi, OFF di default)   │
            │  hi_energia   proxy W/kWh/%, derivati, costi, consigli    │
            │  hi_scenari   script per etichetta (mai hi_critico)       │
            │  hi_diagnostica  offline, errori, stato moduli            │
            │  dashboards/  7 sezioni native                            │
            └───────────────────────────────────────────────────────────┘
```

## Struttura del repository

```
home-intelligence/
├── README.md
├── docker-compose.dev.yml        HA Container per lo sviluppo
├── docs/                         documentazione (questo file e gli altri)
├── inventory/
│   ├── house.yaml                piani, aree, zone termiche, persone, etichette
│   └── devices.yaml              registro dispositivi (reale/non_disponibile/simulazione)
├── homeassistant/                = cartella /config di Home Assistant
│   ├── configuration.yaml
│   ├── packages/                 moduli hi_*.yaml + generated/ (+ zz_simulazione/ solo dev)
│   ├── custom_templates/         macro Jinja: hi_common (ruoli), hi_clima (supervisore)
│   ├── dashboards/               dashboard YAML: views/ (a mano) + generated/
│   ├── themes/                   tema "Home Intelligence"
│   └── www/floorplans/           planimetrie
├── simulations/
│   ├── sim_package.yaml          dispositivi virtuali + modello fisico (solo sviluppo)
│   └── scenari_termici/          scenari temporali per i test del supervisore
├── scripts/                      hi_tool.py, dev-up/down, check_config, deploy_green
└── tests/                        test statici, logica termica, integrazione con HA reale
```

## Strato di astrazione: etichette di ruolo

Nelle logiche non compare mai un entity_id di dispositivo. Le macro di `hi_common.jinja` risolvono un **ruolo**:

| Macro | Restituisce |
|---|---|
| `hi_ruolo('hi_pdc_inferiore')` | entità con quell'etichetta, filtrate per ambiente (simulato o reale) |
| `hi_media('hi_temp_mansarda')` | media dei sensori validi (i non disponibili vengono esclusi) |
| `hi_potenza_w` / `hi_energia_kwh` / `hi_percentuale` | valore normalizzato del primo sensore valido (W, kWh, %) |
| `hi_comandabili('hi_luce')` | entità del ruolo, disponibili, **esclusi** i `hi_critico` |

Per associare un dispositivo a un ambiente e a una funzione:
1. in `devices.yaml` indica `area`, `etichette` ed `entita`;
2. esegui `hi_tool.py sync --apply`.

In alternativa si assegnano area ed etichette dall'interfaccia (Impostazioni → Entità). Il risultato è lo stesso, ma `devices.yaml` resta la documentazione di riferimento.

## Separazione tra simulazione e realtà

- Le entità simulate esistono **solo** se c'è `packages/zz_simulazione/` (cartella copiata dagli script di sviluppo ed esclusa da git).
- `input_boolean.sim_ambiente_simulato` = on → i ruoli usano solo `sim_*`; off → solo entità reali.
- In simulazione, lo script di attuazione accetta come bersaglio solo `climate.sim_*`: un Daikin reale raggiungibile dal PC di sviluppo non può essere comandato da logiche alimentate da dati simulati.
- Su ogni vista compare un avviso quando la simulazione è attiva.
- Un test statico verifica che i pacchetti di produzione non facciano riferimento a entità `sim_`.

## Regole di sicurezza (fail-safe)

1. **Un solo scrittore** della modalità casa (`script.hi_imposta_modo`), che ignora le richieste ridondanti.
2. Le automazioni che reagiscono alle modalità non cambiano la modalità: niente cicli.
3. I trigger ignorano le transizioni `unknown`/`unavailable`, quindi un riavvio non genera eventi spuri.
4. **Avvio sicuro:** nessun comando a dispositivi finché `binary_sensor.hi_sistema_pronto` è off (5 minuti dopo l'avvio, configurabile).
5. Le entità con etichetta `hi_critico` sono escluse da scenari e spegnimenti di massa.
6. Il clima non comanda nulla senza consenso generale **e** consenso per fonte (tutti OFF di default). Se il sensore non è disponibile, nessun comando. In override manuale, nessun comando.
7. Il pavimento radiante non riceve mai `cool`: la regola è nella logica e nell'attuazione ed è verificata da test.
8. Valvole e caldaie non vengono comandate: il pavimento si gestisce solo tramite il setpoint del termostato.
9. Gli scenari usano `mode: single`, gli avvisi hanno un tempo minimo di ripetizione e gli errori delle automazioni sono deduplicati.
10. Nessuna esposizione su Internet è richiesta. Per l'accesso remoto si consiglia Home Assistant Cloud (Nabu Casa) o una VPN (WireGuard/Tailscale), mai il port forwarding.

## Persistenza e aggiornamenti

- Tutta la logica è YAML versionato. Lo stato (`.storage`, database) resta fuori dal repository.
- Gli helper senza `initial` conservano i valori tra i riavvii. I valori predefiniti si impostano **una sola volta** (`script.hi_inizializza_predefiniti`, rieseguibile).
- Si usano solo funzioni documentate di HA (labels, `default_entity_id`, template moderni, card native). Ad ogni aggiornamento maggiore di HA eseguire `scripts/check_config.sh` e la suite di test.
