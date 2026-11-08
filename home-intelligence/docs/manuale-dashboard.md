# Manuale delle dashboard

Dashboard **Home Intelligence** (barra laterale). È pensata per lo smartphone e si adatta a tablet e desktop: le viste *sections* riorganizzano le colonne da sole. Tema consigliato: *Home Intelligence* (chiaro/scuro automatico).

| Vista | Contenuto | Azioni rapide |
|---|---|---|
| **Home** | modalità, profilo, occupazione, avvisi (simulazione, dispositivi offline), temperature di zona e decisioni del supervisore, persone, sintesi energia | cambio modalità con un tocco; Buongiorno / Buonanotte / Esco |
| **Casa** | piani con luci accese e temperature per ambiente; elenco luci accese; altre aree | "Spegni luci e carichi non essenziali" (con conferma); apertura dei piani |
| **Piano inferiore / Mansarda** | planimetria (provvisoria) con lampadina, temperatura e occupazione per ambiente; una card *area* per ambiente con i controlli dei dispositivi | **tocco sulla lampadina** = accende/spegne le luci dell'ambiente; pressione lunga = dettagli |
| **Clima** | stagione, profilo, consenso generale; per zona: temperatura, setpoint, decisione e motivo, modalità, fonte preferita, override, termostati, programma, consensi, storico 24 h; parametri del supervisore | modifica dei setpoint e degli orari comfort, override |
| **Energia** | flussi istantanei, SoC, autosufficienza, contatori giorno/mese, costi, storico, parametri | — |
| **Persone** | occupazione, persone e ultimo aggiornamento, avvisi di posizione non aggiornata, impostazioni presenza, mappa (se configurata) | ospiti, override presenza |
| **Automazioni** | scenari, interruttore generale, orari notte, notifiche | tutti gli scenari; notifica di prova |
| **Diagnostica** | stato moduli (🟢 attivo · 🟣 simulato · ⚪ predisposto), entità non disponibili, ruoli associati, dettaglio del supervisore, registro | azzera contatore errori (pressione lunga) |

## Elementi non disponibili

- Le card dei sensori non ancora collegati mostrano **"Non disponibile"**: nessun valore inventato.
- Le sezioni FV/batteria e i termostati mostrano un avviso *"non ancora disponibile"*.
- In simulazione compare l'avviso viola **Ambiente di simulazione** e le entità hanno il prefisso **[SIM]**.

## Personalizzare

- **Ambienti e piani:** modifica `inventory/house.yaml` → `hi_tool.py generate` → `sync --apply` → ricarica la dashboard.
- **Planimetria reale:** copia l'immagine in `homeassistant/www/floorplans/`, imposta `immagine:` sul piano e le coordinate `planimetria` (in %) di ogni area, poi `generate`.
- **Nuovi dispositivi:** compaiono da soli nelle card *area* e negli aggregati di ambiente non appena sono assegnati all'area giusta. Per i Daikin e i termostati reali, `generate` aggiunge le card dei termostati nella vista Clima.
- Le viste in `dashboards/views/` si modificano a mano. Quelle in `dashboards/generated/` vengono rigenerate.
