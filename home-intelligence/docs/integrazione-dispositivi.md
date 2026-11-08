# Integrazione dei dispositivi identificati

Aggiornato con le informazioni fornite il 08/11/2026.

## 1. Pompe di calore Daikin (2 unità, adattatore BRP069B4x)

**Esito: compatibili con l'integrazione core *Daikin AC*, in locale.**
Il BRP069B4x è uno degli adattatori supportati (polling LAN, nessun cloud, nessuna chiave richiesta).

| Unità | Modello | IP attuale | Zona (house.yaml) |
|---|---|---|---|
| Salotto | Perfera FTXM71N2V1B (2020) + BRP069B4x | 192.168.1.15 | `inferiore` |
| Mansarda | Perfera serie FTXM-N + BRP069B4x | 192.168.1.16 | `mansarda` |

**Procedura** (su Green o sulla VM HAOS, che devono stare nella stessa LAN dei condizionatori):
1. Nel router assegna un **IP fisso** (DHCP statico) ai due adattatori.
2. Impostazioni → Dispositivi e servizi: HA di solito **rileva da solo** le unità (zeroconf `_dkapi._tcp`). In alternativa: Aggiungi integrazione → *Daikin AC* → indirizzo IP.
3. Annota gli entity_id creati e aggiornali in `inventory/devices.yaml` (`entita`, `stato: reale`), poi `hi_tool.py validate` → `sync --apply` → `generate`.

**Cosa espone l'integrazione** (secondo il codice dell'integrazione in HA 2026.2; quali entità compaiono davvero dipende dall'unità):

| Entità | Uso nel progetto |
|---|---|
| `climate`: modalità (heat, cool, dry, fan_only, heat_cool, off), setpoint, ventola, swing, preset eco/boost/away | ruolo `hi_pdc_<zona>`, comandato solo con il consenso all'attuazione |
| Temperatura interna (sensore sull'unità a parete) | riferimento **provvisorio** finché non arrivano i termostati; vedi nota sotto |
| Temperatura esterna (sensore sull'unità esterna) | ruolo `hi_temp_esterna`: abilita la regola "esterna troppo fredda" |
| Potenza stimata compressore, energia (totale, caldo, freddo), frequenza compressore | monitoraggio consumi, utili in futuro per stimare il COP |
| Switch *streamer* (se presente) | non usato dalle automazioni |

**Coesistenza con l'app Daikin:** l'app continua a funzionare. Se cambi modalità o setpoint dall'app mentre l'attuazione automatica è attiva, il sistema lo rileva come **intervento manuale** e sospende il controllo per la durata dell'override.

**Nota sulla temperatura interna:** la misura viene presa in alto, dentro l'unità, ed è falsata quando l'unità è in funzione. Due opzioni:
- *(consigliata)* usarla solo come riferimento e aggiungere un **sensore Zigbee di temperatura** per zona, con etichetta `hi_temp_<zona>` (vedi §3);
- usarla subito come `hi_temp_<zona>` con l'attuazione **spenta**, solo per osservare le decisioni del supervisore.

## 2. Interruttori Sonoff Wi-Fi (app eWeLink)

Modelli rilevati: **MINI** (R2, ESP8266, firmware `PSF-BD1-GL`) e **MINIR4** (ESP32). Nessuno dei due supporta Matter (la variante Matter è MINIR4M). Home Assistant non ha un'integrazione core per eWeLink.

| Opzione | Pro | Contro | Valutazione |
|---|---|---|---|
| **SonoffLAN** (HACS, AlexxIT) | Controllo **locale** con ripiego sul cloud. eWeLink e Google Home restano funzionanti. Nessuna modifica hardware. | Componente non core (aggiornamenti via HACS); serve il login eWeLink per ricavare le chiavi locali | **Consigliata adesso** |
| Flash **ESPHome/Tasmota** | 100% locale e nativo (ESPHome) | Apertura del dispositivo e flash seriale; si perdono eWeLink e il collegamento diretto con Google (si recupera esponendo HA) | Possibile in futuro, interruttore per interruttore |
| Google Assistant SDK | — | Solo comandi, nessuno stato | Sconsigliata |

Secondo testimonianze della community, il MINIR4 non ha la "DIY mode", ma il controllo locale via LAN funziona. Va verificato sul primo dispositivo.

**Procedura** (consigliata):
1. Installa **HACS** su Green (procedura ufficiale HACS), poi HACS → *SonoffLAN* → riavvio.
2. Aggiungi l'integrazione *Sonoff* con l'account eWeLink, modalità **auto** (locale se raggiungibile, altrimenti cloud).
3. Tieni Green e i Sonoff **sulla stessa rete/VLAN**: il controllo locale su VLAN diverse è segnalato come poco affidabile.
4. Per ogni interruttore: in `devices.yaml` area corretta, etichette (`hi_luce` se comanda una luce, `hi_luce_ingresso`, `hi_carico_non_essenziale`, oppure `hi_critico`), entità e `stato: reale`. Poi `sync --apply`.

**Impostazione consigliata nell'app eWeLink:** *Stato all'accensione* = **Spento** (già così sul MINI) oppure "Ultimo stato". Dopo un'interruzione di corrente così non si accende nulla da solo.

## 3. Zigbee (dongle Sonoff previsto)

- Modello acquistato: **SONOFF Dongle Plus MG24** (EFR32MG24), successore del ZBDongle-E, supportato da ZHA. Vanno bene anche ZBDongle-E e ZBDongle-P.
- Integrazione: **Zigbee2MQTT** (add-on Zigbee2MQTT + add-on broker Mosquitto, entrambi disponibili su HAOS/Green). L'ho scelta al posto di ZHA perché i termostati Tuya (TS0601) sono supportati molto meglio da Zigbee2MQTT: in ZHA spesso vengono riconosciuti senza entità. Un dongle serve **una sola** delle due integrazioni.
- Configurazione dell'add-on Zigbee2MQTT per l'MG24:
  ```yaml
  serial:
    port: /dev/serial/by-id/usb-…    # scegliere il percorso proposto dall'add-on (stabile ai riavvii)
    adapter: ember                   # chip Silicon Labs EFR32MG24
  ```
  Se il dongle ha il firmware "Thread/Matter", va prima aggiornato al firmware **Zigbee (EmberZNet)** con il flasher web di SONOFF. Di fabbrica di solito è già Zigbee.
- Installazione: prolunga USB da 1–2 m, lontano dal router Wi-Fi e dalle porte USB 3; canale Zigbee 15, 20 o 25.
- **Primi acquisti utili per il progetto** (non obbligatori):
  - un **sensore di temperatura/umidità per zona** (`hi_temp_inferiore`, `hi_temp_mansarda`): migliora molto il supervisore rispetto al sensore interno del Daikin;
  - **contatti finestra** nelle stanze con climatizzazione (`hi_finestra_<zona>`);
  - **sensori di movimento/presenza** in ingresso e corridoi (`hi_presenza_supplementare`);
  - **prese smart con misura di energia** per gli elettrodomestici programmabili (`hi_carico_programmabile`). Le prese Zigbee fanno anche da ripetitori.

Fonti: [SonoffLAN](https://github.com/alexxit/sonofflan) · [MINIR4 e modalità LAN (forum eWeLink)](https://forum.ewelink.cc/t/how-to-enable-diy-mode-on-sonoff-minir4-without-soldering/207592) · [Dongle Plus MG24](https://sonoff.tech/de-eu/products/sonoff-zigbee-thread-usb-dongle-dongle-plus-mg24) · [MG24 e ZHA (community HA)](https://community.home-assistant.io/t/itead-s-new-sonoff-dongle-plus-mg24-based-on-silicon-labs-efr32mg24-radio-microcontroller-soc-has-now-been-launched/926690)

## 4. Termostati smart (in arrivo) – requisiti di compatibilità

Situazione attuale: termostati **a batteria**, 2 fili, **contatto pulito** che apre la valvola di zona. L'acqua calda viene dalla caldaia condominiale.

Il termostato sostitutivo deve avere:
1. un **relè a contatto pulito** (morsetti NO/COM, a volte indicati come "caldaia" o "boiler"), con un carico ammesso di almeno 1 A;
2. **alimentazione a batteria**: al muro non arrivano neutro né 230 V. I modelli che chiedono un "filo C" o la 230 V non vanno bene senza modificare l'impianto;
3. **integrazione locale con HA**: Zigbee (con il dongle previsto), Matter, oppure un'integrazione core locale;
4. un'entità `climate` con `set_temperature`, che è l'unico comando usato dal supervisore.

Se il modello acquistato è Wi-Fi solo-cloud o richiede la 230 V, valutiamo insieme le alternative prima di installarlo.

### Termostati scelti: EZAIOT Zigbee a batteria (piattaforma Tuya)

Valutazione: **adatti** all'impianto (batteria + contatto pulito per "caldaia a gas"), con queste condizioni:

1. **Variante corretta:** verifica di aver ordinato la versione **Zigbee** (non Wi-Fi) per **caldaia a gas / a batteria** (contatto pulito). Le varianti "riscaldamento ad acqua" ed "elettrico" vogliono la 230 V e non vanno bene.
2. **Serve il coordinatore Zigbee** (il dongle) per collegarli a HA. Non serve un gateway Tuya né il cloud Tuya.
3. **Integrazione:** Zigbee2MQTT. Al primo abbinamento annota il *manufacturer id* (stringa `_TZE200_…`/`_TZE284_…`) e verifica che compaia nell'elenco dei dispositivi supportati da Zigbee2MQTT. Mandamelo e controllo io quali funzioni espone.
4. **Modalità manuale:** il termostato ha programmi interni. Va impostato in modalità **manuale** (preset `manual` o simile), altrimenti il suo programma sovrascrive il setpoint inviato da HA.
5. **Dispositivo a batteria:** i comandi possono arrivare con qualche secondo o minuto di ritardo e la temperatura viene riportata a intervalli. Il supervisore lo tollera (valuta ogni minuto e rispetta tempi minimi lunghi).
6. **Sensore di temperatura:** il termostato è in ambiente, quindi la sua temperatura (`current_temperature`) è più affidabile di quella del Daikin. Nel registro ha già l'etichetta `hi_temp_<zona>`: le macro del progetto leggono direttamente la temperatura dalle entità `climate`.
7. **Installazione:** collega i 2 fili della valvola ai morsetti del contatto pulito (spesso NO/COM). Prima di sostituire il vecchio termostato, fotografa il cablaggio esistente.

Fonti: [Zigbee2MQTT – TS0601 thermostat](https://www.zigbee2mqtt.io/devices/TS0601_thermostat.html) · [Beca BHT-003 (gas boiler)](https://zigbee.blakadder.com/Beca_BHT-003.html) · [TS0601 senza entità in ZHA (community HA)](https://community.home-assistant.io/t/ts0601-by-tze200-viy9ihs7-no-functions/804150)
