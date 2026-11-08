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

- Modello consigliato: **SONOFF Dongle Plus MG24** (EFR32MG24), successore del ZBDongle-E, supportato da ZHA. Vanno bene anche ZBDongle-E e ZBDongle-P.
- Integrazione: **ZHA** (core, la più semplice). In alternativa Zigbee2MQTT (add-on + broker MQTT), che conviene solo se servono dispositivi supportati unicamente da Z2M. Un dongle serve **una sola** delle due.
- Installazione: prolunga USB da 1–2 m, lontano dal router Wi-Fi e dalle porte USB 3; canale Zigbee 15, 20 o 25.
- **Primi acquisti utili per il progetto** (non obbligatori):
  - un **sensore di temperatura/umidità per zona** (`hi_temp_inferiore`, `hi_temp_mansarda`): migliora molto il supervisore rispetto al sensore interno del Daikin;
  - **contatti finestra** nelle stanze con climatizzazione (`hi_finestra_<zona>`);
  - **sensori di movimento/presenza** in ingresso e corridoi (`hi_presenza_supplementare`);
  - **prese smart con misura di energia** per gli elettrodomestici programmabili (`hi_carico_programmabile`). Le prese Zigbee fanno anche da ripetitori.

Fonti: [SonoffLAN](https://github.com/alexxit/sonofflan) · [MINIR4 e modalità LAN (forum eWeLink)](https://forum.ewelink.cc/t/how-to-enable-diy-mode-on-sonoff-minir4-without-soldering/207592) · [Dongle Plus MG24](https://sonoff.tech/de-eu/products/sonoff-zigbee-thread-usb-dongle-dongle-plus-mg24) · [MG24 e ZHA (community HA)](https://community.home-assistant.io/t/itead-s-new-sonoff-dongle-plus-mg24-based-on-silicon-labs-efr32mg24-radio-microcontroller-soc-has-now-been-launched/926690)
