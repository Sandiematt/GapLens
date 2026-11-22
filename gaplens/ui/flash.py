"""Flash messages that survive st.rerun()."""
from __future__ import annotations

import streamlit as st

_KEY = "_flash_messages"


def flash(message: str, kind: str = "success") -> None:
    """Queue a message (kind: success, error, warning, info) for the next render."""
    st.session_state.setdefault(_KEY, []).append((kind, message))


def show_flash() -> None:
    """Render and clear queued messages. Call once per run, near the top of the page."""
    for kind, message in st.session_state.pop(_KEY, []):
        getattr(st, kind if kind in ("success", "error", "warning", "info") else "info")(message)
