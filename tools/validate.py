#!/usr/bin/env python3
"""Validate Demote button packs.

Usage: python tools/validate.py [FILE ...]
With no arguments, validates every packs/*.json and examples/*.json.

Runs the JSON Schema in schema/pack.schema.json, then the rules a schema
can't express: file name matches id, unique ids, known icons, every {{slot}}
defined in scope, engine-specific variable types, text lengths, the size
limit, and that a "local" pack names no public host.
"""

from __future__ import annotations

import ipaddress
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "pack.schema.json").read_text())
ICONS = set(json.loads((ROOT / "schema" / "icons.json").read_text())["icons"])

MAX_BYTES = 64 * 1024
MAX_NAME = 32
MAX_DESCRIPTION = 120
MAX_LABEL = 24
SLOT = re.compile(r"\{\{\s*([^}]*?)\s*\}\}")
SLOT_ID = re.compile(r"^[a-z][a-z0-9_]{0,31}$")


def _strings(value):
    """Every string inside a JSON value, keys included."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for k, v in value.items():
            yield k
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _is_local_host(host: str) -> bool:
    host = host.strip("[]").lower()
    if host.endswith(".local") or host == "localhost":
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_private or ip.is_link_local or ip.is_loopback


def check_pack(path: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        errors.append(f"file is {len(raw)} bytes; the limit is {MAX_BYTES}")
    try:
        pack = json.loads(raw)
    except json.JSONDecodeError as e:
        return [f"not valid JSON: {e}"]

    for i, b in enumerate(pack.get("buttons", []) if isinstance(pack, dict) else []):
        if isinstance(b, dict) and ("request" in b) == ("service" in b):
            errors.append(f"buttons/{i}: a button needs exactly one of \"request\" (http) or \"service\" (home_assistant)")
    if errors:
        return errors

    for e in sorted(Draft202012Validator(SCHEMA).iter_errors(pack), key=lambda e: list(e.path)):
        where = "/".join(str(p) for p in e.path) or "(root)"
        errors.append(f"{where}: {e.message}")
    if errors:
        return errors  # the rules below assume the shape is right

    if path.parent.name == "packs" and path.stem != pack["id"]:
        errors.append(f'file name must be "{pack["id"]}.json"')

    for lang, text in pack["name"].items():
        if len(text) > MAX_NAME:
            errors.append(f"name.{lang} is {len(text)} characters; the limit is {MAX_NAME}")
    for lang, text in pack["description"].items():
        if len(text) > MAX_DESCRIPTION:
            errors.append(f"description.{lang} is {len(text)} characters; the limit is {MAX_DESCRIPTION}")
    if pack["icon"] not in ICONS:
        errors.append(f'icon "{pack["icon"]}" is not in schema/icons.json')

    engine = pack["engine"]
    pack_vars = {v["id"]: v for v in pack.get("variables", [])}
    for v in pack.get("variables", []):
        if v["scope"] != "pack":
            errors.append(f'variables/{v["id"]}: pack-level variables must have scope "pack"')
    errors += _check_variables("variables", pack.get("variables", []), engine)

    seen_buttons: set[str] = set()
    for i, b in enumerate(pack["buttons"]):
        where = f'buttons/{b["id"]}'
        if b["id"] in seen_buttons:
            errors.append(f"{where}: duplicate button id")
        seen_buttons.add(b["id"])
        for lang, text in b["label"].items():
            if len(text) > MAX_LABEL:
                errors.append(f"{where}: label.{lang} is {len(text)} characters; the limit is {MAX_LABEL}")
        if b["icon"] not in ICONS:
            errors.append(f'{where}: icon "{b["icon"]}" is not in schema/icons.json')

        button_vars = {v["id"]: v for v in b.get("variables", [])}
        for v in b.get("variables", []):
            if v["scope"] != "button":
                errors.append(f'{where}/variables/{v["id"]}: button variables must have scope "button"')
            if v["id"] in pack_vars:
                errors.append(f'{where}/variables/{v["id"]}: shadows a pack variable')
        errors += _check_variables(f"{where}/variables", b.get("variables", []), engine)
        in_scope = {**pack_vars, **button_vars}

        if engine == "http" and "request" not in b:
            errors.append(f'{where}: an "http" pack needs "request" on every button')
        if engine == "home_assistant" and "service" not in b:
            errors.append(f'{where}: a "home_assistant" pack needs "service" on every button')

        action = b.get("request") or b.get("service")
        for s in _strings(action):
            for slot in SLOT.findall(s):
                if not SLOT_ID.match(slot):
                    errors.append(f'{where}: "{{{{{slot}}}}}" is not a plain variable name')
                elif slot not in in_scope:
                    errors.append(f'{where}: "{{{{{slot}}}}}" is not a variable of this pack or button')

        req = b.get("request")
        if req:
            if req.get("contentType") != "application/json" and not isinstance(req.get("body", ""), str):
                errors.append(f'{where}: a JSON body needs contentType "application/json"')
            errors += _check_host(where, req["url"], in_scope, pack["network"])
    return errors


def _check_variables(where: str, variables: list[dict], engine: str) -> list[str]:
    errors = []
    seen: set[str] = set()
    for v in variables:
        if v["id"] in seen:
            errors.append(f'{where}/{v["id"]}: duplicate variable id')
        seen.add(v["id"])
        if v["type"] == "ha_entity" and engine != "home_assistant":
            errors.append(f'{where}/{v["id"]}: ha_entity is only for "home_assistant" packs')
        if v["type"] == "secret" and "default" in v:
            errors.append(f'{where}/{v["id"]}: a secret cannot have a default')
    return errors


def _check_host(where: str, url: str, in_scope: dict, network: str) -> list[str]:
    host_part = urlsplit(SLOT.sub("slot", url)).hostname or ""
    raw_netloc = url.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0]
    slots = SLOT.findall(raw_netloc)
    if slots:
        bad = [s for s in slots if s in in_scope and in_scope[s]["type"] not in ("host", "port")]
        if bad:
            return [f'{where}: the URL host may only use "host" or "port" variables ({", ".join(bad)})']
        return []
    if network == "local" and not _is_local_host(host_part):
        return [f'{where}: "{host_part}" is not a local address, so this pack must be "network": "internet"']
    return []


def main(argv: list[str]) -> int:
    files = [Path(a) for a in argv] or sorted([*ROOT.glob("packs/*.json"), *ROOT.glob("examples/*.json")])
    ids: dict[str, Path] = {}
    failed = 0
    for f in files:
        errs = check_pack(f)
        try:
            pid = json.loads(f.read_text()).get("id")
        except Exception:
            pid = None
        if pid and f.parent.name == "packs":
            if pid in ids:
                errs.append(f"id {pid} is also used by {ids[pid].name}")
            ids[pid] = f
        rel = f.resolve().relative_to(ROOT) if f.resolve().is_relative_to(ROOT) else f
        if errs:
            failed += 1
            print(f"FAIL {rel}")
            for e in errs:
                print(f"  - {e}")
        else:
            print(f"ok   {rel}")
    print(f"\n{len(files) - failed} of {len(files)} packs valid.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
