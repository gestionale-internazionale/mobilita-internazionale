"""Configurazione pytest.

I test di integrazione richiedono un'istanza Home Assistant REALE:
  - se HI_URL e HI_TOKEN sono impostati, usa quell'istanza (già in profilo dev);
  - altrimenti avvia un'istanza temporanea con `hass` (HASS=percorso, oppure
    dev/venv/bin/hass) in una cartella runtime temporanea, profilo dev
    (con simulazione), esegue onboarding, sync del modello e attende l'avvio.
I test statici (test_static.py) non richiedono Home Assistant.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from ha_client import HA  # noqa: E402

PORT = 8123


def _hass_bin() -> str | None:
    for c in (os.environ.get("HASS"), str(ROOT / "dev" / "venv" / "bin" / "hass"), shutil.which("hass")):
        if c and Path(c).exists():
            return c
    return None


def _link_runtime(rt: Path, profilo: str = "dev") -> None:
    subprocess.run(["bash", "-c", f'source "{ROOT}/scripts/_common.sh" && link_runtime "{rt}" {profilo}'],
                   check=True)


class Instance:
    def __init__(self):
        self.proc = None
        self.runtime: Path | None = None
        self.ha: HA | None = None
        self.hass = _hass_bin()

    def start(self):
        self._out = open(self.runtime / "hass.out", "ab")
        self.proc = subprocess.Popen([self.hass, "-c", str(self.runtime)], stdout=self._out,
                                     stderr=subprocess.STDOUT)
        self.ha.wait_up(300)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(60)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def restart(self):
        self.stop()
        time.sleep(2)
        self.start()
        self.ha.wait_for(lambda: self.ha.s("sensor.hi_versione") == "0.1.0", 120, msg="riavvio")


@pytest.fixture(scope="session")
def instance():
    inst = Instance()
    url, token = os.environ.get("HI_URL"), os.environ.get("HI_TOKEN")
    if url and token:
        inst.ha = HA(url, token)
        yield inst
        return
    if not inst.hass:
        pytest.skip("Home Assistant non disponibile (imposta HASS o esegui scripts/dev-up.sh venv)")
    inst.runtime = Path(tempfile.mkdtemp(prefix="hi-test-"))
    _link_runtime(inst.runtime, "dev")
    inst.ha = HA(f"http://localhost:{PORT}")
    inst.start()
    time.sleep(3)
    inst.ha.onboard()
    # l'onboarding crea aree predefinite (Soggiorno, Cucina, …): rimosse per il test
    for a in inst.ha.ws("config/area_registry/list"):
        inst.ha.ws("config/area_registry/delete", area_id=a["area_id"])
    token = inst.ha.long_lived_token()
    inst.ha.token = token
    env = dict(os.environ, HI_TOKEN=token, HI_URL=inst.ha.url)
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "hi_tool.py"), "sync", "--profilo", "dev", "--apply"],
                       env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    inst.ha.wait_for(lambda: inst.ha.s("sensor.hi_ruoli_configurati") not in (None, "0", "unknown"), 60,
                     msg="ruoli configurati")
    yield inst
    inst.stop()
    log = inst.runtime / "home-assistant.log"
    if log.exists():
        dest = ROOT / "tests" / "report"
        dest.mkdir(exist_ok=True)
        shutil.copy(log, dest / "home-assistant.log")
    shutil.rmtree(inst.runtime, ignore_errors=True)


@pytest.fixture(scope="session")
def ha(instance) -> HA:
    return instance.ha


@pytest.fixture(scope="session")
def pronto(ha):
    """Sistema pronto (attesa post-avvio azzerata) per i test di attuazione."""
    ha.call("input_number", "set_value", entity_id="input_number.hi_avvio_attesa_min", value=0)
    ha.wait_for(lambda: ha.s("binary_sensor.hi_sistema_pronto") == "on", 75, msg="sistema pronto")
    return ha
