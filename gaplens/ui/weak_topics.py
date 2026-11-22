"""Reusable weak-topics block (student tab now; SAN-127 reuses it for supplementary focus)."""
from __future__ import annotations

import streamlit as st

import config
from core import suggestions
from ui import components


def _resource_columns(subject_name: str, row: dict) -> None:
    left, right = st.columns(2, gap="medium")
    with left:
        components.render('<div class="gl-eyebrow2">From your faculty</div>')
        if row["resources"]:
            components.render("".join(components.resource_card(r) for r in row["resources"]))
        else:
            st.caption("No verified resources for this topic yet. Try the searches.")
    with right:
        components.render('<div class="gl-eyebrow2">More to explore</div>')
        components.render("".join(components.resource_card(link, verified=False)
                                  for link in suggestions.search_links(subject_name, row["topic"])))


def render_weak_topics(subject: dict, losses: list[dict], top_n: int = config.TOP_WEAK_TOPICS,
                       key: str = "weak") -> None:
    """``losses``: rows from ``insights.weak_topic_rows`` (topic, lost, max, lost_pct, resources),
    most marks lost first. Shows the top ``top_n`` with resources, then every topic in an expander."""
    losses = [r for r in losses if r["lost"] > 0]
    if not losses:
        components.render(components.coming_soon(
            "No weak topics yet", "Nothing to work on: either no marks are in yet, or you kept "
            "every mark.", "&#127881;"))
        return
    top = losses[:top_n]
    for col, (i, r) in zip(st.columns(len(top)), enumerate(top, start=1)):
        with col, components.card(f"{key}_rank_{i}"):
            components.render(components.weak_topic_header(
                i, r["topic"], r["lost"], r["max"], r["lost_pct"]))
    st.write("")
    with components.card(f"{key}_resources"):
        st.markdown("### Resources by topic")
        st.caption("Verified links come from your faculty. Auto-suggested links are searches, "
                   "not checked by anyone.")
        tabs = st.tabs([r["topic"] for r in top])
        for tab, r in zip(tabs, top):
            with tab:
                _resource_columns(subject["name"], r)
    with st.expander("Every topic"):
        for r in losses:
            st.markdown(f'**{r["topic"]}** · lost {components.num(r["lost"])} of '
                        f'{components.num(r["max"])} marks ({r["lost_pct"]:.0f}%)')
