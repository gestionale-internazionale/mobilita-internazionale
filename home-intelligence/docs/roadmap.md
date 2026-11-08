# Roadmap

| Fase | Contenuto | Prerequisiti |
|---|---|---|
| **v0.1 (questa)** | Ambiente avviabile, modello casa, 7 viste, presenza, modalità, scenari, supervisore (solo decisioni), attuazione protetta, predisposizione energia, diagnostica, test | — |
| v0.2 – Dispositivi esistenti | Censimento interruttori e dispositivi Google Home; Matter multi-admin e integrazioni dei produttori; ambienti reali e planimetria | elenco dispositivi e ambienti, planimetrie |
| v0.3 – Daikin | Scelta dell'integrazione (locale/Onecta), verifica delle capacità, attuazione PdC per zona | modelli Daikin e adattatori |
| v0.4 – Termostati | Integrazione, verifica dell'impianto radiante, attuazione pavimento, taratura di isteresi, tempi minimi e `inerzia_ore` con dati reali | Green, termostati, schema impianto |
| v0.5 – Energia | Inverter, batteria, Energy Dashboard, prezzi (fasce F1/F2/F3 o PUN), anomalie | impianto installato |
| v0.6 – Carichi | Gestione `hi_carico_programmabile` con surplus FV (prima suggerimenti, poi comando con consenso) | dati FV reali, prese smart con misura |
| v0.7 – Predittivo | Stima automatica dell'inerzia dallo storico, pre-riscaldamento prima dell'arrivo o del programma, meteo (integrazione meteo nativa), convenienza PdC vs pavimento (COP vs temperatura esterna, costo energia, SoC batteria) | almeno 1 stagione di dati |

Principio: si aggiunge complessità solo quando i dati reali permettono di verificarla.
