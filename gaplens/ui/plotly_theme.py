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


# --- CIA analysis and progress (SAN-124) ----------------------------------------
OK_LOSS = "#F7E7CE"  # champagne: marks lost on questions marked OK


def question_compare_figure(labels: list[str], you: list[float], topper: list[float],
                            class_avg: list[float]) -> go.Figure:
    """Grouped bars: % of each question's max for you, the topper and the class."""
    fig = go.Figure()
    for name, ys, colour in (("You", you, YOU), ("Topper", topper, TOPPER),
                             ("Class avg", class_avg, CLASS_AVG)):
        fig.add_bar(x=labels, y=ys, name=name, marker_color=colour,
                    hovertemplate=f"{name} · %{{x}}: %{{y:.0f}}%<extra></extra>")
    fig.update_yaxes(range=[0, 105], ticksuffix="%", title=None)
    fig.update_xaxes(categoryorder="array", categoryarray=labels)
    fig.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08, height=300,
                      legend=dict(orientation="h", y=1.12, x=1, xanchor="right"))
    return style_figure(fig)


def mistake_donut_figure(lost: dict[str, float]) -> go.Figure:
    """Donut of marks lost by mistake type; the centre shows the total lost."""
    keys = [k for k, v in lost.items() if v > 0]
    values = [lost[k] for k in keys]
    colours = [MISTAKE.get(k, OK_LOSS) for k in keys]
    labels = [f"{k} · {v:g}" for k, v in zip(keys, values)]  # legend shows the marks
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.62, sort=False,
                           marker=dict(colors=colours, line=dict(color="#FFFFFF", width=2)),
                           textinfo="none", hovertemplate="%{label} marks<extra></extra>"))
    total = sum(values)
    fig.add_annotation(text=f"<b>{total:g}</b><br><span style='font-size:12px'>lost</span>",
                       showarrow=False, font=dict(size=22, color=TEXT))
    fig.update_layout(height=330, showlegend=True,
                      legend=dict(orientation="h", y=-0.05, x=0.5, xanchor="center", yanchor="top"),
                      margin=dict(l=8, r=8, t=8, b=8))
    return style_figure(fig)


def topic_progress_figure(rows, components: list[str]) -> go.Figure:
    """One line per topic across papers. ``rows``: DataFrame of component, topic, pct."""
    fig = go.Figure()
    # Invisible anchor so every paper keeps its slot, in order, even before it has marks.
    fig.add_scatter(x=list(components), y=[None] * len(components), mode="markers",
                    showlegend=False, hoverinfo="skip", marker=dict(opacity=0))
    for i, (topic, g) in enumerate(rows.groupby("topic", sort=False)):
        colour = TOPIC_LINES[i % len(TOPIC_LINES)]
        g = g.set_index("component").reindex([c for c in components if c in set(g["component"])])
        fig.add_scatter(x=list(g.index), y=list(g["pct"]), name=topic, mode="lines+markers",
                        line=dict(color=colour, width=3),
                        marker=dict(size=10, color="#FFFFFF", line=dict(color=colour, width=3)),
                        hovertemplate=f"{topic} · %{{x}}: %{{y:.0f}}%<extra></extra>")
    fig.update_xaxes(categoryorder="array", categoryarray=list(components), type="category",
                     range=[-0.3, len(components) - 0.7])
    fig.update_yaxes(range=[0, 105], ticksuffix="%", title=None)
    fig.update_layout(height=340, legend=dict(orientation="v", x=1.02, y=1))
    return style_figure(fig)
