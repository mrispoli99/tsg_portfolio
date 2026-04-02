"""
app.py — TSG Consumer Portfolio Dashboard
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from drilldown import (
    set_drill, clear_drill, has_drill, get_drill,
    drill_company_detail, drill_tev_history,
    drill_flag_metric, drill_income_line
)
from db import (
    load_portfolio_overview, load_fund_summary, load_company_master,
    load_flags, load_ltm_snapshot, load_quarterly, load_yoy_growth,
    get_company_list, format_millions, format_multiple, format_pct,
    flag_color, flag_emoji
)
from ai import build_portfolio_context, build_company_context, ask_claude

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="TSG Consumer | Portfolio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# TSG Brand Colors
# ---------------------------------------------------------------------------
NAVY       = "#071733"
SLATE      = "#3F6680"
SKY        = "#A8CFDE"
XANTHOUS   = "#F3B51F"
CELADON    = "#85D7B0"
SEA_GREEN  = "#06865C"
MAGENTA    = "#A21586"
EGGPLANT   = "#483348"
PAPAYA     = "#FDEFD5"
RED_FLAG   = "#C0392B"
LIGHT_BG   = "#F4F6F9"
BORDER     = "#E0E4EA"

COMPANY_COLORS = [
    NAVY, SLATE, SKY, XANTHOUS, CELADON,
    SEA_GREEN, MAGENTA, EGGPLANT, "#3498DB", "#E67E22",
    "#9B59B6", "#1ABC9C", "#E74C3C", "#2ECC71", "#F39C12",
    "#16A085", "#8E44AD", "#D35400", "#27AE60", "#2980B9",
]

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown(f"""
<style>
    /* ---- Reset & base ---- */
    .stApp {{ background-color: {LIGHT_BG}; }}
    #MainMenu, footer, .stDeployButton {{ visibility: hidden; }}

    /* ---- Hide sidebar entirely ---- */
    [data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="collapsedControl"] {{ display: none !important; }}

    /* ---- Remove Streamlit default top padding ---- */
    .block-container {{ padding-top: 0 !important; max-width: 100% !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}

    /* ---- Top brand bar ---- */
    .tsg-brand-bar {{
        background: {NAVY};
        padding: 0 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 52px;
        position: sticky;
        top: 0;
        z-index: 999;
        margin-bottom: 0;
    }}
    .tsg-brand-logo {{
        font-size: 18px;
        font-weight: 700;
        color: white;
        font-family: Arial, sans-serif;
        letter-spacing: 0.5px;
        white-space: nowrap;
    }}
    .tsg-brand-meta {{
        font-size: 11px;
        color: {SKY};
        font-family: Arial, sans-serif;
        text-align: right;
    }}

    /* ---- Nav tab bar ---- */
    .tsg-nav-bar {{
        background: white;
        border-bottom: 2px solid {BORDER};
        padding: 0 24px;
        display: flex;
        align-items: center;
        gap: 0;
        overflow-x: auto;
        white-space: nowrap;
        margin-bottom: 0;
    }}
    .tsg-nav-tab {{
        display: inline-block;
        padding: 12px 18px;
        font-size: 13px;
        font-family: Arial, sans-serif;
        font-weight: 500;
        color: {SLATE};
        cursor: pointer;
        border-bottom: 3px solid transparent;
        margin-bottom: -2px;
        text-decoration: none;
        transition: all 0.15s;
        white-space: nowrap;
    }}
    .tsg-nav-tab:hover {{
        color: {NAVY};
        border-bottom-color: {SKY};
    }}
    .tsg-nav-tab.active {{
        color: {NAVY};
        font-weight: 700;
        border-bottom-color: {NAVY};
    }}

    /* ---- Alert badge in nav ---- */
    .tsg-nav-badge {{
        display: inline-block;
        background: {RED_FLAG};
        color: white;
        font-size: 9px;
        font-weight: 700;
        border-radius: 8px;
        padding: 1px 5px;
        margin-left: 4px;
        vertical-align: middle;
    }}

    /* ---- Page content area ---- */
    .tsg-page-content {{
        padding: 16px 24px;
    }}

    /* ---- Standardized KPI tiles ---- */
    .kpi-tile {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 14px 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .kpi-tile-value {{
        font-size: 24px;
        font-weight: 700;
        color: {NAVY};
        font-family: Arial, sans-serif;
        line-height: 1.2;
        white-space: nowrap;
    }}
    .kpi-tile-label {{
        font-size: 10px;
        color: {SLATE};
        font-family: Arial, sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}
    .kpi-tile-delta {{
        font-size: 10px;
        font-family: Arial, sans-serif;
        margin-top: 2px;
    }}

    /* ---- Pending data tile (greyed out) ---- */
    .kpi-tile-pending {{
        background: #F8F9FA;
        border: 1px dashed #CCCCCC;
        border-radius: 6px;
        padding: 14px 16px;
        text-align: center;
        height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        opacity: 0.7;
    }}
    .kpi-tile-pending-value {{
        font-size: 20px;
        font-weight: 700;
        color: #999999;
        font-family: Arial, sans-serif;
    }}
    .kpi-tile-pending-label {{
        font-size: 10px;
        color: #999999;
        font-family: Arial, sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}
    .kpi-tile-pending-note {{
        font-size: 9px;
        color: #BBBBBB;
        font-family: Arial, sans-serif;
        margin-top: 3px;
        font-style: italic;
    }}

    /* ---- Keep old kpi-card for compatibility ---- */
    .kpi-card {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .kpi-value {{
        font-size: 28px;
        font-weight: 700;
        color: {NAVY};
        font-family: Arial, sans-serif;
        line-height: 1.2;
    }}
    .kpi-label {{
        font-size: 11px;
        color: {SLATE};
        font-family: Arial, sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }}
    .kpi-delta {{
        font-size: 12px;
        font-family: Arial, sans-serif;
        margin-top: 2px;
    }}

    /* ---- Company cards ---- */
    .company-card {{
        background: white;
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 14px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .company-name {{
        font-size: 14px;
        font-weight: 700;
        color: {NAVY};
        font-family: Arial, sans-serif;
    }}
    .company-sector {{
        font-size: 11px;
        color: {SLATE};
        font-family: Arial, sans-serif;
    }}
    .metric-pill {{
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        font-family: Arial, sans-serif;
        margin: 2px;
    }}

    /* ---- Flag badges ---- */
    .flag-red    {{ background: #FDECEA; color: {RED_FLAG}; border: 1px solid {RED_FLAG}; }}
    .flag-yellow {{ background: #FEF9E7; color: #B7860B;   border: 1px solid {XANTHOUS}; }}
    .flag-green  {{ background: #EAFAF1; color: {SEA_GREEN}; border: 1px solid {SEA_GREEN}; }}

    /* ---- Section headers ---- */
    .section-header {{
        font-size: 12px;
        font-weight: 700;
        color: {SLATE};
        font-family: Arial, sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        border-bottom: 2px solid {SKY};
        padding-bottom: 6px;
        margin-bottom: 14px;
        margin-top: 20px;
    }}

    /* ---- Alert banner ---- */
    .alert-banner {{
        background: #FDECEA;
        border-left: 4px solid {RED_FLAG};
        border-radius: 4px;
        padding: 10px 14px;
        margin-bottom: 12px;
        font-size: 13px;
        color: {NAVY};
        font-family: Arial, sans-serif;
    }}

    /* ---- Chat bubbles ---- */
    .chat-user {{
        background: {NAVY};
        color: white;
        padding: 10px 14px;
        border-radius: 12px 12px 2px 12px;
        margin: 6px 0;
        font-size: 13px;
        font-family: Arial, sans-serif;
        max-width: 80%;
        margin-left: auto;
    }}
    .chat-assistant {{
        background: white;
        color: {NAVY};
        padding: 10px 14px;
        border-radius: 12px 12px 12px 2px;
        border: 1px solid {BORDER};
        margin: 6px 0;
        font-size: 13px;
        font-family: Arial, sans-serif;
        max-width: 90%;
    }}

    /* ---- Streamlit button styling in nav ---- */
    .stButton > button {{
        background: transparent;
        border: none;
        padding: 0;
        font-size: 13px;
        font-family: Arial, sans-serif;
    }}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def check_password() -> bool:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    # Login page
    st.markdown(f"""
    <div style="max-width:400px; margin:80px auto;">
        <div style="background:{NAVY}; padding:24px; border-radius:8px 8px 0 0; text-align:center;">
            <p style="color:white; font-size:22px; font-weight:700; margin:0; font-family:Arial;">
                TSG <span style="color:{SKY};">CONSUMER</span>
            </p>
            <p style="color:{SKY}; font-size:12px; margin:4px 0 0 0; font-family:Arial;">
                Portfolio Analytics
            </p>
        </div>
        <div style="background:white; padding:24px; border-radius:0 0 8px 8px;
                    border:1px solid {BORDER}; border-top:none;">
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown("<br>", unsafe_allow_html=True)
        password = st.text_input("Password", type="password", label_visibility="collapsed",
                                  placeholder="Enter password")
        login_btn = st.button("Sign In", use_container_width=True, type="primary")

        if login_btn:
            from db import get_secret
            if password == get_secret("password", "auth"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")

    st.markdown("</div></div>", unsafe_allow_html=True)
    return False


# ---------------------------------------------------------------------------
# Header component
# ---------------------------------------------------------------------------

def render_header(title: str, subtitle: str = "TSG Consumer Partners"):
    """Compatibility shim."""
    from ui import render_page_header as _rph
    _rph(title)


# ---------------------------------------------------------------------------
# Top navigation bar
# ---------------------------------------------------------------------------

PAGES = [
    ("Portfolio Overview",  "portfolio_overview"),
    ("Fund Snapshot",       "fund_summary"),
    ("Company Detail",      "company_detail"),
    ("Flags & Alerts",      "flags_alerts"),
    ("Consumer KPIs",       "consumer_kpis"),
    ("Portfolio Flags",     "portfolio_flags"),
    ("AI Analyst",          "ai_analyst"),
    ("Export to PPT",       "export_ppt"),
]


def render_top_nav():
    """Render the TSG brand bar + horizontal nav using st.radio styled as tabs."""
    current = st.session_state.get("page", "portfolio_overview")

    try:
        flags_df  = load_flags()
        red_count = int((flags_df["overall_flag"] == "Red").sum()) if not flags_df.empty else 0
    except Exception:
        red_count = 0

    as_of = ""
    try:
        ltm = load_ltm_snapshot()
        if not ltm.empty and "as_of_date" in ltm.columns:
            as_of = str(ltm["as_of_date"].max())[:10]
    except Exception:
        pass

    # AI panel toggle state
    if "ai_panel_open" not in st.session_state:
        st.session_state["ai_panel_open"] = False
    ai_open = st.session_state.get("ai_panel_open", False)

    # Brand bar — pure HTML, full width
    st.markdown(f"""
    <div class="tsg-brand-bar">
        <div class="tsg-brand-logo">
            TSG <span style="color:{SKY}; font-weight:400;">CONSUMER</span>
        </div>
        <div class="tsg-brand-meta">
            {"As of " + as_of if as_of else "Portfolio Analytics"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Nav tab row — page buttons + AI toggle at the end
    all_nav = list(PAGES) + [("AI Chat" if not ai_open else "✕ Close AI", "_ai_toggle")]
    btn_cols = st.columns(len(all_nav))

    for i, (label, key) in enumerate(all_nav):
        col = btn_cols[i]

        if key == "_ai_toggle":
            # AI toggle — always shown at right end
            if col.button(label, key="toggle_ai_panel",
                           use_container_width=True,
                           type="primary" if ai_open else "secondary"):
                st.session_state["ai_panel_open"] = not ai_open
                st.rerun()
        else:
            display   = f"{label} ({red_count})" if key == "flags_alerts" and red_count > 0 else label
            is_active = (key == current)
            prefix    = "nav_active_" if is_active else "nav_"
            if col.button(display, key=f"{prefix}{key}",
                           use_container_width=True,
                           type="primary" if is_active else "secondary"):
                if key != current:
                    st.session_state["page"] = key
                    if key != "company_detail":
                        st.session_state.pop("selected_company", None)
                    for k in ["drill_page", "drill_company", "drill_metric", "flag_filter_company"]:
                        st.session_state.pop(k, None)
                    st.rerun()

    # Style nav buttons as tabs
    st.markdown(f"""
    <style>
    /* Style all nav buttons as tabs */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) button {{
        border: none !important;
        border-radius: 0 !important;
        border-bottom: 3px solid transparent !important;
        background: transparent !important;
        color: {SLATE} !important;
        font-size: 13px !important;
        font-family: Arial, sans-serif !important;
        font-weight: 500 !important;
        padding: 8px 4px !important;
        margin-bottom: -2px !important;
    }}
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) button:hover {{
        color: {NAVY} !important;
        border-bottom-color: {SKY} !important;
        background: transparent !important;
    }}
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) button[kind="primary"] {{
        color: {NAVY} !important;
        font-weight: 700 !important;
        border-bottom: 3px solid {NAVY} !important;
        background: transparent !important;
    }}
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) {{
        background: white !important;
        border-bottom: 2px solid {BORDER} !important;
        padding: 0 8px !important;
        gap: 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


def render_page_header(title: str):
    """Slim page title — replaces the old full render_header."""
    st.markdown(f"""
    <div style="padding: 12px 0 8px 0; border-bottom: 1px solid {BORDER}; margin-bottom: 16px;">
        <span style="font-size:18px; font-weight:700; color:{NAVY};
                     font-family:Arial;">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def kpi_tile(value: str, label: str, delta: str = "", delta_color: str = SLATE) -> str:
    """Standardized KPI tile — fixed height, consistent sizing."""
    delta_html = (f'<div class="kpi-tile-delta" style="color:{delta_color};">{delta}</div>'
                  if delta else "")
    return f"""
    <div class="kpi-tile">
        <div class="kpi-tile-value">{value}</div>
        <div class="kpi-tile-label">{label}</div>
        {delta_html}
    </div>"""


def kpi_tile_pending(label: str, note: str = "** Pending Investran data") -> str:
    """Greyed-out placeholder tile for data not yet available."""
    return f"""
    <div class="kpi-tile-pending">
        <div class="kpi-tile-pending-value">—</div>
        <div class="kpi-tile-pending-label">{label}</div>
        <div class="kpi-tile-pending-note">{note}</div>
    </div>"""


def kpi_card(value: str, label: str, delta: str = "", delta_color: str = SLATE):
    return f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {"" if not delta else f'<div class="kpi-delta" style="color:{delta_color};">{delta}</div>'}
    </div>
    """




def flag_badge(flag: str) -> str:
    css = {"Red": "flag-red", "Yellow": "flag-yellow", "Green": "flag-green"}.get(flag, "")
    return f'<span class="metric-pill {css}">{flag_emoji(flag)} {flag}</span>'


# ---------------------------------------------------------------------------
# Page 1: Portfolio Overview
# ---------------------------------------------------------------------------

def page_portfolio_overview():
    # Check for drill-down state
    if has_drill():
        d = get_drill()
        if d["page"] == "overview" and d["company"]:
            drill_company_detail(d["company"])
            return

    render_page_header("Portfolio Overview")

    _ov_df = load_portfolio_overview()
    if _ov_df.empty:
        st.error("Portfolio overview data not loaded. Check CSV files.")
        st.stop()
    overview = _ov_df.iloc[0]
    flags    = load_flags()
    fs       = load_fund_summary()

    # -----------------------------------------------------------------------
    # FILTERS
    # -----------------------------------------------------------------------
    with st.expander("Filters", expanded=False):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            all_cos = sorted(fs["company_name"].dropna().unique().tolist()) if not fs.empty else []
            sel_companies_po = st.multiselect("Portfolio Company", all_cos,
                                               default=all_cos, key="po_company")
        with fc2:
            sectors = sorted(fs["sector"].dropna().unique().tolist()) if not fs.empty else []
            sel_sectors = st.multiselect("Sector", sectors, default=sectors, key="po_sector")
        with fc3:
            if not fs.empty and "investment_date" in fs.columns:
                fs["_inv_year"] = pd.to_datetime(fs["investment_date"], errors="coerce").dt.year
                years = sorted(fs["_inv_year"].dropna().unique().astype(int).tolist())
            else:
                years = []
            yr_range = st.slider("Acquisition Year",
                                  min_value=int(min(years)) if years else 2018,
                                  max_value=int(max(years)) if years else 2024,
                                  value=(int(min(years)) if years else 2018,
                                         int(max(years)) if years else 2024),
                                  key="po_year") if years else None
        with fc4:
            po_funds = sorted(fs["funds"].dropna().unique().tolist())                        if not fs.empty and "funds" in fs.columns else []
            sel_funds_po = st.multiselect("Fund", po_funds, default=po_funds,
                                           key="po_fund") if po_funds else []

    # Apply filters
    fs_filtered = fs.copy()
    if sel_companies_po:
        fs_filtered = fs_filtered[fs_filtered["company_name"].isin(sel_companies_po)]
    if sel_sectors:
        fs_filtered = fs_filtered[fs_filtered["sector"].isin(sel_sectors)]
    if yr_range and "_inv_year" in fs_filtered.columns:
        fs_filtered = fs_filtered[fs_filtered["_inv_year"].between(yr_range[0], yr_range[1])]
    if sel_funds_po and "funds" in fs_filtered.columns:
        fs_filtered = fs_filtered[fs_filtered["funds"].isin(sel_funds_po)]

    # Recompute overview metrics from filtered set
    total_tev      = fs_filtered["current_tev"].sum() if not fs_filtered.empty else None
    total_revenue  = fs_filtered["ltm_revenue"].sum()   if not fs_filtered.empty else None
    total_ebitda   = fs_filtered["ltm_adj_ebitda"].sum() if not fs_filtered.empty else None
    avg_leverage   = (fs_filtered["net_leverage"] * fs_filtered["current_tev"]).sum() /                      fs_filtered["current_tev"].sum()                      if not fs_filtered.empty and fs_filtered["current_tev"].sum() > 0 else None
    avg_margin     = fs_filtered["ltm_adj_ebitda_margin"].mean() if not fs_filtered.empty else None

    # -----------------------------------------------------------------------
    # ALERT BANNER
    # -----------------------------------------------------------------------
    flags_filtered = flags[flags["company_name"].isin(fs_filtered["company_name"])]                      if not flags.empty else flags
    red_companies  = flags_filtered[flags_filtered["overall_flag"] == "Red"]["company_name"].tolist()
    if red_companies:
        issues = []
        for _, row in flags_filtered[flags_filtered["overall_flag"] == "Red"].iterrows():
            parts = []
            if row.get("net_leverage_flag")   == "Red":
                parts.append(f"Net Lev {format_multiple(row.get('net_leverage'))}")
            if row.get("revenue_growth_flag") == "Red":
                parts.append(f"Rev Growth {format_pct(row.get('revenue_yoy'))}")
            if row.get("ebitda_margin_flag")  == "Red":
                parts.append(f"EBITDA Margin {format_pct(row.get('ltm_adj_ebitda_margin'))}")
            issues.append(f"<b>{row['company_name']}</b>: {', '.join(parts)}")
        st.markdown(f"""
        <div class="alert-banner">
            🚨 <b>{len(red_companies)} Red Flag{"s" if len(red_companies)>1 else ""}</b> —
            {" · ".join(issues)}
        </div>
        """, unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # KPI TILES — standardized, fixed height, pending for IRR/MOIC
    # -----------------------------------------------------------------------
    tile_cols = st.columns(8)
    tiles = [
        (format_millions(total_tev),    "Total TEV",         "", False),
        (format_millions(total_revenue),"LTM Revenue",       "", False),
        (format_millions(total_ebitda), "LTM EBITDA",        "", False),
        (format_multiple(avg_leverage), "Avg Net Leverage",  "", False),
        (format_pct(avg_margin),        "Avg EBITDA Margin", "", False),
        (None, "Gross MOIC",            "",                      True),
        (None, "Gross IRR",             "",                      True),
        (None, "Net IRR",               "",                      True),
    ]
    for col, (val, label, delta, pending) in zip(tile_cols, tiles):
        if pending:
            col.markdown(kpi_tile_pending(label), unsafe_allow_html=True)
        else:
            col.markdown(kpi_tile(val, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # CHARTS — Revenue/EBITDA (wider) + Sector donut (smaller)
    # -----------------------------------------------------------------------
    col_left, col_right = st.columns([4, 1])   # wider left chart

    with col_left:
        st.markdown('<div class="section-header">Portfolio Revenue & EBITDA — Quarterly LTM</div>',
                    unsafe_allow_html=True)
        quarterly = load_quarterly()
        if not quarterly.empty:
            q_filt = quarterly[quarterly["company_name"].isin(fs_filtered["company_name"])]                      if not fs_filtered.empty else quarterly
            agg = q_filt.groupby("period_label").agg(
                revenue        = ("revenue",    "sum"),
                adj_ebitda     = ("adj_ebitda", "sum"),
                cash_flow_date = ("cash_flow_date", "max")
            ).reset_index().sort_values("cash_flow_date").tail(12)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=agg["period_label"], y=agg["revenue"],
                                  name="Revenue ($M)", marker_color=SLATE, opacity=0.85),
                          secondary_y=False)
            fig.add_trace(go.Bar(x=agg["period_label"], y=agg["adj_ebitda"],
                                  name="Adj. EBITDA ($M)", marker_color=SKY, opacity=0.85),
                          secondary_y=False)
            margin = agg["adj_ebitda"] / agg["revenue"].replace(0, float("nan"))
            fig.add_trace(go.Scatter(x=agg["period_label"], y=margin,
                                      name="EBITDA Margin %", mode="lines+markers",
                                      line=dict(color=XANTHOUS, width=2), marker=dict(size=5)),
                          secondary_y=True)
            fig.update_layout(
                height=320, plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0), barmode="group",
                legend=dict(orientation="h", y=-0.18, font=dict(size=10)),
                font=dict(family="Arial", color=NAVY, size=10)
            )
            fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False)
            fig.update_yaxes(tickformat=".0%", secondary_y=True)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">% by Sector</div>', unsafe_allow_html=True)
        sector_data = fs_filtered.groupby("sector")["current_tev"].sum().reset_index()
        sector_data = sector_data.dropna().sort_values("current_tev", ascending=False)
        if not sector_data.empty:
            fig2 = px.pie(sector_data, values="current_tev", names="sector", hole=0.6,
                           color_discrete_sequence=[NAVY, SLATE, SKY, XANTHOUS,
                                                     CELADON, SEA_GREEN, MAGENTA, EGGPLANT])
            fig2.update_traces(textposition="inside", textinfo="percent",
                               textfont_size=9)
            fig2.update_layout(
                height=320, showlegend=True,
                legend=dict(font=dict(size=9), orientation="v"),
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="white"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------------------------------------------------
    # ACTIVE PORTFOLIO COMPANIES
    # -----------------------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)

    hdr_col, btn_col = st.columns([6, 1])
    with hdr_col:
        st.markdown('<div class="section-header">Active Portfolio Companies</div>',
                    unsafe_allow_html=True)
    with btn_col:
        if st.button("View All Flags →", key="goto_flags_from_overview"):
            st.session_state["page"] = "flags_alerts"
            st.rerun()

    companies = fs_filtered.sort_values(
        "overall_flag",
        key=lambda x: x.map({"Red": 0, "Yellow": 1, "Green": 2})
    )
    card_cols = st.columns(3)
    for i, (_, row) in enumerate(companies.iterrows()):
        col        = card_cols[i % 3]
        cname      = row.get("company_name", "")
        rev_yoy    = row.get("revenue_yoy")
        rev_color  = SEA_GREEN if pd.notna(rev_yoy) and rev_yoy > 0 else RED_FLAG
        yoy_str    = format_pct(rev_yoy) if pd.notna(rev_yoy) else "—"

        # Year acquired
        inv_date   = row.get("investment_date", "")
        try:
            inv_year = str(pd.to_datetime(inv_date).year)
        except Exception:
            inv_year = "—"

        col.markdown(f"""
        <div class="company-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div class="company-name">{cname}</div>
                    <div class="company-sector">
                        {row.get("sector","")} · Acq. {inv_year}
                    </div>
                </div>
                {flag_badge(row.get("overall_flag",""))}
            </div>
            <div style="margin-top:10px; display:flex; gap:14px; flex-wrap:wrap;">
                <div>
                    <span style="font-size:13px;font-weight:700;color:{NAVY};">
                        {format_millions(row.get("ltm_revenue"))}</span><br>
                    <span style="font-size:10px;color:{SLATE};">LTM Rev</span>
                </div>
                <div>
                    <span style="font-size:13px;font-weight:700;color:{NAVY};">
                        {format_multiple(row.get("net_leverage"))}</span><br>
                    <span style="font-size:10px;color:{SLATE};">Net Lev</span>
                </div>
                <div>
                    <span style="font-size:13px;font-weight:700;color:{NAVY};">
                        {format_pct(row.get("ltm_adj_ebitda_margin"))}</span><br>
                    <span style="font-size:10px;color:{SLATE};">EBITDA Mgn</span>
                </div>
                <div>
                    <span style="font-size:13px;font-weight:700;color:{rev_color};">
                        {yoy_str}</span><br>
                    <span style="font-size:10px;color:{SLATE};">Rev Growth</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Two buttons: Company Detail and Flags
        btn_c1, btn_c2 = col.columns(2)
        if btn_c1.button("View Detail", key=f"detail_{cname}", use_container_width=True):
            st.session_state["page"]         = "company_detail"
            st.session_state["selected_company"] = cname
            for k in ["drill_page", "drill_company", "drill_metric"]:
                st.session_state.pop(k, None)
            st.rerun()
        if btn_c2.button("Alerts", key=f"alerts_{cname}", use_container_width=True):
            st.session_state["page"]              = "flags_alerts"
            st.session_state["flag_filter_company"] = cname
            st.rerun()


# ---------------------------------------------------------------------------
# Page 2: Fund Summary
# ---------------------------------------------------------------------------

def page_fund_summary():
    render_page_header("Fund Snapshot")

    fs = load_fund_summary()

    if fs.empty:
        st.info("No fund data available.")
        return

    # -----------------------------------------------------------------------
    # FILTERS
    # -----------------------------------------------------------------------
    with st.expander("Filters", expanded=False):
        ff1, ff2, ff3 = st.columns(3)
        with ff1:
            sectors = sorted(fs["sector"].dropna().unique().tolist())
            sel_sectors = st.multiselect("Sector", sectors, default=sectors,
                                          key="fs_sector")
        with ff2:
            fs["_inv_year"] = pd.to_datetime(fs["investment_date"], errors="coerce").dt.year
            years = sorted(fs["_inv_year"].dropna().unique().astype(int).tolist())
            yr_range = st.slider("Acquisition Year",
                                  min_value=int(min(years)) if years else 2018,
                                  max_value=int(max(years)) if years else 2024,
                                  value=(int(min(years)) if years else 2018,
                                         int(max(years)) if years else 2024),
                                  key="fs_year") if years else None
        with ff3:
            funds = sorted(fs["funds"].dropna().unique().tolist()) if "funds" in fs.columns else []
            sel_funds = st.multiselect("Fund", funds, default=funds, key="fs_fund") if funds else funds

    # Apply filters
    fs_f = fs.copy()
    if sel_sectors:
        fs_f = fs_f[fs_f["sector"].isin(sel_sectors)]
    if yr_range:
        fs_f = fs_f[fs_f["_inv_year"].between(yr_range[0], yr_range[1])]
    if sel_funds and "funds" in fs_f.columns:
        fs_f = fs_f[fs_f["funds"].isin(sel_funds)]

    # -----------------------------------------------------------------------
    # KPI TILES
    # -----------------------------------------------------------------------
    total_tev  = fs_f["current_tev"].sum()   if not fs_f.empty else None
    entry_tev  = fs_f["entry_tev"].sum()     if not fs_f.empty else None
    avg_lev    = (fs_f["net_leverage"] * fs_f["current_tev"]).sum() /                  fs_f["current_tev"].sum() if not fs_f.empty and fs_f["current_tev"].sum() > 0 else None
    co_count   = len(fs_f)

    t_cols = st.columns(7)
    tiles  = [
        (str(co_count),               "Investments",      False),
        (format_millions(entry_tev),  "Total Cost",       False),
        (format_millions(total_tev),  "Total TEV",        False),
        (format_multiple(avg_lev),    "Avg Net Leverage", False),
        ("Gross MOIC",                "Gross MOIC",       True),
        ("Gross IRR",                 "Gross IRR",        True),
        ("Net IRR",                   "Net IRR",          True),
    ]
    for col, (val, label, pending) in zip(t_cols, tiles):
        if pending:
            col.markdown(kpi_tile_pending(label), unsafe_allow_html=True)
        else:
            col.markdown(kpi_tile(val, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # TABS
    # -----------------------------------------------------------------------
    tab_invest, tab_perf, tab_charts = st.tabs([
        "Investment Summary", "Performance Charts", "Entry vs Current"
    ])

    # ---- TAB 1: Investment Summary table ----
    with tab_invest:
        st.markdown('<div class="section-header">TSG Investment Summary</div>',
                    unsafe_allow_html=True)

        display = fs_f[[
            "company_name", "sector", "investment_date", "security_type",
            "ownership_structure", "entry_tev", "current_tev", "gross_moi",
            "ltm_revenue", "ltm_adj_ebitda", "ltm_adj_ebitda_margin",
            "net_leverage", "revenue_yoy", "overall_flag"
        ]].copy()
        display["investment_date"]       = pd.to_datetime(display["investment_date"]).dt.strftime("%b %Y")
        display["entry_tev"]             = display["entry_tev"].apply(format_millions)
        display["current_tev"]           = display["current_tev"].apply(format_millions)
        display["gross_moi"]             = display["gross_moi"].apply(format_multiple)
        display["ltm_revenue"]           = display["ltm_revenue"].apply(format_millions)
        display["ltm_adj_ebitda"]        = display["ltm_adj_ebitda"].apply(format_millions)
        display["ltm_adj_ebitda_margin"] = display["ltm_adj_ebitda_margin"].apply(format_pct)
        display["net_leverage"]          = display["net_leverage"].apply(format_multiple)
        display["revenue_yoy"]           = display["revenue_yoy"].apply(format_pct)
        display["overall_flag"]          = display["overall_flag"].apply(
            lambda x: f"{flag_emoji(x)} {x}")
        display.columns = [
            "Company", "Sector", "Entry Date", "Security", "Ownership",
            "Entry TEV", "Current TEV", "Gross MOI",
            "LTM Revenue", "LTM EBITDA", "EBITDA Mgn",
            "Net Lev", "Rev Growth", "Flag"
        ]
        st.dataframe(display.set_index("Company"), use_container_width=True, height=500)

        # Drill-down check
        if has_drill():
            d = get_drill()
            if d["page"] == "fund_summary" and d["company"]:
                drill_tev_history(d["company"])
                return

        st.caption("Drill into TEV & valuation history:")
        drill_cols = st.columns(5)
        for i, (_, row) in enumerate(fs_f.iterrows()):
            cname = row["company_name"]
            if drill_cols[i % 5].button(cname, key=f"fs_drill_{cname}",
                                         use_container_width=True):
                set_drill("fund_summary", company=cname)
                st.rerun()

    # ---- TAB 2: Performance Charts ----
    with tab_perf:
        # -- Capital Flow Bridge (pending Investran) --
        st.markdown('<div class="section-header">Capital Flow Bridge</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#F8F9FA; border:1px dashed #CCCCCC; border-radius:6px;
                    padding:32px; text-align:center; margin-bottom:16px;">
            <div style="font-size:15px; font-weight:700; color:#999; font-family:Arial;">
                Capital Committed → Paid-In Capital → Distributions → Remaining NAV
            </div>
            <div style="font-size:11px; color:#BBBBBB; font-family:Arial; margin-top:8px;">
                ** Pending Investran data — Waterfall chart will render here
            </div>
        </div>
        """, unsafe_allow_html=True)

        # -- TVPI / DPI / RVPI (pending Investran) --
        st.markdown('<div class="section-header">TVPI, DPI, RVPI Over Time</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#F8F9FA; border:1px dashed #CCCCCC; border-radius:6px;
                    padding:32px; text-align:center; margin-bottom:16px;">
            <div style="font-size:15px; font-weight:700; color:#999; font-family:Arial;">
                TVPI · DPI · RVPI — Time Series
            </div>
            <div style="font-size:11px; color:#BBBBBB; font-family:Arial; margin-top:8px;">
                ** Pending Investran data — Line chart will render here
            </div>
        </div>
        """, unsafe_allow_html=True)

        # -- Value & MOIC by Investment (built from available data) --
        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown('<div class="section-header">Current TEV by Company</div>',
                        unsafe_allow_html=True)
            tev_df = fs_f.dropna(subset=["current_tev"]).sort_values("current_tev", ascending=True)
            if not tev_df.empty:
                fig_tev = go.Figure(go.Bar(
                    x=tev_df["current_tev"],
                    y=tev_df["company_name"],
                    orientation="h",
                    marker_color=NAVY,
                    text=tev_df["current_tev"].apply(format_millions),
                    textposition="outside"
                ))
                fig_tev.update_layout(
                    height=max(300, len(tev_df) * 28),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=60, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat="$,.0f", gridcolor=BORDER)
                )
                st.plotly_chart(fig_tev, use_container_width=True)

        with chart_right:
            st.markdown('<div class="section-header">Gross MOI by Company</div>',
                        unsafe_allow_html=True)
            moi_df = fs_f.dropna(subset=["gross_moi"]).sort_values("gross_moi", ascending=True)
            if not moi_df.empty:
                moi_df["color"] = moi_df["gross_moi"].apply(
                    lambda x: SEA_GREEN if x > 2.0 else XANTHOUS if x > 1.5 else RED_FLAG
                )
                fig_moi = go.Figure(go.Bar(
                    x=moi_df["gross_moi"],
                    y=moi_df["company_name"],
                    orientation="h",
                    marker_color=moi_df["color"].tolist(),
                    text=moi_df["gross_moi"].apply(lambda x: f"{x:.2f}x"),
                    textposition="outside"
                ))
                fig_moi.add_vline(x=1.0, line_dash="dash", line_color=RED_FLAG,
                                   annotation_text="1.0x")
                fig_moi.add_vline(x=2.0, line_dash="dot",  line_color=SEA_GREEN,
                                   annotation_text="2.0x")
                fig_moi.update_layout(
                    height=max(300, len(moi_df) * 28),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=60, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat=".2f", gridcolor=BORDER)
                )
                st.plotly_chart(fig_moi, use_container_width=True)

        # -- Invested Capital (pending) --
        st.markdown('<div class="section-header">Invested Capital by Company (Cost Basis)</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#F8F9FA; border:1px dashed #CCCCCC; border-radius:6px;
                    padding:24px; text-align:center;">
            <div style="font-size:13px; font-weight:700; color:#999; font-family:Arial;">
                Invested Capital / Cost Basis
            </div>
            <div style="font-size:11px; color:#BBBBBB; font-family:Arial; margin-top:6px;">
                ** Pending Investran data
            </div>
        </div>
        """, unsafe_allow_html=True)

        # -- TEV vs EBITDA Margin scatter --
        st.markdown('<div class="section-header">TEV vs EBITDA Margin</div>',
                    unsafe_allow_html=True)
        scatter_df = fs_f.dropna(subset=["current_tev", "ltm_adj_ebitda_margin"])
        if not scatter_df.empty:
            fig_sc = px.scatter(
                scatter_df,
                x="ltm_adj_ebitda_margin", y="current_tev",
                size="ltm_revenue", color="overall_flag",
                color_discrete_map={"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN},
                hover_name="company_name", text="company_name",
                size_max=50,
                labels={"ltm_adj_ebitda_margin": "LTM EBITDA Margin",
                        "current_tev": "Current TEV ($M)", "overall_flag": "Flag"}
            )
            fig_sc.update_traces(textposition="top center", textfont_size=9)
            fig_sc.update_layout(
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Arial", color=NAVY, size=10),
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(tickformat=".0%", gridcolor=BORDER),
                yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
            )
            st.plotly_chart(fig_sc, use_container_width=True)

    # ---- TAB 3: Entry vs Current ----
    with tab_charts:
        st.markdown('<div class="section-header">Entry vs Current EBITDA — Company Level</div>',
                    unsafe_allow_html=True)

        entry_df = fs_f.dropna(subset=["entry_tev", "current_tev"]).copy()
        if not entry_df.empty:
            # Use entry EBITDA proxy: entry_tev / assumed entry multiple
            # and current EBITDA from LTM
            ebitda_df = entry_df.dropna(subset=["ltm_adj_ebitda"]).copy()
            ebitda_df = ebitda_df.sort_values("ltm_adj_ebitda", ascending=True)

            fig_entry = go.Figure()
            # Current EBITDA
            fig_entry.add_trace(go.Bar(
                name="LTM Adj. EBITDA",
                x=ebitda_df["company_name"],
                y=ebitda_df["ltm_adj_ebitda"],
                marker_color=NAVY
            ))
            # Entry EBITDA proxy (if valuation_ltm_ebitda available)
            if "valuation_ltm_ebitda" in ebitda_df.columns:
                entry_ebitda = ebitda_df["valuation_ltm_ebitda"].dropna()
                if not entry_ebitda.empty:
                    fig_entry.add_trace(go.Bar(
                        name="Entry EBITDA (Proxy)",
                        x=ebitda_df["company_name"],
                        y=ebitda_df["valuation_ltm_ebitda"],
                        marker_color=SKY
                    ))
            fig_entry.update_layout(
                height=360, plot_bgcolor="white", paper_bgcolor="white",
                barmode="group",
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                legend=dict(orientation="h", y=-0.15),
                yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
                xaxis=dict(tickangle=-30)
            )
            st.plotly_chart(fig_entry, use_container_width=True)

        # Entry vs Current TEV (Debt proxy)
        st.markdown('<div class="section-header">Entry vs Current TEV — Company Level</div>',
                    unsafe_allow_html=True)
        tev_comp_df = fs_f.dropna(subset=["entry_tev", "current_tev"]).sort_values(
            "current_tev", ascending=True)
        if not tev_comp_df.empty:
            fig_tev2 = go.Figure()
            fig_tev2.add_trace(go.Bar(
                name="Entry TEV",
                x=tev_comp_df["company_name"],
                y=tev_comp_df["entry_tev"],
                marker_color=SKY
            ))
            fig_tev2.add_trace(go.Bar(
                name="Current TEV",
                x=tev_comp_df["company_name"],
                y=tev_comp_df["current_tev"],
                marker_color=NAVY
            ))
            fig_tev2.update_layout(
                height=360, plot_bgcolor="white", paper_bgcolor="white",
                barmode="group",
                margin=dict(l=0, r=0, t=10, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                legend=dict(orientation="h", y=-0.15),
                yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
                xaxis=dict(tickangle=-30)
            )
            st.plotly_chart(fig_tev2, use_container_width=True)

        # Net Leverage: Entry vs Current (fund-level pending)
        st.markdown('<div class="section-header">Entry vs Current Debt — Fund Level</div>',
                    unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:#F8F9FA; border:1px dashed #CCCCCC; border-radius:6px;
                    padding:24px; text-align:center;">
            <div style="font-size:13px; font-weight:700; color:#999; font-family:Arial;">
                Fund-Level Debt: Entry vs Current
            </div>
            <div style="font-size:11px; color:#BBBBBB; font-family:Arial; margin-top:6px;">
                ** Pending Investran data — requires paid-in capital and debt at entry
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Net Leverage trend by company (available from quarterly data)
        st.markdown('<div class="section-header">Net Leverage Over Time — Company Level</div>',
                    unsafe_allow_html=True)
        quarterly_all = load_quarterly()
        if not quarterly_all.empty:
            lev_df = quarterly_all[
                quarterly_all["company_name"].isin(fs_f["company_name"])
            ].dropna(subset=["net_leverage"]).copy()
            lev_df = lev_df.sort_values("cash_flow_date")

            company_colors_map = {
                name: COMPANY_COLORS[i % len(COMPANY_COLORS)]
                for i, name in enumerate(sorted(lev_df["company_name"].unique()))
            }
            fig_lev = go.Figure()
            for cname in lev_df["company_name"].unique():
                co_df = lev_df[lev_df["company_name"] == cname]
                fig_lev.add_trace(go.Scatter(
                    x=co_df["period_label"], y=co_df["net_leverage"],
                    name=cname, mode="lines+markers",
                    line=dict(color=company_colors_map.get(cname, NAVY), width=1.5),
                    marker=dict(size=4)
                ))
            fig_lev.add_hline(y=6.0, line_dash="dash", line_color=RED_FLAG,
                               annotation_text="6.0x Covenant")
            fig_lev.add_hline(y=5.0, line_dash="dot",  line_color=XANTHOUS,
                               annotation_text="5.0x Watch")
            fig_lev.update_layout(
                height=380, plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=80, t=10, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                legend=dict(font=dict(size=9), orientation="h", y=-0.2),
                yaxis=dict(tickformat=".1f", ticksuffix="x", gridcolor=BORDER),
                xaxis=dict(tickangle=-45)
            )
            st.plotly_chart(fig_lev, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 3: Company Detail
# ---------------------------------------------------------------------------

def page_company_detail():
    render_page_header("Company Detail")

    companies = get_company_list()
    selected  = st.selectbox("Select Company", companies, label_visibility="collapsed")

    if not selected:
        return

    flags   = load_flags()
    company_flag = flags[flags["company_name"] == selected]
    flag_row = company_flag.iloc[0] if len(company_flag) > 0 else None

    # Company header
    if flag_row is not None:
        overall = flag_row.get("overall_flag", "")
        col_h1, col_h2 = st.columns([5, 1])
        with col_h1:
            st.markdown(f"""
            <div style="background:white; border:1px solid {BORDER}; border-radius:6px;
                        padding:16px 20px; margin-bottom:16px;">
                <div style="display:flex; align-items:center; gap:12px;">
                    <div style="background:{NAVY}; color:white; padding:8px 14px;
                                border-radius:4px; font-weight:700; font-family:Arial; font-size:16px;">
                        {selected[:2].upper()}
                    </div>
                    <div>
                        <div style="font-size:20px; font-weight:700; color:{NAVY}; font-family:Arial;">
                            {selected}
                        </div>
                        <div style="font-size:12px; color:{SLATE}; font-family:Arial;">
                            {flag_badge(overall)}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # KPI strip
        kpi_cols = st.columns(6)
        kpis = [
            (format_millions(flag_row.get("ltm_revenue")),           "LTM Net Sales"),
            (format_millions(flag_row.get("ltm_adj_ebitda")),         "LTM Adj. EBITDA"),
            (format_pct(flag_row.get("ltm_adj_ebitda_margin")),       "EBITDA Margin"),
            (format_multiple(flag_row.get("net_leverage")),            "Net Leverage"),
            (format_pct(flag_row.get("revenue_yoy")),                  "Rev Growth YoY"),
            (format_pct(flag_row.get("ltm_gross_margin")),             "Gross Margin"),
        ]
        for col, (val, label) in zip(kpi_cols, kpis):
            col.markdown(kpi_card(val, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Revenue & EBITDA trend
    quarterly = load_quarterly(selected)
    if not quarterly.empty:
        st.markdown('<div class="section-header">Revenue & EBITDA Trend</div>',
                    unsafe_allow_html=True)

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(
            x=quarterly["period_label"],
            y=quarterly["revenue"].combine_first(quarterly["net_sales"]),
            name="Revenue ($M)", marker_color=NAVY, opacity=0.8
        ), secondary_y=False)
        fig.add_trace(go.Bar(
            x=quarterly["period_label"],
            y=quarterly["adj_ebitda"],
            name="Adj. EBITDA ($M)", marker_color=SLATE, opacity=0.8
        ), secondary_y=False)
        margin = quarterly["adj_ebitda"] / quarterly["revenue"].replace(0, float("nan"))
        fig.add_trace(go.Scatter(
            x=quarterly["period_label"], y=margin,
            name="EBITDA Margin %", mode="lines+markers",
            line=dict(color=XANTHOUS, width=2), marker=dict(size=5)
        ), secondary_y=True)
        fig.update_layout(
            height=300, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0), barmode="group",
            legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
            font=dict(family="Arial", color=NAVY, size=10)
        )
        fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False)
        fig.update_yaxes(tickformat=".0%", secondary_y=True)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Net Leverage trend
        col_lev, col_margin = st.columns(2)

        with col_lev:
            st.markdown('<div class="section-header">Net Leverage — Quarterly</div>',
                        unsafe_allow_html=True)
            lev_df = quarterly.dropna(subset=["net_leverage"])
            if not lev_df.empty:
                fig3 = go.Figure()
                fig3.add_hline(y=6.0, line_dash="dash", line_color=RED_FLAG,
                               annotation_text="6.0x Covenant", annotation_position="right")
                fig3.add_hline(y=5.0, line_dash="dot", line_color=XANTHOUS,
                               annotation_text="5.0x Watch")
                fig3.add_trace(go.Bar(
                    x=lev_df["period_label"], y=lev_df["net_leverage"],
                    marker_color=[RED_FLAG if v > 6 else XANTHOUS if v > 5 else NAVY
                                  for v in lev_df["net_leverage"]]
                ))
                fig3.update_layout(
                    height=240, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    yaxis=dict(title="Net Leverage (x)", gridcolor=BORDER)
                )
                fig3.update_xaxes(tickangle=-45)
                st.plotly_chart(fig3, use_container_width=True)

        with col_margin:
            st.markdown('<div class="section-header">EBITDA Margin % — Quarterly</div>',
                        unsafe_allow_html=True)
            mgn_df = quarterly.dropna(subset=["adj_ebitda_margin_pct"])
            if not mgn_df.empty:
                fig4 = go.Figure()
                fig4.add_hline(y=0.18, line_dash="dash", line_color=SEA_GREEN,
                               annotation_text="18% Benchmark")
                fig4.add_hline(y=0.10, line_dash="dot", line_color=XANTHOUS,
                               annotation_text="10% Watch")
                fig4.add_trace(go.Scatter(
                    x=mgn_df["period_label"], y=mgn_df["adj_ebitda_margin_pct"],
                    mode="lines+markers",
                    line=dict(color=SLATE, width=2),
                    fill="tozeroy", fillcolor=f"rgba(63,102,128,0.1)"
                ))
                fig4.update_layout(
                    height=240, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    yaxis=dict(tickformat=".0%", gridcolor=BORDER)
                )
                fig4.update_xaxes(tickangle=-45)
                st.plotly_chart(fig4, use_container_width=True)

    # AI chat for this company
    st.markdown('<div class="section-header">AI Analyst — Ask about ' + selected + '</div>',
                unsafe_allow_html=True)

    chat_key = f"chat_{selected}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    context = build_company_context(selected)

    # Suggested prompts
    prompts = [
        f"Summarize {selected}'s performance in 3 bullet points",
        f"What are the key risks for {selected}?",
        f"Write a board memo update for {selected}",
        f"How is {selected}'s leverage trending?",
    ]
    cols = st.columns(4)
    for col, prompt in zip(cols, prompts):
        if col.button(prompt, key=f"prompt_{prompt[:20]}", use_container_width=True):
            st.session_state[chat_key].append({"role": "user", "content": prompt})
            response = ask_claude(prompt, context, st.session_state[chat_key][:-1])
            st.session_state[chat_key].append({"role": "assistant", "content": response})

    # Chat history
    for msg in st.session_state[chat_key]:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>',
                        unsafe_allow_html=True)

    # Input
    user_input = st.chat_input(f"Ask anything about {selected}...")
    if user_input:
        st.session_state[chat_key].append({"role": "user", "content": user_input})
        with st.spinner("Analysing..."):
            response = ask_claude(user_input, context, st.session_state[chat_key][:-1])
        st.session_state[chat_key].append({"role": "assistant", "content": response})
        st.rerun()


# ---------------------------------------------------------------------------
# Page 4: Flags & Alerts  (unified — consolidates Consumer KPIs + Portfolio Flags)
# ---------------------------------------------------------------------------

def page_flags_alerts():
    render_page_header("Flags & Alerts")

    flags    = load_flags()
    fs       = load_fund_summary()

    try:
        from db import load_portfolio_flags
        pf_df = load_portfolio_flags()
    except Exception:
        pf_df = pd.DataFrame()

    # -----------------------------------------------------------------------
    # FILTERS
    # -----------------------------------------------------------------------
    with st.expander("Filters", expanded=False):
        fc1, fc2, fc3, fc4, fc5 = st.columns(5)
        with fc1:
            all_companies = sorted(flags["company_name"].dropna().unique().tolist())
            pre_co        = st.session_state.pop("flag_filter_company", None)
            default_co    = [pre_co] if pre_co and pre_co in all_companies else all_companies
            sel_companies = st.multiselect("Company", all_companies, default=default_co,
                                            key="fa_company")
        with fc2:
            all_sectors = sorted(fs["sector"].dropna().unique().tolist()) if not fs.empty else []
            sel_sectors = st.multiselect("Sector", all_sectors, default=all_sectors,
                                          key="fa_sector")
        with fc3:
            if not fs.empty and "investment_date" in fs.columns:
                fs["_inv_year"] = pd.to_datetime(fs["investment_date"], errors="coerce").dt.year
                years = sorted(fs["_inv_year"].dropna().unique().astype(int).tolist())
            else:
                years = []
            yr_range = st.slider("Acquisition Year",
                                  min_value=int(min(years)) if years else 2018,
                                  max_value=int(max(years)) if years else 2024,
                                  value=(int(min(years)) if years else 2018,
                                         int(max(years)) if years else 2024),
                                  key="fa_year") if years else None
        with fc4:
            all_funds = sorted(fs["funds"].dropna().unique().tolist())                         if not fs.empty and "funds" in fs.columns else []
            sel_funds = st.multiselect("Fund", all_funds, default=all_funds,
                                        key="fa_fund") if all_funds else []
        with fc5:
            metric_types = ["Leverage / Credit", "Coverage", "Revenue Growth",
                             "EBITDA / Margin", "Returns", "Liquidity"]
            sel_metrics  = st.multiselect("Metric Type", metric_types,
                                           default=metric_types, key="fa_metric")

    # Apply filters
    flags_filtered = flags.copy()
    if sel_companies:
        flags_filtered = flags_filtered[flags_filtered["company_name"].isin(sel_companies)]
    if sel_sectors and not fs.empty:
        sc = fs[fs["sector"].isin(sel_sectors)]["company_name"].tolist()
        flags_filtered = flags_filtered[flags_filtered["company_name"].isin(sc)]
    if yr_range and not fs.empty and "_inv_year" in fs.columns:
        yc = fs[fs["_inv_year"].between(yr_range[0], yr_range[1])]["company_name"].tolist()
        flags_filtered = flags_filtered[flags_filtered["company_name"].isin(yc)]
    if sel_funds and not fs.empty and "funds" in fs.columns:
        fc_list = fs[fs["funds"].isin(sel_funds)]["company_name"].tolist()
        flags_filtered = flags_filtered[flags_filtered["company_name"].isin(fc_list)]
    if not pf_df.empty:
        pf_filtered = pf_df[pf_df["company_name"].isin(flags_filtered["company_name"])]
    else:
        pf_filtered = pd.DataFrame()

    red    = flags_filtered[flags_filtered["overall_flag"] == "Red"]
    yellow = flags_filtered[flags_filtered["overall_flag"] == "Yellow"]
    green  = flags_filtered[flags_filtered["overall_flag"] == "Green"]

    # -----------------------------------------------------------------------
    # SUMMARY TILES
    # -----------------------------------------------------------------------
    tc = st.columns(5)
    tc[0].markdown(kpi_tile(str(len(red)),            "Red Flags",       "Requires attention"), unsafe_allow_html=True)
    tc[1].markdown(kpi_tile(str(len(yellow)),         "Yellow Flags",    "Watch list"),         unsafe_allow_html=True)
    tc[2].markdown(kpi_tile(str(len(green)),          "Green / On Track","Within thresholds"),  unsafe_allow_html=True)
    tc[3].markdown(kpi_tile(str(len(flags_filtered)), "Companies",       "In current filter"),  unsafe_allow_html=True)
    distress = int(pf_filtered["signal_distress"].sum()) if not pf_filtered.empty and "signal_distress" in pf_filtered.columns else 0
    tc[4].markdown(kpi_tile(str(distress),            "Distress Signals","High default risk"),   unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # VIEW TOGGLE — Portfolio KPIs | Company KPIs | Scorecard Table
    # -----------------------------------------------------------------------
    view_mode = st.radio(
        "View",
        ["Portfolio KPIs", "Company KPIs", "Scorecard Table"],
        horizontal=True,
        label_visibility="collapsed",
        key="flags_view_mode"
    )

    # -----------------------------------------------------------------------
    # DRILL-DOWN CHECK
    # -----------------------------------------------------------------------
    if has_drill():
        d = get_drill()
        if d["page"] == "flags" and d["company"] and d["metric"]:
            drill_flag_metric(d["company"], d["metric"])
            return

    # -----------------------------------------------------------------------
    # VIEW 1: Portfolio KPIs  (flag expanders — existing behaviour)
    # -----------------------------------------------------------------------
    if view_mode == "Portfolio KPIs":

        def ai_flag_summary(cname: str, row) -> str:
            """Generate a one-line AI summary for a flagged company."""
            key = f"ai_flag_summary_{cname}"
            if key in st.session_state:
                return st.session_state[key]
            try:
                from ai import ask_claude, build_portfolio_context
                ctx    = build_portfolio_context()
                prompt = (
                    f"In 1-2 sentences, explain the key driver behind {cname}'s flag status. "
                    f"Revenue growth: {format_pct(row.get('revenue_yoy'))}, "
                    f"EBITDA margin: {format_pct(row.get('ltm_adj_ebitda_margin'))}, "
                    f"Net leverage: {format_multiple(row.get('net_leverage'))}. "
                    f"Be specific and concise — no preamble."
                )
                summary = ask_claude(prompt, ctx, [])
                st.session_state[key] = summary
                return summary
            except Exception:
                return ""

        def render_flag_section(df, color, title):
            if df.empty:
                return
            st.markdown(
                f'<div class="section-header" style="color:{color};">{title}</div>',
                unsafe_allow_html=True
            )
            for _, row in df.iterrows():
                cname    = row["company_name"]
                inv_year = "—"
                if not fs.empty and "investment_date" in fs.columns:
                    fs_row = fs[fs["company_name"] == cname]
                    if not fs_row.empty:
                        try:
                            inv_year = str(pd.to_datetime(
                                fs_row.iloc[0]["investment_date"]).year)
                        except Exception:
                            pass

                with st.expander(
                    f"{flag_emoji(row['overall_flag'])}  {cname}  |  "
                    f"Acq. {inv_year}  |  "
                    f"Net Lev: {format_multiple(row.get('net_leverage'))}  |  "
                    f"Rev: {format_pct(row.get('revenue_yoy'))}  |  "
                    f"EBITDA Mgn: {format_pct(row.get('ltm_adj_ebitda_margin'))}"
                ):
                    # KPI metrics
                    mc = st.columns(5)
                    mc[0].metric("LTM Revenue",     format_millions(row.get("ltm_revenue")))
                    mc[1].metric("LTM Adj. EBITDA", format_millions(row.get("ltm_adj_ebitda")))
                    mc[2].metric("EBITDA Margin",   format_pct(row.get("ltm_adj_ebitda_margin")))
                    mc[3].metric("Net Leverage",    format_multiple(row.get("net_leverage")))
                    mc[4].metric("Rev Growth",      format_pct(row.get("revenue_yoy")))

                    # Flag badges — colored
                    fc_row = st.columns(4)
                    for idx, (fc_label, fc_key) in enumerate([
                        ("Revenue Growth", "revenue_growth_flag"),
                        ("EBITDA Margin",  "ebitda_margin_flag"),
                        ("Net Leverage",   "net_leverage_flag"),
                        ("Int. Coverage",  "interest_coverage_flag"),
                    ]):
                        fval = row.get(fc_key, "") or ""
                        fclr = {"Red": RED_FLAG, "Yellow": XANTHOUS,
                                 "Green": SEA_GREEN}.get(fval, SLATE)
                        fc_row[idx].markdown(
                            f"<div style='font-size:10px;color:{SLATE};'>{fc_label}</div>"
                            f"<div style='font-size:13px;font-weight:700;color:{fclr};'>"
                            f"{flag_emoji(fval)} {fval}</div>",
                            unsafe_allow_html=True
                        )

                    # AI Summary
                    ai_col, btn_col = st.columns([4, 1])
                    with btn_col:
                        if st.button("AI Summary", key=f"ai_sum_{cname}",
                                      use_container_width=True):
                            with st.spinner("Generating..."):
                                # Force refresh
                                k = f"ai_flag_summary_{cname}"
                                st.session_state.pop(k, None)
                                ai_flag_summary(cname, row)
                    with ai_col:
                        summary = st.session_state.get(f"ai_flag_summary_{cname}", "")
                        if summary:
                            st.markdown(
                                f"<div style='background:{LIGHT_BG};border-left:3px solid {SLATE};"
                                f"padding:8px 10px;border-radius:4px;font-size:12px;"
                                f"color:{NAVY};font-family:Arial;'>"
                                f"<b>AI:</b> {summary}</div>",
                                unsafe_allow_html=True
                            )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Action buttons
                    ac = st.columns(5)
                    if ac[0].button("View Company", key=f"goto_co_{cname}",
                                     use_container_width=True):
                        st.session_state["page"]             = "company_detail"
                        st.session_state["selected_company"] = cname
                        st.rerun()
                    for metric_name, btn_col in zip(
                        ["Net Leverage", "EBITDA Margin", "Rev Growth", "Gross Margin"],
                        ac[1:]
                    ):
                        if btn_col.button(metric_name,
                                           key=f"flag_drill_{cname}_{metric_name}",
                                           use_container_width=True):
                            set_drill("flags", company=cname, metric=metric_name)
                            st.rerun()

        render_flag_section(red,    RED_FLAG,  "RED — Covenant or Material Breach")
        render_flag_section(yellow, "#B7860B", "YELLOW — Watch List")
        render_flag_section(green,  SEA_GREEN, "GREEN — Notable Outperformers")

    # -----------------------------------------------------------------------
    # VIEW 2: Company KPIs  (from vw_portfolio_flags — detailed metrics)
    # -----------------------------------------------------------------------
    elif view_mode == "Company KPIs":
        if pf_filtered.empty:
            st.info("Portfolio flags data not available. "
                    "Run export_to_csv.py to generate portfolio_flags.csv.")
        else:
            company_sel = st.selectbox(
                "Select Company",
                sorted(pf_filtered["company_name"].unique().tolist()),
                key="fa_company_kpi_sel"
            )
            if company_sel:
                company_row = pf_filtered[pf_filtered["company_name"] == company_sel]
                if not company_row.empty:
                    from page_portfolio_flags import render_company_scorecard
                    render_company_scorecard(company_row.iloc[0])

                    # AI summary for this company
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown('<div class="section-header">AI Analysis</div>',
                                unsafe_allow_html=True)
                    ai_key = f"ai_company_kpi_{company_sel}"
                    aicol1, aicol2 = st.columns([4, 1])
                    with aicol2:
                        if st.button("Generate AI Summary", key=f"gen_ai_kpi_{company_sel}",
                                      use_container_width=True):
                            try:
                                from ai import ask_claude, build_company_context_with_news
                                ctx  = build_company_context_with_news(company_sel)
                                resp = ask_claude(
                                    f"Write a 3-bullet analysis of {company_sel}'s credit "
                                    f"and operating performance based on the KPI flags. "
                                    f"Lead each bullet with the metric name.",
                                    ctx, []
                                )
                                st.session_state[ai_key] = resp
                            except Exception as exc:
                                st.error(f"AI error: {exc}")
                    with aicol1:
                        if ai_key in st.session_state:
                            st.markdown(
                                f"<div style='background:{LIGHT_BG};"
                                f"border-left:3px solid {NAVY};padding:10px 14px;"
                                f"border-radius:4px;font-size:12px;color:{NAVY};"
                                f"font-family:Arial;white-space:pre-line;'>"
                                f"{st.session_state[ai_key]}</div>",
                                unsafe_allow_html=True
                            )

                    if st.button(f"Go to {company_sel} Detail →",
                                  key=f"fa_goto_{company_sel}"):
                        st.session_state["page"]             = "company_detail"
                        st.session_state["selected_company"] = company_sel
                        st.rerun()

    # -----------------------------------------------------------------------
    # VIEW 3: Scorecard Table  (full portfolio datasheet view)
    # -----------------------------------------------------------------------
    else:
        st.markdown('<div class="section-header">Full Portfolio KPI Scorecard</div>',
                    unsafe_allow_html=True)

        # Merge flags + portfolio flags for a comprehensive table
        score_cols = [
            "company_name", "ltm_revenue", "ltm_ebitda", "ltm_adj_ebitda",
            "ltm_adj_ebitda_margin", "revenue_yoy", "ebitda_yoy",
            "net_leverage", "interest_coverage",
            "overall_flag", "revenue_growth_flag",
            "ebitda_margin_flag", "net_leverage_flag", "interest_coverage_flag"
        ]
        available = [c for c in score_cols if c in flags_filtered.columns]
        score_df  = flags_filtered[available].copy()

        # Add portfolio flags columns if available
        if not pf_filtered.empty:
            pf_cols = ["company_name"]
            for c in ["flag_tev_ebitda", "flag_moic", "flag_free_cash_flow",
                      "flag_cash_to_debt", "signal_distress", "signal_watchlist",
                      "signal_outperformer"]:
                if c in pf_filtered.columns:
                    pf_cols.append(c)
            if len(pf_cols) > 1:
                score_df = score_df.merge(pf_filtered[pf_cols], on="company_name", how="left")

        # Add sector + year from fund summary
        if not fs.empty:
            fs_meta = fs[["company_name","sector","investment_date"]].copy()
            fs_meta["acq_year"] = pd.to_datetime(
                fs_meta["investment_date"], errors="coerce").dt.year.astype("Int64").astype(str)
            score_df = score_df.merge(
                fs_meta[["company_name","sector","acq_year"]],
                on="company_name", how="left"
            )

        # Format display
        def fmt_flag_cell(flag):
            emoji = flag_emoji(str(flag)) if pd.notna(flag) else "⚪"
            return f"{emoji} {flag}" if pd.notna(flag) and flag else "—"

        def fmt_signal(val):
            if pd.isna(val): return "—"
            return "Yes" if int(val) == 1 else "No"

        fmt_map = {
            "ltm_revenue":            format_millions,
            "ltm_ebitda":             format_millions,
            "ltm_adj_ebitda":         format_millions,
            "ltm_adj_ebitda_margin":  format_pct,
            "revenue_yoy":            format_pct,
            "ebitda_yoy":             format_pct,
            "net_leverage":           format_multiple,
            "interest_coverage":      format_multiple,
            "overall_flag":           fmt_flag_cell,
            "revenue_growth_flag":    fmt_flag_cell,
            "ebitda_margin_flag":     fmt_flag_cell,
            "net_leverage_flag":      fmt_flag_cell,
            "interest_coverage_flag": fmt_flag_cell,
            "flag_tev_ebitda":        fmt_flag_cell,
            "flag_moic":              fmt_flag_cell,
            "flag_free_cash_flow":    fmt_flag_cell,
            "flag_cash_to_debt":      fmt_flag_cell,
            "signal_distress":        fmt_signal,
            "signal_watchlist":       fmt_signal,
            "signal_outperformer":    fmt_signal,
        }
        for col, fn in fmt_map.items():
            if col in score_df.columns:
                score_df[col] = score_df[col].apply(fn)

        rename_map = {
            "company_name":           "Company",
            "sector":                 "Sector",
            "acq_year":               "Acq. Year",
            "ltm_revenue":            "LTM Revenue",
            "ltm_ebitda":             "LTM EBITDA",
            "ltm_adj_ebitda":         "LTM Adj. EBITDA",
            "ltm_adj_ebitda_margin":  "EBITDA Margin",
            "revenue_yoy":            "Rev Growth",
            "ebitda_yoy":             "EBITDA Growth",
            "net_leverage":           "Net Leverage",
            "interest_coverage":      "Int. Coverage",
            "overall_flag":           "Overall",
            "revenue_growth_flag":    "Rev Flag",
            "ebitda_margin_flag":     "Margin Flag",
            "net_leverage_flag":      "Lev Flag",
            "interest_coverage_flag": "Cov Flag",
            "flag_tev_ebitda":        "TEV/EBITDA",
            "flag_moic":              "MOIC Flag",
            "flag_free_cash_flow":    "FCF Flag",
            "flag_cash_to_debt":      "Liquidity",
            "signal_distress":        "Distress",
            "signal_watchlist":       "Watchlist",
            "signal_outperformer":    "Outperformer",
        }
        score_df = score_df.rename(columns={k: v for k, v in rename_map.items()
                                             if k in score_df.columns})

        flag_display_cols = [c for c in ["Overall","Rev Flag","Margin Flag","Lev Flag",
                                          "Cov Flag","TEV/EBITDA","MOIC Flag","FCF Flag",
                                          "Liquidity"] if c in score_df.columns]

        def color_flag_cell(val):
            s = str(val)
            if "Red"    in s: return f"color: {RED_FLAG}; font-weight: 700"
            if "Yellow" in s: return f"color: #B7860B; font-weight: 700"
            if "Green"  in s: return f"color: {SEA_GREEN}; font-weight: 700"
            if "Yes"    in s: return f"color: {RED_FLAG}; font-weight: 700"
            return ""

        if "Company" in score_df.columns:
            styled = (score_df.set_index("Company")
                              .style.map(color_flag_cell, subset=flag_display_cols))
        else:
            styled = score_df.style.map(color_flag_cell, subset=flag_display_cols)

        st.dataframe(styled, use_container_width=True, height=600)

        # Click-through buttons below table
        st.caption("Navigate to company detail:")
        nav_cols = st.columns(min(6, len(score_df)))
        companies_list = score_df.index.tolist() if "Company" not in score_df.columns                          else score_df.get("Company", pd.Series()).tolist()
        for i, cname in enumerate(companies_list):
            if nav_cols[i % len(nav_cols)].button(
                str(cname), key=f"sc_goto_{cname}", use_container_width=True
            ):
                st.session_state["page"]             = "company_detail"
                st.session_state["selected_company"] = str(cname)
                st.rerun()


# ---------------------------------------------------------------------------
# Portfolio AI page
# ---------------------------------------------------------------------------

def page_portfolio_ai():
    render_page_header("Portfolio AI Analyst")

    st.markdown("""
    <div style="background:white; border:1px solid #E0E4EA; border-radius:6px;
                padding:14px 18px; margin-bottom:16px; font-family:Arial; font-size:13px; color:#3F6680;">
        Ask anything about your portfolio — fund-level metrics, company comparisons,
        narrative generation, or memo bullets. Claude has access to all LTM financials,
        flags, and company profiles.
    </div>
    """, unsafe_allow_html=True)

    if "portfolio_chat" not in st.session_state:
        st.session_state.portfolio_chat = []

    context = build_portfolio_context()

    # Suggested prompts
    st.markdown('<div class="section-header">Suggested Questions</div>', unsafe_allow_html=True)
    prompts = [
        "Which companies have the highest net leverage risk?",
        "Rank all companies by LTM revenue growth",
        "Write a fund overview paragraph for the Q3 board deck",
        "Which companies are underperforming on EBITDA margin?",
        "Compare revenue growth across Beauty & Personal Care companies",
        "Summarize all red flag companies in bullet points",
    ]
    cols = st.columns(3)
    for i, prompt in enumerate(prompts):
        if cols[i % 3].button(prompt, key=f"pf_prompt_{i}", use_container_width=True):
            st.session_state.portfolio_chat.append({"role": "user", "content": prompt})
            with st.spinner("Analysing portfolio..."):
                response = ask_claude(prompt, context, st.session_state.portfolio_chat[:-1])
            st.session_state.portfolio_chat.append({"role": "assistant", "content": response})

    # Chat history
    st.markdown('<div class="section-header">Conversation</div>', unsafe_allow_html=True)
    for msg in st.session_state.portfolio_chat:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">{msg["content"]}</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>',
                        unsafe_allow_html=True)

    if st.session_state.portfolio_chat:
        if st.button("Clear conversation", type="secondary"):
            st.session_state.portfolio_chat = []
            st.rerun()

    user_input = st.chat_input("Ask about your portfolio...")
    if user_input:
        st.session_state.portfolio_chat.append({"role": "user", "content": user_input})
        with st.spinner("Analysing..."):
            response = ask_claude(user_input, context, st.session_state.portfolio_chat[:-1])
        st.session_state.portfolio_chat.append({"role": "assistant", "content": response})
        st.rerun()


# ---------------------------------------------------------------------------
# Persistent AI panel — renders in right column when toggled open
# ---------------------------------------------------------------------------

def render_ai_panel():
    """Persistent AI analyst panel shown alongside any page."""
    page    = st.session_state.get("page", "portfolio_overview")
    company = st.session_state.get("selected_company")

    st.markdown(f"""
    <div style="background:{NAVY}; padding:10px 14px; border-radius:6px 6px 0 0;
                margin-bottom:0;">
        <span style="color:white; font-size:13px; font-weight:700;
                     font-family:Arial;">AI Analyst</span>
        <span style="color:{SKY}; font-size:11px; font-family:Arial;
                     margin-left:8px;">Ask anything</span>
    </div>
    <div style="background:white; border:1px solid {BORDER}; border-top:none;
                border-radius:0 0 6px 6px; padding:10px; margin-bottom:12px;">
    """, unsafe_allow_html=True)

    # Build context based on current page
    try:
        from ai import (build_portfolio_context_with_news,
                        build_company_context_with_news, ask_claude)
        if page == "company_detail" and company:
            context     = build_company_context_with_news(company)
            placeholder = f"Ask about {company}..."
            suggested   = [
                f"Summarize {company} in 3 bullets",
                f"Key risks for {company}?",
                f"Write a board update for {company}",
            ]
        else:
            context     = build_portfolio_context_with_news()
            placeholder = "Ask about the portfolio..."
            suggested   = [
                "Which companies have the highest leverage?",
                "Summarize red flag companies",
                "Rank companies by revenue growth",
                "Write a fund overview paragraph",
            ]
        ai_available = True
    except Exception:
        ai_available = False
        context      = ""
        placeholder  = "AI unavailable"
        suggested    = []

    # Chat history — keyed by page so context resets on navigation
    chat_key = f"ai_panel_{page}_{company or 'portfolio'}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    history = st.session_state[chat_key]

    # Suggested prompts
    if suggested and not history:
        for prompt in suggested:
            if st.button(prompt, key=f"panel_prompt_{prompt[:25]}",
                          use_container_width=True):
                history.append({"role": "user", "content": prompt})
                if ai_available:
                    with st.spinner("Thinking..."):
                        response = ask_claude(prompt, context, [])
                    history.append({"role": "assistant", "content": response})
                st.session_state[chat_key] = history
                st.rerun()

    # Chat messages
    for msg in history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="background:{NAVY}; color:white; padding:8px 10px;
                        border-radius:10px 10px 2px 10px; margin:4px 0;
                        font-size:12px; font-family:Arial;">
                {msg["content"]}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:{LIGHT_BG}; color:{NAVY}; padding:8px 10px;
                        border-radius:10px 10px 10px 2px; margin:4px 0;
                        font-size:12px; font-family:Arial; border:1px solid {BORDER};">
                {msg["content"]}
            </div>""", unsafe_allow_html=True)

    if history:
        if st.button("Clear", key="ai_panel_clear", use_container_width=True):
            st.session_state[chat_key] = []
            st.rerun()

    # Input
    if ai_available:
        user_input = st.chat_input(placeholder, key="ai_panel_input")
        if user_input:
            history.append({"role": "user", "content": user_input})
            with st.spinner("Thinking..."):
                response = ask_claude(user_input, context, history[:-1])
            history.append({"role": "assistant", "content": response})
            st.session_state[chat_key] = history
            st.rerun()
    else:
        st.info("Add Anthropic API key to secrets to enable AI.")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not check_password():
        return

    # Pre-warm cache
    load_portfolio_overview()
    load_fund_summary()
    load_flags()
    load_ltm_snapshot()
    load_company_master()

    # Initialise page state
    if "page" not in st.session_state:
        st.session_state["page"] = "portfolio_overview"

    # Render top nav bar
    render_top_nav()

    # Route to current page — split layout when AI panel is open
    page       = st.session_state.get("page", "portfolio_overview")
    ai_open    = st.session_state.get("ai_panel_open", False)

    if ai_open:
        main_col, ai_col = st.columns([3, 1])
    else:
        main_col = st.container()
        ai_col   = None

    with main_col:
        if page == "portfolio_overview":
            page_portfolio_overview()
        elif page == "fund_summary":
            page_fund_summary()
        elif page == "company_detail":
            from pages_extra import page_company_detail_enhanced
            page_company_detail_enhanced()
        elif page == "flags_alerts":
            page_flags_alerts()
        elif page == "consumer_kpis":
            from pages_extra import page_consumer_kpis
            page_consumer_kpis()
        elif page == "portfolio_flags":
            from page_portfolio_flags import page_portfolio_flags
            page_portfolio_flags()
        elif page == "ai_analyst":
            page_portfolio_ai()
        elif page == "export_ppt":
            from export_ppt import page_export
            page_export()

    if ai_open and ai_col is not None:
        with ai_col:
            render_ai_panel()


if __name__ == "__main__":
    main()
