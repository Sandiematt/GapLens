"""HTML helpers. Every user-supplied string is escaped here.

Each helper returns an HTML string; ``render`` writes one to the page.
Use ``st.container(border=True)`` (styled as a card) for widget groups.
"""
from __future__ import annotations

from html import escape

import streamlit as st

import config
from core import analysis, suggestions
from ui import theme


def _h(html: str) -> str:
    """Collapse to one line so Markdown never treats indentation as code."""
    return "".join(line.strip() for line in html.strip().splitlines())


def render(html: str) -> None:
    st.markdown(_h(html), unsafe_allow_html=True)


def num(x: float) -> str:
    """1 decimal place, trailing zeros dropped (the one number format for marks)."""
    return suggestions.fmt(x)


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


def target_card(label: str, value: str, unit: str) -> str:
    """A white mini card on the hero banner (e.g. 'CIA-3 target 18 / 25')."""
    return (f'<div class="gl-target-card"><small>{escape(label)}</small>'
            f'<b>{escape(value)}</b> <span>{escape(unit)}</span></div>')


# Goal status -> pill kind (see theme.PILLS).
STATUS_KIND = {analysis.ON_TRACK: "on-track", analysis.STRETCH: "stretch",
               analysis.AT_RISK: "at-risk", analysis.OUT_OF_REACH: "out-of-reach",
               analysis.ACHIEVED: "ok", analysis.MISSED: "at-risk",
               analysis.NO_DATA: "not-attempted"}


def status_pill(status: str, label: str | None = None) -> str:
    return pill(label or status, STATUS_KIND.get(status, "gold"))


def status_kpi_card(label: str, status: str, sub: str = "", pill_text: str | None = None) -> str:
    sub_html = f'<div class="gl-kpi-sub">{escape(sub)}</div>' if sub else ""
    return _h(f'<div class="gl-kpi"><div class="gl-kpi-label">{escape(label)}</div>'
              f'<div class="gl-kpi-pill">{status_pill(status, pill_text)}</div>{sub_html}</div>')


def section_card(title: str, body_html: str = "") -> str:
    """``body_html`` is trusted HTML: escape any user text before passing it."""
    return _h(f'<div class="gl-section">{card_title(title)}{body_html}</div>')


def card_title(title: str, subtitle: str = "", aside_html: str = "") -> str:
    """The one card title: 18 px bold, an optional muted subtitle, and ``aside_html``
    (trusted HTML, e.g. a pill) pinned to the right on the title's line."""
    sub = f'<p class="gl-card-sub">{escape(subtitle)}</p>' if subtitle else ""
    aside = f'<div class="gl-card-aside">{aside_html}</div>' if aside_html else ""
    return _h(f'<div class="gl-card-head"><div class="gl-card-head-row">'
              f'<div class="gl-card-title">{escape(title)}</div>{aside}</div>{sub}</div>')


def card_eyebrow(text: str) -> str:
    """Small uppercase label at the top of a card (e.g. 'Final mark vs target')."""
    return f'<div class="gl-kpi-label">{escape(text)}</div>'


def big_figure(value: str, aside: str = "") -> str:
    """A large figure inside a card, with optional muted text after it."""
    a = f' <span class="gl-figure-aside">{escape(aside)}</span>' if aside else ""
    return f'<div class="gl-figure">{escape(value)}{a}</div>'


def empty_state(title: str, text: str, icon: str = "&#128218;") -> str:
    """A small dashed card for 'nothing here yet' (``icon`` is trusted HTML)."""
    return _h(f'<div class="gl-empty"><div class="gl-empty-icon">{icon}</div><div>'
              f'<div class="gl-empty-title">{escape(title)}</div>'
              f'<div class="gl-empty-text">{escape(text)}</div></div></div>')


def table(headers: list[str], rows: list[list[str]], numeric: tuple[int, ...] = (),
          classes: dict[int, str] | None = None, scroll: bool = False) -> str:
    """Read-only table. Cells are trusted HTML: escape user text before passing it.

    ``numeric`` column indexes are right-aligned (header and cells); ``classes``
    adds a css class to every cell of a column. ``scroll`` caps the height and
    keeps the header row in view.
    """
    classes = classes or {}

    def cls(i: int) -> str:
        names = (["gl-num-col"] if i in numeric else []) + ([classes[i]] if i in classes else [])
        return f' class="{" ".join(names)}"' if names else ""

    head = "".join(f"<th{cls(i)}>{escape(h)}</th>" for i, h in enumerate(headers))
    body = "".join("<tr>" + "".join(f"<td{cls(i)}>{c}</td>" for i, c in enumerate(r)) + "</tr>"
                   for r in rows)
    wrap = "gl-table-wrap gl-table-scroll" if scroll else "gl-table-wrap"
    return _h(f'<div class="{wrap}"><table class="gl-table"><thead><tr>{head}</tr></thead>'
              f'<tbody>{body}</tbody></table></div>')


def readonly_field(label: str, value: str) -> str:
    """A labelled read-only value that lines up with the inputs beside it."""
    return _h(f'<div class="gl-field"><div class="gl-field-label">{escape(label)}</div>'
              f'<div class="gl-field-value">{escape(value)}</div></div>')


def pill_row(pills_html: str) -> str:
    """Pills (trusted HTML) on one wrapping row with even gaps."""
    return f'<div class="gl-pill-row">{pills_html}</div>'


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


def label(text: str, extra_class: str = "") -> str:
    """Small uppercase label (sidebar sections)."""
    cls = f"gl-label {extra_class}".strip()
    return f'<div class="{cls}">{escape(text)}</div>'


def eyebrow(text: str) -> str:
    """Uppercase sub-heading inside a card."""
    return f'<div class="gl-eyebrow2">{escape(text)}</div>'


def profile_chip(name: str, sub: str) -> str:
    """Avatar, name and one line under it (the sidebar's active profile)."""
    return _h(f'<div class="gl-profile"><div class="gl-avatar">{escape(initials(name))}</div><div>'
              f'<div class="gl-profile-name">{escape(name)}</div>'
              f'<div class="gl-profile-sub">{escape(sub)}</div></div></div>')


# --- goal tab ----------------------------------------------------------------------
def rule_row(pill_html: str, text: str) -> str:
    """One status-rule line: a pill (trusted HTML) and its explanation."""
    return f'<div class="gl-rule">{pill_html}<span>{escape(text)}</span></div>'


def formula(main: str, note: str = "", fail: bool = False) -> str:
    """A champagne formula strip; ``fail`` makes it the red pass-mark warning."""
    n = f'<span class="gl-formula-note">{escape(note)}</span>' if note else ""
    cls = "gl-formula gl-formula-fail" if fail else "gl-formula"
    return f'<div class="{cls}">{escape(main)}{n}</div>'


def chart_title(title: str, aside: str = "") -> str:
    """Small bold label above a chart inside a card."""
    a = f' <span class="gl-chart-aside">· {escape(aside)}</span>' if aside else ""
    return f'<div class="gl-chart-title">{escape(title)}{a}</div>'


# --- CIA analysis (SAN-124) ----------------------------------------------------
# Mistake type -> pill kind (see theme.PILLS) and the css suffix used for cards.
MISTAKE_KIND = {analysis.OK: "ok", analysis.CONCEPT_GAP: "concept-gap",
                analysis.NOT_ATTEMPTED: "not-attempted", analysis.SILLY_FLAGGED: "silly-flagged",
                analysis.SILLY_LOSS: "silly-loss", analysis.TIME_PRESSURE: "time-pressure"}


def mistake_pill(mistake: str) -> str:
    return pill(mistake, MISTAKE_KIND.get(mistake, "gold"))


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
    headers = ["Q", "Topic", "Max", "You", "Topper", "Class avg", "Percentile", "Mistake type"]
    body = [[f'Q{int(r["q_no"])}', escape(r["topic"]), escape(r["max"]), escape(r["you"]),
             escape(r["topper"]), escape(r["class_avg"]), escape(r["percentile"]),
             mistake_pill(r["mistake"])] for r in rows]
    return table(headers, body, numeric=(2, 3, 4, 5, 6),
                 classes={0: "gl-q", 2: "gl-muted", 3: "gl-you"})


def tip_card_html(mistake: str, gain: float, title: str, text: str) -> str:
    gain_text = f"Up to +{num(gain)} mark" + ("" if abs(gain - 1) < 1e-9 else "s")
    return _h(f'<div class="gl-row">{mistake_pill(mistake)}<span class="gl-gain">{escape(gain_text)}</span></div>'
              f'<div class="gl-tip-title">{escape(title)}</div><div class="gl-tip-text">{escape(text)}</div>')


def section_head(title: str, aside: str = "") -> str:
    """Section title outside a card, with an optional caption on the right."""
    a = f'<span>{escape(aside)}</span>' if aside else ""
    return _h(f'<div class="gl-section-head"><div class="gl-section-title">{escape(title)}</div>{a}</div>')


def tab_heading(title: str, subtitle: str = "") -> str:
    """Section-sized heading at the top of a dashboard tab (never page-sized)."""
    sub = f'<p class="gl-tab-sub">{escape(subtitle)}</p>' if subtitle else ""
    return _h(f'<div class="gl-tab-head"><div class="gl-section-title">{escape(title)}</div>{sub}</div>')


def tip_card(key: str, mistake: str):
    """Card container for a suggestion; the top edge takes the mistake colour."""
    return st.container(border=True, key=f"tip_{MISTAKE_KIND.get(mistake, 'ok')}_{key}")


TREND_STYLE = {analysis.TREND_UP: ("ok", "&#8599; "), analysis.TREND_DOWN: ("at-risk", "&#8600; "),
               analysis.TREND_FLAT: ("stretch", "")}


def progress_chip(topic: str, first: float, last: float) -> str:
    kind, arrow = TREND_STYLE[analysis.trend_direction(first, last)]
    bg, fg = theme.PILLS[kind]
    return (f'<span class="gl-pill" style="background:{bg};color:{fg}">{arrow}'
            f'{escape(topic)}: {first:.0f}% → {last:.0f}%</span>')


def progress_chips(trends) -> str:
    """One chip per row of ``analysis.topic_trends`` (topic, first, last), in its order."""
    return _h('<div class="gl-chips">' + "".join(
        progress_chip(r.topic, r.first, r.last) for r in trends.itertuples()) + "</div>")


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
    # Only inline tags inside <a>: a <div> there makes Markdown split the card apart.
    return _h(f'<a class="{cls}" href="{href}" target="_blank" rel="noopener noreferrer">'
              f'<span class="gl-res-icon">{icon}</span><span class="gl-res-body">'
              f'<span class="gl-res-title">{escape(res["title"])}</span>'
              f'<span class="gl-res-meta">{meta}</span></span><span class="gl-res-go">&#8599;</span></a>')


def resource_list(cards: list[str]) -> str:
    """Wrap resource cards in a block element so Markdown keeps them as raw HTML."""
    return _h(f'<div class="gl-res-list">{"".join(cards)}</div>')


def gap_pill(lost_pct: float) -> str:
    """Big gap (lost% at or over BIG_GAP_PCT): start with basics; otherwise go to practice."""
    if lost_pct >= config.BIG_GAP_PCT:
        return pill("Big gap · start with basics", "at-risk")
    return pill("Small gap · go to practice", "stretch")


def weak_topic_header(rank: int, title: str, lost: float, mx: float, pct: float) -> str:
    """Rank card body: rank, topic, marks lost, a bar and the gap pill."""
    color = "#DC2626" if pct >= config.BIG_GAP_PCT else "#F59E0B"
    return _h(f'<div class="gl-rank"><div class="gl-rank-n">#{rank}</div>'
              f'<div class="gl-rank-title">{escape(title)}</div></div>'
              f'<div class="gl-rank-lost">Lost {num(lost)} of {num(mx)} marks ({pct:.0f}%)</div>'
              f'<div class="gl-bar"><div style="width:{min(100, pct):.0f}%;background:{color}"></div></div>'
              f'<div class="gl-rank-gap">{gap_pill(pct)}</div>')


# --- student My Subjects card ------------------------------------------------------
# Banner variants alternate between the hero gold and deep gold, as in the design.
BANNERS = [("gl-banner-hero", "&#128214;"), ("gl-banner-deep", "&lt;/&gt;")]
SEG_COLORS = [theme.SHADES["lemon"][1], theme.SHADES["honey"][1],
              theme.SHADES["marigold"][1], theme.SHADES["bronze"][1]]


def weight_split(cia_weight: float) -> str:
    """CIA/ESE split labels over a bar with one segment per component, sized by weight."""
    cia_pct, ese_pct = round(cia_weight * 100), round((1 - cia_weight) * 100)
    parts = " + ".join(f"{c} /{config.COMPONENTS[c]}" for c in config.CIA_COMPONENTS)
    scale = ("halved" if abs(cia_weight - config.DEFAULT_CIA_WEIGHT) < 1e-9
             else f"scaled to {cia_pct}")
    weights = analysis.component_weights(cia_weight)
    segs = "".join(f'<div style="flex:{weights[c]};background:{color}"></div>'
                   for c, color in zip(config.COMPONENTS, SEG_COLORS) if weights[c] > 0)
    return _h(f'<div><div class="gl-split-labels"><span class="gl-split-cia">'
              f'CIA {cia_pct} · {parts}, {scale}</span><span class="gl-split-ese">ESE {ese_pct}</span>'
              f'</div><div class="gl-bar gl-bar-split">{segs}</div></div>')


def subject_card(subject: dict, idx: int, topics: list[dict], meta: str) -> str:
    """Banner, faculty, weight split and topic chips of one subject card."""
    cls, icon = BANNERS[idx % len(BANNERS)]
    chips = "".join(chip(t["title"], i) for i, t in enumerate(topics))
    return _h(
        f'<div class="gl-banner {cls}"><div>'
        f'<div class="gl-banner-code">{escape(subject["code"])} · {escape(subject["class_name"])}</div>'
        f'<div class="gl-banner-name">{escape(subject["name"])}</div></div>'
        f'<div class="gl-banner-icon">{icon}</div></div>'
        f'<div class="gl-card-body"><div class="gl-row"><div class="gl-fac">'
        f'<div class="gl-fac-avatar">{escape(initials(subject["faculty_name"]))}</div><div>'
        f'<div class="gl-meta">Faculty</div><div class="gl-fac-name">'
        f'{escape(subject["faculty_name"])}</div></div></div>'
        f'<span class="gl-meta">{escape(meta)}</span></div>'
        f'{weight_split(subject["cia_weight"])}<div class="gl-topics">{chips}</div></div>')


def faculty_subject_summary(code: str, name: str, pills_html: str) -> str:
    """Title and pills of a faculty subject card (``pills_html`` is trusted)."""
    return _h(f'<div class="gl-card-title">{escape(code)} {escape(name)}</div>'
              f'<div class="gl-pill-row">{pills_html}</div>')
