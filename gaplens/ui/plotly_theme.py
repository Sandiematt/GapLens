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


def goal_figure(scored: dict[str, float], pending: list[str], required: float | None,
                order: list[str] | None = None) -> go.Figure:
    """Score-by-component bars. ``scored`` maps label -> percent.

    Pending bars stand at the required % with a dashed outline; a dashed
    horizontal line marks the required %.
    """
    fig = go.Figure()
    if scored:
        fig.add_bar(x=list(scored), y=list(scored.values()), name="Scored", marker_color=HONEY,
                    marker_line=dict(color=BRONZE, width=1), text=[f"{v:.0f}%" for v in scored.values()],
                    textposition="outside", hovertemplate="%{x}: %{y:.1f}%<extra></extra>")
    if pending and required is not None:
        height = max(0.0, min(required, 100.0))
        fig.add_bar(x=list(pending), y=[height] * len(pending), name="Still to write",
                    marker_color=PENDING_FILL,
                    text=[f"Need {required:.0f}%"] * len(pending), textposition="outside",
                    hovertemplate="%{x}: %{text}<extra></extra>")
        # Plotly bar outlines cannot be dashed, so draw dashed rectangles over the bars.
        cats = order or (list(scored) + list(pending))
        half = (1 - 0.45) / 2
        for label in pending:
            i = cats.index(label)
            fig.add_shape(type="rect", x0=i - half, x1=i + half, y0=0, y1=height, xref="x", yref="y",
                          line=dict(color=PENDING_OUTLINE, width=2, dash="dash"))
        fig.update_xaxes(categoryorder="array", categoryarray=cats)
    if required is not None:
        fig.add_hline(y=max(0.0, min(required, 100.0)), line=dict(color=REQUIRED_LINE, dash="dash", width=2),
                      annotation_text=f"Required {required:.0f}%", annotation_position="top left")
    fig.update_yaxes(range=[0, 115], ticksuffix="%", title=None)
    fig.update_layout(bargap=0.45, height=340, showlegend=True)
    return style_figure(fig)
