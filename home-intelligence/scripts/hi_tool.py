#!/usr/bin/env python3
"""Home Intelligence – strumento di gestione del modello della casa.

Comandi:
  validate   verifica inventory/house.yaml e inventory/devices.yaml
  generate   rigenera pacchetti, viste dashboard e planimetrie da house.yaml
  docs       rigenera docs/registro-dispositivi.md da devices.yaml
  sync       allinea piani, aree, etichette e associazioni in Home Assistant
             (WebSocket API). Default: simulazione a secco (dry-run).

Esempi:
  python3 scripts/hi_tool.py validate
  python3 scripts/hi_tool.py generate
  HI_URL=http://homeassistant.local:8123 HI_TOKEN=... \\
      python3 scripts/hi_tool.py sync --profilo prod --apply

Il token (long-lived access token) si legge SOLO da variabile d'ambiente:
non viene mai scritto su file.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
HA = ROOT / "homeassistant"
INV = ROOT / "inventory"
GEN_PKG = HA / "packages" / "generated"
GEN_DASH = HA / "dashboards" / "generated"
FLOORPLANS = HA / "www" / "floorplans"
IDRONICHE = {"pavimento": "Pavimento radiante", "radiatori": "Radiatori"}


def idro(z: dict) -> tuple[str | None, str]:
    """Fonte idronica della zona (tipo, nome leggibile)."""
    for f in z.get("fonti", []):
        if f in IDRONICHE:
            return f, IDRONICHE[f]
    return None, "Fonte idronica"


SLUG = re.compile(r"^[a-z][a-z0-9_]*$")
STATI = {"reale", "non_disponibile", "simulazione"}
HEADER = (
    "# =============================================================================\n"
    "# FILE GENERATO da scripts/hi_tool.py a partire da inventory/house.yaml.\n"
    "# NON MODIFICARE A MANO: modifica il modello e riesegui\n"
    "#   python3 scripts/hi_tool.py generate\n"
    "# =============================================================================\n"
)


# ----------------------------------------------------------------- caricamento
def load_model() -> tuple[dict, dict]:
    house = yaml.safe_load((INV / "house.yaml").read_text(encoding="utf-8"))
    devices = yaml.safe_load((INV / "devices.yaml").read_text(encoding="utf-8"))
    return house, devices


# ----------------------------------------------------------------- validazione
def validate(house: dict, devices: dict) -> list[str]:
    err: list[str] = []
    floors = [f["id"] for f in house.get("piani", [])]
    areas = [a["id"] for a in house.get("aree", [])]
    zones = [z["id"] for z in house.get("zone_termiche", [])]
    labels = [lb["id"] for lb in house.get("etichette", [])]

    for kind, ids in (("piano", floors), ("area", areas), ("zona", zones), ("etichetta", labels)):
        for i in ids:
            if not SLUG.match(i):
                err.append(f"{kind} '{i}': id non valido (usa [a-z0-9_])")
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            err.append(f"{kind}: id duplicati {sorted(dup)}")
    if set(floors) & set(areas):
        err.append(f"id condivisi tra piani e aree: {sorted(set(floors) & set(areas))}")
    for lb in labels:
        if not lb.startswith("hi_"):
            err.append(f"etichetta '{lb}': deve iniziare con 'hi_'")

    for a in house.get("aree", []):
        if a.get("piano") is not None and a["piano"] not in floors:
            err.append(f"area '{a['id']}': piano '{a['piano']}' inesistente")
        pl = a.get("planimetria")
        if pl:
            for k in ("x", "y", "w", "h"):
                if not isinstance(pl.get(k), (int, float)):
                    err.append(f"area '{a['id']}': planimetria.{k} mancante")
            if pl.get("x", 0) + pl.get("w", 0) > 100 or pl.get("y", 0) + pl.get("h", 0) > 100:
                err.append(f"area '{a['id']}': rettangolo planimetria oltre il 100%")

    for z in house.get("zone_termiche", []):
        if z.get("piano") not in floors:
            err.append(f"zona '{z['id']}': piano '{z.get('piano')}' inesistente")
        for f in z.get("fonti", []):
            if f not in ("pavimento", "radiatori", "pompa_di_calore"):
                err.append(f"zona '{z['id']}': fonte '{f}' non prevista")
        if len([f for f in z.get("fonti", []) if f in IDRONICHE]) > 1:
            err.append(f"zona '{z['id']}': al massimo una fonte idronica (pavimento o radiatori)")
        for lb in (f"hi_temp_{z['id']}", f"hi_pdc_{z['id']}", f"hi_termostato_{z['id']}",
                   f"hi_finestra_{z['id']}", f"hi_umidita_{z['id']}"):
            if lb not in labels:
                err.append(f"zona '{z['id']}': manca l'etichetta '{lb}' in house.yaml")
        p = z.get("predefiniti", {})
        for k in ("comfort", "eco", "raffrescamento", "idro_min_on", "idro_min_off", "inerzia_ore"):
            if not isinstance(p.get(k), (int, float)):
                err.append(f"zona '{z['id']}': predefiniti.{k} mancante")
        for k in ("feriali", "festivi"):
            for kk in ("inizio", "fine"):
                if not re.match(r"^\d{2}:\d{2}$", str(p.get(k, {}).get(kk, ""))):
                    err.append(f"zona '{z['id']}': predefiniti.{k}.{kk} non in formato HH:MM")

    for p in house.get("persone", []) or []:
        if not re.match(r"^person\.[a-z0-9_]+$", str(p)):
            err.append(f"persona '{p}': deve essere un entity_id person.*")

    ids = []
    for d in devices.get("dispositivi", []):
        did = d.get("id", "?")
        ids.append(did)
        if d.get("stato") not in STATI:
            err.append(f"dispositivo '{did}': stato '{d.get('stato')}' non valido {sorted(STATI)}")
        if d.get("area") is not None and d["area"] not in areas:
            err.append(f"dispositivo '{did}': area '{d['area']}' inesistente")
        for lb in d.get("etichette", []) or []:
            if lb not in labels:
                err.append(f"dispositivo '{did}': etichetta '{lb}' non definita in house.yaml")
        ent = d.get("entita", []) or []
        for e in ent:
            if not re.match(r"^[a-z_]+\.[a-z0-9_]+$", str(e)):
                err.append(f"dispositivo '{did}': entity_id '{e}' non valido")
                continue
            is_sim = e.split(".", 1)[1].startswith("sim_")
            if d.get("stato") == "simulazione" and not is_sim:
                err.append(f"dispositivo '{did}': entità simulata '{e}' senza prefisso sim_")
            if d.get("stato") != "simulazione" and is_sim:
                err.append(f"dispositivo '{did}': entità reale '{e}' con prefisso sim_ (vietato)")
        if d.get("stato") == "simulazione" and "hi_simulazione" not in (d.get("etichette") or []):
            err.append(f"dispositivo '{did}': manca l'etichetta hi_simulazione")
        if d.get("stato") == "reale" and not ent:
            err.append(f"dispositivo '{did}': stato 'reale' ma nessuna entità indicata")
        for e, lbs in (d.get("ruoli") or {}).items():
            if e not in ent:
                err.append(f"dispositivo '{did}': ruolo per entità '{e}' non elencata in 'entita'")
            for lb in lbs:
                if lb not in labels:
                    err.append(f"dispositivo '{did}': etichetta di ruolo '{lb}' non definita")
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        err.append(f"dispositivi: id duplicati {sorted(dup)}")
    all_ent = [e for d in devices.get("dispositivi", []) for e in (d.get("entita") or [])]
    dup = {e for e in all_ent if all_ent.count(e) > 1}
    if dup:
        err.append(f"entità assegnate a più dispositivi: {sorted(dup)}")
    return err


# ------------------------------------------------------------------ generazione
def _q(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def gen_aree(house: dict) -> str:
    out = [HEADER, "# Sensori aggregati per area (luci accese, temperatura, occupazione).\n",
           "# Usano area_entities(): ogni dispositivo assegnato all'area viene\n",
           "# considerato automaticamente, senza modificare questo file.\n\ntemplate:\n"]
    for a in house["aree"]:
        i, n = a["id"], a["nome"]
        out.append(f"""  # --- {n} ({i}) ---
  - binary_sensor:
      - name: {_q('Luci · ' + n)}
        unique_id: hi_area_{i}_luci
        default_entity_id: binary_sensor.hi_area_{i}_luci
        device_class: light
        icon: "{{{{ 'mdi:lightbulb-on' if this.state == 'on' else 'mdi:lightbulb-outline' }}}}"
        state: >
          {{% set l = (area_entities('{i}') | select('match', 'light\\\\.') | list
                      + area_entities('{i}') | select('in', label_entities('hi_luce')) | list) | unique | list %}}
          {{{{ l | select('is_state', 'on') | list | count > 0 }}}}
        attributes:
          accese: >
            {{% set l = (area_entities('{i}') | select('match', 'light\\\\.') | list
                        + area_entities('{i}') | select('in', label_entities('hi_luce')) | list) | unique | list %}}
            {{{{ l | select('is_state', 'on') | list | count }}}}
          totali: >
            {{{{ (area_entities('{i}') | select('match', 'light\\\\.') | list
                 + area_entities('{i}') | select('in', label_entities('hi_luce')) | list) | unique | list | count }}}}
      - name: {_q('Occupazione · ' + n)}
        unique_id: hi_area_{i}_occupata
        default_entity_id: binary_sensor.hi_area_{i}_occupata
        device_class: occupancy
        state: >
          {{% set ns = namespace(l=[]) %}}
          {{% for e in area_entities('{i}') | select('match', 'binary_sensor\\\\.') %}}
            {{% if state_attr(e, 'device_class') in ['motion', 'occupancy', 'presence'] %}}{{% set ns.l = ns.l + [e] %}}{{% endif %}}
          {{% endfor %}}
          {{{{ ns.l | select('is_state', 'on') | list | count > 0 }}}}
        availability: >
          {{% set ns = namespace(l=[]) %}}
          {{% for e in area_entities('{i}') | select('match', 'binary_sensor\\\\.') %}}
            {{% if state_attr(e, 'device_class') in ['motion', 'occupancy', 'presence'] %}}{{% set ns.l = ns.l + [e] %}}{{% endif %}}
          {{% endfor %}}
          {{{{ ns.l | reject('is_state', ['unavailable', 'unknown']) | list | count > 0 }}}}
  - sensor:
      - name: {_q('Temperatura · ' + n)}
        unique_id: hi_area_{i}_temperatura
        default_entity_id: sensor.hi_area_{i}_temperatura
        device_class: temperature
        unit_of_measurement: "°C"
        state_class: measurement
        state: >
          {{% set v = area_entities('{i}') | select('match', 'sensor\\\\.')
             | select('is_state_attr', 'device_class', 'temperature') | map('states') | select('is_number') | map('float') | list %}}
          {{{{ (v | sum / v | count) | round(1) if v | count > 0 else none }}}}
        availability: >
          {{{{ area_entities('{i}') | select('match', 'sensor\\\\.') | select('is_state_attr', 'device_class', 'temperature')
             | map('states') | select('is_number') | list | count > 0 }}}}
""")
    return "".join(out)


def gen_zone(house: dict) -> str:
    zones = house["zone_termiche"]
    o = [HEADER, "# Zone termiche: helper, misure aggregate, supervisore, attuazione.\n\n"]
    # ---- helper
    o.append("input_select:\n")
    for z in zones:
        i, n = z["id"], z["nome"]
        tipo_idro = idro(z)[0] or "idronico"
        o.append(f"""  hi_clima_modo_{i}:
    name: {_q('Clima ' + n + ' – modalità')}
    icon: mdi:thermostat-auto
    options: [automatico, comfort, eco, manuale, spento]
  hi_clima_fonte_{i}:
    name: {_q('Clima ' + n + ' – fonte preferita')}
    icon: mdi:heat-wave
    options: [auto, {tipo_idro}, pompa_di_calore]
""")
    o.append("\ninput_number:\n")
    for z in zones:
        i, n = z["id"], z["nome"]
        for key, label, mn, mx, ic in (("comfort", "comfort", 16, 24, "mdi:sofa"),
                                        ("eco", "eco", 14, 22, "mdi:leaf"),
                                        ("raffrescamento", "raffrescamento", 22, 30, "mdi:snowflake")):
            o.append(f"""  hi_clima_{i}_{key}:
    name: {_q('Setpoint ' + label + ' ' + n)}
    min: {mn}
    max: {mx}
    step: 0.5
    unit_of_measurement: "°C"
    icon: {ic}
    mode: box
""")
        nid = idro(z)[1]
        o.append(f"""  hi_clima_{i}_idro_min_on:
    name: {_q(nid + ' ' + n + ' – tempo minimo acceso')}
    min: 0
    max: 360
    step: 5
    unit_of_measurement: min
    icon: mdi:timer-outline
    mode: box
  hi_clima_{i}_idro_min_off:
    name: {_q(nid + ' ' + n + ' – tempo minimo spento')}
    min: 0
    max: 360
    step: 5
    unit_of_measurement: min
    icon: mdi:timer-off-outline
    mode: box
  hi_clima_{i}_inerzia_ore:
    name: {_q(nid + ' ' + n + ' – compensazione inerzia (0 = off)')}
    min: 0
    max: 4
    step: 0.25
    unit_of_measurement: h
    icon: mdi:weight
    mode: box
""")
    o.append("\ninput_boolean:\n")
    for z in zones:
        i, n = z["id"], z["nome"]
        o.append(f"""  hi_clima_override_{i}:
    name: {_q('Override manuale ' + n)}
    icon: mdi:hand-back-right
  hi_clima_attuazione_pdc_{i}:
    name: {_q('Consenso comando pompa di calore ' + n)}
    icon: mdi:heat-pump
  hi_clima_attuazione_pavimento_{i}:
    name: {_q('Consenso comando termostato ' + n + ' (' + idro(z)[1].lower() + ')')}
    icon: mdi:heating-coil
""")
    o.append("\ninput_text:\n")
    for z in zones:
        o.append(f"""  hi_clima_{z['id']}_comandato:
    name: {_q('Ultimo comando clima ' + z['nome'])}
    max: 255
""")
    o.append("\ninput_datetime:\n")
    for z in zones:
        for g, gn in (("feriali", "feriali"), ("festivi", "sabato/festivi")):
            for k in ("inizio", "fine"):
                o.append(f"""  hi_clima_{z['id']}_{g}_{k}:
    name: {_q('Comfort ' + z['nome'] + ' ' + gn + ' – ' + k)}
    has_date: false
    has_time: true
""")
    o.append("\ntimer:\n")
    for z in zones:
        o.append(f"""  hi_clima_override_{z['id']}:
    name: {_q('Scadenza override ' + z['nome'])}
    restore: true
    icon: mdi:timer-sand
""")
    # ---- derivative
    o.append("\nsensor:\n")
    for z in zones:
        o.append(f"""  - platform: derivative
    source: sensor.hi_{z['id']}_temperatura
    name: hi_{z['id']}_variazione
    unique_id: hi_{z['id']}_variazione
    unit_time: h
    time_window: "00:30:00"
    round: 2
""")
    o.append("\nhomeassistant:\n  customize:\n")
    for z in zones:
        o.append(f"    sensor.hi_{z['id']}_variazione:\n      friendly_name: {_q('Variazione temperatura ' + z['nome'])}\n      icon: mdi:chart-line-variant\n")
    # ---- template
    o.append("\ntemplate:\n")
    for z in zones:
        i, n = z["id"], z["nome"]
        fonti = "[" + ", ".join(f"'{x}'" for x in z.get("fonti", [])) + "]"
        o.append(f"""  # =========================== ZONA {n.upper()} ===========================
  - sensor:
      - name: {_q('Temperatura ' + n)}
        unique_id: hi_{i}_temperatura
        default_entity_id: sensor.hi_{i}_temperatura
        unit_of_measurement: "°C"
        device_class: temperature
        state_class: measurement
        state: "{{% from 'hi_common.jinja' import hi_media %}}{{{{ hi_media('hi_temp_{i}') }}}}"
        availability: "{{% from 'hi_common.jinja' import hi_media %}}{{{{ hi_media('hi_temp_{i}') | is_number }}}}"
        attributes:
          sensori_validi: "{{% from 'hi_common.jinja' import hi_validi %}}{{{{ hi_validi('hi_temp_{i}') }}}}"
          sensori: "{{% from 'hi_common.jinja' import hi_ruolo %}}{{{{ hi_ruolo('hi_temp_{i}') | from_json }}}}"
      - name: {_q('Umidità ' + n)}
        unique_id: hi_{i}_umidita
        default_entity_id: sensor.hi_{i}_umidita
        unit_of_measurement: "%"
        device_class: humidity
        state_class: measurement
        state: "{{% from 'hi_common.jinja' import hi_media %}}{{{{ hi_media('hi_umidita_{i}', 0) }}}}"
        availability: "{{% from 'hi_common.jinja' import hi_media %}}{{{{ hi_media('hi_umidita_{i}', 0) | is_number }}}}"
      - name: {_q('Setpoint effettivo ' + n)}
        unique_id: hi_{i}_setpoint
        default_entity_id: sensor.hi_{i}_setpoint
        unit_of_measurement: "°C"
        device_class: temperature
        # Niente "variables" qui: nelle entità a stato le variabili non
        # registrano le dipendenze e il sensore non si aggiornerebbe.
        state: "{{% from 'hi_clima.jinja' import hi_setpoint_zona %}}{{{{ (hi_setpoint_zona('{i}') | from_json).setpoint }}}}"
        availability: "{{% from 'hi_clima.jinja' import hi_setpoint_zona %}}{{{{ (hi_setpoint_zona('{i}') | from_json).setpoint is number }}}}"
        attributes:
          origine: "{{% from 'hi_clima.jinja' import hi_setpoint_zona %}}{{{{ (hi_setpoint_zona('{i}') | from_json).origine }}}}"
  - binary_sensor:
      - name: {_q('Finestre aperte ' + n)}
        unique_id: hi_{i}_finestra
        default_entity_id: binary_sensor.hi_{i}_finestra
        device_class: window
        # Ritardo: brevi aperture non interrompono la climatizzazione.
        delay_on: {{minutes: 2}}
        state: "{{% from 'hi_common.jinja' import hi_qualcuno_on %}}{{{{ hi_qualcuno_on('hi_finestra_{i}') == 'on' }}}}"
      - name: {_q('Scostamento manuale ' + n)}
        unique_id: hi_{i}_scostamento
        default_entity_id: binary_sensor.hi_{i}_scostamento
        icon: mdi:hand-back-right-outline
        # on se un'unità comandata dal sistema è stata modificata dall'esterno
        # (app Daikin, telecomando, termostato). Valutato solo con attuazione
        # attiva e almeno 15 minuti dopo l'ultimo comando (polling cloud).
        state: >
          {{% from 'hi_common.jinja' import hi_disponibili %}}
          {{% set c = states('input_text.hi_clima_{i}_comandato') %}}
          {{% set c = c | from_json if c.startswith('{{') else {{}} %}}
          {{% set ts = c.get('ts') | as_datetime if c.get('ts') else none %}}
          {{% set ns = namespace(dev=false) %}}
          {{% if ts is not none and (now() - ts).total_seconds() > 900 %}}
            {{% for e in hi_disponibili('hi_pdc_{i}') | from_json if c.get('pdc') in ['heat', 'cool', 'off'] %}}
              {{% if states(e) != c.pdc %}}{{% set ns.dev = true %}}
              {{% elif c.pdc != 'off' and c.t is number and ((state_attr(e, 'temperature') | float(0)) - c.t) | abs > 0.6 %}}{{% set ns.dev = true %}}{{% endif %}}
            {{% endfor %}}
            {{% for e in hi_disponibili('hi_termostato_{i}') | from_json if c.get('pav') in ['on', 'off'] %}}
              {{% set atteso = c.t if c.pav == 'on' else c.tb %}}
              {{% if atteso is number and ((state_attr(e, 'temperature') | float(0)) - atteso) | abs > 0.6 %}}{{% set ns.dev = true %}}{{% endif %}}
            {{% endfor %}}
          {{% endif %}}
          {{{{ ns.dev }}}}
  # Supervisore: rivalutato ogni minuto e a ogni variazione degli ingressi.
  - triggers:
      - trigger: time_pattern
        minutes: "/1"
      - trigger: state
        entity_id:
          - sensor.hi_{i}_temperatura
          - sensor.hi_{i}_setpoint
          - input_select.hi_clima_stagione
          - input_select.hi_clima_modo_{i}
          - input_select.hi_clima_fonte_{i}
          - input_boolean.hi_clima_override_{i}
          - binary_sensor.hi_{i}_finestra
          - binary_sensor.hi_centrale_disponibile
    sensor:
      - name: {_q('Supervisore ' + n)}
        unique_id: hi_{i}_supervisore
        default_entity_id: sensor.hi_{i}_supervisore
        icon: mdi:brain
        variables:
          r: "{{% from 'hi_clima.jinja' import hi_decidi_zona %}}{{{{ hi_decidi_zona('{i}', 'sensor.hi_{i}_supervisore', {fonti}) | from_json }}}}"
        state: "{{{{ r.stato }}}}"
        attributes:
          pav: "{{{{ r.pav }}}}"
          pdc: "{{{{ r.pdc }}}}"
          motivo: "{{{{ r.motivo }}}}"
          errore: "{{{{ r.errore }}}}"
          attesa: "{{{{ r.attesa }}}}"
          primaria: "{{{{ r.primaria }}}}"
          pav_ultimo: "{{{{ r.pav_ultimo }}}}"
          pav_dal: "{{{{ r.pav_dal }}}}"
          pdc_ultimo: "{{{{ r.pdc_ultimo }}}}"
          pdc_dal: "{{{{ r.pdc_dal }}}}"
          temperatura: "{{{{ r.temperatura }}}}"
          setpoint: "{{{{ r.setpoint }}}}"
          esterna: "{{{{ r.esterna }}}}"
          variazione: "{{{{ r.variazione }}}}"
          pav_disponibile: "{{{{ r.pav_disponibile }}}}"
          pdc_disponibile: "{{{{ r.pdc_disponibile }}}}"
          fonti_previste: "{{{{ {fonti} }}}}"
""")
    # ---- automazioni
    o.append("\nautomation:\n")
    for z in zones:
        i, n = z["id"], z["nome"]
        o.append(f"""  # =========================== ZONA {n.upper()} ===========================
  - id: hi_clima_attuazione_{i}
    alias: {_q('HI · Clima · Attuazione ' + n)}
    description: >-
      Applica le decisioni del supervisore. Non fa nulla finché il consenso
      generale e i consensi per fonte sono disattivati (impostazione predefinita).
    mode: queued
    max: 3
    triggers:
      - trigger: state
        entity_id: sensor.hi_{i}_supervisore
        attribute: pav_ultimo
      - trigger: state
        entity_id: sensor.hi_{i}_supervisore
        attribute: pdc_ultimo
      - trigger: state
        entity_id:
          - input_boolean.hi_clima_controllo_automatico
          - input_boolean.hi_clima_attuazione_pdc_{i}
          - input_boolean.hi_clima_attuazione_pavimento_{i}
        to: "on"
      - trigger: state
        entity_id: sensor.hi_{i}_setpoint
        not_from: [unknown, unavailable]
        not_to: [unknown, unavailable]
    conditions:
      - condition: state
        entity_id: input_boolean.hi_clima_controllo_automatico
        state: "on"
      - condition: state
        entity_id: binary_sensor.hi_sistema_pronto
        state: "on"
      - condition: template
        value_template: "{{{{ states('sensor.hi_{i}_supervisore') not in ['unknown', 'unavailable', 'manuale', 'sicurezza_sensore'] }}}}"
    actions:
      - action: script.hi_clima_attua
        data:
          zona: {i}
          pav: "{{{{ state_attr('sensor.hi_{i}_supervisore', 'pav') }}}}"
          pdc: "{{{{ state_attr('sensor.hi_{i}_supervisore', 'pdc') }}}}"

  - id: hi_clima_rileva_manuale_{i}
    alias: {_q('HI · Clima · Rileva intervento manuale ' + n)}
    mode: single
    triggers:
      - trigger: state
        entity_id: binary_sensor.hi_{i}_scostamento
        to: "on"
        for: {{minutes: 2}}
    conditions:
      - condition: state
        entity_id: input_boolean.hi_clima_override_{i}
        state: "off"
    actions:
      - action: input_boolean.turn_on
        target: {{entity_id: input_boolean.hi_clima_override_{i}}}
      - action: script.hi_notifica
        data:
          livello: info
          id: hi_clima_manuale_{i}
          titolo: {_q('Clima ' + n + ': intervento manuale')}
          messaggio: >-
            Rilevata una modifica manuale. Il controllo automatico è sospeso per
            {{{{ states('input_number.hi_clima_override_ore') }}}} ore.

  - id: hi_clima_override_avvio_{i}
    alias: {_q('HI · Clima · Override avviato ' + n)}
    mode: restart
    triggers:
      - trigger: state
        entity_id: input_boolean.hi_clima_override_{i}
        from: "off"
        to: "on"
    actions:
      - action: timer.start
        target: {{entity_id: timer.hi_clima_override_{i}}}
        data:
          duration: "{{{{ (states('input_number.hi_clima_override_ore') | float(3) * 3600) | int }}}}"

  - id: hi_clima_override_fine_{i}
    alias: {_q('HI · Clima · Override terminato ' + n)}
    mode: single
    triggers:
      - trigger: event
        event_type: timer.finished
        event_data: {{entity_id: timer.hi_clima_override_{i}}}
      - trigger: state
        entity_id: input_boolean.hi_clima_override_{i}
        to: "off"
    actions:
      - action: input_boolean.turn_off
        target: {{entity_id: input_boolean.hi_clima_override_{i}}}
      - action: timer.cancel
        target: {{entity_id: timer.hi_clima_override_{i}}}

  - id: hi_clima_allarme_{i}
    alias: {_q('HI · Clima · Temperatura fuori limiti ' + n)}
    mode: single
    max_exceeded: silent
    triggers:
      - trigger: template
        value_template: >
          {{% set t = states('sensor.hi_{i}_temperatura') %}}
          {{{{ t | is_number and (t | float < states('input_number.hi_clima_allarme_min') | float(12)
              or t | float > states('input_number.hi_clima_allarme_max') | float(30)) }}}}
        for: {{minutes: 30}}
    actions:
      - action: script.hi_notifica
        data:
          livello: importante
          id: hi_clima_allarme_{i}
          titolo: {_q('Temperatura fuori limiti: ' + n)}
          messaggio: "{{{{ states('sensor.hi_{i}_temperatura') }}}} °C (limiti {{{{ states('input_number.hi_clima_allarme_min') }}}}–{{{{ states('input_number.hi_clima_allarme_max') }}}} °C)."
      - delay: {{hours: 2}}

""")
    # ---- script predefiniti
    o.append("script:\n  hi_inizializza_zone:\n    alias: HI · Clima · Predefiniti zone\n    mode: single\n    sequence:\n")
    for z in zones:
        i = z["id"]
        p = z["predefiniti"]
        o.append(f"""      # {z['nome']}
      - action: input_select.select_option
        target: {{entity_id: input_select.hi_clima_modo_{i}}}
        data: {{option: automatico}}
      - action: input_select.select_option
        target: {{entity_id: input_select.hi_clima_fonte_{i}}}
        data: {{option: auto}}
      - action: input_boolean.turn_off
        target:
          entity_id:
            - input_boolean.hi_clima_override_{i}
            - input_boolean.hi_clima_attuazione_pdc_{i}
            - input_boolean.hi_clima_attuazione_pavimento_{i}
      - action: input_number.set_value
        target: {{entity_id: input_number.hi_clima_{i}_comfort}}
        data: {{value: {p['comfort']}}}
      - action: input_number.set_value
        target: {{entity_id: input_number.hi_clima_{i}_eco}}
        data: {{value: {p['eco']}}}
      - action: input_number.set_value
        target: {{entity_id: input_number.hi_clima_{i}_raffrescamento}}
        data: {{value: {p['raffrescamento']}}}
      - action: input_number.set_value
        target: {{entity_id: input_number.hi_clima_{i}_idro_min_on}}
        data: {{value: {p['idro_min_on']}}}
      - action: input_number.set_value
        target: {{entity_id: input_number.hi_clima_{i}_idro_min_off}}
        data: {{value: {p['idro_min_off']}}}
      - action: input_number.set_value
        target: {{entity_id: input_number.hi_clima_{i}_inerzia_ore}}
        data: {{value: {p['inerzia_ore']}}}
""")
        for g in ("feriali", "festivi"):
            for k in ("inizio", "fine"):
                o.append(f"""      - action: input_datetime.set_datetime
        target: {{entity_id: input_datetime.hi_clima_{i}_{g}_{k}}}
        data: {{time: "{p[g][k]}:00"}}
""")
    return "".join(o)


def floorplan_svg(house: dict, piano: dict) -> str:
    W = house["planimetria"]["larghezza"]
    H = house["planimetria"]["altezza"]
    prov = house["planimetria"].get("stato") != "definitiva"
    rects = []
    for a in house["aree"]:
        if a.get("piano") != piano["id"] or not a.get("planimetria"):
            continue
        p = a["planimetria"]
        x, y, w, h = p["x"] * W / 100, p["y"] * H / 100, p["w"] * W / 100, p["h"] * H / 100
        rects.append(
            f'  <g class="room"><rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" rx="14"/>'
            f'<text x="{x + 18:.0f}" y="{y + 36:.0f}" class="name">{a["nome"]}</text>'
            + (f'<text x="{x + 18:.0f}" y="{y + 60:.0f}" class="hint">provvisoria</text>' if a.get("provvisoria") else "")
            + "</g>"
        )
    watermark = (
        f'  <text x="{W - 20}" y="{H - 16}" class="wm" text-anchor="end">'
        "PLANIMETRIA PROVVISORIA · schema non in scala · sostituibile</text>\n" if prov else ""
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- GENERATO da scripts/hi_tool.py: {piano['nome']}. Planimetria schematica provvisoria. -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <style>
    .bg {{ fill: #f4f5f7; }}
    .room rect {{ fill: #ffffff; stroke: #c5cad3; stroke-width: 3; }}
    .name {{ font: 600 26px system-ui, -apple-system, Segoe UI, Roboto, sans-serif; fill: #3a4150; }}
    .hint {{ font: italic 18px system-ui, sans-serif; fill: #9aa1ad; }}
    .wm {{ font: 600 16px system-ui, sans-serif; fill: #b0563a; letter-spacing: 1px; }}
  </style>
  <rect class="bg" x="0" y="0" width="{W}" height="{H}" rx="20"/>
{chr(10).join(rects)}
{watermark}</svg>
"""


def _yaml(obj) -> str:
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=100)


def gen_view_piano(house: dict, devices: dict, piano: dict) -> str:
    aree = [a for a in house["aree"] if a.get("piano") == piano["id"]]
    img = f"/local/floorplans/{piano['immagine']}" if piano.get("immagine") else f"/local/floorplans/{piano['id']}.svg"
    elements = []
    for a in aree:
        p = a.get("planimetria")
        if not p:
            continue
        cx, cy = p["x"] + p["w"] / 2, p["y"] + p["h"] / 2
        elements += [
            {"type": "state-icon", "entity": f"binary_sensor.hi_area_{a['id']}_luci",
             "style": {"left": f"{cx:.1f}%", "top": f"{cy:.1f}%", "--mdc-icon-size": "38px"},
             "tap_action": {"action": "perform-action", "perform_action": "script.hi_area_luci_commuta",
                            "data": {"area": a["id"]}},
             "hold_action": {"action": "more-info"}},
            {"type": "conditional",
             "conditions": [{"entity": f"sensor.hi_area_{a['id']}_temperatura", "state_not": "unavailable"}],
             "elements": [{"type": "state-label", "entity": f"sensor.hi_area_{a['id']}_temperatura",
                           "style": {"left": f"{cx:.1f}%", "top": f"{cy + 11:.1f}%", "font-size": "15px",
                                     "font-weight": "600", "color": "#3a4150"}}]},
            {"type": "state-icon", "entity": f"binary_sensor.hi_area_{a['id']}_occupata",
             "style": {"left": f"{p['x'] + p['w'] - 5:.1f}%", "top": f"{p['y'] + 8:.1f}%"}},
        ]
    zona = next((z for z in house["zone_termiche"] if z["piano"] == piano["id"]), None)
    sections = [{
        "type": "grid",
        "column_span": 2,
        "cards": [
            {"type": "heading", "heading": f"{piano['nome']} · planimetria",
             "heading_style": "title", "icon": piano.get("icona", "mdi:floor-plan")},
            {"type": "markdown",
             "content": ("{% if is_state('binary_sensor.hi_ambiente_simulazione','on') %}"
                         "<ha-alert alert-type=\"warning\">Ambiente di <b>SIMULAZIONE</b>: le entità [SIM] sono virtuali.</ha-alert>"
                         "{% endif %}"
                         + ("<ha-alert alert-type=\"info\">Planimetria <b>provvisoria</b> e ambienti da confermare. "
                            "Tocca la lampadina per accendere/spegnere le luci dell'ambiente.</ha-alert>"
                            if house["planimetria"].get("stato") != "definitiva" else ""))},
            {"type": "picture-elements", "image": img, "elements": elements},
        ],
    }]
    if zona:
        sections[0]["cards"].append({
            "type": "tile", "entity": f"sensor.hi_{zona['id']}_supervisore", "name": f"Clima {zona['nome']}",
            "tap_action": {"action": "navigate", "navigation_path": "/home-intelligence/clima"},
        })
    for a in aree:
        sections.append({
            "type": "grid",
            "cards": [
                {"type": "heading", "heading": a["nome"] + (" (provvisoria)" if a.get("provvisoria") else ""),
                 "heading_style": "subtitle", "icon": a.get("icona", "mdi:texture-box")},
                {"type": "area", "area": a["id"], "display_type": "compact",
                 "alert_classes": ["moisture", "motion", "window", "door"],
                 "sensor_classes": ["temperature", "humidity"],
                 "features": [{"type": "area-controls"}],
                 "features_position": "inline",
                 "navigation_path": f"/config/areas/area/{a['id']}"},
            ],
        })
    view = {"title": piano["nome"], "path": f"casa-{piano['id']}", "icon": piano.get("icona"),
            "subview": True, "back_path": "/home-intelligence/casa", "type": "sections",
            "max_columns": 3, "sections": sections}
    return HEADER + _yaml(view)


def _climate_entities(devices: dict, label: str) -> tuple[list[str], list[str]]:
    real, sim = [], []
    for d in devices["dispositivi"]:
        for e in d.get("entita") or []:
            labels = list(d.get("etichette") or []) + list((d.get("ruoli") or {}).get(e, []))
            if label in labels and e.startswith("climate."):
                if d["stato"] == "simulazione":
                    sim.append(e)
                elif d["stato"] == "reale":
                    real.append(e)
    return real, sim


def gen_view_clima(house: dict, devices: dict) -> str:
    sections = [{
        "type": "grid",
        "cards": [
            {"type": "heading", "heading": "Impostazioni generali", "heading_style": "title", "icon": "mdi:tune"},
            {"type": "tile", "entity": "input_select.hi_clima_stagione", "name": "Stagione",
             "features": [{"type": "select-options"}], "features_position": "bottom"},
            {"type": "tile", "entity": "input_select.hi_profilo_energia", "name": "Profilo",
             "features": [{"type": "select-options"}], "features_position": "bottom"},
            {"type": "tile", "entity": "sensor.hi_temperatura_esterna", "name": "Esterna"},
            {"type": "tile", "entity": "binary_sensor.hi_centrale_disponibile", "name": "Caldaia condominiale"},
            {"type": "entities", "title": "Riscaldamento condominiale", "state_color": True, "entities": [
                {"entity": "input_boolean.hi_centrale_vincolo_orari", "name": "Considera gli orari"},
                {"entity": "input_datetime.hi_centrale_inizio", "name": "Accensione"},
                {"entity": "input_datetime.hi_centrale_fine", "name": "Spegnimento"}]},
            {"type": "tile", "entity": "input_boolean.hi_clima_controllo_automatico",
             "name": "Controllo automatico (consenso generale)", "icon": "mdi:shield-lock-open",
             "tap_action": {"action": "more-info"}},
            {"type": "markdown", "content": (
                "{% if is_state('input_boolean.hi_clima_controllo_automatico','off') %}"
                "<ha-alert alert-type=\"info\">Il supervisore calcola le decisioni ma <b>non comanda</b> "
                "i dispositivi: l'attuazione è disattivata.</ha-alert>{% else %}"
                "<ha-alert alert-type=\"warning\">Attuazione <b>abilitata</b> per le fonti con consenso attivo.</ha-alert>{% endif %}")},
        ],
    }]
    for z in house["zone_termiche"]:
        i, n = z["id"], z["nome"]
        cards = [
            {"type": "heading", "heading": n, "heading_style": "title", "icon": "mdi:home-thermometer",
             "badges": [{"type": "entity", "entity": f"sensor.hi_{i}_umidita", "show_state": True, "show_icon": True},
                        {"type": "entity", "entity": f"binary_sensor.hi_{i}_finestra", "show_state": False,
                         "show_icon": True, "visibility": [{"condition": "state", "entity": f"binary_sensor.hi_{i}_finestra", "state": "on"}]}]},
            {"type": "tile", "entity": f"sensor.hi_{i}_temperatura", "name": "Temperatura"},
            {"type": "tile", "entity": f"sensor.hi_{i}_setpoint", "name": "Setpoint effettivo"},
            {"type": "markdown", "content": (
                f"{{% set s = 'sensor.hi_{i}_supervisore' %}}"
                "**Supervisore:** `{{ states(s) }}`  \n"
                "Pavimento: **{{ state_attr(s,'pav') }}** · Pompa di calore: **{{ state_attr(s,'pdc') }}**  \n"
                "<small>{{ state_attr(s,'motivo') }}"
                f"{{% if has_value('sensor.hi_{i}_setpoint') %}} · origine setpoint: {{{{ state_attr('sensor.hi_{i}_setpoint','origine') }}}}{{% endif %}}</small>")},
            {"type": "tile", "entity": f"input_select.hi_clima_modo_{i}", "name": "Modalità zona",
             "features": [{"type": "select-options"}], "features_position": "bottom"},
            {"type": "tile", "entity": f"input_select.hi_clima_fonte_{i}", "name": "Fonte preferita",
             "features": [{"type": "select-options"}], "features_position": "bottom"},
            {"type": "tile", "entity": f"input_boolean.hi_clima_override_{i}", "name": "Override manuale",
             "tap_action": {"action": "toggle"}},
            {"type": "tile", "entity": f"timer.hi_clima_override_{i}", "name": "Scadenza override",
             "visibility": [{"condition": "state", "entity": f"input_boolean.hi_clima_override_{i}", "state": "on"}]},
        ]
        nid = idro(z)[1]
        for lab, title in ((f"hi_pdc_{i}", "Pompa di calore"), (f"hi_termostato_{i}", f"Termostato ({nid.lower()})")):
            real, sim = _climate_entities(devices, lab)
            for e in real:
                cards.append({"type": "thermostat", "entity": e, "name": title,
                              "features": [{"type": "climate-hvac-modes"}]})
            for e in sim:
                cards.append({"type": "thermostat", "entity": e, "name": f"[SIM] {title}",
                              "visibility": [{"condition": "state", "entity": "binary_sensor.hi_ambiente_simulazione", "state": "on"}]})
            if not real:
                cards.append({"type": "markdown",
                              "visibility": [{"condition": "state", "entity": "binary_sensor.hi_ambiente_simulazione", "state": "off"}],
                              "content": f"<ha-alert alert-type=\"info\">{title}: <b>non ancora disponibile</b> "
                                         f"(nessun dispositivo reale con etichetta <code>{lab}</code>).</ha-alert>"})
        cards.append({"type": "entities", "title": "Programma e setpoint", "state_color": True, "entities": [
            f"input_number.hi_clima_{i}_comfort", f"input_number.hi_clima_{i}_eco",
            f"input_number.hi_clima_{i}_raffrescamento",
            f"input_datetime.hi_clima_{i}_feriali_inizio", f"input_datetime.hi_clima_{i}_feriali_fine",
            f"input_datetime.hi_clima_{i}_festivi_inizio", f"input_datetime.hi_clima_{i}_festivi_fine",
            {"type": "section", "label": f"{nid}: parametri"},
            f"input_number.hi_clima_{i}_idro_min_on", f"input_number.hi_clima_{i}_idro_min_off",
            f"input_number.hi_clima_{i}_inerzia_ore"]})
        cards.append({"type": "entities", "title": "Consensi all'attuazione", "state_color": True, "entities": [
            {"entity": f"input_boolean.hi_clima_attuazione_pdc_{i}", "name": "Comando pompa di calore"},
            {"entity": f"input_boolean.hi_clima_attuazione_pavimento_{i}", "name": f"Comando termostato ({nid.lower()})"},
            {"entity": f"input_text.hi_clima_{i}_comandato", "name": "Ultimo comando"}]})
        cards.append({"type": "history-graph", "title": "Ultime 24 ore", "hours_to_show": 24, "entities": [
            {"entity": f"sensor.hi_{i}_temperatura", "name": "Temperatura"},
            {"entity": f"sensor.hi_{i}_setpoint", "name": "Setpoint"},
            {"entity": f"sensor.hi_{i}_supervisore", "name": "Decisione"}]})
        sections.append({"type": "grid", "cards": cards})
    sections.append({
        "type": "grid",
        "cards": [
            {"type": "heading", "heading": "Parametri del supervisore", "heading_style": "subtitle", "icon": "mdi:cog"},
            {"type": "entities", "state_color": True, "entities": [
                "input_number.hi_clima_isteresi", "input_number.hi_clima_soglia_boost",
                "input_number.hi_clima_pdc_min_on", "input_number.hi_clima_pdc_min_off",
                "input_number.hi_clima_pdc_min_esterna", "input_number.hi_clima_boost_dopo_min",
                "input_number.hi_clima_variazione_min",
                {"type": "section", "label": "Setpoint globali"},
                "input_number.hi_clima_assenza", "input_number.hi_clima_vacanza",
                "input_number.hi_clima_raffr_assenza", "input_number.hi_clima_pavimento_setback",
                {"type": "section", "label": "Sicurezza e allarmi"},
                "input_number.hi_clima_t_min_sicurezza", "input_number.hi_clima_t_max_sicurezza",
                "input_number.hi_clima_allarme_min", "input_number.hi_clima_allarme_max",
                "input_number.hi_clima_override_ore"]},
        ],
    })
    view = {"title": "Clima", "path": "clima", "icon": "mdi:thermostat", "type": "sections",
            "max_columns": 3, "sections": sections}
    return HEADER + _yaml(view)


def gen_view_persone(house: dict) -> str:
    persone = house.get("persone") or []
    cards = [{"type": "heading", "heading": "Presenza", "heading_style": "title", "icon": "mdi:account-group"},
             {"type": "tile", "entity": "sensor.hi_occupazione", "name": "Occupazione"},
             {"type": "tile", "entity": "sensor.hi_persone_in_casa", "name": "Persone in casa"}]
    for p in persone:
        cards.append({"type": "tile", "entity": p})
    cards.append({"type": "markdown", "content": (
        "{% set pp = states.person | list %}"
        "{% if pp | count == 0 %}<ha-alert alert-type=\"info\">Nessuna persona configurata. "
        "Installa la Companion App e associa il telefono in Impostazioni → Persone.</ha-alert>"
        "{% else %}| Persona | Stato | Aggiornato |\n|---|---|---|\n"
        "{% for p in pp %}| {{ p.name }} | {{ 'In casa' if p.state == 'home' else ('Fuori' if p.state == 'not_home' else p.state) }} "
        "| {{ relative_time(p.last_changed) }} fa |\n{% endfor %}{% endif %}"
        "{% set ob = state_attr('sensor.hi_persone_in_casa','tracker_obsoleti') or [] %}"
        "{% if ob | count > 0 %}\n<ha-alert alert-type=\"warning\">Posizione non aggiornata: {{ ob | join(', ') }}</ha-alert>{% endif %}")})
    impostazioni = [{"type": "heading", "heading": "Impostazioni presenza", "heading_style": "subtitle", "icon": "mdi:cog"},
                    {"type": "tile", "entity": "input_select.hi_presenza_override", "name": "Override presenza",
                     "features": [{"type": "select-options"}], "features_position": "bottom"},
                    {"type": "tile", "entity": "input_boolean.hi_ospiti", "name": "Ospiti in casa",
                     "tap_action": {"action": "toggle"}},
                    {"type": "entities", "entities": ["input_number.hi_assenza_ritardo_min",
                                                      "input_number.hi_tracker_obsoleto_ore",
                                                      "input_boolean.hi_prepara_arrivo",
                                                      "binary_sensor.hi_presenza_supplementare"]},
                    {"type": "markdown", "content": (
                        "<small>La posizione è usata solo per le funzioni domotiche ed è visibile solo agli utenti "
                        "di questa istanza. Ogni persona può disattivare la localizzazione dalla Companion App.</small>")}]
    sections = [{"type": "grid", "cards": cards}, {"type": "grid", "cards": impostazioni}]
    if persone:
        sections.append({"type": "grid", "column_span": 2, "cards": [
            {"type": "map", "entities": persone, "hours_to_show": 0, "default_zoom": 13, "theme_mode": "auto"}]})
    view = {"title": "Persone", "path": "persone", "icon": "mdi:account-group", "type": "sections",
            "max_columns": 3, "sections": sections}
    return HEADER + _yaml(view)


def gen_view_casa(house: dict) -> str:
    cards = [{"type": "heading", "heading": "Piani", "heading_style": "title", "icon": "mdi:floor-plan"}]
    for p in sorted(house["piani"], key=lambda x: x.get("livello", 0)):
        aree = [a for a in house["aree"] if a.get("piano") == p["id"]]
        cards.append({
            "type": "markdown",
            "content": (f"## {p['nome']}\n"
                        + " · ".join(
                            f"{a['nome']} {{{{ '💡' if is_state('binary_sensor.hi_area_{a['id']}_luci','on') else '' }}}}"
                            f"{{{{ ' ' ~ states('sensor.hi_area_{a['id']}_temperatura') ~ '°' if has_value('sensor.hi_area_{a['id']}_temperatura') else '' }}}}"
                            for a in aree)),
        })
        cards.append({"type": "button", "name": f"Apri {p['nome']}", "icon": p.get("icona", "mdi:floor-plan"),
                      "show_state": False, "tap_action": {"action": "navigate",
                                                           "navigation_path": f"/home-intelligence/casa-{p['id']}"}})
    altre = [a for a in house["aree"] if not a.get("piano")]
    sec2 = [{"type": "heading", "heading": "Altre aree", "heading_style": "subtitle", "icon": "mdi:texture-box"}]
    for a in altre:
        sec2.append({"type": "area", "area": a["id"], "display_type": "compact",
                     "sensor_classes": ["temperature", "humidity"], "features": [{"type": "area-controls"}],
                     "features_position": "inline"})
    sec3 = [{"type": "heading", "heading": "Luci accese", "heading_style": "subtitle", "icon": "mdi:lightbulb-group"},
            {"type": "markdown", "content": (
                "{% set accese = (states.light | selectattr('state','eq','on') | map(attribute='entity_id') | list"
                " + label_entities('hi_luce') | select('is_state','on') | list) | unique | list %}"
                "{% if accese | count == 0 %}Tutte le luci sono spente.{% else %}"
                "{% for e in accese %}- {{ state_attr(e,'friendly_name') }}"
                "{% if area_name(e) %} · <small>{{ area_name(e) }}</small>{% endif %}\n{% endfor %}{% endif %}")},
            {"type": "button", "name": "Spegni luci e carichi non essenziali", "icon": "mdi:power",
             "tap_action": {"action": "perform-action", "perform_action": "script.hi_spegni_non_essenziali",
                            "confirmation": {"text": "Spegnere tutte le luci e i carichi non essenziali?"}}}]
    view = {"title": "Casa", "path": "casa", "icon": "mdi:floor-plan", "type": "sections", "max_columns": 3,
            "sections": [{"type": "grid", "cards": cards}, {"type": "grid", "cards": sec3},
                         {"type": "grid", "cards": sec2}]}
    return HEADER + _yaml(view)


def generate(house: dict, devices: dict) -> list[Path]:
    GEN_PKG.mkdir(parents=True, exist_ok=True)
    GEN_DASH.mkdir(parents=True, exist_ok=True)
    FLOORPLANS.mkdir(parents=True, exist_ok=True)
    files: dict[Path, str] = {
        GEN_PKG / "hi_aree.yaml": gen_aree(house),
        GEN_PKG / "hi_zone.yaml": gen_zone(house),
        GEN_DASH / "vista_casa.yaml": gen_view_casa(house),
        GEN_DASH / "vista_clima.yaml": gen_view_clima(house, devices),
        GEN_DASH / "vista_persone.yaml": gen_view_persone(house),
    }
    for p in house["piani"]:
        files[GEN_DASH / f"vista_piano_{p['id']}.yaml"] = gen_view_piano(house, devices, p)
        files[FLOORPLANS / f"{p['id']}.svg"] = floorplan_svg(house, p)
    # dashboard principale: elenco ordinato delle viste
    piani = sorted(house["piani"], key=lambda x: x.get("livello", 0))
    files[HA / "dashboards" / "home_intelligence.yaml"] = (
        HEADER + "# Dashboard principale Home Intelligence (modalità YAML).\n"
        "# Viste scritte a mano: dashboards/views/ · viste generate: dashboards/generated/\n\n"
        "title: Home Intelligence\n"
        "views:\n"
        "  - !include views/home.yaml\n"
        "  - !include generated/vista_casa.yaml\n"
        + "".join(f"  - !include generated/vista_piano_{p['id']}.yaml\n" for p in piani)
        + "  - !include generated/vista_clima.yaml\n"
        "  - !include views/energia.yaml\n"
        "  - !include generated/vista_persone.yaml\n"
        "  - !include views/automazioni.yaml\n"
        "  - !include views/diagnostica.yaml\n")
    # rimuove file generati obsoleti (piani eliminati)
    for old in list(GEN_DASH.glob("vista_piano_*.yaml")) + list(FLOORPLANS.glob("*.svg")):
        if old not in files and old.read_text(encoding="utf-8", errors="ignore").find("GENERATO") >= 0:
            old.unlink()
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    return list(files)


# ------------------------------------------------------------------- documenti
def docs(house: dict, devices: dict) -> Path:
    stato_lbl = {"reale": "🟢 reale", "non_disponibile": "⚪ non disponibile", "simulazione": "🟣 simulazione"}
    aree = {a["id"]: a["nome"] for a in house["aree"]}
    rows = ["# Registro dispositivi\n",
            "> File generato da `scripts/hi_tool.py docs` a partire da `inventory/devices.yaml`.\n",
            "> Per aggiungere o aggiornare un dispositivo modifica il file YAML e rigenera.\n",
            "\n| Dispositivo | Stato | Tipo | Marca / modello | Integrazione | Area | Etichette | Entità |",
            "\n|---|---|---|---|---|---|---|---|"]
    for d in devices["dispositivi"]:
        mm = " ".join(x for x in (d.get("marca"), d.get("modello")) if x) or "_da fornire_"
        rows.append(
            f"\n| {d['nome']} | {stato_lbl.get(d['stato'], d['stato'])} | {d.get('tipo', '')} | {mm} | "
            f"{d.get('integrazione', '')} | {aree.get(d.get('area'), '—')} | "
            f"{', '.join('`' + x + '`' for x in d.get('etichette') or [])} | "
            f"{'<br>'.join('`' + x + '`' for x in d.get('entita') or []) or '—'} |")
    rows.append("\n\n## Note di configurazione\n")
    for d in devices["dispositivi"]:
        if d.get("note"):
            rows.append(f"\n- **{d['nome']}**: {d['note'].strip()}")
        if d.get("monitoraggio") or d.get("comando"):
            rows.append(f"\n  - monitoraggio: {', '.join(d.get('monitoraggio') or []) or '—'}; "
                        f"comando: {', '.join(d.get('comando') or []) or '—'}")
    path = ROOT / "docs" / "registro-dispositivi.md"
    path.write_text("".join(rows) + "\n", encoding="utf-8")
    return path


# ------------------------------------------------------------------------ sync
class WS:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/").replace("http", "ws", 1) + "/api/websocket"
        self.token = token
        self.i = 0

    async def __aenter__(self):
        import websockets  # dipendenza: pip install websockets
        self.c = await websockets.connect(self.url, max_size=2**25)
        await self.c.recv()
        await self.c.send(json.dumps({"type": "auth", "access_token": self.token}))
        r = json.loads(await self.c.recv())
        if r.get("type") != "auth_ok":
            raise SystemExit(f"Autenticazione fallita: {r}")
        return self

    async def __aexit__(self, *a):
        await self.c.close()

    async def call(self, typ: str, **kw):
        self.i += 1
        await self.c.send(json.dumps({"id": self.i, "type": typ, **kw}))
        while True:
            r = json.loads(await self.c.recv())
            if r.get("id") == self.i:
                if not r.get("success"):
                    raise RuntimeError(f"{typ}: {r.get('error')}")
                return r.get("result")


async def _sync(house: dict, devices: dict, url: str, token: str, profilo: str, apply: bool) -> int:
    act = "APPLICO" if apply else "DRY-RUN"
    warnings = 0
    async with WS(url, token) as ws:
        floors = {f["floor_id"]: f for f in await ws.call("config/floor_registry/list")}
        areas = {a["area_id"]: a for a in await ws.call("config/area_registry/list")}
        labels = {lb["label_id"]: lb for lb in await ws.call("config/label_registry/list")}
        ents = {e["entity_id"]: e for e in await ws.call("config/entity_registry/list")}

        async def ensure(kind, reg, wanted_id, fields, create_type, update_type, id_key):
            nonlocal warnings
            if wanted_id in reg:
                cur = reg[wanted_id]
                diff = {k: v for k, v in fields.items() if cur.get(k) != v}
                if diff:
                    print(f"[{act}] {kind} {wanted_id}: aggiorno {diff}")
                    if apply:
                        try:
                            await ws.call(update_type, **{id_key: wanted_id}, **diff)
                        except RuntimeError as e:
                            warnings += 1
                            print(f"  ! {kind} {wanted_id}: aggiornamento non riuscito ({e})")
                return
            print(f"[{act}] {kind} {wanted_id}: creo ({fields.get('name')})")
            if apply:
                # crea con nome = id per ottenere l'id desiderato, poi rinomina
                base = {k: v for k, v in fields.items() if v is not None}
                r = await ws.call(create_type, **{**base, "name": wanted_id})
                if r[id_key] != wanted_id:
                    print(f"  ! id ottenuto '{r[id_key]}' diverso da '{wanted_id}'")
                try:
                    await ws.call(update_type, **{id_key: r[id_key]},
                                  **{k: v for k, v in fields.items() if v is not None})
                except RuntimeError as e:
                    warnings += 1
                    print(f"  ! {kind} {wanted_id}: impossibile impostare {fields} ({e}).\n"
                          f"    Probabile nome già usato da un elemento esistente: rinominalo o eliminalo "
                          f"dall'interfaccia e riesegui sync.")

        for p in house["piani"]:
            await ensure("piano", floors, p["id"], {"name": p["nome"], "level": p.get("livello"),
                                                     "icon": p.get("icona")},
                         "config/floor_registry/create", "config/floor_registry/update", "floor_id")
        for a in house["aree"]:
            await ensure("area", areas, a["id"], {"name": a["nome"], "floor_id": a.get("piano"),
                                                   "icon": a.get("icona")},
                         "config/area_registry/create", "config/area_registry/update", "area_id")
        for lb in house["etichette"]:
            await ensure("etichetta", labels, lb["id"], {"name": lb["nome"], "icon": lb.get("icona"),
                                                          "color": lb.get("colore"),
                                                          "description": lb.get("descrizione")},
                         "config/label_registry/create", "config/label_registry/update", "label_id")

        hi_labels = {lb["id"] for lb in house["etichette"]}
        for d in devices["dispositivi"]:
            if d["stato"] == "simulazione" and profilo != "dev":
                continue
            if d["stato"] == "non_disponibile" and not d.get("entita"):
                continue
            for e in d.get("entita") or []:
                reg = ents.get(e)
                if reg is None:
                    print(f"  ! {e}: non presente nel registro entità (manca unique_id o non esiste) – salto")
                    warnings += 1
                    continue
                want = set(d.get("etichette") or []) | set((d.get("ruoli") or {}).get(e, []))
                cur = set(reg.get("labels") or [])
                # le etichette hi_* sono gestite dal modello; le altre restano
                new = (cur - hi_labels) | want
                upd = {}
                if new != cur:
                    upd["labels"] = sorted(new)
                area = d.get("area")
                if area and reg.get("area_id") != area:
                    upd["area_id"] = area
                if upd:
                    print(f"[{act}] entità {e}: {upd}")
                    if apply:
                        await ws.call("config/entity_registry/update", entity_id=e, **upd)
        if apply:
            await ws.call("call_service", domain="template", service="reload")
            print("Template ricaricati.")
    print(f"Completato ({act}), avvisi: {warnings}")
    return 0


# ------------------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sub.add_parser("generate")
    sub.add_parser("docs")
    s = sub.add_parser("sync")
    s.add_argument("--url", default=os.environ.get("HI_URL", "http://localhost:8123"))
    s.add_argument("--profilo", choices=["dev", "prod"], default=os.environ.get("HI_PROFILO", "prod"),
                   help="dev include i dispositivi simulati; prod li esclude")
    s.add_argument("--apply", action="store_true", help="applica le modifiche (default: dry-run)")
    a = ap.parse_args()

    house, devices = load_model()
    errors = validate(house, devices)
    if errors:
        print("ERRORI nel modello:")
        for e in errors:
            print("  -", e)
        return 1
    if a.cmd == "validate":
        print("Modello valido: "
              f"{len(house['piani'])} piani, {len(house['aree'])} aree, {len(house['zone_termiche'])} zone, "
              f"{len(house['etichette'])} etichette, {len(devices['dispositivi'])} dispositivi.")
        return 0
    if a.cmd == "generate":
        for p in generate(house, devices):
            print("generato", p.relative_to(ROOT))
        print("generato", docs(house, devices).relative_to(ROOT))
        return 0
    if a.cmd == "docs":
        print("generato", docs(house, devices).relative_to(ROOT))
        return 0
    if a.cmd == "sync":
        token = os.environ.get("HI_TOKEN")
        if not token:
            print("Imposta HI_TOKEN (token di accesso a lunga durata) nell'ambiente.")
            return 2
        return asyncio.run(_sync(house, devices, a.url, token, a.profilo, a.apply))
    return 1


if __name__ == "__main__":
    sys.exit(main())
