"""
page_portfolio_flags.py
=======================
Portfolio Metric Flags dashboard page.
Implements the TSG flag framework from Portfolio_Metric_Flags.xlsx.

Sections:
  1. Portfolio heatmap — all companies x all metrics
  2. Signal summary — Distress / Watchlist / Outperformer counts
  3. Category deep dives — Leverage, Coverage, Valuation, etc.
  4. Company scorecard — full flag breakdown for one company
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

from db import get_engine, get_company_list, format_millions, format_multiple, format_pct
from sqlalchemy import text

# Brand colors
NAVY      = "#071733"
SLATE     = "#3F6680"
SKY       = "#A8CFDE"
XANTHOUS  = "#F3B51F"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
LIGHT_BG  = "#F4F6F9"
BORDER    = "#E0E4EA"
BEST_CLR  = "#1A5276"   # dark navy for "Best"

FLAG_COLORS = {
    "Best":   BEST_CLR,
    "Green":  SEA_GREEN,
    "Yellow": XANTHOUS,
    "Red":    RED_FLAG,
    "N/A":    "#CCCCCC",
}

FLAG_EMOJI = {
    "Best":   "⭐",
    "Green":  "🟢",
    "Yellow": "🟡",
    "Red":    "🔴",
    "N/A":    "⚪",
}

FLAG_SORT = {"Red": 0, "Yellow": 1, "Green": 2, "Best": 3, "N/A": 4}

# Metric definitions — display name, category, format function
METRICS = [
    # (column, display_name, category, format_fn)
    ("net_leverage",            "Net Debt / EBITDA",      "Leverage",   lambda x: f"{x:.1f}x"),
    ("gross_leverage",          "Gross Debt / EBITDA",    "Leverage",   lambda x: f"{x:.1f}x"),
    ("senior_secured_leverage", "Senior Secured / EBITDA","Leverage",   lambda x: f"{x:.1f}x"),
    ("interest_coverage",       "Interest Coverage",       "Coverage",   lambda x: f"{x:.1f}x"),
    ("debt_service_coverage",   "Debt Service Coverage",   "Coverage",   lambda x: f"{x:.1f}x"),
    ("free_cash_flow",          "Free Cash Flow ($M)",     "Cash Flow",  lambda x: f"${x:.1f}M"),
    ("ebitda_margin",           "EBITDA Margin",           "Operating",  lambda x: f"{x*100:.1f}%"),
    ("tev_to_revenue",          "TEV / Revenue",           "Valuation",  lambda x: f"{x:.1f}x"),
    ("tev_to_ebitda",           "TEV / EBITDA",            "Valuation",  lambda x: f"{x:.1f}x"),
    ("gross_moi",               "MOIC",                    "Returns",    lambda x: f"{x:.2f}x"),
    ("cash_to_debt",            "Cash / Gross Debt",       "Liquidity",  lambda x: f"{x*100:.1f}%"),
    ("floating_rate_pct",       "Floating Rate Debt %",    "Liquidity",  lambda x: f"{x*100:.1f}%"),
]

FLAG_COLS = [
    ("flag_net_leverage",      "Net Debt / EBITDA"),
    ("flag_gross_leverage",    "Gross Debt / EBITDA"),
    ("flag_senior_secured",    "Sr. Secured / EBITDA"),
    ("flag_interest_coverage", "Interest Coverage"),
    ("flag_debt_service",      "Debt Service"),
    ("flag_free_cash_flow",    "Free Cash Flow"),
    ("flag_ebitda_margin",     "EBITDA Margin"),
    ("flag_tev_revenue",       "TEV / Revenue"),
    ("flag_tev_ebitda",        "TEV / EBITDA"),
    ("flag_moic",              "MOIC"),
    ("flag_cash_to_debt",      "Cash / Debt"),
    ("flag_floating_rate",     "Floating Rate %"),
]

SIGNAL_COLS = [
    ("signal_distress",     "Distress",          RED_FLAG,  "High default risk"),
    ("signal_liquidity_risk","Liquidity Risk",    RED_FLAG,  "Low cash buffer"),
    ("signal_refi_risk",    "Refi Risk",          XANTHOUS,  "Near-term maturity wall"),
    ("signal_rate_risk",    "Rate Risk",          XANTHOUS,  "Floating rate exposure"),
    ("signal_watchlist",    "Watchlist",          XANTHOUS,  "Weakening credit profile"),
    ("signal_healthy",      "Healthy",            SEA_GREEN, "Stable performer"),
    ("signal_outperformer", "Outperformer",       BEST_CLR,  "Top quartile deal"),
]


@st.cache_data(ttl=86400)
def load_portfolio_flags() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM dbo.vw_portfolio_flags ORDER BY red_flag_count DESC, company_name",
                       get_engine())


def flag_badge_html(flag: str) -> str:
    color = FLAG_COLORS.get(flag, "#ccc")
    emoji = FLAG_EMOJI.get(flag, "⚪")
    return (f'<span style="background:{color}20; color:{color}; border:1px solid {color}; '
            f'border-radius:10px; padding:2px 8px; font-size:10px; font-weight:600; '
            f'font-family:Arial;">{emoji} {flag}</span>')


def section_header(title: str):
    st.markdown(
        f'<div style="font-size:12px; font-weight:700; color:{SLATE}; font-family:Arial; '
        f'text-transform:uppercase; letter-spacing:0.8px; border-bottom:2px solid {SKY}; '
        f'padding-bottom:6px; margin:20px 0 14px 0;">{title}</div>',
        unsafe_allow_html=True
    )


def page_portfolio_flags():
    from ui import render_page_header
    render_page_header("Portfolio Metric Flags")

    df = load_portfolio_flags()

    if df.empty:
        st.error("vw_portfolio_flags view not found. Run vw_portfolio_flags.sql in SSMS first.")
        return

    # -----------------------------------------------------------------------
    # 1. SIGNAL SUMMARY STRIP
    # -----------------------------------------------------------------------
    section_header("Portfolio Signals")

    sig_cols = st.columns(len(SIGNAL_COLS))
    for col, (sig_col, label, color, desc) in zip(sig_cols, SIGNAL_COLS):
        count = int(df[sig_col].sum()) if sig_col in df.columns else 0
        companies = df[df[sig_col] == 1]["company_name"].tolist() if sig_col in df.columns else []
        col.markdown(f"""
        <div style="background:white;border:1px solid {BORDER};border-top:3px solid {color};
                    border-radius:6px;padding:12px 10px;text-align:center;">
            <div style="font-size:24px;font-weight:700;color:{color};font-family:Arial;">
                {count}</div>
            <div style="font-size:10px;font-weight:700;color:{NAVY};font-family:Arial;
                        margin-top:2px;">{label}</div>
            <div style="font-size:9px;color:{SLATE};font-family:Arial;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
        if companies and count > 0:
            col.caption(", ".join(companies[:3]) + ("..." if len(companies) > 3 else ""))

    # -----------------------------------------------------------------------
    # 2. PORTFOLIO HEATMAP
    # -----------------------------------------------------------------------
    section_header("Portfolio Flag Heatmap — All Companies × All Metrics")

    # Build heatmap data
    flag_col_names  = [c for c, _ in FLAG_COLS]
    flag_disp_names = [n for _, n in FLAG_COLS]

    # Map flags to numeric for color scale
    flag_to_num = {"Red": 0, "Yellow": 1, "Green": 2, "Best": 3, "N/A": -1}
    num_to_color = {-1: "#EEEEEE", 0: RED_FLAG, 1: XANTHOUS, 2: SEA_GREEN, 3: BEST_CLR}

    companies = df["company_name"].tolist()
    heatmap_z   = []
    heatmap_text = []

    for _, row in df.iterrows():
        z_row    = []
        txt_row  = []
        for fc in flag_col_names:
            flag_val = row.get(fc, "N/A") or "N/A"
            z_row.append(flag_to_num.get(flag_val, -1))
            # Get the raw value for hover
            metric_col = fc.replace("flag_", "")
            # map flag col back to value col
            val_map = {
                "flag_net_leverage":      "net_leverage",
                "flag_gross_leverage":    "gross_leverage",
                "flag_senior_secured":    "senior_secured_leverage",
                "flag_interest_coverage": "interest_coverage",
                "flag_debt_service":      "debt_service_coverage",
                "flag_free_cash_flow":    "free_cash_flow",
                "flag_ebitda_margin":     "ebitda_margin",
                "flag_tev_revenue":       "tev_to_revenue",
                "flag_tev_ebitda":        "tev_to_ebitda",
                "flag_moic":              "gross_moi",
                "flag_cash_to_debt":      "cash_to_debt",
                "flag_floating_rate":     "floating_rate_pct",
            }
            val_col = val_map.get(fc)
            val = row.get(val_col) if val_col else None
            val_str = f"{val:.2f}" if val is not None and not pd.isna(val) else "—"
            txt_row.append(f"{flag_val}<br>{val_str}")
        heatmap_z.append(z_row)
        heatmap_text.append(txt_row)

    colorscale = [
        [0.0,  "#EEEEEE"],
        [0.25, RED_FLAG],
        [0.5,  XANTHOUS],
        [0.75, SEA_GREEN],
        [1.0,  BEST_CLR],
    ]

    fig = go.Figure(go.Heatmap(
        z=heatmap_z,
        x=flag_disp_names,
        y=companies,
        text=heatmap_text,
        texttemplate="%{text}",
        textfont=dict(size=8, color="white"),
        colorscale=colorscale,
        zmin=-1, zmax=3,
        showscale=False,
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        height=max(400, len(companies) * 30 + 100),
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family="Arial", color=NAVY, size=9),
        xaxis=dict(tickangle=-45, side="top"),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"""
    <div style="font-size:10px; color:{SLATE}; font-family:Arial; margin-top:-10px;">
        ⭐ <b>Best</b> &nbsp;|&nbsp;
        🟢 <b>Green</b> = on track &nbsp;|&nbsp;
        🟡 <b>Yellow</b> = watch &nbsp;|&nbsp;
        🔴 <b>Red</b> = breach &nbsp;|&nbsp;
        ⚪ N/A = insufficient data
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # 3. CATEGORY DEEP DIVES
    # -----------------------------------------------------------------------
    section_header("Flag Details by Category")

    categories = ["Leverage", "Coverage", "Cash Flow", "Valuation", "Returns", "Liquidity", "Operating"]
    cat_tabs   = st.tabs(categories)

    cat_flag_map = {
        "Leverage":  [("flag_net_leverage","Net Debt/EBITDA","net_leverage"),
                      ("flag_gross_leverage","Gross Debt/EBITDA","gross_leverage"),
                      ("flag_senior_secured","Sr. Secured/EBITDA","senior_secured_leverage")],
        "Coverage":  [("flag_interest_coverage","Interest Coverage","interest_coverage"),
                      ("flag_debt_service","Debt Service Coverage","debt_service_coverage")],
        "Cash Flow": [("flag_free_cash_flow","Free Cash Flow ($M)","free_cash_flow")],
        "Valuation": [("flag_tev_revenue","TEV / Revenue","tev_to_revenue"),
                      ("flag_tev_ebitda","TEV / EBITDA","tev_to_ebitda")],
        "Returns":   [("flag_moic","MOIC","gross_moi")],
        "Liquidity": [("flag_cash_to_debt","Cash / Gross Debt","cash_to_debt"),
                      ("flag_floating_rate","Floating Rate %","floating_rate_pct")],
        "Operating": [("flag_ebitda_margin","EBITDA Margin","ebitda_margin")],
    }

    fmt_map = {
        "net_leverage":            lambda x: f"{x:.1f}x",
        "gross_leverage":          lambda x: f"{x:.1f}x",
        "senior_secured_leverage": lambda x: f"{x:.1f}x",
        "interest_coverage":       lambda x: f"{x:.1f}x",
        "debt_service_coverage":   lambda x: f"{x:.1f}x",
        "free_cash_flow":          lambda x: f"${x:.1f}M",
        "tev_to_revenue":          lambda x: f"{x:.1f}x",
        "tev_to_ebitda":           lambda x: f"{x:.1f}x",
        "gross_moi":               lambda x: f"{x:.2f}x",
        "cash_to_debt":            lambda x: f"{x*100:.1f}%",
        "floating_rate_pct":       lambda x: f"{x*100:.1f}%",
        "ebitda_margin":           lambda x: f"{x*100:.1f}%",
    }

    for tab, cat in zip(cat_tabs, categories):
        with tab:
            metrics = cat_flag_map.get(cat, [])
            for flag_col, disp_name, val_col in metrics:
                st.markdown(f"**{disp_name}**")
                plot_df = df[["company_name", flag_col, val_col]].copy()
                plot_df = plot_df.dropna(subset=[val_col])
                plot_df = plot_df.sort_values(val_col, ascending=True)
                plot_df["color"] = plot_df[flag_col].map(FLAG_COLORS).fillna("#ccc")
                plot_df["flag"]  = plot_df[flag_col].fillna("N/A")
                fmt = fmt_map.get(val_col, lambda x: f"{x:.2f}")
                plot_df["label"] = plot_df[val_col].apply(fmt)

                fig = go.Figure(go.Bar(
                    x=plot_df[val_col],
                    y=plot_df["company_name"],
                    orientation="h",
                    marker_color=plot_df["color"].tolist(),
                    text=plot_df["label"],
                    textposition="outside",
                    customdata=plot_df["flag"],
                    hovertemplate="<b>%{y}</b><br>%{x:.2f}<br>Flag: %{customdata}<extra></extra>",
                ))
                fig.update_layout(
                    height=max(250, len(plot_df) * 28 + 60),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=60, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(gridcolor=BORDER),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------------------------
    # 4. COMPANY SCORECARD
    # -----------------------------------------------------------------------
    section_header("Company Scorecard — Full Flag Breakdown")

    selected = st.selectbox("Select Company", df["company_name"].tolist(),
                             label_visibility="collapsed")

    if selected:
        row = df[df["company_name"] == selected].iloc[0]
        render_company_scorecard(row)


def render_company_scorecard(row: pd.Series):
    """Render the full flag scorecard for one company — used on Company Detail page too."""
    company_name = row.get("company_name", "")

    # Signal badges
    active_signals = []
    for sig_col, label, color, desc in SIGNAL_COLS:
        if row.get(sig_col) == 1:
            active_signals.append((label, color, desc))

    if active_signals:
        badges = " ".join([
            f'<span style="background:{c}20;color:{c};border:1px solid {c};'
            f'border-radius:10px;padding:3px 10px;font-size:11px;font-weight:600;'
            f'font-family:Arial;margin-right:6px;">{l}</span>'
            for l, c, d in active_signals
        ])
        st.markdown(f'<div style="margin-bottom:12px;">{badges}</div>',
                    unsafe_allow_html=True)

    # Flag grid
    flag_items = [
        ("Net Debt / EBITDA",       "flag_net_leverage",      "net_leverage",            lambda x: f"{x:.1f}x"),
        ("Gross Debt / EBITDA",     "flag_gross_leverage",    "gross_leverage",           lambda x: f"{x:.1f}x"),
        ("Sr. Secured / EBITDA",    "flag_senior_secured",    "senior_secured_leverage",  lambda x: f"{x:.1f}x"),
        ("Interest Coverage",       "flag_interest_coverage", "interest_coverage",        lambda x: f"{x:.1f}x"),
        ("Debt Service Coverage",   "flag_debt_service",      "debt_service_coverage",    lambda x: f"{x:.1f}x"),
        ("Free Cash Flow",          "flag_free_cash_flow",    "free_cash_flow",           lambda x: f"${x:.1f}M"),
        ("EBITDA Margin",           "flag_ebitda_margin",     "ebitda_margin",            lambda x: f"{x*100:.1f}%"),
        ("TEV / Revenue",           "flag_tev_revenue",       "tev_to_revenue",           lambda x: f"{x:.1f}x"),
        ("TEV / EBITDA",            "flag_tev_ebitda",        "tev_to_ebitda",            lambda x: f"{x:.1f}x"),
        ("MOIC",                    "flag_moic",              "gross_moi",                lambda x: f"{x:.2f}x"),
        ("Cash / Gross Debt",       "flag_cash_to_debt",      "cash_to_debt",             lambda x: f"{x*100:.1f}%"),
        ("Floating Rate Debt %",    "flag_floating_rate",     "floating_rate_pct",        lambda x: f"{x*100:.1f}%"),
    ]

    cols = st.columns(4)
    for i, (label, flag_col, val_col, fmt) in enumerate(flag_items):
        col   = cols[i % 4]
        flag  = row.get(flag_col, "N/A") or "N/A"
        val   = row.get(val_col)
        color = FLAG_COLORS.get(flag, "#ccc")
        val_str = fmt(val) if val is not None and not pd.isna(val) else "—"

        col.markdown(f"""
        <div style="background:white;border:1px solid {BORDER};border-left:4px solid {color};
                    border-radius:4px;padding:10px 12px;margin-bottom:8px;">
            <div style="font-size:18px;font-weight:700;color:{color};font-family:Arial;">
                {val_str}</div>
            <div style="font-size:10px;color:{SLATE};font-family:Arial;margin-top:2px;">
                {label}</div>
            <div style="margin-top:4px;">{flag_badge_html(flag)}</div>
        </div>
        """, unsafe_allow_html=True)

    # Summary counts
    red_count    = int(row.get("red_flag_count", 0))
    yellow_count = int(row.get("yellow_flag_count", 0))
    green_best   = sum(1 for _, fc, _, _ in flag_items
                       if row.get(fc) in ("Green", "Best"))

    st.markdown(f"""
    <div style="background:white;border:1px solid {BORDER};border-radius:6px;
                padding:12px 16px;margin-top:8px;display:flex;gap:24px;align-items:center;">
        <span style="font-size:13px;color:{NAVY};font-family:Arial;font-weight:700;">
            Summary:</span>
        <span style="color:{RED_FLAG};font-weight:700;">🔴 {red_count} Red</span>
        <span style="color:{XANTHOUS};font-weight:700;">🟡 {yellow_count} Yellow</span>
        <span style="color:{SEA_GREEN};font-weight:700;">🟢 {green_best} Green/Best</span>
    </div>
    """, unsafe_allow_html=True)
