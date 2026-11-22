"""Gemini key and model getters. Never log or commit the key."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path

import streamlit as st

# Streamlit only reads .streamlit/secrets.toml from the working directory, so a run
# from the repo root (`streamlit run gaplens/app.py`) would miss gaplens/.streamlit.
_APP_SECRETS = Path(__file__).resolve().parents[1] / ".streamlit" / "secrets.toml"


def _app_secrets() -> dict:
    try:
        with _APP_SECRETS.open("rb") as fh:
            return tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _lookup(name: str) -> str | None:
    try:
        value = st.secrets.get(name)  # raises if no secrets.toml exists
    except Exception:
        value = None
    value = value or _app_secrets().get(name) or os.environ.get(name)
    return str(value).strip() or None if value else None


def get_gemini_key() -> str | None:
    """Key from Streamlit secrets or the GEMINI_API_KEY env var, else None."""
    return _lookup("GEMINI_API_KEY")


def get_gemini_model() -> str | None:
    """Optional model override (GEMINI_MODEL); None means choose automatically."""
    return _lookup("GEMINI_MODEL")
