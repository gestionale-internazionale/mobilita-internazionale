# Informazioni da fornire (in ordine di priorità)

Non bloccano il lavoro: servono per passare da *predisposto* a *reale*.

| # | Informazione | Perché serve | Formato utile |
|---|---|---|---|
| 1 | ✅ *Ambienti ricevuti (piano inferiore + mansarda open space/bagno).* **Manca:** mappe di dettaglio (disposizione). Elenco ambienti per piano (+ planimetrie, anche foto) | aree reali, planimetria, card per ambiente | elenco "piano → ambienti"; immagine PNG/SVG/PDF |
| 2 | ✅ *Salotto: Perfera FTXM71N2V1B; mansarda: Perfera FTXM-N; entrambe con BRP069B4x (integrazione locale).* Modelli Daikin (unità interne/esterne) e **adattatore Wi-Fi** (sigla BRP…) + app usata (Onecta/altro) | scelta tra integrazione locale e cloud, funzioni disponibili | foto dell'etichetta o sigla |
| 3 | ✅ *Sonoff MINI R2 / MINIR4 (eWeLink).* **Manca:** elenco completo, ambiente e piano di ciascuno, cosa comandano (luce o altro). Interruttori smart: marca/modello e app usata | integrazione diretta o via Matter | elenco o foto |
| 4 | **Dispositivi in Google Home:** esporta l'elenco (nome, stanza, marca) e indica quali dichiarano Matter | percorso di integrazione per ciascuno | screenshot dell'app |
| 5 | **Termostati acquistati:** marca/modello (vedi anche riga 6) | protocollo (Matter/Zigbee/Wi-Fi), integrazione | sigla |
| 6 | ✅ *Caldaia condominiale; termostati a batteria, 2 fili, contatto pulito → valvola di zona; termoarredi ad acqua.* ✅ *Termostati: EZAIOT Zigbee a batteria (Tuya).* *Riscaldamento condominiale attivo h24 in stagione.* **Manca:** al momento dell'abbinamento, il manufacturer id dei termostati. Impianto | sicurezza dei comandi | foto |
| 7 | **Smartphone** delle persone (iOS/Android) e consenso alla localizzazione | Companion App, presenza | — |
| 8 | **Contratto elettrico:** potenza impegnata (3/4,5/6 kW), tariffa (monoraria/fasce) | soglia di prelievo, costi | bolletta |
| 9 | **Inverter e batteria** (quando scelti) | integrazione locale e ruoli energetici | sigla |
| 10 | **Computer di sviluppo:** sistema operativo e se puoi usare Docker o una VM | scelta Container vs HAOS VM per i test con dispositivi reali | — |
