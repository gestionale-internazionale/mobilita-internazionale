"""Test della logica del supervisore termico.

Le funzioni pure (hi_decidi, hi_calcola_setpoint) vengono eseguite dal motore
template di Home Assistant REALE tramite /api/template: si testa esattamente il
codice che girerà su Green.

Gli scenari temporali (simulations/scenari_termici/*.yaml) usano un modello
fisico semplificato: verificano proprietà qualitative (assenza di oscillazioni,
rispetto dei tempi minimi, fail-safe), NON il comportamento della casa reale.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent

PAR = {"isteresi": 0.3, "soglia_boost": 1.5, "pav_min_on": 60, "pav_min_off": 60, "pdc_min_on": 20,
       "pdc_min_off": 15, "pdc_min_esterna": -15, "t_min_sic": 16, "t_max_sic": 28, "boost_dopo_min": 90,
       "variazione_min": 0.2, "inerzia_ore": 1.0}


def ingressi(**kw):
    base = {"stagione": "inverno", "modo": "automatico", "override": False, "temp": 19.0, "setpoint": 20.5,
            "variazione": None, "esterna": 5.0, "finestra": False, "fonte": "auto", "disp_pav": True,
            "disp_pdc": True, "pav_prec": "off", "pdc_prec": "off", "pav_min_da": 999, "pdc_min_da": 999,
            "par": dict(PAR)}
    base.update(kw)
    return base


def decidi(ha, **kw) -> dict:
    i = json.dumps(ingressi(**kw)).replace("'", "\\'")
    out = ha.template("{% from 'hi_clima.jinja' import hi_decidi %}"
                      "{% set i = '" + i + "' | from_json %}{{ hi_decidi(i) }}")
    return json.loads(out)


def setpoint(ha, **kw) -> dict:
    base = {"stagione": "inverno", "modo": "automatico", "modo_casa": "Casa", "profilo": "normale",
            "in_programma": True, "comfort": 20.5, "eco": 18.5, "raffrescamento": 26.0, "assenza": 17.0,
            "vacanza": 14.0, "raffr_assenza": 29.0}
    base.update(kw)
    i = json.dumps(base).replace("'", "\\'")
    return json.loads(ha.template("{% from 'hi_clima.jinja' import hi_calcola_setpoint %}"
                                  "{% set i = '" + i + "' | from_json %}{{ hi_calcola_setpoint(i) }}"))


# ================================================================ fail-safe
class TestFailSafe:
    def test_sensore_non_disponibile_nessun_comando(self, ha):
        r = decidi(ha, temp=None, pav_prec="on", pdc_prec="heat")
        assert r["stato"] == "sicurezza_sensore"
        assert r["pav"] == "invariato" and r["pdc"] == "invariato"

    def test_setpoint_non_disponibile_nessun_comando(self, ha):
        r = decidi(ha, setpoint=None)
        assert r["stato"] == "sicurezza_sensore" and r["pav"] == r["pdc"] == "invariato"

    def test_override_manuale_prevale(self, ha):
        r = decidi(ha, override=True, temp=15.0)
        assert r["stato"] == "manuale" and r["pav"] == r["pdc"] == "invariato"

    def test_modalita_manuale(self, ha):
        r = decidi(ha, modo="manuale", temp=15.0)
        assert r["stato"] == "manuale" and r["pav"] == r["pdc"] == "invariato"

    def test_sovratemperatura_spegne_subito(self, ha):
        r = decidi(ha, temp=28.5, setpoint=30, pav_prec="on", pdc_prec="heat", pav_min_da=1, pdc_min_da=1)
        assert r["stato"] == "sovratemperatura" and r["pav"] == "off" and r["pdc"] == "off"

    def test_nessuna_fonte_disponibile(self, ha):
        r = decidi(ha, disp_pav=False, disp_pdc=False, temp=15)
        assert r["stato"] == "nessuna_fonte" and r["pav"] == r["pdc"] == "invariato"

    def test_dispositivo_non_disponibile_non_comandato(self, ha):
        r = decidi(ha, disp_pdc=False, temp=15)
        assert r["pdc"] == "invariato" and r["pav"] == "on"


# =========================================================== inverno
class TestInverno:
    def test_errore_moderato_solo_pavimento(self, ha):
        r = decidi(ha, temp=19.8)  # errore 0.7
        assert (r["stato"], r["pav"], r["pdc"]) == ("riscaldamento_pavimento", "on", "off")

    def test_errore_grande_integrazione_pdc(self, ha):
        r = decidi(ha, temp=18.5)  # errore 2.0 >= soglia_boost
        assert (r["stato"], r["pav"], r["pdc"]) == ("riscaldamento_combinato", "on", "heat")

    @pytest.mark.parametrize("prec", ["on", "off"])
    def test_isteresi_mantiene_stato(self, ha, prec):
        r = decidi(ha, temp=20.4, pav_prec=prec)  # errore 0.1 < isteresi
        assert r["pav"] == prec

    def test_sopra_setpoint_spegne_pavimento(self, ha):
        r = decidi(ha, temp=20.9, pav_prec="on")
        assert r["pav"] == "off" and r["stato"] == "in_temperatura"

    def test_tempo_minimo_acceso_rispettato(self, ha):
        r = decidi(ha, temp=21.0, pav_prec="on", pav_min_da=10)
        assert r["pav"] == "on" and r["attesa"] is True

    def test_tempo_minimo_spento_rispettato(self, ha):
        r = decidi(ha, temp=19.0, pav_prec="off", pav_min_da=10)
        assert r["pav"] == "off" and r["attesa"] is True

    def test_tempo_minimo_pdc(self, ha):
        r = decidi(ha, temp=18.0, pdc_prec="off", pdc_min_da=5)
        assert r["pdc"] == "off" and r["attesa"] is True
        r = decidi(ha, temp=18.0, pdc_prec="off", pdc_min_da=16)
        assert r["pdc"] == "heat"

    def test_boost_resta_fino_a_setpoint(self, ha):
        r = decidi(ha, temp=20.0, pav_prec="on", pdc_prec="heat")  # errore 0.5: mantiene integrazione
        assert r["pdc"] == "heat"
        r = decidi(ha, temp=20.6, pav_prec="on", pdc_prec="heat")  # raggiunto
        assert r["pdc"] == "off"

    def test_salita_lenta_attiva_integrazione(self, ha):
        r = decidi(ha, temp=19.8, pav_prec="on", pav_min_da=120, variazione=0.05)
        assert r["pdc"] == "heat" and "salita lenta" in r["motivo"]
        r = decidi(ha, temp=19.8, pav_prec="on", pav_min_da=30, variazione=0.05)
        assert r["pdc"] == "off"

    def test_nome_fonte_idronica_nel_motivo(self, ha):
        r = decidi(ha, temp=19.8, nome_idro="Radiatori")
        assert r["motivo"].startswith("Radiatori come fonte di base") and r["pav"] == "on"

    def test_esterna_troppo_fredda_esclude_pdc(self, ha):
        r = decidi(ha, temp=17.0, esterna=-20, pdc_prec="heat", pdc_min_da=999)
        assert r["pdc"] == "off" and r["pav"] == "on"

    def test_esterna_sconosciuta_non_blocca(self, ha):
        r = decidi(ha, temp=17.0, esterna=None)
        assert r["pdc"] == "heat"

    def test_fonte_preferita_pdc(self, ha):
        r = decidi(ha, fonte="pompa_di_calore", temp=20.0)
        assert r["primaria"] == "pdc" and r["pdc"] == "heat" and r["pav"] == "off"

    def test_senza_pavimento_usa_pdc(self, ha):
        r = decidi(ha, disp_pav=False, temp=20.0)
        assert r["primaria"] == "pdc" and r["pdc"] == "heat" and r["pav"] == "invariato"

    def test_finestra_aperta(self, ha):
        r = decidi(ha, finestra=True, temp=18.0, pav_prec="off", pdc_prec="heat", pdc_min_da=1)
        assert r["stato"] == "finestra_aperta" and r["pdc"] == "off" and r["pav"] == "off"

    def test_cambio_stagione_immediato(self, ha):
        r = decidi(ha, temp=18.0, pdc_prec="cool", pdc_min_da=1)
        assert r["pdc"] == "heat"

    def test_spento(self, ha):
        r = decidi(ha, stagione="spento", pav_prec="on", pdc_prec="heat", pav_min_da=1)
        assert r["pav"] == "off" and r["pdc"] == "off"


# ============================================================= estate
class TestEstate:
    def test_raffresca(self, ha):
        r = decidi(ha, stagione="estate", temp=27.0, setpoint=26.0)
        assert r["pdc"] == "cool" and r["stato"] == "raffrescamento_pdc"

    @pytest.mark.parametrize("temp", [15.0, 22.0, 26.0, 30.0])
    def test_pavimento_mai_acceso(self, ha, temp):
        for prec in ("on", "off"):
            r = decidi(ha, stagione="estate", temp=temp, setpoint=26.0, pav_prec=prec, pav_min_da=1)
            assert r["pav"] != "on"

    def test_pavimento_rimasto_acceso_viene_spento(self, ha):
        r = decidi(ha, stagione="estate", temp=27, setpoint=26, pav_prec="on", pav_min_da=1)
        assert r["pav"] == "off"

    def test_sottotemperatura_spegne(self, ha):
        r = decidi(ha, stagione="estate", temp=15.5, setpoint=26.0, pdc_prec="cool", pdc_min_da=1)
        assert r["pdc"] == "off" and r["stato"] == "sottotemperatura"

    def test_mai_heat_in_estate(self, ha):
        r = decidi(ha, stagione="estate", temp=18.0, setpoint=26.0, pdc_prec="heat", pdc_min_da=1)
        assert r["pdc"] == "off"


# ============================================================ setpoint
class TestSetpoint:
    @pytest.mark.parametrize("kw,atteso", [
        ({}, 20.5),
        ({"in_programma": False}, 18.5),
        ({"modo_casa": "Notte"}, 18.5),
        ({"modo_casa": "Assente"}, 17.0),
        ({"modo_casa": "Vacanza"}, 14.0),
        ({"profilo": "comfort", "in_programma": False}, 20.5),
        ({"profilo": "risparmio"}, 18.5),
        ({"modo": "eco"}, 18.5),
        ({"modo": "comfort", "modo_casa": "Assente"}, 20.5),
        ({"stagione": "estate"}, 26.0),
        ({"stagione": "estate", "modo_casa": "Assente"}, 29.0),
        ({"stagione": "estate", "profilo": "risparmio"}, 27.0),
    ])
    def test_setpoint(self, ha, kw, atteso):
        assert setpoint(ha, **kw)["setpoint"] == atteso

    @pytest.mark.parametrize("kw", [{"modo": "manuale"}, {"modo": "spento"}, {"stagione": "spento"}])
    def test_nessun_setpoint(self, ha, kw):
        assert setpoint(ha, **kw)["setpoint"] is None


# ================================================== scenari temporali
SCENARI = sorted((ROOT / "simulations" / "scenari_termici").glob("*.yaml"))


def _sp(sc, ora):
    val = None
    for s in sc["setpoint"]:
        if ora >= s["da_ora"]:
            val = s["valore"]
    return val


def esegui_scenario(ha, sc):
    par = dict(PAR, **sc.get("parametri", {}))
    f = dict({"t_mandata": 35, "k_riscaldo": 0.5, "k_scambio": 0.4, "k_ambiente": 0.6, "k_disperso": 0.08},
             **sc.get("fisica", {}))
    passo = sc["passo_min"]
    dt = passo / 60
    t, m, est = sc["iniziale"]["t"], sc["iniziale"]["m"], sc["iniziale"]["esterna"]
    guasto = False
    pav_prec, pdc_prec, pav_da, pdc_da = "off", "off", 999.0, 999.0
    storia = []
    eventi = sorted(sc.get("eventi", []), key=lambda e: e["ora"])
    t_prec = None
    for k in range(int(sc["durata_ore"] * 60 / passo)):
        ora = k * dt
        for e in eventi:
            if abs(e["ora"] - ora) < dt / 2:
                est = e.get("esterna", est)
                if "sensore" in e:
                    guasto = e["sensore"] == "guasto"
        sp = _sp(sc, ora)
        var = None if t_prec is None else round((t - t_prec) / dt, 2)
        r = decidi(ha, stagione=sc["stagione"], fonte=sc.get("fonte", "auto"), temp=None if guasto else round(t, 1),
                   setpoint=sp, esterna=est, variazione=var, pav_prec=pav_prec, pdc_prec=pdc_prec,
                   pav_min_da=pav_da, pdc_min_da=pdc_da, par=par,
                   nome_idro=sc.get("nome_idro", "Pavimento"))
        nuovo_pav = r["pav"] if r["pav"] in ("on", "off") else pav_prec
        nuovo_pdc = r["pdc"] if r["pdc"] in ("heat", "cool", "off") else pdc_prec
        pav_da = 0.0 if nuovo_pav != pav_prec else pav_da + passo
        pdc_da = 0.0 if nuovo_pdc != pdc_prec else pdc_da + passo
        storia.append({"ora": ora, "t": t, "sp": sp, "guasto": guasto, "r": r, "pav": nuovo_pav, "pdc": nuovo_pdc})
        pav_prec, pdc_prec = nuovo_pav, nuovo_pdc
        # modello fisico: i dispositivi regolano da soli attorno al setpoint
        pav_call = 1 if (nuovo_pav == "on" and t < sp + 0.2) else 0
        pdc_heat = 1 if (nuovo_pdc == "heat" and t < sp + 0.3) else 0
        pdc_cool = 1 if (nuovo_pdc == "cool" and t > sp - 0.3) else 0
        t_prec = t
        m2 = m + dt * (f["k_riscaldo"] * (f["t_mandata"] - m) * pav_call - f["k_scambio"] * (m - t))
        t = t + dt * (f["k_ambiente"] * (m - t) + 1.5 * pdc_heat - 2.0 * pdc_cool - f["k_disperso"] * (t - est))
        m = m2
    return storia


def _commutazioni(storia, chiave):
    return sum(1 for a, b in zip(storia, storia[1:]) if a[chiave] != b[chiave])


def _durate_minime(storia, chiave, passo):
    """Durata (min) di ogni stato intermedio tra due commutazioni."""
    durate, corrente = [], 0
    for a, b in zip(storia, storia[1:]):
        corrente += passo
        if a[chiave] != b[chiave]:
            durate.append((a[chiave], corrente))
            corrente = 0
    return durate[1:]  # il primo stato non ha un inizio noto


@pytest.mark.parametrize("file", SCENARI, ids=[f.stem for f in SCENARI])
def test_scenario(ha, file):
    sc = yaml.safe_load(file.read_text(encoding="utf-8"))
    storia = esegui_scenario(ha, sc)
    PARS = dict(PAR, **sc.get("parametri", {}))
    att = sc.get("attese", {})
    passo = sc["passo_min"]
    report = ROOT / "tests" / "report"
    report.mkdir(exist_ok=True)
    (report / f"scenario_{file.stem}.csv").write_text(
        "ora;temperatura;setpoint;guasto;stato;pavimento;pompa_di_calore\n" + "".join(
            f"{h['ora']:.2f};{h['t']:.2f};{h['sp']};{int(h['guasto'])};{h['r']['stato']};{h['pav']};{h['pdc']}\n"
            for h in storia), encoding="utf-8")

    # proprietà sempre valide
    for h in storia:
        if sc["stagione"] == "estate":
            assert h["pav"] != "on", f"pavimento acceso in estate alle {h['ora']}"
            assert h["pdc"] != "heat"
        if h["guasto"]:
            assert h["r"]["pav"] == "invariato" and h["r"]["pdc"] == "invariato"
    # tempi minimi (tolleranza di un passo di campionamento)
    for stato, durata in _durate_minime(storia, "pav", passo):
        lim = PARS["pav_min_on"] if stato == "on" else PARS["pav_min_off"]
        assert durata + passo >= lim, f"pavimento {stato} per soli {durata} min"
    for stato, durata in _durate_minime(storia, "pdc", passo):
        lim = PAR["pdc_min_on"] if stato in ("heat", "cool") else PAR["pdc_min_off"]
        assert durata + passo >= lim, f"pompa di calore {stato} per soli {durata} min"

    if "max_commutazioni_pav" in att:
        assert _commutazioni(storia, "pav") <= att["max_commutazioni_pav"]
    if "max_commutazioni_pdc" in att:
        assert _commutazioni(storia, "pdc") <= att["max_commutazioni_pdc"]
    if att.get("pavimento_mai_on"):
        assert all(h["pav"] != "on" for h in storia)
    if "pdc_modo_ammesso" in att:
        assert all(h["pdc"] in att["pdc_modo_ammesso"] for h in storia)
    if att.get("pdc_usata"):
        assert any(h["pdc"] == "heat" for h in storia)
    if "errore_max_dopo_ore" in att:
        e = att["errore_max_dopo_ore"]
        for h in storia:
            if e["ore"] <= h["ora"] < e.get("fino_a", 1e9) and not h["guasto"]:
                assert abs(h["sp"] - h["t"]) <= e["max"] + 0.01, f"errore {h['sp'] - h['t']:.2f} alle {h['ora']:.1f}"
    if "motivo_contiene" in att:
        assert any(att["motivo_contiene"] in h["r"]["motivo"] for h in storia)
    if "pdc_off_dopo_ora" in att:
        assert all(h["pdc"] == "off" for h in storia if h["ora"] >= att["pdc_off_dopo_ora"] + 0.5)
