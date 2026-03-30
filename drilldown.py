"""
drilldown.py
============
Drill-down state management and rendering for the TSG dashboard.
Uses st.session_state to track what's been clicked and render detail views.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots

from db import (
    load_quarterly, load_yoy_growth, load_fund_summary,
    load_flags, load_income_statement_ltm,
    format_millions, format_multiple, format_pct, flag_color
)

# Brand colors
NAVY      = "#071733"
SLATE     = "#3F6680"
SKY       = "#A8CFDE"
XANTHOUS  = "#F3B51F"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
BORDER    = "#E0E4EA"


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------

def set_drill(page: str, company: str = None, metric: str = None):
    """Set drill-down state."""
    st.session_state["drill_page"]    = page
    st.session_state["drill_company"] = company
    st.session_state["drill_metric"]  = metric


def clear_drill():
    """Clear drill-down state."""
    for key in ["drill_page", "drill_company", "drill_metric"]:
        st.session_state.pop(key, None)


def has_drill() -> bool:
    return "drill_page" in st.session_state


def get_drill() -> dict:
    return {
        "page":    st.session_state.get("drill_page"),
        "company": st.session_state.get("drill_company"),
        "metric":  st.session_state.get("drill_metric"),
    }


# ---------------------------------------------------------------------------
# Drill-down renderers
# ---------------------------------------------------------------------------

def render_drill_header(title: str):
    """Render a breadcrumb back button + title."""
    col_back, col_title = st.columns([1, 8])
    with col_back:
        if st.button("← Back", type="secondary", use_container_width=True):
            clear_drill()
            st.rerun()
    with col_title:
        st.markdown(
            f'<div style="font-size:18px; font-weight:700; color:{NAVY}; '
            f'font-family:Arial; padding-top:6px;">{title}</div>',
            unsafe_allow_html=True
        )
    st.markdown(f'<hr style="border-color:{BORDER}; margin:8px 0 16px 0;">',
                unsafe_allow_html=True)


def drill_company_detail(company_name: str):
    """
    Full company detail drill-down — triggered from Portfolio Overview card click.
    Shows KPI strip + Revenue/EBITDA trend + Net Leverage + Margin.
    """
    render_drill_header(f"Company Detail — {company_name}")

    flags        = load_flags()
    company_flag = flags[flags["company_name"] == company_name]
    flag_row     = company_flag.iloc[0] if len(company_flag) > 0 else None

    if flag_row is not None:
        kpi_cols = st.columns(6)
        kpis = [
            (format_millions(flag_row.get("ltm_revenue")),       "LTM Revenue"),
            (format_millions(flag_row.get("ltm_adj_ebitda")),     "LTM EBITDA"),
            (format_pct(flag_row.get("ltm_adj_ebitda_margin")),   "EBITDA Margin"),
            (format_multiple(flag_row.get("net_leverage")),        "Net Leverage"),
            (format_pct(flag_row.get("revenue_yoy")),              "Rev Growth YoY"),
            (flag_row.get("overall_flag", "—"),                   "Overall Flag"),
        ]
        for col, (val, label) in zip(kpi_cols, kpis):
            col.metric(label, val)

    st.markdown("<br>", unsafe_allow_html=True)

    quarterly = load_quarterly(company_name)
    if quarterly.empty:
        st.info("No quarterly data available.")
        return

    # Revenue & EBITDA chart
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    rev = quarterly["revenue"].combine_first(quarterly["net_sales"])
    fig.add_trace(go.Bar(x=quarterly["period_label"], y=rev,
                          name="Revenue", marker_color=NAVY, opacity=0.8),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=quarterly["period_label"], y=quarterly["adj_ebitda"],
                          name="Adj. EBITDA", marker_color=SLATE, opacity=0.8),
                  secondary_y=False)
    margin = quarterly["adj_ebitda"] / rev.replace(0, float("nan"))
    fig.add_trace(go.Scatter(x=quarterly["period_label"], y=margin,
                              name="EBITDA Margin %", mode="lines+markers",
                              line=dict(color=XANTHOUS, width=2)),
                  secondary_y=True)
    fig.update_layout(
        height=320, plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=0), barmode="group",
        title_text="Revenue & EBITDA Trend",
        font=dict(family="Arial", color=NAVY, size=10),
        legend=dict(orientation="h", y=-0.2)
    )
    fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False)
    fig.update_yaxes(tickformat=".0%", secondary_y=True)
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Leverage + Margin side by side
    col_l, col_m = st.columns(2)
    with col_l:
        lev_df = quarterly.dropna(subset=["net_leverage"])
        if not lev_df.empty:
            fig2 = go.Figure()
            fig2.add_hline(y=6.0, line_dash="dash", line_color=RED_FLAG,
                           annotation_text="6.0x Covenant")
            fig2.add_hline(y=5.0, line_dash="dot", line_color=XANTHOUS,
                           annotation_text="5.0x Watch")
            fig2.add_trace(go.Bar(
                x=lev_df["period_label"], y=lev_df["net_leverage"],
                marker_color=[RED_FLAG if v > 6 else XANTHOUS if v > 5 else NAVY
                              for v in lev_df["net_leverage"]]
            ))
            fig2.update_layout(height=260, plot_bgcolor="white", paper_bgcolor="white",
                                title_text="Net Leverage",
                                margin=dict(l=0, r=0, t=30, b=0),
                                font=dict(family="Arial", size=10, color=NAVY),
                                yaxis=dict(gridcolor=BORDER))
            fig2.update_xaxes(tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)

    with col_m:
        mgn_df = quarterly.dropna(subset=["adj_ebitda_margin_pct"])
        if not mgn_df.empty:
            fig3 = go.Figure()
            fig3.add_hline(y=0.18, line_dash="dash", line_color=SEA_GREEN,
                           annotation_text="18% Benchmark")
            fig3.add_hline(y=0.10, line_dash="dot", line_color=XANTHOUS,
                           annotation_text="10% Watch")
            fig3.add_trace(go.Scatter(
                x=mgn_df["period_label"], y=mgn_df["adj_ebitda_margin_pct"],
                mode="lines+markers", line=dict(color=SLATE, width=2),
                fill="tozeroy", fillcolor="rgba(63,102,128,0.1)"
            ))
            fig3.update_layout(height=260, plot_bgcolor="white", paper_bgcolor="white",
                                title_text="EBITDA Margin %",
                                margin=dict(l=0, r=0, t=30, b=0),
                                font=dict(family="Arial", size=10, color=NAVY),
                                yaxis=dict(tickformat=".0%", gridcolor=BORDER))
            fig3.update_xaxes(tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)


def drill_tev_history(company_name: str):
    """
    TEV/MOI history drill-down — triggered from Fund Summary row click.
    """
    render_drill_header(f"TEV & Valuation History — {company_name}")

    quarterly = load_quarterly(company_name)
    if quarterly.empty:
        st.info("No data available.")
        return

    tev_df = quarterly.dropna(subset=["tev"])
    if tev_df.empty:
        st.info("No TEV data available for this company.")
        return

    # Get entry TEV
    fs      = load_fund_summary()
    fs_row  = fs[fs["company_name"] == company_name]
    entry_tev = fs_row["entry_tev"].iloc[0] if len(fs_row) > 0 else None

    col_l, col_r = st.columns([3, 1])

    with col_l:
        fig = go.Figure()
        if entry_tev:
            fig.add_hline(y=entry_tev, line_dash="dash", line_color=SLATE,
                          annotation_text=f"Entry TEV: {format_millions(entry_tev)}")
        fig.add_trace(go.Scatter(
            x=tev_df["period_label"], y=tev_df["tev"],
            mode="lines+markers+text",
            line=dict(color=NAVY, width=2),
            marker=dict(size=8, color=NAVY),
            text=tev_df["tev"].apply(format_millions),
            textposition="top center",
            textfont=dict(size=9),
            name="TEV"
        ))
        # MOI line
        if entry_tev and entry_tev > 0:
            moi = tev_df["tev"] / entry_tev
            fig.add_trace(go.Scatter(
                x=tev_df["period_label"], y=moi * entry_tev,
                mode="none", name="", showlegend=False
            ))

        fig.update_layout(
            height=340, plot_bgcolor="white", paper_bgcolor="white",
            title_text="Total Enterprise Value ($M) — Quarterly",
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(family="Arial", color=NAVY, size=10),
            yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
        )
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown("**Valuation Summary**")
        if entry_tev:
            current_tev = tev_df["tev"].iloc[-1]
            gross_moi   = current_tev / entry_tev
            st.metric("Entry TEV",   format_millions(entry_tev))
            st.metric("Current TEV", format_millions(current_tev))
            st.metric("Gross MOI",   format_multiple(gross_moi))

        # LTM EBITDA used in valuation
        val_ebitda = quarterly["valuation_ltm_ebitda"].dropna()
        if not val_ebitda.empty:
            latest_ebitda  = val_ebitda.iloc[-1]
            latest_tev     = tev_df["tev"].iloc[-1]
            implied_mult   = latest_tev / latest_ebitda if latest_ebitda > 0 else None
            st.metric("Valuation EBITDA", format_millions(latest_ebitda))
            if implied_mult:
                st.metric("Implied EV/EBITDA", format_multiple(implied_mult))

    # EBITDA multiple trend
    val_df = quarterly.dropna(subset=["tev", "valuation_ltm_ebitda"]).copy()
    val_df = val_df[val_df["valuation_ltm_ebitda"] > 0].copy()
    if not val_df.empty:
        val_df["ev_ebitda"] = val_df["tev"] / val_df["valuation_ltm_ebitda"]
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=val_df["period_label"], y=val_df["ev_ebitda"],
            mode="lines+markers",
            line=dict(color=XANTHOUS, width=2),
            marker=dict(size=7)
        ))
        fig2.update_layout(
            height=220, plot_bgcolor="white", paper_bgcolor="white",
            title_text="Implied EV/EBITDA Multiple",
            margin=dict(l=0, r=0, t=40, b=0),
            font=dict(family="Arial", color=NAVY, size=10),
            yaxis=dict(tickformat=".1f", ticksuffix="x", gridcolor=BORDER),
        )
        fig2.update_xaxes(tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)


def drill_flag_metric(company_name: str, metric: str):
    """
    Flag metric trend drill-down — triggered from Flags & Alerts click.
    Shows the specific KPI trend that triggered the flag with benchmarks.
    """
    render_drill_header(f"{metric} Trend — {company_name}")

    quarterly = load_quarterly(company_name)
    growth    = load_yoy_growth(company_name)

    METRIC_CONFIG = {
        "Net Leverage": {
            "col":        "net_leverage",
            "source":     "quarterly",
            "fmt":        lambda x: f"{x:.1f}x",
            "benchmarks": [(6.0, RED_FLAG, "dash",  "6.0x Covenant"),
                           (5.0, XANTHOUS, "dot",   "5.0x Watch")],
            "yformat":    ".1f",
            "ysuffix":    "x",
            "bar":        True,
            "color_fn":   lambda v: RED_FLAG if v > 6 else XANTHOUS if v > 5 else NAVY,
        },
        "EBITDA Margin": {
            "col":        "adj_ebitda_margin_pct",
            "source":     "quarterly",
            "fmt":        lambda x: f"{x*100:.1f}%",
            "benchmarks": [(0.18, SEA_GREEN, "dash", "18% Benchmark"),
                           (0.10, XANTHOUS,  "dot",  "10% Watch")],
            "yformat":    ".0%",
            "bar":        False,
        },
        "Revenue Growth": {
            "col":        "revenue_yoy",
            "source":     "growth",
            "fmt":        lambda x: f"{x*100:.1f}%",
            "benchmarks": [(0.10,  SEA_GREEN, "dash", "10% Benchmark"),
                           (0.00,  XANTHOUS,  "dot",  "0% Watch")],
            "yformat":    ".0%",
            "bar":        False,
        },
        "Gross Margin": {
            "col":        "gross_margin_pct",
            "source":     "quarterly",
            "fmt":        lambda x: f"{x*100:.1f}%",
            "benchmarks": [(0.40, SEA_GREEN, "dash", "40% Benchmark"),
                           (0.30, XANTHOUS,  "dot",  "30% Watch")],
            "yformat":    ".0%",
            "bar":        False,
        },
    }

    cfg = METRIC_CONFIG.get(metric)
    if not cfg:
        st.warning(f"No drill-down configured for metric: {metric}")
        return

    df = growth if cfg["source"] == "growth" else quarterly
    col = cfg["col"]
    plot_df = df.dropna(subset=[col]).copy()

    if plot_df.empty:
        st.info(f"No {metric} data available for {company_name}.")
        return

    # KPI summary
    latest_val = plot_df[col].iloc[-1]
    flag_text  = load_flags()
    flag_row   = flag_text[flag_text["company_name"] == company_name]
    if len(flag_row) > 0:
        flag_status = flag_row.iloc[0].get(
            {"Net Leverage":    "net_leverage_flag",
             "EBITDA Margin":   "ebitda_margin_flag",
             "Revenue Growth":  "revenue_growth_flag",
             "Gross Margin":    "gross_margin_flag"}.get(metric, "overall_flag")
        )
        color = {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}.get(flag_status, SLATE)
        st.markdown(f"""
        <div style="background:white; border-left:4px solid {color};
                    border:1px solid {BORDER}; border-left:4px solid {color};
                    border-radius:4px; padding:12px 16px; margin-bottom:16px;
                    display:inline-block;">
            <span style="font-size:24px; font-weight:700; color:{color};
                         font-family:Arial;">{cfg['fmt'](latest_val)}</span>
            <span style="font-size:12px; color:{SLATE}; font-family:Arial;
                         margin-left:8px;">Latest · {flag_status or ''} Flag</span>
        </div>
        """, unsafe_allow_html=True)

    fig = go.Figure()

    # Benchmarks
    for level, bcolor, dash, label in cfg.get("benchmarks", []):
        fig.add_hline(y=level, line_dash=dash, line_color=bcolor,
                      annotation_text=label, annotation_position="right")

    if cfg.get("bar"):
        color_fn = cfg.get("color_fn", lambda v: NAVY)
        fig.add_trace(go.Bar(
            x=plot_df["period_label"], y=plot_df[col],
            marker_color=[color_fn(v) for v in plot_df[col]],
            text=plot_df[col].apply(cfg["fmt"]),
            textposition="outside"
        ))
    else:
        fig.add_trace(go.Scatter(
            x=plot_df["period_label"], y=plot_df[col],
            mode="lines+markers+text",
            line=dict(color=NAVY, width=2),
            marker=dict(size=7),
            text=plot_df[col].apply(cfg["fmt"]),
            textposition="top center",
            textfont=dict(size=9)
        ))

    yformat = cfg.get("yformat", ".1f")
    fig.update_layout(
        height=360, plot_bgcolor="white", paper_bgcolor="white",
        title_text=f"{metric} — Quarterly History",
        margin=dict(l=0, r=80, t=40, b=0),
        font=dict(family="Arial", color=NAVY, size=10),
        yaxis=dict(tickformat=yformat, gridcolor=BORDER),
    )
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    # Stats table
    stats_df = plot_df[["period_label", col]].copy()
    stats_df.columns = ["Period", metric]
    stats_df[metric] = stats_df[metric].apply(cfg["fmt"])
    st.dataframe(stats_df.set_index("Period"), use_container_width=True)


def drill_income_line(company_name: str, attribute_name: str):
    """
    Income statement line quarterly history — triggered from IS table click.
    """
    render_drill_header(f"{attribute_name} — {company_name}")

    quarterly = load_quarterly(company_name)

    # Map attribute name to column if it exists in the quarterly view
    COL_MAP = {
        "Revenue (Global)":           "revenue",
        "Net Sales":                  "net_sales",
        "Gross Profit":               "gross_profit",
        "Cost of Goods Sold":         "cogs",
        "EBITDA":                     "ebitda",
        "Adj. EBITDA":                "adj_ebitda",
        "Adj. EBITDA (Global)":       "adj_ebitda_global",
        "Interest Expense":           "interest_expense",
        "Depreciation & Amortization":"da",
        "Net Income":                 "net_income",
        "Cash from Operations":       "cfo",
        "Capital Expenditure":        "capex",
        "Net Debt (Global)":          "net_debt",
        "Total Debt / EBITDA (Global)":"net_leverage",
        "EBITDA Margin %":            "ebitda_margin_pct",
        "Adj. EBITDA Margin %":       "adj_ebitda_margin_pct",
        "Gross Profit Margin %":      "gross_margin_pct",
        "Total Enterprise Value (TEV)":"tev",
    }

    col = COL_MAP.get(attribute_name)

    if col and col in quarterly.columns:
        plot_df = quarterly.dropna(subset=[col])
        if not plot_df.empty:
            is_pct = "%" in attribute_name or "Margin" in attribute_name
            is_mult = "EBITDA (Global)" in attribute_name and "Total Debt" in attribute_name

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=plot_df["period_label"], y=plot_df[col],
                marker_color=NAVY, opacity=0.85,
                text=plot_df[col].apply(
                    lambda x: f"{x*100:.1f}%" if is_pct
                    else f"{x:.1f}x" if is_mult
                    else format_millions(x)
                ),
                textposition="outside"
            ))
            # Add YoY growth line
            growth = load_yoy_growth(company_name)
            if not growth.empty and "revenue_yoy" in growth.columns and col == "revenue":
                yoy_df = growth.dropna(subset=["revenue_yoy"])
                fig2_data = yoy_df[["period_label", "revenue_yoy"]].copy()
                # overlay as annotation
            fig.update_layout(
                height=340, plot_bgcolor="white", paper_bgcolor="white",
                title_text=f"{attribute_name} — Quarterly ($M)",
                margin=dict(l=0, r=0, t=40, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                yaxis=dict(
                    tickformat=".0%" if is_pct else "$,.0f",
                    gridcolor=BORDER
                )
            )
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Stats
            stats = plot_df[["period_label", col]].copy()
            stats.columns = ["Period", attribute_name]
            stats[attribute_name] = stats[attribute_name].apply(
                lambda x: f"{x*100:.1f}%" if is_pct else format_millions(x)
            )
            # Add YoY column
            if len(stats) > 4:
                vals = plot_df[col].values
                yoy = [None] * 4 + [
                    (vals[i] - vals[i-4]) / abs(vals[i-4]) if vals[i-4] != 0 else None
                    for i in range(4, len(vals))
                ]
                stats["YoY Growth"] = [
                    f"{v*100:+.1f}%" if v is not None else "—" for v in yoy
                ]
            st.dataframe(stats.set_index("Period"), use_container_width=True)
    else:
        # Fall back to raw IS data
        is_df = load_income_statement_ltm(company_name)
        row   = is_df[is_df["attribute_name"] == attribute_name]
        if not row.empty:
            r = row.iloc[0]
            col1, col2, col3 = st.columns(3)
            col1.metric("LTM Value",    f"{r['ltm_value']:,.1f}M" if r['ltm_value'] else "—")
            col2.metric("PY Value",     f"{r['py_value']:,.1f}M"  if r['py_value']  else "—")
            col3.metric("YoY Change",
                        f"{r['delta_pct']*100:+.1f}%" if r.get('delta_pct') else "—")
            st.info("Quarterly chart not available for this attribute — showing LTM summary only.")
        else:
            st.info(f"No quarterly data found for '{attribute_name}'.")
