"""HTML helpers. Every user-supplied string is escaped here.

Each helper returns an HTML string; ``render`` writes one to the page.
Use ``st.container(border=True)`` (styled as a card) for widget groups.
"""
from __future__ import annotations

from html import escape

import streamlit as st

from ui import theme


def _h(html: str) -> str:
    """Collapse to one line so Markdown never treats indentation as code."""
    return "".join(line.strip() for line in html.strip().splitlines())


def render(html: str) -> None:
    st.markdown(_h(html), unsafe_allow_html=True)


def pill(text: str, kind: str = "gold") -> str:
    bg, fg = theme.PILLS.get(kind, theme.PILLS["gold"])
    return f'<span class="gl-pill" style="background:{bg};color:{fg}">{escape(text)}</span>'


def chip(text: str, index: int = 0) -> str:
    """Topic chip; the gold shade cycles with ``index``."""
    soft, _main, fg = theme.SHADES[theme.SHADE_ORDER[index % len(theme.SHADE_ORDER)]]
    return f'<span class="gl-chip" style="background:{soft};color:{fg}">{escape(text)}</span>'


def kpi_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="gl-kpi-sub">{escape(sub)}</div>' if sub else ""
    return _h(f'<div class="gl-kpi"><div class="gl-kpi-label">{escape(label)}</div>'
              f'<div class="gl-kpi-value">{escape(value)}</div>{sub_html}</div>')


def hero_banner(title: str, text: str = "", eyebrow: str = "", aside_html: str = "") -> str:
    """``aside_html`` is trusted HTML shown on the right (e.g. target cards)."""
    p = f"<p>{escape(text)}</p>" if text else ""
    e = f'<div class="gl-hero-eyebrow">{escape(eyebrow)}</div>' if eyebrow else ""
    aside = f'<div class="gl-targets">{aside_html}</div>' if aside_html else ""
    return _h(f'<div class="gl-hero"><div class="gl-hero-row"><div>{e}<h2>{escape(title)}</h2>{p}</div>'
              f'{aside}</div></div>')


# Goal status -> pill kind (see theme.PILLS).
STATUS_KIND = {"On track": "on-track", "Stretch": "stretch", "At risk": "at-risk",
               "Out of reach": "out-of-reach", "Achieved": "ok", "Missed": "at-risk",
               "No data": "not-attempted"}


def status_pill(status: str, label: str | None = None) -> str:
    return pill(label or status, STATUS_KIND.get(status, "gold"))


def status_kpi_card(label: str, status: str, sub: str = "", pill_text: str | None = None) -> str:
    sub_html = f'<div class="gl-kpi-sub">{escape(sub)}</div>' if sub else ""
    return _h(f'<div class="gl-kpi"><div class="gl-kpi-label">{escape(label)}</div>'
              f'<div style="margin:8px 0 6px">{status_pill(status, pill_text)}</div>{sub_html}</div>')


def section_card(title: str, body_html: str = "") -> str:
    """``body_html`` is trusted HTML: escape any user text before passing it."""
    return _h(f'<div class="gl-section"><h3>{escape(title)}</h3>{body_html}</div>')


def callout(text: str) -> str:
    return _h(f'<div class="gl-callout"><span>&#9432;</span><span>{escape(text)}</span></div>')


def file_summary(name: str, detail: str) -> str:
    """An uploaded file's name and a one-line summary, on a dashed champagne strip."""
    return _h(f'<div class="gl-file"><div class="gl-file-icon">&#128196;</div>'
              f'<div><b>{escape(name)}</b><span>{escape(detail)}</span></div></div>')


def page_header(title: str, subtitle: str = "", chips_html: str = "") -> str:
    sub = f'<p class="gl-subtitle">{escape(subtitle)}</p>' if subtitle else ""
    chips = f'<div class="gl-chips">{chips_html}</div>' if chips_html else ""
    return _h(f'<div class="gl-header"><div><h1 class="gl-title">{escape(title)}</h1>{sub}</div>{chips}</div>')


def coming_soon(title: str, text: str, icon: str = "&#9733;") -> str:
    return _h(f'<div class="gl-soon"><div class="gl-soon-icon">{icon}</div>'
              f'<h3>{escape(title)}</h3><p>{escape(text)}</p></div>')


def initials(name: str) -> str:
    parts = [p for p in name.replace(".", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def placeholder_page(title: str, subtitle: str) -> None:
    """Standard 'coming in a later ticket' page for navigation stubs."""
    render(page_header(title, subtitle))
    render(coming_soon(f"{title} is coming soon",
                       "This page arrives in a later ticket. Navigation is already in place."))


def card(key: str):
    """A white, rounded, shadowed container. ``key`` must be unique per page."""
    return st.container(border=True, key=f"card_{key}")


# --- CIA analysis (SAN-124) ----------------------------------------------------
# Mistake type -> pill kind (see theme.PILLS) and the css suffix used for cards.
MISTAKE_KIND = {"OK": "ok", "Concept gap": "concept-gap", "Not attempted": "not-attempted",
                "Silly error flagged": "silly-flagged", "Silly loss": "silly-loss",
                "Time pressure": "time-pressure"}


def mistake_pill(mistake: str) -> str:
    return pill(mistake, MISTAKE_KIND.get(mistake, "gold"))


def num(x: float) -> str:
    """1 decimal place, trailing zeros dropped."""
    return f"{x:.1f}".rstrip("0").rstrip(".")


def ordinal(n: float) -> str:
    n = int(round(n))
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def stat_tile(label: str, value: str, unit: str = "", icon: str = "&#9679;",
              tone: str = "honey") -> str:
    """Compact KPI tile on a soft gold shade (``icon`` is trusted HTML)."""
    soft, _main, fg = theme.SHADES.get(tone, theme.SHADES["honey"])
    u = f'<span class="gl-tile-unit">{escape(unit)}</span>' if unit else ""
    return _h(f'<div class="gl-tile" style="background:{soft}"><div class="gl-tile-icon" '
              f'style="color:{fg}">{icon}</div><div><div class="gl-tile-label">{escape(label)}</div>'
              f'<div class="gl-tile-value">{escape(value)}{u}</div></div></div>')


def warning_banner(title: str, text: str, icon: str = "&#9719;") -> str:
    return _h(f'<div class="gl-warn"><span class="gl-warn-icon">{icon}</span><div>'
              f'<div class="gl-warn-title">{escape(title)}</div><div>{escape(text)}</div></div></div>')


def question_table(rows: list[dict]) -> str:
    """Read-only question table. Row keys: q_no, topic, max, you, topper, class_avg,
    percentile, mistake (already-formatted strings, except q_no and mistake)."""
    head = "".join(f"<th>{h}</th>" for h in
                   ("Q", "Topic", "Max", "You", "Topper", "Class avg", "Percentile", "Mistake type"))
    body = "".join(
        f'<tr><td class="gl-q">Q{int(r["q_no"])}</td><td>{escape(r["topic"])}</td>'
        f'<td class="gl-muted">{escape(r["max"])}</td><td class="gl-you">{escape(r["you"])}</td>'
        f'<td>{escape(r["topper"])}</td><td>{escape(r["class_avg"])}</td>'
        f'<td>{escape(r["percentile"])}</td><td>{mistake_pill(r["mistake"])}</td></tr>'
        for r in rows)
    return _h(f'<div class="gl-table-wrap"><table class="gl-table"><thead><tr>{head}</tr></thead>'
              f'<tbody>{body}</tbody></table></div>')


def tip_card_html(mistake: str, gain: float, title: str, text: str) -> str:
    g = f"Up to +{num(gain)} mark" + ("" if abs(gain - 1) < 1e-9 else "s")
    return _h(f'<div class="gl-row">{mistake_pill(mistake)}<span class="gl-gain">{escape(g)}</span></div>'
              f'<div class="gl-tip-title">{escape(title)}</div><div class="gl-tip-text">{escape(text)}</div>')


def section_head(title: str, aside: str = "") -> str:
    """Section title outside a card, with an optional caption on the right."""
    a = f'<span>{escape(aside)}</span>' if aside else ""
    return _h(f'<div class="gl-section-head"><div class="gl-section-title">{escape(title)}</div>{a}</div>')


def tip_card(key: str, mistake: str):
    """Card container for a suggestion; the top edge takes the mistake colour."""
    return st.container(border=True, key=f"tip_{MISTAKE_KIND.get(mistake, 'ok')}_{key}")


def progress_chip(topic: str, first: float, last: float) -> str:
    kind = "ok" if last > first + 5 else ("at-risk" if last < first - 5 else "stretch")
    arrow = "&#8599; " if kind == "ok" else ("&#8600; " if kind == "at-risk" else "")
    bg, fg = theme.PILLS[kind]
    return (f'<span class="gl-pill" style="background:{bg};color:{fg}">{arrow}'
            f'{escape(topic)}: {first:.0f}% → {last:.0f}%</span>')


# --- resources (SAN-125) ---------------------------------------------------------
RTYPE_ICON = {"video": "&#9654;", "reading": "&#128214;", "practice": "&#9998;",
              "course": "&#127891;"}
SEARCH_ICON = {"youtube": "&#9654;", "nptel": "&#128269;", "practice": "&#9998;"}


def resource_card(res: dict, verified: bool = True) -> str:
    """One resource row (a link). Verified rows need rtype, difficulty, duration."""
    href = escape(res.get("link") or res.get("url") or "", quote=True)
    if verified:
        icon = RTYPE_ICON.get(res["rtype"], "&#128279;")
        meta = (pill("Verified", "ok") + pill(res["rtype"].capitalize(), "muted")
                + pill(res["difficulty"].capitalize(), "muted"))
        if res.get("duration"):
            meta += pill(res["duration"], "muted")
        cls = "gl-res"
    else:
        icon = SEARCH_ICON.get(res.get("kind"), "&#128269;")
        meta = pill("Auto-suggested", "muted")
        cls = "gl-res gl-auto"
    return _h(f'<a class="{cls}" href="{href}" target="_blank" rel="noopener noreferrer">'
              f'<span style="font-size:18px">{icon}</span><div class="gl-res-body">'
              f'<div class="gl-res-title">{escape(res["title"])}</div>'
              f'<div class="gl-res-meta">{meta}</div></div><span class="gl-res-go">&#8599;</span></a>')


def weak_topic_header(rank: int, title: str, lost: float, mx: float, pct: float) -> str:
    color = "#DC2626" if pct >= 50 else "#F59E0B"
    return _h(f'<div class="gl-rank"><div class="gl-rank-n">#{rank}</div>'
              f'<div class="gl-rank-title">{escape(title)}</div></div>'
              f'<div class="gl-rank-lost">Lost {num(lost)} of {num(mx)} marks ({pct:.0f}%)</div>'
              f'<div class="gl-bar"><div style="width:{min(100, pct):.0f}%;background:{color}"></div></div>')
