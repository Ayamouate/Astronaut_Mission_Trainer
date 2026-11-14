"""Reusable Plotly charts for simulated mission history."""

from __future__ import annotations

from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


COLORS = ["#42D9E8", "#55E6B5", "#F4BC62", "#F16B78", "#7EA6FF"]


def _available(history: pd.DataFrame, indicator_ids: Iterable[str]) -> list[str]:
    return [indicator_id for indicator_id in indicator_ids if indicator_id in history.columns]


def render_history_chart(history: pd.DataFrame, indicator_id: str, indicators: dict[str, dict], title: str | None = None, color: str = "#42D9E8", height: int = 245) -> None:
    """Render one indicator over time with its configured normal band."""
    indicator = indicators.get(indicator_id)
    if not indicator or indicator_id not in history.columns or history.empty:
        st.info(f"No history is available for {indicator.get('short_label', indicator_id) if indicator else indicator_id}.")
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=history.get("timestamp"), y=pd.to_numeric(history[indicator_id], errors="coerce"), mode="lines+markers", name=indicator.get("short_label", indicator_id), line={"color": color, "width": 2}, marker={"size": 5, "color": color}, hovertemplate=f"%{{x|%b %d}}<br><b>%{{y:.1f}} {indicator.get('unit', '')}</b><extra></extra>"))
    normal = indicator.get("thresholds", {}).get("normal")
    if normal and len(normal) == 2:
        fig.add_hrect(y0=normal[0], y1=normal[1], fillcolor=color, opacity=.06, line_width=0)
    _style(fig, height=height, y_title=indicator.get("unit", ""), title=title)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_multi_history_chart(history: pd.DataFrame, indicator_ids: Iterable[str], indicators: dict[str, dict], title: str, height: int = 275) -> None:
    """Render multiple comparable indicators on one chart."""
    available = _available(history, indicator_ids)
    if not available or history.empty:
        st.info("No history is available for this chart yet.")
        return
    fig = go.Figure()
    for index, indicator_id in enumerate(available):
        indicator = indicators[indicator_id]
        fig.add_trace(go.Scatter(x=history.get("timestamp"), y=pd.to_numeric(history[indicator_id], errors="coerce"), mode="lines+markers", name=indicator.get("short_label", indicator_id), line={"color": COLORS[index % len(COLORS)], "width": 2}, marker={"size": 4}))
    _style(fig, height=height, y_title="configured units", title=title)
    fig.update_layout(showlegend=True, legend={"orientation": "h", "y": 1.12, "font": {"size": 10}})
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_bar_chart(history: pd.DataFrame, indicator_id: str, indicators: dict[str, dict], title: str, days: int = 7) -> None:
    """Render a compact recent-activity bar chart."""
    indicator = indicators.get(indicator_id)
    if not indicator or indicator_id not in history.columns or history.empty:
        st.info("No activity history is available yet.")
        return
    recent = history.tail(days)
    fig = go.Figure(go.Bar(x=recent.get("timestamp"), y=pd.to_numeric(recent[indicator_id], errors="coerce"), marker_color="#42D9E8", hovertemplate=f"%{{x|%b %d}}<br><b>%{{y:.0f}} {indicator.get('unit', '')}</b><extra></extra>"))
    _style(fig, height=250, y_title=indicator.get("unit", ""), title=title)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _style(fig: go.Figure, height: int, y_title: str, title: str | None) -> None:
    fig.update_layout(title=title, height=height, margin={"l": 8, "r": 8, "t": 28 if title else 10, "b": 8}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font={"family": "JetBrains Mono", "color": "#93A9B9", "size": 11}, showlegend=False, xaxis={"showgrid": False, "linecolor": "#29435A", "tickfont": {"size": 10}}, yaxis={"showgrid": True, "gridcolor": "#1D3548", "zeroline": False, "title": {"text": y_title, "font": {"size": 10}}, "tickfont": {"size": 10}})

