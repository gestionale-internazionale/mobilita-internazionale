"""Test di integrazione contro un'istanza Home Assistant REALE in profilo dev
(pacchetto di simulazione caricato). Verificano il comportamento effettivo di
helper, template, automazioni e script, non una loro imitazione.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

import pytest

SIM_LUCI = ["light.sim_luce_giorno", "light.sim_luce_cucina", "light.sim_luce_ingresso",
            "light.sim_luce_mansarda", "light.sim_luce_notte"]


def on(ha, *ids):
    ha.call("homeassistant", "turn_on", entity_id=list(ids))


def off(ha, *ids):
    ha.call("homeassistant", "turn_off", entity_id=list(ids))


def persona(ha, n: int, dove: str):
    ha.call("script", "sim_persona_entra" if dove == "home" else "sim_persona_esce", n=n)
    ha.wait_for(lambda: ha.s(f"person.sim_persona_{n}") == dove, 15, msg=f"persona {n} {dove}")


def imposta_modo(ha, modo):
    ha.call("script", "hi_imposta_modo", modo=modo, origine="test")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") == modo, 10, msg=f"modo {modo}")


@pytest.fixture(autouse=True)
def stato_base(ha):
    """Condizioni iniziali note prima di ogni test."""
    ha.call("input_select", "select_option", entity_id="input_select.hi_presenza_override", option="automatico")
    off(ha, "input_boolean.hi_ospiti", "input_boolean.sim_movimento_ingresso_stato",
        "input_boolean.sim_guasto_sensore_inferiore", "input_boolean.sim_guasto_sensore_mansarda",
        "input_boolean.sim_finestra_mansarda_stato", "input_boolean.hi_clima_controllo_automatico",
        "input_boolean.hi_clima_override_inferiore", "input_boolean.hi_clima_override_mansarda",
        "input_boolean.sim_fisica_attiva")
    on(ha, "input_boolean.sim_ambiente_simulato", "input_boolean.hi_automazioni_attive")
    ha.call("input_number", "set_value", entity_id="input_number.hi_assenza_ritardo_min", value=0)
    yield


# ---------------------------------------------------------------- struttura
def test_entita_principali(ha):
    for e in ["input_select.hi_modo_casa", "sensor.hi_occupazione", "sensor.hi_inferiore_supervisore",
              "sensor.hi_mansarda_supervisore", "sensor.hi_en_pv_potenza", "script.hi_scenario_buonanotte",
              "binary_sensor.hi_sistema_pronto", "sensor.hi_entita_offline", "counter.hi_errori_automazioni",
              "timer.hi_clima_override_inferiore", "binary_sensor.hi_area_inferiore_salotto_luci"]:
        assert ha.state(e) is not None, f"manca {e}"


def test_log_senza_errori_di_configurazione(ha):
    """Nessun errore di configurazione/template nel log di sistema."""
    righe = ha.ws("system_log/list")
    errori = [r for r in righe if r["level"] in ("ERROR", "CRITICAL")
              and any(k in r["name"] for k in ("template", "automation", "script", "config", "setup", "lovelace"))
              and "sim_persona" not in json.dumps(r["message"])]
    assert not errori, json.dumps(errori, ensure_ascii=False)[:2000]


def test_dashboard_carica_e_riferimenti_validi(ha):
    cfg = ha.ws("lovelace/config", url_path="home-intelligence")
    assert len(cfg["views"]) >= 8
    esistenti = {s["entity_id"] for s in ha.states()}
    trovati = set()

    def walk(n):
        if isinstance(n, dict):
            for k, v in n.items():
                if k in ("entity", "entity_id") and isinstance(v, str) and "." in v:
                    trovati.add(v)
                elif k == "entities" and isinstance(v, list):
                    for x in v:
                        if isinstance(x, str):
                            trovati.add(x)
                walk(v)
        elif isinstance(n, list):
            for x in n:
                walk(x)
    walk(cfg)
    mancanti = sorted(e for e in trovati if e not in esistenti)
    assert not mancanti, f"entità referenziate dalla dashboard ma inesistenti: {mancanti}"


def test_modello_sincronizzato(ha):
    piani = {f["floor_id"] for f in ha.ws("config/floor_registry/list")}
    aree = {a["area_id"]: a for a in ha.ws("config/area_registry/list")}
    assert {"piano_inferiore", "mansarda"} <= piani
    assert aree["inferiore_salotto"]["floor_id"] == "piano_inferiore"
    assert aree["inferiore_salotto"]["name"] == "Salotto"
    etichette = {lb["label_id"] for lb in ha.ws("config/label_registry/list")}
    assert {"hi_luce", "hi_critico", "hi_pdc_inferiore", "hi_simulazione"} <= etichette


# --------------------------------------------------- separazione sim / reale
def test_ruoli_risolti_solo_con_entita_simulate(ha):
    r = json.loads(ha.template("{% from 'hi_common.jinja' import hi_ruolo %}{{ hi_ruolo('hi_pdc_inferiore') }}"))
    assert r == ["climate.sim_daikin_inferiore"]
    assert ha.s("binary_sensor.hi_ambiente_simulazione") == "on"


def test_disattivando_simulazione_nessun_dato_fittizio(ha):
    off(ha, "input_boolean.sim_ambiente_simulato")
    try:
        ha.wait_for(lambda: ha.s("sensor.hi_inferiore_temperatura") == "unavailable", 15, msg="temp non disp.")
        assert ha.s("sensor.hi_en_pv_potenza") == "unavailable"
        r = json.loads(ha.template("{% from 'hi_common.jinja' import hi_ruolo %}{{ hi_ruolo('hi_pdc_inferiore') }}"))
        assert r == []  # nessun dispositivo reale ancora associato
        ha.wait_for(lambda: ha.s("sensor.hi_inferiore_supervisore") == "sicurezza_sensore", 15, msg="fail-safe")
        assert ha.attr("sensor.hi_inferiore_supervisore", "pav") == "invariato"
    finally:
        on(ha, "input_boolean.sim_ambiente_simulato")
    ha.wait_for(lambda: ha.s("sensor.hi_inferiore_temperatura") not in ("unavailable", None), 15, msg="ripristino")


# ------------------------------------------------------------------ presenza
def test_tutti_fuori_attiva_assente_e_spegne_carichi(pronto):
    ha = pronto
    imposta_modo(ha, "Casa")
    persona(ha, 1, "home")
    persona(ha, 2, "home")
    on(ha, "light.sim_luce_giorno", "switch.sim_presa_tv", "switch.sim_frigorifero")
    persona(ha, 1, "not_home")
    assert ha.s("sensor.hi_occupazione") == "occupata"
    persona(ha, 2, "not_home")
    ha.wait_for(lambda: ha.s("sensor.hi_occupazione") == "vuota", 15, msg="vuota")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") == "Assente", 20, msg="Assente")
    ha.wait_for(lambda: ha.s("light.sim_luce_giorno") == "off", 15, msg="luce spenta")
    assert ha.s("switch.sim_presa_tv") == "off"
    assert ha.s("switch.sim_frigorifero") == "on", "un carico critico non deve essere spento"
    # rientro
    persona(ha, 1, "home")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") in ("Casa", "Notte"), 20, msg="rientro")
    persona(ha, 2, "home")


def test_ospiti_impediscono_assente(pronto):
    ha = pronto
    imposta_modo(ha, "Casa")
    on(ha, "input_boolean.hi_ospiti")
    persona(ha, 1, "not_home")
    persona(ha, 2, "not_home")
    time.sleep(3)
    assert ha.s("sensor.hi_occupazione") == "occupata"
    assert ha.s("input_select.hi_modo_casa") == "Casa"
    persona(ha, 1, "home")
    persona(ha, 2, "home")


def test_override_presenza(pronto):
    ha = pronto
    imposta_modo(ha, "Casa")
    ha.call("input_select", "select_option", entity_id="input_select.hi_presenza_override", option="forza_presente")
    persona(ha, 1, "not_home")
    persona(ha, 2, "not_home")
    time.sleep(3)
    assert ha.s("sensor.hi_occupazione") == "occupata"
    assert ha.s("input_select.hi_modo_casa") == "Casa"
    ha.call("input_select", "select_option", entity_id="input_select.hi_presenza_override", option="forza_assente")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") == "Assente", 20, msg="forza_assente")
    persona(ha, 1, "home")
    persona(ha, 2, "home")
    ha.call("input_select", "select_option", entity_id="input_select.hi_presenza_override", option="automatico")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") in ("Casa", "Notte"), 20, msg="ritorno")


def test_movimento_impedisce_assente(pronto):
    ha = pronto
    imposta_modo(ha, "Casa")
    on(ha, "input_boolean.sim_movimento_ingresso_stato")
    persona(ha, 1, "not_home")
    persona(ha, 2, "not_home")
    time.sleep(3)
    assert ha.s("binary_sensor.hi_presenza_supplementare") == "on"
    assert ha.s("input_select.hi_modo_casa") == "Casa"
    persona(ha, 1, "home")
    persona(ha, 2, "home")


# ------------------------------------------------------------------- scenari
def test_scenario_buonanotte_e_buongiorno(pronto):
    ha = pronto
    imposta_modo(ha, "Casa")
    on(ha, *SIM_LUCI, "switch.sim_frigorifero")
    ha.call("script", "hi_scenario_buonanotte")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") == "Notte", 10, msg="Notte")
    ha.wait_for(lambda: ha.s("light.sim_luce_giorno") == "off", 10, msg="luci spente")
    assert ha.s("light.sim_luce_notte") == "on", "la luce notturna resta accesa"
    assert ha.s("switch.sim_frigorifero") == "on"
    ha.call("script", "hi_scenario_buongiorno")
    ha.wait_for(lambda: ha.s("input_select.hi_modo_casa") == "Casa", 10, msg="Casa")
    ha.wait_for(lambda: ha.s("light.sim_luce_notte") == "off", 10, msg="notturna spenta")
    assert "Buongiorno" in ha.s("input_text.hi_ultimo_scenario")


def test_scenari_ripetuti_senza_errori(pronto):
    ha = pronto
    for _ in range(3):
        ha.call("script", "turn_on", entity_id="script.hi_scenario_esco")
    ha.call("script", "hi_scenario_comfort")
    assert ha.s("input_select.hi_profilo_energia") == "comfort"
    ha.call("script", "hi_scenario_risparmio")
    assert ha.s("input_select.hi_profilo_energia") == "risparmio"
    ha.call("script", "hi_scenario_normale")
    assert ha.s("input_select.hi_profilo_energia") == "normale"


def test_scenari_vacanza_tutti_fuori_rientro(pronto):
    ha = pronto
    ha.call("script", "hi_scenario_vacanza")
    assert ha.s("input_select.hi_modo_casa") == "Vacanza"
    ha.wait_for(lambda: ha.s("sensor.hi_inferiore_setpoint") == ha.s("input_number.hi_clima_vacanza"), 10,
                msg="setpoint vacanza")
    ha.call("script", "hi_scenario_tutti_fuori")
    assert ha.s("input_select.hi_modo_casa") == "Assente"
    ha.call("script", "hi_scenario_rientro")
    assert ha.s("input_select.hi_modo_casa") in ("Casa", "Notte")


def test_commuta_luci_area_dalla_planimetria(pronto):
    ha = pronto
    off(ha, "light.sim_luce_giorno")
    ha.call("script", "hi_area_luci_commuta", area="inferiore_salotto")
    ha.wait_for(lambda: ha.s("light.sim_luce_giorno") == "on", 10, msg="accesa")
    ha.wait_for(lambda: ha.s("binary_sensor.hi_area_inferiore_salotto_luci") == "on", 10, msg="aggregato area")
    ha.call("script", "hi_area_luci_commuta", area="inferiore_salotto")
    ha.wait_for(lambda: ha.s("light.sim_luce_giorno") == "off", 10, msg="spenta")


# ---------------------------------------------------------------- clima
def _temp(ha, z, v):
    ha.call("input_number", "set_value", entity_id=f"input_number.sim_t_{z}", value=v)
    ha.wait_for(lambda: ha.s(f"sensor.hi_{z}_temperatura") == str(float(v)), 15, msg=f"temp {z}={v}")


def test_sensore_guasto_supervisore_fail_safe(ha):
    on(ha, "input_boolean.sim_guasto_sensore_inferiore")
    ha.wait_for(lambda: ha.s("sensor.hi_inferiore_supervisore") == "sicurezza_sensore", 15, msg="sicurezza")
    assert ha.attr("sensor.hi_inferiore_supervisore", "pav") == "invariato"
    assert ha.attr("sensor.hi_inferiore_supervisore", "pdc") == "invariato"
    ha.wait_for(lambda: int(ha.s("sensor.hi_entita_offline")) >= 1, 15, msg="diagnostica offline")
    assert "sensor.sim_temperatura_inferiore" in ha.attr("sensor.hi_entita_offline", "elenco")
    off(ha, "input_boolean.sim_guasto_sensore_inferiore")
    ha.wait_for(lambda: ha.s("sensor.hi_inferiore_supervisore") != "sicurezza_sensore", 15, msg="ripresa")


def test_attuazione_disattivata_non_comanda(pronto):
    ha = pronto
    ha.call("climate", "set_hvac_mode", entity_id="climate.sim_daikin_mansarda", hvac_mode="off")
    _temp(ha, "mansarda", 16.0)
    ha.wait_for(lambda: ha.attr("sensor.hi_mansarda_supervisore", "pdc") == "heat", 15, msg="decisione heat")
    time.sleep(3)
    assert ha.s("climate.sim_daikin_mansarda") == "off", "senza consenso nessun comando"


def test_attuazione_con_consensi_comanda_simulati(pronto):
    ha = pronto
    z = "inferiore"
    for e in ("input_boolean.hi_clima_attuazione_pdc_inferiore", "input_boolean.hi_clima_attuazione_pavimento_inferiore"):
        on(ha, e)
    ha.call("input_select", "select_option", entity_id="input_select.hi_clima_stagione", option="inverno")
    ha.call("input_select", "select_option", entity_id="input_select.hi_clima_modo_inferiore", option="comfort")
    _temp(ha, z, 17.0)
    ha.wait_for(lambda: ha.attr("sensor.hi_inferiore_supervisore", "pdc") == "heat", 15, msg="decisione")
    on(ha, "input_boolean.hi_clima_controllo_automatico")
    sp = float(ha.s("sensor.hi_inferiore_setpoint"))
    ha.wait_for(lambda: ha.s("climate.sim_daikin_inferiore") == "heat", 20, msg="daikin in heat")
    assert float(ha.attr("climate.sim_daikin_inferiore", "temperature")) == sp
    ha.wait_for(lambda: float(ha.attr("climate.sim_termostato_inferiore", "temperature")) == sp, 20, msg="termostato")
    comandato = json.loads(ha.s("input_text.hi_clima_inferiore_comandato"))
    assert comandato["pdc"] == "heat" and comandato["pav"] == "on"
    # override manuale: il supervisore smette di decidere, nessun nuovo comando
    on(ha, "input_boolean.hi_clima_override_inferiore")
    ha.wait_for(lambda: ha.s("sensor.hi_inferiore_supervisore") == "manuale", 15, msg="manuale")
    assert ha.s("timer.hi_clima_override_inferiore") == "active"
    _temp(ha, z, 23.0)
    time.sleep(3)
    assert ha.s("climate.sim_daikin_inferiore") == "heat", "con override non deve comandare"
    off(ha, "input_boolean.hi_clima_override_inferiore", "input_boolean.hi_clima_controllo_automatico",
        "input_boolean.hi_clima_attuazione_pdc_inferiore", "input_boolean.hi_clima_attuazione_pavimento_inferiore")
    ha.wait_for(lambda: ha.s("timer.hi_clima_override_inferiore") == "idle", 10, msg="timer annullato")
    ha.call("input_select", "select_option", entity_id="input_select.hi_clima_modo_inferiore", option="automatico")
    _temp(ha, z, 19.0)


def test_scostamento_manuale_rilevato(ha):
    vecchio = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    ha.call("climate", "set_hvac_mode", entity_id="climate.sim_daikin_mansarda", hvac_mode="heat")
    ha.call("input_text", "set_value", entity_id="input_text.hi_clima_mansarda_comandato",
            value=json.dumps({"pdc": "off", "pav": "n/d", "t": 20, "tb": 15, "ts": vecchio}))
    ha.wait_for(lambda: ha.s("binary_sensor.hi_mansarda_scostamento") == "on", 70, msg="scostamento")
    ha.call("input_text", "set_value", entity_id="input_text.hi_clima_mansarda_comandato", value="")
    ha.call("climate", "set_hvac_mode", entity_id="climate.sim_daikin_mansarda", hvac_mode="off")


def test_finestra_aperta_spegne_pdc(ha):
    _temp(ha, "mansarda", 16.5)
    on(ha, "input_boolean.sim_finestra_mansarda_stato")
    ha.wait_for(lambda: ha.s("sensor.hi_mansarda_supervisore") == "finestra_aperta", 160, msg="finestra (ritardo 2 min)")
    assert ha.attr("sensor.hi_mansarda_supervisore", "pdc") == "off"
    off(ha, "input_boolean.sim_finestra_mansarda_stato")


def test_setpoint_segue_modalita_casa(pronto):
    ha = pronto
    ha.call("input_select", "select_option", entity_id="input_select.hi_clima_stagione", option="inverno")
    imposta_modo(ha, "Assente")
    ha.wait_for(lambda: ha.s("sensor.hi_inferiore_setpoint") == ha.s("input_number.hi_clima_assenza"), 10, msg="assenza")
    assert ha.attr("sensor.hi_inferiore_setpoint", "origine") == "assenza"
    imposta_modo(ha, "Casa")


# ---------------------------------------------------------------- energia
def test_energia_bilancio_coerente(ha):
    on(ha, "input_boolean.sim_fisica_attiva")
    try:
        ha.wait_for(lambda: ha.s("sensor.hi_en_casa_potenza") not in ("unavailable", "unknown", None), 70, msg="energia")
        time.sleep(65)  # almeno un passo del modello
        v = {k: float(ha.s(f"sensor.hi_en_{k}")) for k in
             ("pv_potenza", "rete_prelievo", "rete_immissione", "batt_carica", "batt_scarica", "casa_potenza")}
        bilancio = v["pv_potenza"] + v["rete_prelievo"] - v["rete_immissione"] + v["batt_scarica"] - v["batt_carica"]
        assert abs(bilancio - v["casa_potenza"]) <= 5, v
        assert v["rete_prelievo"] == 0 or v["rete_immissione"] == 0
        assert ha.attr("sensor.hi_en_batt_soc", "unit_of_measurement") == "%"
        assert ha.attr("sensor.hi_en_pv_potenza", "unit_of_measurement") == "W"
        assert ha.attr("sensor.hi_en_pv_energia", "unit_of_measurement") == "kWh"
        assert ha.attr("sensor.hi_en_batt_residua", "device_class") == "energy_storage"
    finally:
        off(ha, "input_boolean.sim_fisica_attiva")


def test_notifica_importante(ha):
    ha.call("script", "hi_notifica", livello="importante", id="hi_test", titolo="Test", messaggio="Prova")


# ---------------------------------------------------------------- riavvio
def test_riavvio_sicuro(instance):
    """Dopo un riavvio: nessuna accensione indiscriminata, stato ripristinato,
    nessun comando durante l'attesa post-avvio."""
    ha = instance.ha
    if instance.proc is None:
        pytest.skip("istanza esterna: riavvio non gestito dal test")
    off(ha, *SIM_LUCI, "switch.sim_presa_tv")
    imposta_modo(ha, "Casa")
    ha.call("input_number", "set_value", entity_id="input_number.hi_avvio_attesa_min", value=5)
    on(ha, "input_boolean.hi_clima_controllo_automatico", "input_boolean.hi_clima_attuazione_pdc_mansarda")
    ha.call("climate", "set_hvac_mode", entity_id="climate.sim_daikin_mansarda", hvac_mode="off")
    time.sleep(2)
    pav_dal = ha.attr("sensor.hi_inferiore_supervisore", "pav_dal")
    instance.restart()
    assert ha.s("binary_sensor.hi_sistema_pronto") == "off"
    _temp(ha, "mansarda", 15.5)
    time.sleep(5)
    assert all(ha.s(e) == "off" for e in SIM_LUCI), "nessuna luce accesa dal riavvio"
    assert ha.s("switch.sim_presa_tv") == "off"
    assert ha.s("input_select.hi_modo_casa") == "Casa"
    assert ha.s("climate.sim_daikin_mansarda") == "off", "nessun comando prima di 'sistema pronto'"
    assert ha.attr("sensor.hi_inferiore_supervisore", "pav_dal") == pav_dal, "stato del supervisore ripristinato"
    off(ha, "input_boolean.hi_clima_controllo_automatico", "input_boolean.hi_clima_attuazione_pdc_mansarda")
    ha.call("input_number", "set_value", entity_id="input_number.hi_avvio_attesa_min", value=0)
