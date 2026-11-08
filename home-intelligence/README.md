# Home Intelligence

Sistema domotico modulare basato su **Home Assistant**, preparato per **Home Assistant Green**: climatizzazione con pavimento radiante e pompe di calore Daikin, presenza, scenari, energia (FV e accumulo previsti) e diagnostica.

> Stato: **v0.1.0**, prima versione. Sviluppata e testata su Home Assistant 2026.2.3 con dispositivi **simulati**. Nessun dispositivo reale è stato ancora collegato. Il dettaglio è in [docs/stato-funzioni.md](docs/stato-funzioni.md).

## Cosa contiene

- **Modello digitale della casa** (`inventory/house.yaml`): piani, ambienti (provvisori), zone termiche, etichette funzionali. Un comando genera pacchetti, viste e planimetrie; un altro sincronizza piani, aree ed etichette in HA.
- **Registro dispositivi** (`inventory/devices.yaml`) con stato *reale / non disponibile / simulazione*.
- **Moduli HA nativi** (packages): core e modalità, presenza, clima e supervisore termico, energia, scenari, diagnostica.
- **Dashboard** nativa a 7 sezioni (più le viste per piano), pensata per lo smartphone.
- **Simulazione** separata (solo sviluppo) con modello fisico e iniezione di guasti.
- **Test**: statici, logica termica eseguita nel motore template di HA, integrazione contro un'istanza HA reale, riavvio.

## Avvio rapido (sviluppo)

```bash
cd home-intelligence
scripts/dev-up.sh docker        # oppure: scripts/dev-up.sh venv
# http://localhost:8123 → onboarding → token → sync del modello:
HI_URL=http://localhost:8123 HI_TOKEN=<token> python3 scripts/hi_tool.py sync --profilo dev --apply
```

Dettagli in [docs/ambiente-sviluppo.md](docs/ambiente-sviluppo.md).

## Comandi principali

| Comando | Scopo |
|---|---|
| `python3 scripts/hi_tool.py validate` | verifica il modello e il registro dispositivi |
| `python3 scripts/hi_tool.py generate` | rigenera i file derivati dal modello |
| `python3 scripts/hi_tool.py sync [--profilo dev\|prod] [--apply]` | allinea HA (piani, aree, etichette, associazioni) |
| `scripts/check_config.sh` | controllo ufficiale della configurazione HA (prod + dev) |
| `python3 -m pytest tests` | suite di test |
| `scripts/deploy_green.sh root@homeassistant.local [--apply]` | copia la configurazione di produzione su Green/VM |

## Documentazione

| Documento | Contenuto |
|---|---|
| [analisi-tecnica.md](docs/analisi-tecnica.md) | scelte architetturali, ambiente di sviluppo, Google Home, Daikin, fattibilità |
| [architettura.md](docs/architettura.md) | struttura, strato di astrazione, separazione simulazione/realtà, fail-safe |
| [ambiente-sviluppo.md](docs/ambiente-sviluppo.md) | avvio, simulazione, test, VM HAOS |
| [manuale-dashboard.md](docs/manuale-dashboard.md) | uso e personalizzazione delle dashboard |
| [clima-supervisore.md](docs/clima-supervisore.md) | regole del supervisore, sicurezza, attivazione graduale |
| [presenza-e-modalita.md](docs/presenza-e-modalita.md) | Companion App, occupazione, modalità |
| [energia.md](docs/energia.md) | ruoli energetici, Energy Dashboard, ottimizzazione |
| [registro-dispositivi.md](docs/registro-dispositivi.md) | dispositivi da configurare (generato) |
| [stato-funzioni.md](docs/stato-funzioni.md) | funzioni reali / simulate / predisposte, esito dei test |
| [migrazione-green.md](docs/migrazione-green.md) | procedura passo-passo, backup e ripristino |
| [roadmap.md](docs/roadmap.md) | sviluppi successivi |
| [dati-richiesti.md](docs/dati-richiesti.md) | informazioni da fornire |

## Sicurezza

Il repository non contiene segreti, token né coordinate. Un test lo verifica. L'attuazione del clima è **disattivata** di default. Le entità `hi_critico` non sono mai comandate in massa. Non serve esporre HA su Internet.
