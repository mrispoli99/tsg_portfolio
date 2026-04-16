"""
page_company_kpis.py
====================
Standalone Company-Specific KPI page.

Navigation: sidebar links per company.
Layout: KPI summary cards (top) + 2-column time-series chart grid (below).
Data:   company_kpis.csv (from vw_company_kpis) + company_kpi_config.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from db import load_company_kpis, load_company_kpis_all, load_company_master, format_millions, format_multiple, format_pct
from company_kpi_config import COMPANY_KPI_CONFIG

# ── Colour palette (matches the rest of the app) ─────────────────────────────
NAVY      = "#1B2A4A"
SLATE     = "#4A6FA5"
SKY       = "#A8C4E0"
XANTHOUS  = "#F3B51F"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
BORDER    = "#E0E4EA"
LIGHT_BG  = "#F7F8FA"

CHART_COLORS = [
    "#4A6FA5", "#1D9E75", "#F3B51F", "#D85A30",
    "#7F77DD", "#D4537E", "#378ADD", "#639922",
    "#BA7517", "#888780", "#1B2A4A", "#0F6E56",
]


def _fmt(value, fmt: str) -> str:
    """Format a single value using the configured format string."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if fmt == "millions":
        return format_millions(v)
    if fmt == "pct":
        # values stored as decimals (0.142) or whole numbers (14.2) — detect
        if abs(v) <= 2.0:
            return f"{v * 100:.1f}%"
        return f"{v:.1f}%"
    if fmt == "multiple":
        return format_multiple(v)
    if fmt == "number":
        return f"{int(round(v)):,}"
    if fmt == "thousands":
        return f"${v:,.0f}k" if abs(v) < 1000 else f"${v / 1000:.1f}M"
    return str(round(v, 2))


def _delta_str(current, previous, fmt: str) -> tuple[str, str]:
    """Return (delta_text, color) comparing current to previous period."""
    if current is None or previous is None:
        return "", SLATE
    try:
        c, p = float(current), float(previous)
    except (TypeError, ValueError):
        return "", SLATE
    if p == 0:
        return "", SLATE
    pct = (c - p) / abs(p) * 100
    sign = "+" if pct >= 0 else ""
    color = SEA_GREEN if pct >= 0 else RED_FLAG
    return f"{sign}{pct:.1f}% vs. PY", color


def _make_bar_chart(df: pd.DataFrame, attr: str, label: str,
                    fmt: str, color: str) -> go.Figure:
    """Grouped bar chart — one bar per period."""
    y = df[attr] if attr in df.columns else pd.Series(dtype=float)
    # Normalise pct stored as decimals
    if fmt == "pct" and not y.empty and y.dropna().abs().max() <= 2.0:
        y = y * 100
    fig = go.Figure(go.Bar(
        x=df["period_label"],
        y=y,
        marker_color=color,
        opacity=0.88,
        text=y.apply(lambda v: _fmt(v, fmt) if pd.notna(v) else ""),
        textposition="outside",
        textfont=dict(size=9),
    ))
    fig.update_layout(
        height=220,
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=8, b=0),
        font=dict(family="Arial", color=NAVY, size=10),
        showlegend=False,
        xaxis=dict(tickangle=-45, tickfont=dict(size=9), gridcolor=BORDER,
                   tickmode="array",
                   tickvals=df["period_label"].tolist(),
                   ticktext=df["period_label"].tolist()),
        yaxis=dict(gridcolor=BORDER,
                   tickformat=".0%" if fmt == "pct" else None,
                   showticklabels=True,
                   tickfont=dict(size=9)),
    )
    return fig


def _make_line_chart(df: pd.DataFrame, attr: str, label: str,
                     fmt: str, color: str) -> go.Figure:
    """Line chart — time-series trend."""
    y = df[attr] if attr in df.columns else pd.Series(dtype=float)
    if fmt == "pct" and not y.empty and y.dropna().abs().max() <= 2.0:
        y = y * 100
    fig = go.Figure(go.Scatter(
        x=df["period_label"],
        y=y,
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=5, color=color),
        connectgaps=True,
    ))
    fig.update_layout(
        height=220,
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=8, b=0),
        font=dict(family="Arial", color=NAVY, size=10),
        showlegend=False,
        xaxis=dict(tickangle=-45, tickfont=dict(size=9), gridcolor=BORDER,
                   tickmode="array",
                   tickvals=df["period_label"].tolist(),
                   ticktext=df["period_label"].tolist()),
        yaxis=dict(gridcolor=BORDER,
                   tickformat=".1f" if fmt == "pct" else None,
                   tickfont=dict(size=9)),
    )
    return fig


def page_company_kpis():
    """Main render function — called from app.py."""

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .kpi-card-co {
        background: #F7F8FA;
        border-radius: 8px;
        padding: 14px 16px;
    }
    .kpi-card-co .label {
        font-size: 11px;
        color: #6B7280;
        font-family: Arial;
        margin-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .kpi-card-co .value {
        font-size: 22px;
        font-weight: 500;
        color: #1B2A4A;
        font-family: Arial;
    }
    .kpi-card-co .delta {
        font-size: 11px;
        font-family: Arial;
        margin-top: 3px;
    }
    .chart-card-co {
        background: white;
        border: 0.5px solid #E0E4EA;
        border-radius: 10px;
        padding: 14px 16px 10px;
        margin-bottom: 12px;
    }
    .chart-title-co {
        font-size: 12px;
        font-weight: 500;
        color: #1B2A4A;
        font-family: Arial;
        margin-bottom: 6px;
    }
    .section-header-co {
        font-size: 11px;
        font-weight: 500;
        color: #888;
        font-family: Arial;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        border-bottom: 1px solid #E0E4EA;
        padding-bottom: 6px;
        margin: 16px 0 12px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Company list from config ──────────────────────────────────────────────
    companies = sorted(COMPANY_KPI_CONFIG.keys())

    # ── Sidebar selector ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### Company KPIs")
        selected = st.radio(
            "Select company",
            companies,
            label_visibility="collapsed",
            key="kpi_page_company",
        )

    if selected not in COMPANY_KPI_CONFIG:
        st.info("No KPI config found for this company.")
        return

    cfg = COMPANY_KPI_CONFIG[selected]
    kpi_cards  = cfg.get("kpi_cards", [])
    kpi_charts = cfg.get("kpi_charts", [])

    # ── Period selector ───────────────────────────────────────────────────────
    all_attrs = [k["attribute"] for k in kpi_cards] + [k["attribute"] for k in kpi_charts]

    period_col, _, info_col = st.columns([2, 4, 2])
    with period_col:
        period_mode = st.radio(
            "Period",
            ["Monthly", "Quarterly", "Annual"],
            index=1,
            horizontal=True,
            key="kpi_page_period",
        )
    period_map = {"Monthly": "Monthly", "Quarterly": "Quarterly", "Annual": "Annual"}
    period_val = period_map[period_mode]

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_company_kpis(selected, all_attrs, period_val)

    # ── Company header ────────────────────────────────────────────────────────
    initials = "".join(w[0] for w in selected.split()[:2]).upper()
    last_date = df["cash_flow_date"].max().strftime("%b %Y") if not df.empty else "—"

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:14px; margin-bottom:20px;">
        <div style="width:44px;height:44px;border-radius:8px;background:#1B2A4A;
                    display:flex;align-items:center;justify-content:center;
                    font-size:14px;font-weight:500;color:white;font-family:Arial;
                    flex-shrink:0;">{initials}</div>
        <div>
            <div style="font-size:20px;font-weight:500;color:#1B2A4A;font-family:Arial;">
                {selected}</div>
            <div style="font-size:12px;color:#6B7280;font-family:Arial;margin-top:2px;">
                Company-Specific KPIs &nbsp;·&nbsp; Last updated {last_date}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.info(f"No {period_mode} data found for **{selected}**. "
                f"Check that `company_kpis.csv` has been exported and contains data for this company.")
        return

    # ── KPI cards ─────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header-co">Latest period</div>', unsafe_allow_html=True)

    latest = df.sort_values("cash_flow_date").iloc[-1]
    prev_rows = df.sort_values("cash_flow_date")
    prev = prev_rows.iloc[-2] if len(prev_rows) >= 2 else None

    cols = st.columns(len(kpi_cards)) if kpi_cards else []
    for i, card in enumerate(kpi_cards):
        attr  = card["attribute"]
        fmt   = card["format"]
        label = card["label"]
        val   = latest.get(attr) if attr in latest.index else None
        pval  = prev.get(attr) if (prev is not None and attr in prev.index) else None
        delta, dcol = _delta_str(val, pval, fmt)
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card-co">
                <div class="label">{label}</div>
                <div class="value">{_fmt(val, fmt)}</div>
                <div class="delta" style="color:{dcol};">{delta}&nbsp;</div>
            </div>
            """, unsafe_allow_html=True)

    # ── KPI Charts ────────────────────────────────────────────────────────────
    if kpi_charts:
        st.markdown('<div class="section-header-co">Trend charts</div>', unsafe_allow_html=True)

        # Cap at last 12 periods for readability
        chart_df = df.sort_values("cash_flow_date").tail(12)

        # 2-column grid
        for row_start in range(0, len(kpi_charts), 2):
            pair = kpi_charts[row_start: row_start + 2]
            cols = st.columns(2)
            for col_idx, chart_cfg in enumerate(pair):
                attr  = chart_cfg["attribute"]
                fmt   = chart_cfg["format"]
                label = chart_cfg["label"]
                ctype = chart_cfg.get("chart", "bar")
                color = CHART_COLORS[row_start + col_idx % len(CHART_COLORS)]

                with cols[col_idx]:
                    # Check data exists
                    has_data = attr in chart_df.columns and chart_df[attr].notna().any()

                    st.markdown(f'<div class="chart-card-co">'
                                f'<div class="chart-title-co">{label}</div></div>',
                                unsafe_allow_html=True)

                    if not has_data:
                        st.caption(f"No data available for '{attr}'")
                        continue

                    if ctype == "line":
                        fig = _make_line_chart(chart_df, attr, label, fmt, color)
                    else:
                        fig = _make_bar_chart(chart_df, attr, label, fmt, color)

                    st.plotly_chart(fig, use_container_width=True,
                                    config={"displayModeBar": False})
