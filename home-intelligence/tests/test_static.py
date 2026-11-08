"""Test statici: non richiedono Home Assistant in esecuzione.

Verificano struttura, coerenza del modello, file generati aggiornati,
separazione simulazione/produzione, assenza di segreti e riferimenti corretti.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
HA_DIR = ROOT / "homeassistant"
spec = importlib.util.spec_from_file_location("hi_tool", ROOT / "scripts" / "hi_tool.py")
hi_tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hi_tool)


# ----------------------------------------------------------- loader YAML minimo
class Loader(yaml.SafeLoader):
    pass


def _include(loader, node):
    p = Path(loader.name).parent / loader.construct_scalar(node)
    return load(p)


def _dir_named(loader, node):
    d = Path(loader.name).parent / loader.construct_scalar(node)
    return {f.stem: load(f) for f in sorted(d.rglob("*.yaml"))}


def _dir_merge_named(loader, node):
    d = Path(loader.name).parent / loader.construct_scalar(node)
    out = {}
    for f in sorted(d.rglob("*.yaml")):
        out.update(load(f) or {})
    return out


Loader.add_constructor("!include", _include)
Loader.add_constructor("!include_dir_named", _dir_named)
Loader.add_constructor("!include_dir_merge_named", _dir_merge_named)
Loader.add_constructor("!secret", lambda loader, node: "SECRET")


def load(path: Path):
    with open(path, encoding="utf-8") as fh:
        loader = Loader(fh)
        loader.name = str(path)
        try:
            return loader.get_single_data()
        finally:
            loader.dispose()


PROD_PACKAGES = sorted(p for p in (HA_DIR / "packages").rglob("*.yaml") if "zz_simulazione" not in p.parts)


# ------------------------------------------------------------------------ test
def test_yaml_validi():
    files = list(HA_DIR.rglob("*.yaml")) + list((ROOT / "inventory").glob("*.yaml")) + \
        list((ROOT / "simulations").rglob("*.yaml"))
    assert files
    for f in files:
        if "zz_simulazione" in f.parts:
            continue
        load(f)


def test_configurazione_principale_include_dashboard():
    cfg = load(HA_DIR / "configuration.yaml")
    assert "packages" in cfg["homeassistant"]
    dash = load(HA_DIR / "dashboards" / "home_intelligence.yaml")
    paths = [v["path"] for v in dash["views"]]
    for p in ("home", "casa", "clima", "energia", "persone", "automazioni", "diagnostica"):
        assert p in paths, f"vista {p} mancante"
    assert len(paths) == len(set(paths)), "path di vista duplicati"


def test_modello_valido():
    house, devices = hi_tool.load_model()
    assert hi_tool.validate(house, devices) == []


def test_file_generati_aggiornati():
    """I file generati devono corrispondere al modello (eseguire `hi_tool.py generate`)."""
    house, devices = hi_tool.load_model()
    attesi = {
        HA_DIR / "packages/generated/hi_aree.yaml": hi_tool.gen_aree(house),
        HA_DIR / "packages/generated/hi_zone.yaml": hi_tool.gen_zone(house),
        HA_DIR / "dashboards/generated/vista_clima.yaml": hi_tool.gen_view_clima(house, devices),
        HA_DIR / "dashboards/generated/vista_casa.yaml": hi_tool.gen_view_casa(house),
        HA_DIR / "dashboards/generated/vista_persone.yaml": hi_tool.gen_view_persone(house),
    }
    for p in house["piani"]:
        attesi[HA_DIR / f"dashboards/generated/vista_piano_{p['id']}.yaml"] = hi_tool.gen_view_piano(house, devices, p)
        attesi[HA_DIR / f"www/floorplans/{p['id']}.svg"] = hi_tool.floorplan_svg(house, p)
    for path, content in attesi.items():
        assert path.read_text(encoding="utf-8") == content, f"{path.name} non aggiornato: esegui generate"


def test_validazione_rileva_errori():
    house, devices = hi_tool.load_model()
    devices = {"dispositivi": [dict(devices["dispositivi"][0], entita=["climate.sim_finto"], stato="reale")]}
    err = hi_tool.validate(house, devices)
    assert any("prefisso sim_" in e for e in err)


def test_id_automazioni_unici():
    ids = []
    for f in PROD_PACKAGES:
        data = load(f) or {}
        for a in data.get("automation", []) or []:
            assert "id" in a, f"automazione senza id in {f.name}: {a.get('alias')}"
            ids.append(a["id"])
    assert len(ids) == len(set(ids)), f"id duplicati: {[i for i in ids if ids.count(i) > 1]}"


SIM_REF = re.compile(r"\b(?:sensor|light|switch|climate|binary_sensor|input_number|input_boolean|person|"
                     r"device_tracker|script|automation)\.sim_[a-z0-9_]+")


def test_produzione_non_referenzia_simulazione():
    """I pacchetti di produzione non fanno riferimento a entità simulate, salvo
    l'interruttore che distingue i due ambienti."""
    consentiti = {"input_boolean.sim_ambiente_simulato"}
    for f in PROD_PACKAGES + list((HA_DIR / "custom_templates").glob("*.jinja")):
        refs = set(SIM_REF.findall(f.read_text(encoding="utf-8"))) - consentiti
        assert not refs, f"{f.relative_to(ROOT)} referenzia entità simulate: {refs}"


def _walk_cards(node, visibile_solo_sim=False):
    if isinstance(node, dict):
        vis = node.get("visibility") or []
        sim = visibile_solo_sim or any(
            c.get("entity") == "binary_sensor.hi_ambiente_simulazione" and c.get("state") == "on" for c in vis)
        yield node, sim
        for v in node.values():
            yield from _walk_cards(v, sim)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_cards(v, visibile_solo_sim)


def test_dashboard_entita_simulate_solo_se_simulazione_attiva():
    dash = load(HA_DIR / "dashboards" / "home_intelligence.yaml")
    for card, sim in _walk_cards(dash):
        ent = card.get("entity")
        if isinstance(ent, str) and SIM_REF.fullmatch(ent):
            assert sim, f"entità simulata {ent} visibile anche fuori dalla simulazione"


def test_pacchetto_simulazione_non_versionato():
    gi = (ROOT / ".gitignore").read_text()
    assert "homeassistant/packages/zz_simulazione/" in gi
    r = subprocess.run(["git", "ls-files", "homeassistant/packages/zz_simulazione"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.stdout.strip() == "", "il pacchetto di simulazione non deve essere nel repository"


def test_entita_simulate_marcate():
    sim = load(ROOT / "simulations" / "sim_package.yaml")
    for blocco in sim["template"]:
        for dominio, entita in blocco.items():
            for e in entita:
                assert e["name"].startswith("[SIM]"), e["name"]
                assert e["default_entity_id"].split(".")[1].startswith("sim_"), e["default_entity_id"]
    for c in sim["climate"]:
        assert c["name"].startswith("[SIM]") and c["unique_id"].startswith("sim_")
    for k, v in sim["input_boolean"].items():
        assert k.startswith("sim_") and v["name"].startswith("[SIM]")


SEGRETI = [
    re.compile(r"^\s*(latitude|longitude|elevation)\s*:\s*-?\d", re.M),
    re.compile(r"-?\d{1,2}\.\d{5,}\s*,\s*-?\d{1,3}\.\d{5,}"),           # coppie di coordinate
    re.compile(r"(api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{12,}", re.I),
    re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"),         # JWT
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.(?:com|it|org|net|eu|io|me|info)\b"),  # e-mail
]
ESCLUSI_SEGRETI = {"tests/ha_client.py", "tests/test_static.py"}


def test_nessun_segreto_nel_repository():
    r = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, capture_output=True, text=True)
    for rel in r.stdout.split():
        if rel in ESCLUSI_SEGRETI or not (ROOT / rel).is_file():
            continue
        if Path(rel).suffix not in {".yaml", ".yml", ".py", ".sh", ".md", ".jinja", ".json", ".svg", ".txt", ""}:
            continue
        txt = (ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        for rx in SEGRETI:
            m = rx.search(txt)
            assert not m, f"possibile dato sensibile in {rel}: {m.group(0)[:40]!r}"


LABEL_CALL = re.compile(r"(?:label_entities|hi_ruolo|hi_media|hi_validi|hi_potenza_w|hi_energia_kwh|"
                        r"hi_percentuale|hi_qualcuno_on|hi_disponibili|hi_comandabili)\(\s*'([a-z0-9_]+)'\s*[,)]")


def test_etichette_referenziate_esistono():
    house, _ = hi_tool.load_model()
    labels = {lb["id"] for lb in house["etichette"]}
    files = PROD_PACKAGES + list((HA_DIR / "custom_templates").glob("*.jinja")) + \
        list((HA_DIR / "dashboards").rglob("*.yaml"))
    for f in files:
        for lb in LABEL_CALL.findall(f.read_text(encoding="utf-8")):
            assert lb in labels, f"{f.name}: etichetta '{lb}' non definita in house.yaml"


def test_pavimento_mai_in_raffrescamento():
    """Nel codice di attuazione del pavimento non compare mai la modalità cool."""
    txt = (HA_DIR / "packages" / "hi_clima.yaml").read_text(encoding="utf-8")
    blocco = txt.split("# --- Pavimento radiante")[1].split("# --- Registro")[0]
    assert "cool" not in blocco
    assert "hvac_mode: heat" in blocco


def test_attuazione_protetta_da_consensi():
    data = load(HA_DIR / "packages" / "hi_clima.yaml")
    seq = yaml.safe_dump(data["script"]["hi_clima_attua"])
    for k in ("hi_clima_controllo_automatico", "hi_clima_attuazione_pdc_", "hi_clima_attuazione_pavimento_",
              "binary_sensor.hi_sistema_pronto"):
        assert k in seq
    zone = load(HA_DIR / "packages" / "generated" / "hi_zone.yaml")
    init = yaml.safe_dump(zone["script"]["hi_inizializza_zone"])
    assert "input_boolean.turn_off" in init and "hi_clima_attuazione_pdc_" in init


@pytest.mark.parametrize("vista", sorted((HA_DIR / "dashboards" / "views").glob("*.yaml")))
def test_viste_sections(vista):
    v = load(vista)
    assert v.get("type") == "sections" and v.get("sections"), vista.name
