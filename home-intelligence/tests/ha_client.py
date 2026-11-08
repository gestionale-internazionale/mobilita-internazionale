"""Client minimale per i test di integrazione contro un'istanza Home Assistant
REALE (avviata con scripts/dev-up.sh o da tests/conftest.py).

Gestisce: onboarding automatico di un'istanza vuota (solo ambienti di test),
token, REST (/api/template, /api/services, /api/states) e WebSocket.
"""
from __future__ import annotations

import asyncio
import json
import time
import urllib.error
import urllib.parse
import urllib.request

CLIENT_ID = "http://localhost:8123/"


class HA:
    def __init__(self, url: str = "http://localhost:8123", token: str | None = None):
        self.url = url.rstrip("/")
        self.token = token

    # ------------------------------------------------------------------ http
    def _req(self, method: str, path: str, data=None, form: bool = False, auth: bool = True, timeout=30):
        headers = {}
        body = None
        if data is not None:
            if form:
                body = urllib.parse.urlencode(data).encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                body = json.dumps(data).encode()
                headers["Content-Type"] = "application/json"
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = urllib.request.Request(self.url + path, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode()
            ctype = r.headers.get("Content-Type", "")
            return json.loads(raw) if "json" in ctype and raw else raw

    def wait_up(self, timeout: int = 300) -> None:
        t0 = time.time()
        while time.time() - t0 < timeout:
            try:
                self._req("GET", "/manifest.json", auth=False, timeout=5)
                return
            except urllib.error.HTTPError:
                return  # il server HTTP risponde
            except Exception:
                time.sleep(2)
        raise TimeoutError("Home Assistant non raggiungibile")

    # ------------------------------------------------------------ onboarding
    def onboard(self, username="hi_test", password="hi_test_password_123") -> str:
        """Onboarding di un'istanza vuota. Restituisce un access token."""
        steps = {s["step"]: s["done"] for s in self._req("GET", "/api/onboarding", auth=False)}
        if not steps.get("user"):
            r = self._req("POST", "/api/onboarding/users", {
                "client_id": CLIENT_ID, "name": "HI Test", "username": username,
                "password": password, "language": "it"}, auth=False)
            code = r["auth_code"]
        else:
            # utente già creato: login con flusso di autenticazione
            flow = self._req("POST", "/auth/login_flow", {
                "client_id": CLIENT_ID, "handler": ["homeassistant", None], "redirect_uri": CLIENT_ID},
                auth=False)
            r = self._req("POST", f"/auth/login_flow/{flow['flow_id']}", {
                "client_id": CLIENT_ID, "username": username, "password": password}, auth=False)
            code = r["result"]
        tok = self._req("POST", "/auth/token", {"grant_type": "authorization_code", "code": code,
                                                "client_id": CLIENT_ID}, form=True, auth=False)
        self.token = tok["access_token"]
        for step, path, data in (("core_config", "/api/onboarding/core_config", {}),
                                 ("analytics", "/api/onboarding/analytics", {}),
                                 ("integration", "/api/onboarding/integration",
                                  {"client_id": CLIENT_ID, "redirect_uri": CLIENT_ID})):
            if not steps.get(step):
                try:
                    self._req("POST", path, data)
                except urllib.error.HTTPError:
                    pass
        return self.token

    # ------------------------------------------------------------------ REST
    def template(self, tpl: str) -> str:
        return self._req("POST", "/api/template", {"template": tpl})

    def state(self, entity_id: str) -> dict | None:
        try:
            return self._req("GET", f"/api/states/{entity_id}")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise

    def s(self, entity_id: str) -> str | None:
        st = self.state(entity_id)
        return None if st is None else st["state"]

    def attr(self, entity_id: str, name: str):
        st = self.state(entity_id)
        return None if st is None else st["attributes"].get(name)

    def call(self, domain: str, service: str, **data):
        return self._req("POST", f"/api/services/{domain}/{service}", data, timeout=60)

    def states(self) -> list[dict]:
        return self._req("GET", "/api/states")

    def wait_for(self, fn, timeout: float = 30, interval: float = 0.5, msg: str = ""):
        t0 = time.time()
        last = None
        while time.time() - t0 < timeout:
            try:
                last = fn()
                if last:
                    return last
            except Exception as e:  # noqa: BLE001
                last = e
            time.sleep(interval)
        raise AssertionError(f"Timeout: {msg} (ultimo valore: {last!r})")

    # ------------------------------------------------------------- websocket
    def ws(self, typ: str, **kw):
        return asyncio.run(self._ws(typ, **kw))

    async def _ws(self, typ: str, **kw):
        import websockets
        async with websockets.connect(self.url.replace("http", "ws", 1) + "/api/websocket",
                                      max_size=2**25) as c:
            await c.recv()
            await c.send(json.dumps({"type": "auth", "access_token": self.token}))
            r = json.loads(await c.recv())
            assert r["type"] == "auth_ok", r
            await c.send(json.dumps({"id": 1, "type": typ, **kw}))
            while True:
                r = json.loads(await c.recv())
                if r.get("id") == 1:
                    if not r.get("success"):
                        raise RuntimeError(f"{typ}: {r.get('error')}")
                    return r.get("result")

    def long_lived_token(self, name="hi-tests") -> str:
        return self.ws("auth/long_lived_access_token", client_name=name, lifespan=3650)
