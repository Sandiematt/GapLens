"""Plotly helpers: gold template, transparent background, gold gridlines."""
from __future__ import annotations

import plotly.graph_objects as go

GRID = "#F1E4C3"
TEXT = "#1E1B3A"

# Series colours from the design.
YOU, TOPPER, CLASS_AVG = "#92400E", "#FBBF24", "#FDE047"
HONEY, BRONZE, REQUIRED_LINE = "#FBBF24", "#A16207", "#3B2A06"
PENDING_FILL, PENDING_OUTLINE = "#F7E7CE", "#B7791F"
MISTAKE = {"Concept gap": "#DC2626", "Not attempted": "#4B5563", "Time pressure": "#F59E0B",
           "Silly loss": "#D9826B", "Silly error flagged": "#A16207"}
TOPIC_LINES = ["#92400E", "#F4A300", "#D9826B", "#CA8A04", "#B7791F"]
HEATMAP_SCALE = [[0, "#DC2626"], [0.25, "#F87171"], [0.5, "#FBBF24"],
                 [0.75, "#86EFAC"], [1, "#16A34A"]]
SILLY_BARS = "#CA8A04"


def gold_template() -> go.layout.Template:
    return go.layout.Template(layout=go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color=TEXT, size=13),
        colorway=TOPIC_LINES,
        xaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
        yaxis=dict(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID),
        margin=dict(l=24, r=16, t=32, b=24),
        legend=dict(orientation="h", y=-0.2),
    ))


def style_figure(fig: go.Figure, **layout) -> go.Figure:
    """Apply the gold template (and optional layout overrides) to ``fig``."""
    fig.update_layout(template=gold_template(), **layout)
    return fig
