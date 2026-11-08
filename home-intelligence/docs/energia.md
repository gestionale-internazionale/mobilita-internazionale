# Energia

## Principio

L'architettura non dipende dal produttore dell'inverter. Ogni sensore reale riceve **un'etichetta di ruolo** e i proxy `sensor.hi_en_*` normalizzano le unità:

| Ruolo (etichetta) | Grandezza | Proxy |
|---|---|---|
| `hi_en_pv_potenza` | potenza FV (W/kW) | `sensor.hi_en_pv_potenza` (W) |
| `hi_en_pv_energia` | energia prodotta (Wh/kWh, totale crescente) | `sensor.hi_en_pv_energia` (kWh) |
| `hi_en_rete_prelievo_potenza` / `_immissione_potenza` | potenze separate | `sensor.hi_en_rete_prelievo` / `_immissione` |
| `hi_en_rete_potenza_netta` | potenza unica con segno (+prelievo); `hi_en_inverti_segno_rete` se l'inverter usa la convenzione opposta | come sopra |
| `hi_en_rete_prelievo_energia` / `_immissione_energia` | energia scambiata | kWh |
| `hi_en_batt_soc` | stato di carica (%) | `sensor.hi_en_batt_soc` |
| `hi_en_batt_carica_potenza` / `_scarica_potenza` oppure `hi_en_batt_potenza_netta` (+scarica) | potenza batteria | W |
| `hi_en_batt_energia_carica` / `_scarica` | energia batteria | kWh |
| `hi_en_casa_potenza` | consumo misurato (facoltativo) | se assente, si calcola dal bilancio |

La **capacità** dell'accumulo (kWh) è un parametro (`input_number.hi_en_batt_capacita`), non una misura. Potenza, energia e capacità restano grandezze separate.

Derivati calcolati solo con ingressi validi:
- consumo casa = FV + prelievo − immissione + scarica − carica;
- autoconsumo = FV − immissione;
- autosufficienza istantanea;
- energia autoconsumata e consumata (integrazione di Riemann);
- contatori giornalieri e mensili;
- costi, ricavi e risparmio (con i prezzi impostati in €/kWh).

## Collegare l'impianto reale

1. Integra l'inverter, **preferibilmente in locale** (molte marche hanno integrazioni core o Modbus/SunSpec; da verificare sul modello).
2. In `devices.yaml`, sotto il dispositivo, indica `entita` e `ruoli` (un'etichetta per entità), poi `stato: reale` e `hi_tool.py sync --apply`.
3. Imposta capacità della batteria, prezzi, soglia di surplus e soglia di prelievo (0 = disattivata).
4. **Energy Dashboard nativa** (Impostazioni → Pannelli → Energia): usa i sensori **originali** dell'inverter (rete prelevata/immessa, produzione FV, batteria caricata/scaricata). In alternativa vanno bene i proxy `sensor.hi_en_*_energia`, che hanno `state_class: total_increasing`.

La vista Energia di Home Intelligence funziona subito con i proxy: non va riscritta quando arriva l'impianto.

## Ottimizzazione (predisposta)

- `binary_sensor.hi_en_surplus_fv`: immissione oltre soglia per 10 minuti.
- `binary_sensor.hi_en_prelievo_elevato`: prelievo oltre soglia, con notifica importante.
- `sensor.hi_en_consiglio`: usa_surplus | riduci_consumi | preserva_batteria | neutro | non_configurato.
- `hi_en_gestione_carichi`: solo **suggerimenti** via notifica. Nessun carico viene comandato.

Gli elettrodomestici candidati vanno marcati `hi_carico_programmabile` per la fase successiva (vedi roadmap).
