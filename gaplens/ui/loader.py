"""Branded GapLens loading bar helpers for portal transitions and setup tasks."""
from __future__ import annotations

from html import escape
import time
from typing import Callable, TypeVar

import streamlit as st

import config

T = TypeVar("T")


def _loader_card_html(title: str, status: str, pct: int) -> str:
    return (
        f'<div class="gl-loader-card">'
        f'<div class="gl-loader-row">'
        f'<span class="gl-loader-title"><span class="gl-loader-pulse"></span>{escape(title)}</span>'
        f'<span class="gl-loader-pct">{pct}%</span>'
        f'</div>'
        f'<div class="gl-loader-status">{escape(status)}</div>'
        f'</div>'
    )


def show_loading_bar(
    title: str,
    steps: list[tuple[int, str]],
    step_delay: float | None = None,
) -> None:
    """Animate a branded GapLens progress bar across ``(pct, status_text)`` steps."""
    delay = config.LOADER_STEP_S if step_delay is None else step_delay
    slot = st.empty()
    for idx, (pct, status) in enumerate(steps):
        clamped = max(0, min(100, int(pct)))
        with slot.container():
            st.markdown(_loader_card_html(title, status, clamped), unsafe_allow_html=True)
            st.progress(clamped)
        if delay > 0 and idx < len(steps) - 1:
            time.sleep(delay)
    if delay > 0:
        time.sleep(min(delay, 0.12))
    slot.empty()


def run_with_loading_bar(
    title: str,
    start_status: str,
    fn: Callable[[], T],
    done_status: str = "Ready!",
) -> T:
    """Display a branded loading bar while ``fn`` runs, then clear it."""
    slot = st.empty()
    with slot.container():
        st.markdown(_loader_card_html(title, start_status, 35), unsafe_allow_html=True)
        st.progress(35)
    result = fn()
    with slot.container():
        st.markdown(_loader_card_html(title, done_status, 100), unsafe_allow_html=True)
        st.progress(100)
    slot.empty()
    return result
