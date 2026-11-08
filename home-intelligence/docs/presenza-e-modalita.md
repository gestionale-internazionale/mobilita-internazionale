# Presenza e modalità della casa

## Configurazione con gli smartphone

1. Installa la **Companion App** di Home Assistant su ogni telefono e accedi all'istanza (in locale, oppure da remoto via Nabu Casa o VPN).
2. Concedi il permesso di posizione "sempre", **solo se la persona è d'accordo**. Senza questo permesso la presenza automatica non funziona per quella persona.
3. In Impostazioni → Persone, associa a ogni persona il proprio `device_tracker`.
4. Facoltativo: aggiungi i `person.*` in `inventory/house.yaml → persone` ed esegui `hi_tool.py generate` per avere le card dedicate e la mappa.
5. La zona **Casa** si imposta dalla posizione dell'onboarding (salvata in `.storage`, non nel repository). Altre zone, come `vicino_casa` per la preparazione all'arrivo, si creano dall'interfaccia.

## Stato di occupazione (`sensor.hi_occupazione`)

| Stato | Quando |
|---|---|
| `occupata` | almeno una persona in casa (`zone.home` > 0), **oppure** ospiti attivi, movimento recente (sensori `hi_presenza_supplementare`, 15 minuti) o override "forza_presente" |
| `vuota` | tutte le persone tracciate fuori e nessuna fonte complementare attiva |
| `incerta` | nessuno in casa ma un tracker non si aggiorna da più di N ore, oppure nessuna persona ha un telefono associato. **Non attiva "Assente".** |

Le persone senza un tracker associato, come l'utente amministratore creato dall'onboarding, vengono ignorate.

## Modalità (`input_select.hi_modo_casa`)

| Modalità | Attivazione | Effetti |
|---|---|---|
| Casa | rientro, fine fascia notturna, scenari Buongiorno/Rientro | setpoint da programma e profilo |
| Assente | `vuota` per `hi_assenza_ritardo_min` (10 minuti) senza movimento, oppure scenario Tutti fuori | spegne luci e carichi non essenziali (mai i `hi_critico`); setpoint di assenza |
| Notte | inizio fascia notturna (23:30), scenario Buonanotte | setpoint eco; Buonanotte spegne le luci tranne quelle notturne |
| Vacanza | solo manuale (scenario Vacanza) | setpoint di vacanza; termina automaticamente al primo rientro rilevato, con notifica |

## Funzioni complementari predisposte (non presunte)

- Sensori di movimento/occupazione: basta l'etichetta `hi_presenza_supplementare`.
- Presenza tramite Wi-Fi o router: le integrazioni (es. router, Unifi, Fritz!Box) creano `device_tracker` da associare alle persone, insieme al GPS.
- Preparazione all'arrivo: zona `vicino_casa` + `input_boolean.hi_prepara_arrivo` (disattivato di default).

## Privacy

La posizione è usata solo da questa istanza, per le funzioni domotiche. La dashboard Persone mostra solo stato (in casa / fuori) e ultimo aggiornamento. La mappa compare solo per le persone elencate esplicitamente nel modello. Ogni persona può disattivare la localizzazione dall'app.
