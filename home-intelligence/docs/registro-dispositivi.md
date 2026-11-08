# Registro dispositivi
> File generato da `scripts/hi_tool.py docs` a partire da `inventory/devices.yaml`.
> Per aggiungere o aggiornare un dispositivo modifica il file YAML e rigenera.

| Dispositivo | Stato | Tipo | Marca / modello | Integrazione | Area | Etichette | Entità |
|---|---|---|---|---|---|---|---|
| Pompa di calore salotto (piano inferiore) | ⚪ non disponibile | pompa_di_calore | Daikin Perfera FTXM71N2V1B (unità interna, 2020) + adattatore Wi-Fi BRP069B4x | daikin | Salotto | `hi_pdc_inferiore`, `hi_monitorato` | — |
| Pompa di calore mansarda | ⚪ non disponibile | pompa_di_calore | Daikin Perfera serie FTXM-N (taglia da confermare) + adattatore Wi-Fi BRP069B4x | daikin | Open space mansarda | `hi_pdc_mansarda`, `hi_monitorato` | — |
| Termostato piano inferiore (pavimento radiante) | ⚪ non disponibile | termostato | EZAIOT (piattaforma Tuya Zigbee) termostato Zigbee a batteria per caldaia a gas (contatto pulito), probabile TS0601 | zigbee2mqtt | Salotto | `hi_termostato_inferiore`, `hi_temp_inferiore`, `hi_monitorato` | — |
| Termostato mansarda (radiatori) | ⚪ non disponibile | termostato | EZAIOT (piattaforma Tuya Zigbee) termostato Zigbee a batteria per caldaia a gas (contatto pulito), probabile TS0601 | zigbee2mqtt | Open space mansarda | `hi_termostato_mansarda`, `hi_temp_mansarda`, `hi_monitorato` | — |
| Termoarredi ad acqua bagni piano inferiore (2) | ⚪ non disponibile | termoarredo | _da fornire_ | nessuna | Bagno |  | — |
| Inverter fotovoltaico (~6 kWp) | ⚪ non disponibile | inverter | _da fornire_ | da_verificare | Locale tecnico | `hi_en_pv_potenza`, `hi_en_pv_energia`, `hi_monitorato` | — |
| Sistema di accumulo (10–15 kWh) | ⚪ non disponibile | batteria | _da fornire_ | da_verificare | Locale tecnico | `hi_en_batt_soc`, `hi_en_batt_carica_potenza`, `hi_en_batt_scarica_potenza`, `hi_en_batt_energia_carica`, `hi_en_batt_energia_scarica` | — |
| Misura di scambio con la rete | ⚪ non disponibile | contatore | _da fornire_ | da_verificare | Locale tecnico | `hi_en_rete_prelievo_potenza`, `hi_en_rete_immissione_potenza`, `hi_en_rete_prelievo_energia`, `hi_en_rete_immissione_energia` | — |
| Interruttore Lavanderia | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | Lavanderia (bagno cieco) | `hi_luce`, `hi_monitorato` | — |
| Interruttore Studio | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | Studio | `hi_luce`, `hi_monitorato` | — |
| Interruttore Bagno mansarda | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | Bagno mansarda | `hi_luce`, `hi_monitorato` | — |
| Interruttore Scala | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | Scala | `hi_luce`, `hi_monitorato` | — |
| Interruttore Box Silvia | ⚪ non disponibile | interruttore | SONOFF MINI R2 o MINIR4 | sonofflan | Box | `hi_luce`, `hi_monitorato` | — |
| Altri interruttori Sonoff (elenco da completare) | ⚪ non disponibile | interruttore | SONOFF | sonofflan | — | `hi_luce` | — |
| Coordinatore Zigbee USB (SONOFF) | ⚪ non disponibile | coordinatore | SONOFF Dongle Plus MG24 (Silicon Labs EFR32MG24, firmware EmberZNet) | zigbee2mqtt | Locale tecnico |  | — |
| Smartphone con Companion App | ⚪ non disponibile | tracker | _da fornire_ | mobile_app | — |  | — |
| [SIM] Sensori temperatura/umidità | 🟣 simulazione | sensore | _da fornire_ | template | Salotto | `hi_temp_inferiore`, `hi_simulazione` | `sensor.sim_temperatura_inferiore` |
| [SIM] Umidità piano inferiore | 🟣 simulazione | sensore | _da fornire_ | template | Salotto | `hi_umidita_inferiore`, `hi_simulazione` | `sensor.sim_umidita_inferiore` |
| [SIM] Temperatura mansarda | 🟣 simulazione | sensore | _da fornire_ | template | Open space mansarda | `hi_temp_mansarda`, `hi_simulazione` | `sensor.sim_temperatura_mansarda` |
| [SIM] Temperatura esterna | 🟣 simulazione | sensore | _da fornire_ | template | Esterno | `hi_temp_esterna`, `hi_simulazione` | `sensor.sim_temperatura_esterna` |
| [SIM] Daikin piano inferiore | 🟣 simulazione | pompa_di_calore | _da fornire_ | generic_thermostat | Salotto | `hi_pdc_inferiore`, `hi_monitorato`, `hi_simulazione` | `climate.sim_daikin_inferiore` |
| [SIM] Daikin mansarda | 🟣 simulazione | pompa_di_calore | _da fornire_ | generic_thermostat | Open space mansarda | `hi_pdc_mansarda`, `hi_monitorato`, `hi_simulazione` | `climate.sim_daikin_mansarda` |
| [SIM] Termostato pavimento inferiore | 🟣 simulazione | termostato | _da fornire_ | generic_thermostat | Salotto | `hi_termostato_inferiore`, `hi_monitorato`, `hi_simulazione` | `climate.sim_termostato_inferiore` |
| [SIM] Termostato pavimento mansarda | 🟣 simulazione | termostato | _da fornire_ | generic_thermostat | Open space mansarda | `hi_termostato_mansarda`, `hi_monitorato`, `hi_simulazione` | `climate.sim_termostato_mansarda` |
| [SIM] Luce zona giorno | 🟣 simulazione | luce | _da fornire_ | template | Salotto | `hi_luce`, `hi_simulazione` | `light.sim_luce_giorno` |
| [SIM] Luce cucina | 🟣 simulazione | luce | _da fornire_ | template | Cucina | `hi_luce`, `hi_simulazione` | `light.sim_luce_cucina` |
| [SIM] Luce ingresso | 🟣 simulazione | luce | _da fornire_ | template | Disimpegno | `hi_luce`, `hi_luce_ingresso`, `hi_simulazione` | `light.sim_luce_ingresso` |
| [SIM] Luce mansarda | 🟣 simulazione | luce | _da fornire_ | template | Open space mansarda | `hi_luce`, `hi_simulazione` | `light.sim_luce_mansarda` |
| [SIM] Luce notturna mansarda | 🟣 simulazione | luce | _da fornire_ | template | Open space mansarda | `hi_luce`, `hi_luce_notturna`, `hi_simulazione` | `light.sim_luce_notte` |
| [SIM] Presa TV (non essenziale) | 🟣 simulazione | presa | _da fornire_ | template | Salotto | `hi_carico_non_essenziale`, `hi_simulazione` | `switch.sim_presa_tv` |
| [SIM] Presa frigorifero (critica) | 🟣 simulazione | presa | _da fornire_ | template | Cucina | `hi_critico`, `hi_monitorato`, `hi_simulazione` | `switch.sim_frigorifero` |
| [SIM] Sensore movimento ingresso | 🟣 simulazione | sensore_movimento | _da fornire_ | template | Disimpegno | `hi_presenza_supplementare`, `hi_simulazione` | `binary_sensor.sim_movimento_ingresso` |
| [SIM] Finestra mansarda | 🟣 simulazione | sensore_apertura | _da fornire_ | template | Open space mansarda | `hi_finestra_mansarda`, `hi_simulazione` | `binary_sensor.sim_finestra_mansarda` |
| [SIM] Fotovoltaico, batteria e scambio | 🟣 simulazione | inverter | _da fornire_ | template | Locale tecnico | `hi_simulazione` | `sensor.sim_fv_potenza`<br>`sensor.sim_fv_energia`<br>`sensor.sim_rete_potenza_netta`<br>`sensor.sim_rete_prelievo_energia`<br>`sensor.sim_rete_immissione_energia`<br>`sensor.sim_casa_potenza`<br>`sensor.sim_batteria_soc`<br>`sensor.sim_batteria_potenza_netta` |
| [SIM] Smartphone persone simulate | 🟣 simulazione | tracker | _da fornire_ | device_tracker.see | — | `hi_simulazione` | `device_tracker.sim_telefono_1`<br>`device_tracker.sim_telefono_2` |

## Note di configurazione

- **Pompa di calore salotto (piano inferiore)**: Adattatore BRP069B4x supportato dall'integrazione core locale (nessun cloud, nessuna chiave richiesta). IP attuale 192.168.1.15: riservarlo nel router (DHCP statico). Le entità effettive (sensori di energia, streamer) dipendono dall'unità: verificarle dopo l'integrazione. Il sensore di temperatura ESTERNA dell'unità può alimentare il ruolo hi_temp_esterna (misura sull'unità esterna: può essere falsata da sole e sbrinamento). La temperatura INTERNA è misurata sull'unità a parete: utile come riferimento provvisorio, non ideale per il supervisore (vedi docs/integrazione-dispositivi.md).
  - monitoraggio: stato, modalita, temperatura_impostata, temperatura_interna, temperatura_esterna, ventola, swing, preset, potenza_compressore, energia, frequenza_compressore; comando: accensione, modalita, setpoint, ventola, swing, preset_eco_boost_away, streamer
- **Pompa di calore mansarda**: Stessa serie e stesso adattatore dell'unità del salotto: valgono le stesse capacità e avvertenze. IP attuale 192.168.1.16, da riservare nel router. La sigla completa (es. FTXM25N/35N…) serve solo per conoscere la potenza nominale, non per l'integrazione.
  - monitoraggio: stato, modalita, temperatura_impostata, temperatura_interna, temperatura_esterna, ventola, swing, preset, potenza_compressore, energia, frequenza_compressore; comando: accensione, modalita, setpoint, ventola, swing, preset_eco_boost_away, streamer
- **Termostato piano inferiore (pavimento radiante)**: Termostato attuale: a batteria, 2 fili, contatto pulito (on/off) che apre la valvola di zona (forse anche un circolatore). Acqua calda dalla caldaia CONDOMINIALE: nessun comando alla caldaia. Il sostituto smart deve avere relè a contatto pulito (NO/COM, carico ≥ 1 A) e funzionare A BATTERIA (nessun neutro/230 V al muro). Verificare la compatibilità del modello acquistato prima dell'installazione. Comanda il circuito a pavimento del piano inferiore.
  - monitoraggio: temperatura, setpoint, stato_richiesta_calore; comando: setpoint, modalita
- **Termostato mansarda (radiatori)**: Termostato attuale: a batteria, 2 fili, contatto pulito (on/off) che apre la valvola di zona (forse anche un circolatore). Acqua calda dalla caldaia CONDOMINIALE: nessun comando alla caldaia. Il sostituto smart deve avere relè a contatto pulito (NO/COM, carico ≥ 1 A) e funzionare A BATTERIA (nessun neutro/230 V al muro). Verificare la compatibilità del modello acquistato prima dell'installazione. Comanda ~3 termosifoni + termoarredo del bagno (fonte "radiatori").
  - monitoraggio: temperatura, setpoint, stato_richiesta_calore; comando: setpoint, modalita
- **Termoarredi ad acqua bagni piano inferiore (2)**: Ad acqua, alimentati dall'impianto centralizzato: si scaldano quando la valvola di zona è aperta. Non comandabili separatamente senza una testa termostatica smart dedicata (eventuale sviluppo futuro, es. Zigbee).
- **Inverter fotovoltaico (~6 kWp)**: Assegnare a ogni entità SOLO l'etichetta del ruolo corrispondente (vedi docs/energia.md).
  - monitoraggio: potenza_fv, energia_fv; comando: —
- **Sistema di accumulo (10–15 kWh)**: Nessun comando previsto nella prima versione.
  - monitoraggio: soc, potenza_carica, potenza_scarica, energia; comando: —
  - monitoraggio: prelievo, immissione; comando: —
- **Interruttore Lavanderia**: Confermare se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Interruttore Studio**: Confermare se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Interruttore Bagno mansarda**: Confermare se comanda la luce del bagno.
  - monitoraggio: stato; comando: on_off
- **Interruttore Scala**: Confermare se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Interruttore Box Silvia**: Confermare se comanda una luce o un altro carico.
  - monitoraggio: stato; comando: on_off
- **Altri interruttori Sonoff (elenco da completare)**: L'elenco nell'app continua oltre i 5 dispositivi visibili nello screenshot.
  - monitoraggio: stato; comando: on_off
- **Coordinatore Zigbee USB (SONOFF)**: In Zigbee2MQTT usare adapter "ember" e la porta /dev/serial/by-id/… . Collegare a Green con una prolunga USB di 1–2 m, lontano da router Wi-Fi, SSD e porte USB 3. Scegliere un canale Zigbee non sovrapposto al Wi-Fi (es. 15, 20 o 25).
- **Smartphone con Companion App**: Associare ogni device_tracker alla rispettiva persona da Impostazioni → Persone.
  - monitoraggio: posizione, batteria; comando: notifiche
