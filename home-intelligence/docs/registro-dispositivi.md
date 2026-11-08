# Registro dispositivi
> File generato da `scripts/hi_tool.py docs` a partire da `inventory/devices.yaml`.
> Per aggiungere o aggiornare un dispositivo modifica il file YAML e rigenera.

| Dispositivo | Stato | Tipo | Marca / modello | Integrazione | Area | Etichette | Entità |
|---|---|---|---|---|---|---|---|
| Pompa di calore piano inferiore | ⚪ non disponibile | pompa_di_calore | Daikin | da_verificare | Zona giorno | `hi_pdc_inferiore`, `hi_monitorato` | — |
| Pompa di calore mansarda | ⚪ non disponibile | pompa_di_calore | Daikin | da_verificare | Mansarda principale | `hi_pdc_mansarda`, `hi_monitorato` | — |
| Termostato pavimento piano inferiore | ⚪ non disponibile | termostato | _da fornire_ | da_verificare | Zona giorno | `hi_termostato_inferiore`, `hi_monitorato` | — |
| Termostato pavimento mansarda | ⚪ non disponibile | termostato | _da fornire_ | da_verificare | Mansarda principale | `hi_termostato_mansarda`, `hi_monitorato` | — |
| Inverter fotovoltaico (~6 kWp) | ⚪ non disponibile | inverter | _da fornire_ | da_verificare | Locale tecnico | `hi_en_pv_potenza`, `hi_en_pv_energia`, `hi_monitorato` | — |
| Sistema di accumulo (10–15 kWh) | ⚪ non disponibile | batteria | _da fornire_ | da_verificare | Locale tecnico | `hi_en_batt_soc`, `hi_en_batt_carica_potenza`, `hi_en_batt_scarica_potenza`, `hi_en_batt_energia_carica`, `hi_en_batt_energia_scarica` | — |
| Misura di scambio con la rete | ⚪ non disponibile | contatore | _da fornire_ | da_verificare | Locale tecnico | `hi_en_rete_prelievo_potenza`, `hi_en_rete_immissione_potenza`, `hi_en_rete_prelievo_energia`, `hi_en_rete_immissione_energia` | — |
| Interruttori smart esistenti (gruppo da censire) | ⚪ non disponibile | interruttore | _da fornire_ | da_verificare | — | `hi_luce` | — |
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

- **Pompa di calore piano inferiore**: Compatibilità da verificare sul modello reale. Le funzioni effettivamente esposte (temperatura esterna, consumi, swing, modalità speciali) dipendono da modello e adattatore. Vedi docs/analisi-tecnica.md §Daikin.
  - monitoraggio: stato, modalita, temperatura_impostata, temperatura_interna, ventola; comando: accensione, modalita, setpoint, ventola
- **Pompa di calore mansarda**: Vedi daikin_inferiore.
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
- **Interruttori smart esistenti (gruppo da censire)**: Censire un interruttore per voce quando marca/modello saranno noti, indicando l'area e le etichette (hi_luce, hi_luce_ingresso, …).
  - monitoraggio: stato; comando: on_off
- **Smartphone con Companion App**: Associare ogni device_tracker alla rispettiva persona da Impostazioni → Persone.
  - monitoraggio: posizione, batteria; comando: notifiche
