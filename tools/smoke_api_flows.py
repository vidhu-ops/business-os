#!/usr/bin/env python3
from __future__ import annotations
import json, sys, time, urllib.error, urllib.request
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"

def call(method, path, body=None, token=None):
    url = f"{BASE.rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload

errors = []
code, _ = call("GET", "/api/v1/health")
if code != 200:
    errors.append(f"health {code}")
code, demo = call("POST", "/api/v1/auth/demo", {})
token = demo.get("token", "")
if code != 200 or not token:
    errors.append("demo login")
else:
    code, projects = call("GET", "/api/v1/projects", token=token)
    ids = [p.get("workspace_id") for p in projects.get("projects", [])]
    if "demo_readonly" not in ids:
        errors.append(f"demo sample missing {ids}")
    code, research = call("GET", "/api/v1/research/demo_readonly", token=token)
    if code != 200 or not (research.get("research") or {}).get("available"):
        errors.append("demo research")
    code, gauge = call("GET", "/api/v1/plan/demo_readonly/gauge", token=token)
    if code != 200 or not gauge.get("audit"):
        errors.append("demo gauge")
code, reg = call("POST", "/api/v1/auth/register", {"email": f"smoke_{int(time.time())}@example.com", "password": "testpass123", "name": "Smoke"})
ut = reg.get("token", "")
if code != 200 or not ut:
    errors.append("register")
else:
    code, aw = call("GET", "/api/v1/audit/workspace", token=ut)
    if code != 200 or not aw.get("workspace_id"):
        errors.append("audit workspace")
    code, _ = call("GET", "/api/v1/research/demo_readonly", token=ut)
    if code == 200:
        errors.append("real user read demo should 404")
if errors:
    print("SMOKE FAILED:", errors)
    raise SystemExit(1)
print("SMOKE OK")