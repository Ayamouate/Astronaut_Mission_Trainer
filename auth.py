"""Simple local astronaut account storage for the prototype."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any

from config import ASTRONAUT_DATA_PATH


def _load() -> dict[str, Any]:
    try:
        with ASTRONAUT_DATA_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else {"astronauts": {}}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"astronauts": {}}


def _save(data: dict[str, Any]) -> None:
    ASTRONAUT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = ASTRONAUT_DATA_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(ASTRONAUT_DATA_PATH)


def _password_hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310_000).hex()


def create_account(name: str, callsign: str, email: str, password: str) -> tuple[bool, str]:
    key = email.strip().lower()
    if not name.strip() or not key or not password:
        return False, "Enter your name, email, and password."
    data = _load()
    astronauts = data.setdefault("astronauts", {})
    if key in astronauts:
        return False, "An account with that email already exists."
    salt = secrets.token_bytes(16)
    astronauts[key] = {
        "name": name.strip(),
        "callsign": callsign.strip(),
        "email": key,
        "salt": salt.hex(),
        "password_hash": _password_hash(password, salt),
        "checkins": [],
    }
    _save(data)
    return True, key


def authenticate(email: str, password: str) -> tuple[bool, str]:
    key = email.strip().lower()
    astronaut = _load().get("astronauts", {}).get(key)
    if not astronaut:
        return False, "Email or password was not recognized."
    candidate = _password_hash(password, bytes.fromhex(astronaut["salt"]))
    if not hmac.compare_digest(candidate, astronaut["password_hash"]):
        return False, "Email or password was not recognized."
    return True, key


def get_profile(email: str) -> dict[str, Any] | None:
    return _load().get("astronauts", {}).get(email.strip().lower())


def get_checkins(email: str) -> list[dict[str, Any]]:
    profile = get_profile(email)
    return list(profile.get("checkins", [])) if profile else []


def save_checkin(email: str, entry: dict[str, Any]) -> None:
    data = _load()
    profile = data.get("astronauts", {}).get(email.strip().lower())
    if profile is None:
        return
    profile.setdefault("checkins", []).append(entry)
    _save(data)
