# Registro dispositivi
> File generato da `scripts/hi_tool.py docs` a partire da `inventory/devices.yaml`.
> Per aggiungere o aggiornare un dispositivo modifica il file YAML e rigenera.

| Dispositivo | Stato | Tipo | Marca / modello | Integrazione | Area | Etichette | Entità |
|---|---|---|---|---|---|---|---|
| Pompa di calore salotto (piano inferiore) | ⚪ non disponibile | pompa_di_calore | Daikin Perfera FTXM71N2V1B (unità interna, 2020) + adattatore Wi-Fi BRP069B4x | daikin | Zona giorno | `hi_pdc_inferiore`, `hi_monitorato` | — |
| Seconda pompa di calore (posizione da confermare) | ⚪ non disponibile | pompa_di_calore | Daikin | daikin | Mansarda principale | `hi_pdc_mansarda`, `hi_monitorato` | — |
| Termostato pavimento piano inferiore | ⚪ non disponibile | termostato | _da fornire_ | da_verificare | Zona giorno | `hi_termostato_inferiore`, `hi_monitorato` | — |
| Termostato pavimento mansarda | ⚪ non disponibile | termostato | _da fornire_ | da_verificare | Mansarda principale | `hi_termostato_mansarda`, `hi_monitorato` | — |
| Inverter fotovoltaico (~6 kWp) | ⚪ non disponibile | inverter | _da fornire_ | da_verificare | Locale tecnico | `hi_en_pv_potenza`, `hi_en_pv_energia`, `hi_monitorato` | — |
| Sistema di accumulo (10–15 kWh) | ⚪ non disponibile | batteria | _da fornire_ | da_verificare | Locale tecnico | `hi_en_batt_soc`, `hi_en_batt_carica_potenza`, `hi_en_batt_scarica_potenza`, `hi_en_batt_energia_carica`, `hi_en_batt_energia_scarica` | — |
| Misura di scambio con la rete | ⚪ non disponibile | contatore | _da fornire_ | da_verificare | Locale tecnico | `hi_en_rete_prelievo_potenza`, `hi_en_rete_immissione_potenza`, `hi_en_rete_prelievo_energia`, `hi_en_rete_immissione_energia` | — |
| Interruttore Lavanderia | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | — | `hi_luce`, `hi_monitorato` | — |
| Interruttore Studio | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | — | `hi_luce`, `hi_monitorato` | — |
| Interruttore Bagno mansarda | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | Mansarda principale | `hi_luce`, `hi_monitorato` | — |
| Interruttore Scala | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | — | `hi_luce`, `hi_monitorato` | — |
| Interruttore Box Silvia | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | — | `hi_luce`, `hi_monitorato` | — |
| Altri interruttori Sonoff (elenco da completare) | ⚪ non disponibile | interruttore | SONOFF | sonofflan | — | `hi_luce` | — |
| Coordinatore Zigbee USB (SONOFF) | ⚪ non disponibile | coordinatore | SONOFF | zha | Locale tecnico |  | — |
| Smartphone con Companion App | ⚪ non disponibile | tracker | _da fornire_ | mobile_app | — |  | — |
| [SIM] Sensori temperatura/umidità | 🟣 simulazione | sensore | _da fornire_ | template | Zona giorno | `hi_temp_inferiore`, `hi_simulazione` | `sensor.sim_temperatura_inferiore` |
| [SIM] Umidità piano inferiore | 🟣 simulazione | sensore | _da fornire_ | template | Zona giorno | `hi_umidita_inferiore`, `hi_simulazione` | `sensor.sim_umidita_inferiore` |
| [SIM] Temperatura mansarda | 🟣 simulazione | sensore | _da fornire_ | template | Mansarda principale | `hi_temp_mansarda`, `hi_simulazione` | `sensor.sim_temperatura_mansarda` |
| [SIM] Temperatura esterna | 🟣 simulazione | sensore | _da fornire_ | template | Esterno | `hi_temp_esterna`, `hi_simulazione` | `sensor.sim_temperatura_esterna` |
| [SIM] Daikin piano inferiore | 🟣 simulazione | pompa_di_calore | _da fornire_ | generic_thermostat | Zona giorno | `hi_pdc_inferiore`, `hi_monitorato`, `hi_simulazione` | `climate.sim_daikin_inferiore` |
| [SIM] Daikin mansarda | 🟣 simulazione | pompa_di_calore | _da fornire_ | generic_thermostat | Mansarda principale | `hi_pdc_mansarda`, `hi_monitorato`, `hi_simulazione` | `climate.sim_daikin_mansarda` |
| [SIM] Termostato pavimento inferiore | 🟣 simulazione | termostato | _da fornire_ | generic_thermostat | Zona giorno | `hi_termostato_inferiore`, `hi_monitorato`, `hi_simulazione` | `climate.sim_termostato_inferiore` |
| [SIM] Termostato pavimento mansarda | 🟣 simulazione | termostato | _da fornire_ | generic_thermostat | Mansarda principale | `hi_termostato_mansarda`, `hi_monitorato`, `hi_simulazione` | `climate.sim_termostato_mansarda` |
| [SIM] Luce zona giorno | 🟣 simulazione | luce | _da fornire_ | template | Zona giorno | `hi_luce`, `hi_simulazione` | `light.sim_luce_giorno` |
| [SIM] Luce cucina | 🟣 simulazione | luce | _da fornire_ | template | Cucina | `hi_luce`, `hi_simulazione` | `light.sim_luce_cucina` |
| [SIM] Luce ingresso | 🟣 simulazione | luce | _da fornire_ | template | Ingresso | `hi_luce`, `hi_luce_ingresso`, `hi_simulazione` | `light.sim_luce_ingresso` |
| [SIM] Luce mansarda | 🟣 simulazione | luce | _da fornire_ | template | Mansarda principale | `hi_luce`, `hi_simulazione` | `light.sim_luce_mansarda` |
| [SIM] Luce notturna mansarda | 🟣 simulazione | luce | _da fornire_ | template | Mansarda secondaria | `hi_luce`, `hi_luce_notturna`, `hi_simulazione` | `light.sim_luce_notte` |
| [SIM] Presa TV (non essenziale) | 🟣 simulazione | presa | _da fornire_ | template | Zona giorno | `hi_carico_non_essenziale`, `hi_simulazione` | `switch.sim_presa_tv` |
| [SIM] Presa frigorifero (critica) | 🟣 simulazione | presa | _da fornire_ | template | Cucina | `hi_critico`, `hi_monitorato`, `hi_simulazione` | `switch.sim_frigorifero` |
| [SIM] Sensore movimento ingresso | 🟣 simulazione | sensore_movimento | _da fornire_ | template | Ingresso | `hi_presenza_supplementare`, `hi_simulazione` | `binary_sensor.sim_movimento_ingresso` |
| [SIM] Finestra mansarda | 🟣 simulazione | sensore_apertura | _da fornire_ | template | Mansarda principale | `hi_finestra_mansarda`, `hi_simulazione` | `binary_sensor.sim_finestra_mansarda` |
| [SIM] Fotovoltaico, batteria e scambio | 🟣 simulazione | inverter | _da fornire_ | template | Locale tecnico | `hi_simulazione` | `sensor.sim_fv_potenza`<br>`sensor.sim_fv_energia`<br>`sensor.sim_rete_potenza_netta`<br>`sensor.sim_rete_prelievo_energia`<br>`sensor.sim_rete_immissione_energia`<br>`sensor.sim_casa_potenza`<br>`sensor.sim_batteria_soc`<br>`sensor.sim_batteria_potenza_netta` |
| [SIM] Smartphone persone simulate | 🟣 simulazione | tracker | _da fornire_ | device_tracker.see | — | `hi_simulazione` | `device_tracker.sim_telefono_1`<br>`device_tracker.sim_telefono_2` |

## Note di configurazione

- **Pompa di calore salotto (piano inferiore)**: Adattatore BRP069B4x supportato dall'integrazione core locale (nessun cloud, nessuna chiave richiesta). IP attuale 192.168.1.15: riservarlo nel router (DHCP statico). Le entità effettive (sensori di energia, streamer) dipendono dall'unità: verificarle dopo l'integrazione. Il sensore di temperatura ESTERNA dell'unità può alimentare il ruolo hi_temp_esterna (misura sull'unità esterna: può essere falsata da sole e sbrinamento). La temperatura INTERNA è misurata sull'unità a parete: utile come riferimento provvisorio, non ideale per il supervisore (vedi docs/integrazione-dispositivi.md).
  - monitoraggio: stato, modalita, temperatura_impostata, temperatura_interna, temperatura_esterna, ventola, swing, preset, potenza_compressore, energia, frequenza_compressore; comando: accensione, modalita, setpoint, ventola, swing, preset_eco_boost_away, streamer
- **Seconda pompa di calore (posizione da confermare)**: Adattatore BRP069B4x (IP attuale 192.168.1.16, da riservare nel router). Confermare modello e ambiente: se non è in mansarda, cambiare area ed etichetta di zona (hi_pdc_inferiore / hi_pdc_mansarda).
  - monitoraggio: stato, modalita, temperatura_impostata, temperatura_interna, ventola; comando: accensione, modalita, setpoint, ventola
- **Termostato pavimento piano inferiore**: Il supervisore NON comanda valvole, collettori o caldaie: agisce solo sul setpoint del termostato, dopo verifica dell'architettura dell'impianto. Il pavimento non viene MAI usato in raffrescamento.
  - monitoraggio: temperatura, setpoint, stato_richiesta_calore; comando: setpoint, modalita
- **Termostato pavimento mansarda**: Vedi termostato_inferiore.
  - monitoraggio: temperatura, setpoint, stato_richiesta_calore; comando: setpoint, modalita
- **Inverter fotovoltaico (~6 kWp)**: Assegnare a ogni entità SOLO l'etichetta del ruolo corrispondente (vedi docs/energia.md).
  - monitoraggio: potenza_fv, energia_fv; comando: —
- **Sistema di accumulo (10–15 kWh)**: Nessun comando previsto nella prima versione.
  - monitoraggio: soc, potenza_carica, potenza_scarica, energia; comando: —
  - monitoraggio: prelievo, immissione; comando: —
- **Interruttore Lavanderia**: Indicare ambiente/piano e se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Interruttore Studio**: Indicare ambiente/piano e se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Interruttore Bagno mansarda**: Ambiente provvisorio, in futuro un'area 'Bagno mansarda' dedicata.
  - monitoraggio: stato; comando: on_off
- **Interruttore Scala**: Indicare ambiente/piano e se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Interruttore Box Silvia**: Indicare ambiente/piano e se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Altri interruttori Sonoff (elenco da completare)**: L'elenco nell'app continua oltre i 5 dispositivi visibili nello screenshot.
  - monitoraggio: stato; comando: on_off
- **Coordinatore Zigbee USB (SONOFF)**: Collegare a Green con una prolunga USB di 1–2 m, lontano da router Wi-Fi, SSD e porte USB 3. Scegliere un canale Zigbee non sovrapposto al Wi-Fi (es. 15, 20 o 25).
- **Smartphone con Companion App**: Associare ogni device_tracker alla rispettiva persona da Impostazioni → Persone.
  - monitoraggio: posizione, batteria; comando: notifiche
