# Supervisore termico

## Impianto (informazioni del 08/11/2026)

| Zona | Fonte idronica (termostato) | Pompa di calore | Note |
|---|---|---|---|
| Piano terra | **pavimento radiante** (un circuito) | Daikin Perfera FTXM71N2V1B | i 2 termoarredi dei bagni non sono comandati dal supervisore |
| Mansarda | **radiatori** (~3 termosifoni + termoarredo bagno) | Daikin Perfera FTXM-N | inerzia minore: tempi minimi di 20 minuti e inerzia di 0,25 h di default |

Nel codice la decisione `pav` indica la **fonte idronica** della zona, cioè pavimento o radiatori. Tempi minimi e compensazione dell'inerzia sono **per zona** (`input_number.hi_clima_<zona>_idro_min_on/off`, `hi_clima_<zona>_inerzia_ore`). Né il pavimento né i radiatori vengono mai usati in raffrescamento.

## Livelli

1. **Misure:** `sensor.hi_<zona>_temperatura` (media dei sensori `hi_temp_<zona>` disponibili), umidità, finestre, `sensor.hi_<zona>_variazione` (derivata su 30 minuti, °C/h) e `sensor.hi_temperatura_esterna`.
2. **Setpoint effettivo:** `sensor.hi_<zona>_setpoint`. Dipende da stagione, modalità della zona, modalità casa, profilo energetico e programma orario. L'attributo `origine` ne spiega il motivo.
3. **Supervisore:** `sensor.hi_<zona>_supervisore`, ricalcolato ogni minuto e a ogni variazione degli ingressi. Produce **decisioni**:
   - `pav`: on | off | invariato (pavimento, tramite termostato)
   - `pdc`: heat | cool | off | invariato (pompa di calore)
   - attributi: `motivo`, `errore`, `attesa` (tempo minimo), `pav_dal`/`pdc_dal`, disponibilità delle fonti
4. **Attuazione:** `script.hi_clima_attua`. **Disattivata per impostazione predefinita.**

## Regole (inverno)

| Condizione | Pavimento | Pompa di calore |
|---|---|---|
| errore ≥ isteresi (0,3 °C) e temperatura prevista sotto il setpoint | on | — |
| errore ≤ −isteresi, oppure temperatura prevista oltre setpoint + isteresi | off | — |
| tra le due soglie | mantiene lo stato | — |
| errore ≥ soglia integrazione (1,5 °C) | — | heat |
| pavimento acceso da ≥ 90 min, salita < 0,2 °C/h ed errore ≥ isteresi | — | heat ("salita lenta") |
| errore ≤ 0 (anche come previsione) | — | off |
| esterna < soglia minima pdc (−15 °C) | — | off (esclusa) |
| fonte preferita = pompa_di_calore | off | isteresi propria |

**Temperatura prevista** = attuale + velocità di salita × `hi_clima_<zona>_inerzia_ore` (1 h per il pavimento, 0,25 h per i radiatori). Serve a compensare l'inerzia del massetto: il pavimento si spegne prima, così il calore accumulato non porta la stanza troppo oltre il setpoint.

**Tempi minimi** (anti-ciclo): pavimento 60 minuti acceso e 60 spento, radiatori 20 e 20, pompa di calore 20 minuti accesa e 15 spenta. Non valgono nei casi immediati: spento, sovratemperatura, finestra aperta, cambio di stagione.

## Estate

Si usa solo la pompa di calore (`cool` con isteresi). Il **pavimento non viene mai acceso**: se risulta acceso viene spento. Sotto `hi_clima_t_min_sicurezza` il raffrescamento si spegne.

## Casi di sicurezza

| Stato | Comportamento |
|---|---|
| `sicurezza_sensore` | Temperatura o setpoint non disponibili: **nessun comando**. I dispositivi restano al loro setpoint e si regolano da soli. |
| `manuale` | Override o modalità manuale: nessun comando |
| `nessuna_fonte` | Nessun dispositivo disponibile: nessun comando |
| `sovratemperatura` | ≥ 28 °C in inverno: fonti spente subito |
| `finestra_aperta` | Pompa di calore spenta, pavimento invariato (ha troppa inerzia per reagire) |

## Override manuale

- Toggle `input_boolean.hi_clima_override_<zona>`: si spegne da solo allo scadere del timer (3 ore di default).
- **Rilevamento automatico** (`binary_sensor.hi_<zona>_scostamento`): con l'attuazione attiva, se un'unità comandata viene modificata dall'esterno (app Daikin, telecomando, termostato), dopo 15 minuti più 2 minuti di conferma l'override si attiva e arriva una notifica informativa.

## Attivazione graduale dell'attuazione

1. Collega e verifica i sensori di temperatura reali. Il supervisore decide ma non agisce: osserva le decisioni nella vista Diagnostica per qualche giorno.
2. Daikin: verifica sul modello reale `hvac_modes`, `min_temp` e `max_temp`, poi attiva `hi_clima_controllo_automatico` e `hi_clima_attuazione_pdc_<zona>`.
3. Termostati del pavimento: solo dopo aver verificato l'architettura dell'impianto (chi comanda le valvole, la caldaia o la PdC idronica, cosa succede con il termostato in setback), attiva `hi_clima_attuazione_pavimento_<zona>`.
4. Controllo combinato: entrambi i consensi attivi, con monitoraggio della temperatura e dei consumi.

## Taratura e limiti noti

- I parametri predefiniti sono **ipotesi prudenti**, da tarare sull'impianto reale.
- Negli scenari simulati (`simulations/scenari_termici`, report CSV in `tests/report/`) il pavimento, con il modello fisico *inventato*, mostra sovraelongazioni fino a ~1 °C. Lo scenario serve a verificare proprietà qualitative (niente oscillazioni, tempi minimi, fail-safe), **non** a prevedere la casa reale.
- Le funzioni predittive (apprendimento dell'inerzia, meteo, prezzo dell'energia, FV/batteria) sono predisposte negli ingressi ma **non implementate**: vedi `roadmap.md`.
