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
        login_btn = st.button("Sign In", use_container_width=True, type="secondary")

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
    ("Portfolio",           "portfolio_overview"),
    ("Fund – Coming Soon",  "fund_summary"),
    ("Companies",           "company_detail"),
    ("KPI Metric Alerts",   "flags_alerts"),
    ("SOP & Trainings",     "sop_training"),
    ("Data Export",         "export_ppt"),
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
    all_nav = list(PAGES) + [("AI Companion" if not ai_open else "✕ Close AI", "_ai_toggle")]
    btn_cols = st.columns(len(all_nav))

    for i, (label, key) in enumerate(all_nav):
        col = btn_cols[i]

        if key == "_ai_toggle":
            if col.button(label, key="toggle_ai_panel",
                          use_container_width=True,
                          type="secondary"):
                st.session_state["ai_panel_open"] = not ai_open
                st.rerun()
        else:
            display   = f"{label} ({red_count})" if key == "flags_alerts" and red_count > 0 else label
            is_active = (key == current)
            # All secondary — CSS targets active tab via aria-label key prefix
            prefix    = "nav_active_" if is_active else "nav_"
            if col.button(display, key=f"{prefix}{key}",
                          use_container_width=True,
                          type="secondary"):
                if key != current:
                    st.session_state["page"] = key
                    if key != "company_detail":
                        st.session_state.pop("selected_company", None)
                    for k in ["drill_page", "drill_company", "drill_metric", "flag_filter_company"]:
                        st.session_state.pop(k, None)
                    st.rerun()

    # Nav CSS: all buttons secondary — aria-label selector styles active tab
    st.markdown("""
    <style>
    .tsg-nav-row {{
        background: #FFFFFF;
        border-bottom: 2px solid #E0E4EA;
        padding: 0;
        margin-bottom: 8px;
    }}
    .tsg-nav-row > div[data-testid="stHorizontalBlock"] {{
        gap: 0 !important;
        background: #FFFFFF;
    }}
    .tsg-nav-row button {{
        border: none !important;
        border-bottom: 3px solid transparent !important;
        border-radius: 0 !important;
        background: #FFFFFF !important;
        background-color: #FFFFFF !important;
        box-shadow: none !important;
        color: #3F6680 !important;
        font-size: 13px !important;
        font-family: Arial, sans-serif !important;
        font-weight: 500 !important;
        padding: 10px 8px !important;
        width: 100% !important;
    }}
    .tsg-nav-row button:hover {{
        color: #071733 !important;
        border-bottom-color: #A8CFDE !important;
        background: #FFFFFF !important;
    }}
    .tsg-nav-row button[aria-label^="nav_active_"] {{
        color: #071733 !important;
        font-weight: 700 !important;
        border-bottom: 3px solid #071733 !important;
        background: #FFFFFF !important;
    }}
    /* Global: ensure all buttons have visible text */
    button, .stButton button {{
        color: #071733 !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="tsg-nav-row">', unsafe_allow_html=True)


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
    overview  = _ov_df.iloc[0]
    flags     = load_flags()
    fs        = load_fund_summary()
    quarterly = load_quarterly()

    # -----------------------------------------------------------------------
    # FILTERS
    # -----------------------------------------------------------------------
    with st.expander("Filters", expanded=False):
        fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 2, 1])
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
        with fc5:
            tab_period = st.radio(
                "Period",
                ["Quarterly", "Monthly", "Yearly"],
                key="po_tab_period",
                label_visibility="visible"
            )

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

    filtered_names = fs_filtered["company_name"].tolist()
    q_filt = quarterly[quarterly["company_name"].isin(filtered_names)] \
             if not fs_filtered.empty else quarterly

    # Apply global 3-year rolling window to all portfolio charts
    _three_yr_cutoff = pd.Timestamp.now() - pd.DateOffset(years=3)
    if not q_filt.empty and "cash_flow_date" in q_filt.columns:
        q_filt = q_filt.copy()
        q_filt["cash_flow_date"] = pd.to_datetime(q_filt["cash_flow_date"], errors="coerce")
        q_filt = q_filt[q_filt["cash_flow_date"] >= _three_yr_cutoff]

    flags_filtered = flags[flags["company_name"].isin(filtered_names)] \
                     if not flags.empty else flags

    # -----------------------------------------------------------------------
    # Period-label the quarterly data per the selected filter
    # The CSV already contains pre-calculated LTM figures — we just need to
    # pick the most recent row for each company within the selected period.
    # If multiple rows fall in the same period, take the one with the latest
    # cash_flow_date (most recent LTM as of that period).
    # -----------------------------------------------------------------------
    def _apply_period_label(df, mode):
        """Filter to the right period type and assign _plabel from cash_flow_date."""
        df = df.copy()
        df["cash_flow_date"] = pd.to_datetime(df["cash_flow_date"], errors="coerce")

        # Filter by the period column if it exists (Quarterly / Annual / Monthly)
        if "period" in df.columns:
            period_filter = {"Quarterly": "Quarterly",
                             "Yearly":    "Annual",
                             "Monthly":   "Monthly"}.get(mode, "Quarterly")
            df = df[df["period"] == period_filter]

        # Assign display label from cash_flow_date
        if mode == "Monthly":
            df["_plabel"] = df["cash_flow_date"].dt.strftime("%b %Y")
        elif mode == "Yearly":
            df["_plabel"] = df["cash_flow_date"].dt.strftime("%Y-%m")  # keep full date for sorting
        else:
            df["_plabel"] = (df["period_label"] if "period_label" in df.columns
                             else df["cash_flow_date"].dt.to_period("Q").astype(str))
        return df

    q_period = _apply_period_label(q_filt, tab_period) if not q_filt.empty else pd.DataFrame()

    # Most recent LTM row per company × period (handles duplicate periods by taking latest date)
    if not q_period.empty:
        q_latest_snap = (q_period.sort_values("cash_flow_date")
                                 .groupby("company_name").last().reset_index())
        q_prior_snap  = (q_period.sort_values("cash_flow_date")
                                 .groupby("company_name").nth(-2).reset_index())
    else:
        q_latest_snap = pd.DataFrame()
        q_prior_snap  = pd.DataFrame()

    # -----------------------------------------------------------------------
    # KPI tile values — pull pre-calculated LTM figures directly from
    # fund_summary (fs_filtered). Do NOT recalculate from quarterly data.
    # -----------------------------------------------------------------------
    total_tev     = fs_filtered["current_tev"].sum() \
                    if not fs_filtered.empty and "current_tev" in fs_filtered.columns else None

    total_revenue = fs_filtered["ltm_revenue"].sum() \
                    if not fs_filtered.empty and "ltm_revenue" in fs_filtered.columns else None

    total_ebitda  = fs_filtered["ltm_adj_ebitda"].sum() \
                    if not fs_filtered.empty and "ltm_adj_ebitda" in fs_filtered.columns else None

    # TEV-weighted avg net leverage
    if not fs_filtered.empty and "net_leverage" in fs_filtered.columns and \
       "current_tev" in fs_filtered.columns and fs_filtered["current_tev"].sum() > 0:
        avg_leverage = ((fs_filtered["net_leverage"] * fs_filtered["current_tev"]).sum()
                        / fs_filtered["current_tev"].sum())
    else:
        avg_leverage = None

    avg_margin    = fs_filtered["ltm_adj_ebitda_margin"].mean() \
                    if not fs_filtered.empty and "ltm_adj_ebitda_margin" in fs_filtered.columns else None

    _period_label_str = {"Quarterly": "quarter", "Monthly": "month", "Yearly": "year"}.get(tab_period, "period")

    # Alert banner removed per feedback (4/7/26)

    # -----------------------------------------------------------------------
    # KPI TILES
    # -----------------------------------------------------------------------
    tile_cols = st.columns(8)
    tiles = [
        (format_millions(total_tev),    "Total TEV",         False),
        (format_millions(total_revenue),"LTM Revenue",       False),
        (format_millions(total_ebitda), "LTM EBITDA",        False),
        (format_multiple(avg_leverage), "Avg Net Leverage",  False),
        (format_pct(avg_margin),        "Avg EBITDA Margin", False),
        ("Gross MOIC",                  "Gross MOIC",        True),
        ("Gross IRR",                   "Gross IRR",         True),
        ("Net IRR",                     "Net IRR",           True),
    ]
    for col, (val, label, pending) in zip(tile_cols, tiles):
        if pending:
            col.markdown(kpi_tile_pending(label), unsafe_allow_html=True)
        else:
            col.markdown(kpi_tile(val, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # TOP 4 FLAG SUMMARY — period-aware Δ in key metrics
    # -----------------------------------------------------------------------
    st.markdown('<div class="section-header">Portfolio Alerts</div>', unsafe_allow_html=True)
    flag_row_cols = st.columns([1, 1, 1, 1])

    # pop_ebitda already computed above from q_latest_snap vs q_prior_snap
    # Use ltm_adj_ebitda from flags if available, otherwise fall back to quarterly
    if not q_latest_snap.empty and not q_prior_snap.empty and "adj_ebitda" in q_latest_snap.columns:
        _latest_ebitda = q_latest_snap["adj_ebitda"].sum()
        _prior_ebitda  = q_prior_snap["adj_ebitda"].sum()
        pop_ebitda = float(_latest_ebitda - _prior_ebitda) \
                     if not pd.isna(_latest_ebitda) and not pd.isna(_prior_ebitda) else None
    else:
        pop_ebitda = None

    def _flag_box(col, value_str, label, flag, note=""):
        clr = {
            "Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN
        }.get(flag, SLATE)
        col.markdown(f"""
        <div style="background:white;border:1px solid {BORDER};border-left:4px solid {clr};
                    border-radius:6px;padding:12px 14px;text-align:center;">
            <div style="font-size:20px;font-weight:700;color:{clr};font-family:Arial;">
                {value_str}</div>
            <div style="font-size:10px;color:{NAVY};font-family:Arial;font-weight:700;
                        margin-top:2px;">{label}</div>
            <div style="font-size:9px;color:{SLATE};font-family:Arial;margin-top:2px;">
                {note}</div>
        </div>""", unsafe_allow_html=True)

    # LTM EBITDA period-over-period Δ
    ebitda_flag = ("Green" if pop_ebitda and pop_ebitda > 0
                   else "Red" if pop_ebitda and pop_ebitda < 0 else "Yellow")
    ebitda_str  = (f"{'▲' if pop_ebitda and pop_ebitda > 0 else '▼'} {format_millions(abs(pop_ebitda))}"
                   if pop_ebitda is not None else "—")
    _flag_box(flag_row_cols[0], ebitda_str, "LTM EBITDA Δ", ebitda_flag,
              f"vs prior {_period_label_str}")

    # Avg Revenue Growth (YoY from flags — point-in-time, won't change with period)
    if not flags_filtered.empty and "revenue_yoy" in flags_filtered.columns:
        avg_rev_growth = flags_filtered["revenue_yoy"].mean()
        rev_flag = "Green" if avg_rev_growth > 0.10 else "Yellow" if avg_rev_growth > 0 else "Red"
        rev_str  = format_pct(avg_rev_growth)
    else:
        rev_flag = "Yellow"
        rev_str  = "—"
    _flag_box(flag_row_cols[1], rev_str, "Avg Rev Growth (YoY)", rev_flag, "portfolio average")

    # Avg Net Leverage — from fs_filtered (pre-calculated LTM)
    lev_flag = ("Green" if avg_leverage and avg_leverage < 5
                else "Yellow" if avg_leverage and avg_leverage < 6 else "Red")
    _flag_box(flag_row_cols[2], format_multiple(avg_leverage), "Avg Net Leverage",
              lev_flag, "wtd. by TEV · Red >6x")

    # Gross MOIC (pending)
    flag_row_cols[3].markdown(kpi_tile_pending("Gross MOIC"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -----------------------------------------------------------------------
    # TABS: Portfolio Periodic Trends | By Company Trends | Company Alerts
    # -----------------------------------------------------------------------
    st.markdown("""
    <style>
    [data-testid="stTabs"] button[data-baseweb="tab"]:nth-child(1) { position: relative; }
    </style>
    """, unsafe_allow_html=True)

    po_tab1, po_tab2, po_tab3 = st.tabs([
        "Portfolio Datasheet", "By Company Trends", "Company Alerts"
    ])
    st.markdown("""
    <div title="Select monthly, quarterly, or annual to display period-over-period metrics in total for current TSG portfolio companies" style="display:none"></div>
    """, unsafe_allow_html=True)


    # ---- TAB 1: Portfolio Periodic Trends ----
    with po_tab1:
        chart_col, donut_col = st.columns([3, 1])

        with chart_col:
            view_toggle = tab_period

            # Filter q_filt by the period type column, then group by cash_flow_date
            # Values are already LTM — just sum across companies per period date
            period_filter_map = {"Quarterly": "Quarterly", "Yearly": "Annual", "Monthly": "Monthly"}
            pf = period_filter_map.get(view_toggle, "Quarterly")

            if not q_filt.empty and "period" in q_filt.columns:
                q_chart = q_filt[q_filt["period"] == pf].copy()
            else:
                q_chart = q_filt.copy()

            q_chart["cash_flow_date"] = pd.to_datetime(q_chart["cash_flow_date"], errors="coerce")
            q_chart = q_chart.sort_values("cash_flow_date")

            if not q_chart.empty and "revenue" in q_chart.columns:
                agg = q_chart.groupby("cash_flow_date").agg(
                    revenue    = ("revenue",    "sum"),
                    adj_ebitda = ("adj_ebitda", "sum"),
                ).reset_index().sort_values("cash_flow_date").tail(
                    10 if view_toggle == "Yearly" else 18 if view_toggle == "Monthly" else 12
                )
                agg["period_label"] = agg["cash_flow_date"].dt.strftime(
                    "%Y" if view_toggle == "Yearly" else "%b %Y"
                )
            else:
                agg = pd.DataFrame()

            chart_title = f"Portfolio LTM Revenue & EBITDA — {view_toggle}"

            if not agg.empty:
                st.markdown(f'<div class="section-header">{chart_title}</div>',
                            unsafe_allow_html=True)
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=agg["period_label"], y=agg["revenue"],
                                      name="LTM Net Sales ($M)", marker_color=SLATE, opacity=0.85),
                              secondary_y=False)
                fig.add_trace(go.Bar(x=agg["period_label"], y=agg["adj_ebitda"],
                                      name="LTM Adj. EBITDA ($M)", marker_color=SKY, opacity=0.85),
                              secondary_y=False)
                margin = agg["adj_ebitda"] / agg["revenue"].replace(0, float("nan"))
                fig.add_trace(go.Scatter(x=agg["period_label"], y=margin,
                                          name="EBITDA Margin %", mode="lines+markers",
                                          line=dict(color=XANTHOUS, width=2),
                                          marker=dict(size=5)),
                              secondary_y=True)
                fig.update_layout(
                    height=360, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0), barmode="group",
                    legend=dict(orientation="h", y=-0.18, font=dict(size=11)),
                    font=dict(family="Arial", color=NAVY, size=11)
                )
                fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False,
                                 tickfont=dict(size=11))
                fig.update_yaxes(tickformat=".0%", secondary_y=True, tickfont=dict(size=11))
                fig.update_xaxes(tickangle=-45, tickmode="linear", dtick=1,
                                 tickfont=dict(size=10))
                st.plotly_chart(fig, use_container_width=True)

        with donut_col:
            st.markdown('<div class="section-header">% of Deployed Capital by Sector</div>',
                        unsafe_allow_html=True)
            sector_data = fs_filtered.groupby("sector")["current_tev"].sum().reset_index()
            sector_data = sector_data.dropna().sort_values("current_tev", ascending=False)
            if not sector_data.empty:
                fig2 = px.pie(sector_data, values="current_tev", names="sector", hole=0.55,
                               color_discrete_sequence=[NAVY, SLATE, SKY, XANTHOUS,
                                                         CELADON, SEA_GREEN, MAGENTA, EGGPLANT])
                fig2.update_traces(textposition="inside", textinfo="percent",
                                   textfont_size=12)
                fig2.update_layout(
                    height=340, showlegend=True,
                    legend=dict(font=dict(size=11), orientation="v",
                                x=1.0, xanchor="left"),
                    margin=dict(l=0, r=80, t=10, b=0),
                    paper_bgcolor="white"
                )
                st.plotly_chart(fig2, use_container_width=True)

        # ----------------------------------------------------------------
        # TAB 1 PIVOT TABLE: companies as rows, periods as columns
        # Single metric selectbox (alpha order) above the table
        # ----------------------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Portfolio Datasheet</div>',
                    unsafe_allow_html=True)
        st.caption("Select a metric to see how each company has trended across periods. Δ% = change vs prior period.")

        # Build the same ALL_METRIC_DEFS here so tab 1 is self-contained
        _T1_METRIC_DEFS = [
            ("Current Net Debt / EBITDA","net_leverage",            "q",     format_multiple, False),
            ("Current TEV",             "current_tev",              "fs",    format_millions, False),
            ("Current TEV / EBITDA",    "tev_to_ebitda",            "fs",    format_multiple, False),
            ("Current TEV / Net Sales", "tev_to_revenue",           "fs",    format_multiple, False),
            ("Debt Service Coverage",   "debt_service_coverage",    "q",     format_multiple, False),
            ("EBITDA Margin",           "adj_ebitda_margin_pct",    "q",     format_pct,      True),
            ("Entry EBITDA",            "entry_adj_ebitda",         "fs",    format_millions, False),
            ("Entry Net Debt",          "entry_net_debt",           "fs",    format_millions, False),
            ("Entry Net Debt / EBITDA", "entry_net_leverage",       "fs",    format_multiple, False),
            ("Entry Net Sales",         "entry_revenue",            "fs",    format_millions, False),
            ("Entry TEV",               "entry_tev",                "fs",    format_millions, False),
            ("Entry TEV / EBITDA",      "entry_tev_to_ebitda",      "fs",    format_multiple, False),
            ("Entry TEV / Net Sales",   "entry_tev_to_revenue",     "fs",    format_multiple, False),
            ("Floating Rate Debt",      "floating_rate_debt",       "q",     format_millions, False),
            ("Gross IRR",               "gross_irr",                "fs",    format_pct,      True),
            ("Gross MOI",               "gross_moi",                "fs",    format_multiple, False),
            ("Gross Margin %",          "gross_margin_pct",         "q",     format_pct,      True),
            ("Gross Profit",            "gross_profit",             "q",     format_millions, False),
            ("Interest Coverage",       "interest_coverage",        "q",     format_multiple, False),
            ("LTM Adj. EBITDA",         "adj_ebitda",               "q",     format_millions, False),
            ("LTM Capex (Excl. M&A)",   "capex",                    "q",     format_millions, False),
            ("LTM Cash Interest (Gross)","cash_interest_expense",   "q",     format_millions, False),
            ("LTM Cash Taxes",          "cash_taxes",               "q",     format_millions, False),
            ("LTM Credit Agmt. EBITDA", "credit_agreement_ebitda",  "q",     format_millions, False),
            ("LTM Free Cash Flow",      "free_cash_flow",           "q",     format_millions, False),
            ("LTM Mandatory Pmts",      "mandatory_principal",      "q",     format_millions, False),
            ("LTM Net Sales",           "ltm_revenue",              "q",     format_millions, False),
            ("LTM Revenue",             "ltm_revenue",              "q",     format_millions, False),
            ("LTM Δ NWC",               "change_in_nwc",            "q",     format_millions, False),
            ("Net Debt",                "net_debt",                 "q",     format_millions, False),
            ("PIK Debt",                "pik_debt",                 "q",     format_millions, False),
            ("Rev Growth (YoY)",        "revenue_yoy",              "flags", format_pct,      True),
            ("Sr. Secured Leverage",    "senior_secured_leverage",  "q",     format_multiple, False),
            ("Total Cost",              "entry_tev",                "fs",    format_millions, False),
            ("Total Gross Debt",        "total_gross_debt",         "q",     format_millions, False),
            ("Total Gross Leverage",    "gross_leverage",           "q",     format_multiple, False),
            ("Total Net Leverage",      "net_leverage",             "q",     format_multiple, False),
        ]
        _t1_metric_labels = sorted([d[0] for d in _T1_METRIC_DEFS])
        _t1_metric_lookup = {d[0]: d for d in _T1_METRIC_DEFS}

        # Single selectbox — alpha order
        _t1_sel = st.selectbox(
            "Metric",
            _t1_metric_labels,
            index=_t1_metric_labels.index("LTM Revenue") if "LTM Revenue" in _t1_metric_labels else 0,
            key="t1_metric_select",
            label_visibility="collapsed"
        )

        # Build period labels from q_filt using the tab-level period setting
        _t1_q = q_filt.copy() if not q_filt.empty else pd.DataFrame()
        if not _t1_q.empty:
            _t1_q["cash_flow_date"] = pd.to_datetime(_t1_q["cash_flow_date"], errors="coerce")
            # Filter to correct period type
            _pf_map = {"Quarterly": "Quarterly", "Yearly": "Annual", "Monthly": "Monthly"}
            if "period" in _t1_q.columns:
                _t1_q = _t1_q[_t1_q["period"] == _pf_map.get(tab_period, "Quarterly")]
            # Assign display label
            if tab_period == "Monthly":
                _t1_q["_plabel"] = _t1_q["cash_flow_date"].dt.strftime("%b %Y")
            elif tab_period == "Yearly":
                _t1_q["_plabel"] = _t1_q["cash_flow_date"].dt.strftime("%Y-%m")
            else:
                _t1_q["_plabel"] = (_t1_q["period_label"] if "period_label" in _t1_q.columns
                                    else _t1_q["cash_flow_date"].dt.to_period("Q").astype(str))

        _t1_periods = []
        if not _t1_q.empty:
            _t1_periods = (_t1_q.sort_values("cash_flow_date")["_plabel"]
                           .drop_duplicates().tolist())
        _t1_display_periods = _t1_periods[-12:] if len(_t1_periods) > 12 else _t1_periods

        _t1_companies = sorted(fs_filtered["company_name"].unique().tolist())

        _t1_lbl, _t1_col, _t1_src, _t1_fmt, _t1_is_pct = _t1_metric_lookup[_t1_sel]

        def _t1_get_val(cname, period):
            if _t1_src == "q":
                if _t1_q.empty: return None
                sub = _t1_q[(_t1_q["company_name"] == cname) & (_t1_q["_plabel"] == period)]
                if sub.empty: return None
                # Use exact column as specified in _T1_METRIC_DEFS — no ltm_ prefix guessing.
                # "LTM Revenue" already maps to "ltm_revenue"; non-LTM metrics map to their
                # plain column. Take last non-null to handle duplicate rows per period.
                if _t1_col in sub.columns:
                    non_null = sub[_t1_col].dropna()
                    if not non_null.empty:
                        return float(non_null.iloc[-1])
                return None
            elif _t1_src == "fs":
                sub = fs_filtered[fs_filtered["company_name"] == cname]
                if sub.empty or _t1_col not in sub.columns: return None
                v = sub.iloc[0][_t1_col]
                return None if pd.isna(v) else float(v)
            elif _t1_src == "flags":
                sub = flags_filtered[flags_filtered["company_name"] == cname]
                if sub.empty or _t1_col not in sub.columns: return None
                v = sub.iloc[0][_t1_col]
                return None if pd.isna(v) else float(v)

        # Build pivot: companies as rows, periods as columns
        _t1_rows = []
        for cname in _t1_companies:
            row = {"Company": cname}
            prev_val = None
            for p in _t1_display_periods:
                val = _t1_get_val(cname, p)
                row[p] = _t1_fmt(val) if val is not None else "—"
                if prev_val is not None and val is not None and prev_val != 0:
                    row[f"Δ {p}"] = f"{(val - prev_val) / abs(prev_val) * 100:+.1f}%"
                else:
                    row[f"Δ {p}"] = "—"
                prev_val = val
            _t1_rows.append(row)

        if _t1_rows:
            _t1_df = pd.DataFrame(_t1_rows).set_index("Company")
            _t1_delta_cols = [c for c in _t1_df.columns if c.startswith("Δ ")]

            def _t1_style(r):
                out = []
                for c in r.index:
                    s = str(r[c])
                    if c.startswith("Δ "):
                        if s.startswith("+"): out.append(f"color:{SEA_GREEN};font-weight:600")
                        elif s.startswith("-"): out.append(f"color:{RED_FLAG};font-weight:600")
                        else: out.append("")
                    else:
                        out.append("")
                return out

            try:
                _t1_styled = _t1_df.style.apply(_t1_style, axis=1)
            except Exception:
                _t1_styled = _t1_df.style

            st.dataframe(_t1_styled, use_container_width=True,
                         height=min(600, len(_t1_rows) * 38 + 50))
            st.caption(f"**{_t1_sel}** · {tab_period} · Δ% = change vs prior period")

            # ----------------------------------------------------------------
            # TREND CHART — chart type depends on metric per spec
            # ----------------------------------------------------------------
            # Chart type mapping per spec
            _MULTILINE_METRICS = {
                "LTM Revenue", "LTM Net Sales", "LTM Adj. EBITDA", "LTM Credit Agmt. EBITDA",
                "Gross Profit", "LTM Free Cash Flow", "LTM Cash Interest (Gross)",
                "LTM Cash Taxes", "LTM Mandatory Pmts", "LTM Capex (Excl. M&A)",
                "LTM Δ NWC", "Rev Growth (YoY)", "Gross Margin %", "EBITDA Margin",
            }
            _GROUPED_BAR_METRICS = {
                "Current Net Debt / EBITDA", "Sr. Secured Leverage", "Total Gross Leverage",
                "Debt Service Coverage", "Interest Coverage", "Total Gross Debt",
                "Net Debt", "Current TEV", "Total Net Leverage",
            }
            _STACKED_BAR_METRICS = {"Floating Rate Debt", "PIK Debt"}
            _STATIC_BAR_METRICS  = {
                "Entry Net Debt / EBITDA", "Entry TEV", "Entry Net Debt",
                "Entry Net Sales", "Entry EBITDA", "Total Cost",
            }
            _DUMBBELL_METRICS = {
                "Current TEV / EBITDA", "Entry TEV / EBITDA",
                "Current TEV / Net Sales", "Entry TEV / Net Sales",
            }
            _HORIZ_BAR_METRICS = {"Gross IRR", "Gross MOI"}

            # Distinct line styles for multi-line charts
            _DASH_PATTERNS = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot",
                               "solid", "dash", "dot", "dashdot", "longdash", "longdashdot",
                               "solid", "dash", "dot", "dashdot"]
            _MARKER_SYMBOLS = ["circle", "square", "diamond", "cross", "triangle-up",
                                "star", "hexagon", "pentagon", "circle", "square",
                                "diamond", "cross", "triangle-up", "star", "hexagon", "pentagon"]

            if _t1_sel in _MULTILINE_METRICS and not _t1_q.empty and _t1_src == "q":
                # Use exact column as specified — no ltm_ prefix guessing
                _t1_resolved_col = _t1_col if _t1_col in _t1_q.columns else None

                if _t1_resolved_col:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="section-header">{_t1_sel} — Trend by Company</div>',
                        unsafe_allow_html=True)
                    _fig_line = go.Figure()
                    for ci, cname in enumerate(_t1_companies):
                        _co_ts = (
                            _t1_q[_t1_q["company_name"] == cname]
                            [["_plabel", "cash_flow_date", _t1_resolved_col]]
                            .dropna(subset=[_t1_resolved_col])
                            .sort_values("cash_flow_date")
                            .drop_duplicates(subset=["_plabel"], keep="last")
                            .copy()
                        )
                        if _co_ts.empty:
                            continue
                        _fig_line.add_trace(go.Scatter(
                            x=_co_ts["_plabel"],
                            y=_co_ts[_t1_resolved_col],
                            name=cname,
                            mode="lines+markers",
                            line=dict(
                                color=COMPANY_COLORS[ci % len(COMPANY_COLORS)],
                                width=2,
                                dash=_DASH_PATTERNS[ci % len(_DASH_PATTERNS)],
                            ),
                            marker=dict(
                                size=6,
                                symbol=_MARKER_SYMBOLS[ci % len(_MARKER_SYMBOLS)],
                            ),
                        ))
                    _y_fmt = ".0%" if _t1_is_pct else ",.0f"
                    _fig_line.update_layout(
                        height=420, plot_bgcolor="white", paper_bgcolor="white",
                        margin=dict(l=0, r=0, t=10, b=0),
                        font=dict(family="Arial", color=NAVY, size=10),
                        legend=dict(orientation="h", y=-0.25, font=dict(size=9)),
                        xaxis=dict(tickangle=-45, tickmode="linear", dtick=1,
                                   tickfont=dict(size=9), gridcolor=BORDER),
                        yaxis=dict(tickformat=_y_fmt, gridcolor=BORDER),
                    )
                    st.plotly_chart(_fig_line, use_container_width=True)

            elif _t1_sel in _GROUPED_BAR_METRICS and not _t1_q.empty and _t1_src == "q":
                _t1_resolved_col = _t1_col if _t1_col in _t1_q.columns else None
                if _t1_resolved_col:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f'<div class="section-header">{_t1_sel} — by Company & Period</div>',
                                unsafe_allow_html=True)
                    _fig_gb = go.Figure()
                    for ci, cname in enumerate(_t1_companies):
                        _co_ts = (
                            _t1_q[_t1_q["company_name"] == cname]
                            [["_plabel", "cash_flow_date", _t1_resolved_col]]
                            .dropna(subset=[_t1_resolved_col])
                            .sort_values("cash_flow_date")
                            .drop_duplicates(subset=["_plabel"], keep="last")
                            .copy()
                        )
                        if _co_ts.empty: continue
                        _fig_gb.add_trace(go.Bar(
                            x=_co_ts["_plabel"], y=_co_ts[_t1_resolved_col],
                            name=cname,
                            marker_color=COMPANY_COLORS[ci % len(COMPANY_COLORS)],
                        ))
                    _fig_gb.update_layout(
                        height=400, barmode="group", plot_bgcolor="white",
                        paper_bgcolor="white", margin=dict(l=0, r=0, t=10, b=0),
                        font=dict(family="Arial", color=NAVY, size=10),
                        legend=dict(orientation="h", y=-0.25, font=dict(size=9)),
                        xaxis=dict(tickangle=-45, tickfont=dict(size=9), gridcolor=BORDER),
                        yaxis=dict(tickformat=",.2f", gridcolor=BORDER),
                    )
                    st.plotly_chart(_fig_gb, use_container_width=True)

            elif _t1_sel in _STACKED_BAR_METRICS and not _t1_q.empty and _t1_src == "q":
                _t1_resolved_col = _t1_col if _t1_col in _t1_q.columns else None
                if _t1_resolved_col:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f'<div class="section-header">{_t1_sel} — Stacked by Company</div>',
                                unsafe_allow_html=True)
                    _fig_sb = go.Figure()
                    for ci, cname in enumerate(_t1_companies):
                        _co_ts = (
                            _t1_q[_t1_q["company_name"] == cname]
                            [["_plabel", "cash_flow_date", _t1_resolved_col]]
                            .dropna(subset=[_t1_resolved_col])
                            .sort_values("cash_flow_date")
                            .drop_duplicates(subset=["_plabel"], keep="last")
                            .copy()
                        )
                        if _co_ts.empty: continue
                        _fig_sb.add_trace(go.Bar(
                            x=_co_ts["_plabel"], y=_co_ts[_t1_resolved_col],
                            name=cname,
                            marker_color=COMPANY_COLORS[ci % len(COMPANY_COLORS)],
                        ))
                    _fig_sb.update_layout(
                        height=400, barmode="stack", plot_bgcolor="white",
                        paper_bgcolor="white", margin=dict(l=0, r=0, t=10, b=0),
                        font=dict(family="Arial", color=NAVY, size=10),
                        legend=dict(orientation="h", y=-0.25, font=dict(size=9)),
                        xaxis=dict(tickangle=-45, tickfont=dict(size=9)),
                        yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
                    )
                    st.plotly_chart(_fig_sb, use_container_width=True)

            elif _t1_sel in _STATIC_BAR_METRICS and _t1_src == "fs":
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f'<div class="section-header">{_t1_sel} — at Entry (Static)</div>',
                            unsafe_allow_html=True)
                _static_data = []
                for cname in _t1_companies:
                    v = _t1_get_val(cname, _t1_display_periods[-1] if _t1_display_periods else None)
                    if v is not None:
                        _static_data.append({"company": cname, "value": v})
                if _static_data:
                    _sdf = pd.DataFrame(_static_data).sort_values("value")
                    _fig_st = go.Figure(go.Bar(
                        x=_sdf["value"], y=_sdf["company"], orientation="h",
                        marker_color=NAVY,
                        text=_sdf["value"].apply(_t1_fmt), textposition="outside",
                    ))
                    _fig_st.update_layout(
                        height=max(300, len(_static_data) * 30 + 60),
                        plot_bgcolor="white", paper_bgcolor="white",
                        margin=dict(l=0, r=80, t=10, b=0),
                        font=dict(family="Arial", color=NAVY, size=10),
                        xaxis=dict(gridcolor=BORDER),
                    )
                    st.plotly_chart(_fig_st, use_container_width=True)

            elif _t1_sel in _DUMBBELL_METRICS and _t1_src == "fs":
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f'<div class="section-header">{_t1_sel} — Entry vs. Current</div>',
                            unsafe_allow_html=True)
                # Map to entry equivalent column
                _entry_col_map = {
                    "Current TEV / EBITDA":    "entry_tev_to_ebitda",
                    "Entry TEV / EBITDA":      "entry_tev_to_ebitda",
                    "Current TEV / Net Sales": "entry_tev_to_revenue",
                    "Entry TEV / Net Sales":   "entry_tev_to_revenue",
                }
                _curr_col_map = {
                    "Current TEV / EBITDA":    "tev_to_ebitda",
                    "Entry TEV / EBITDA":      "tev_to_ebitda",
                    "Current TEV / Net Sales": "tev_to_revenue",
                    "Entry TEV / Net Sales":   "tev_to_revenue",
                }
                _ec = _entry_col_map.get(_t1_sel)
                _cc = _curr_col_map.get(_t1_sel)
                if _ec and _cc:
                    _db_rows = []
                    for cname in _t1_companies:
                        fsub = fs_filtered[fs_filtered["company_name"] == cname]
                        if fsub.empty: continue
                        ev = fsub.iloc[0].get(_ec)
                        cv = fsub.iloc[0].get(_cc)
                        if pd.notna(ev) and pd.notna(cv):
                            _db_rows.append({"company": cname, "entry": float(ev), "current": float(cv)})
                    if _db_rows:
                        _dbdf = pd.DataFrame(_db_rows).sort_values("current")
                        _fig_db = go.Figure()
                        for _, r in _dbdf.iterrows():
                            _fig_db.add_trace(go.Scatter(
                                x=[r["entry"], r["current"]], y=[r["company"], r["company"]],
                                mode="lines", line=dict(color=BORDER, width=3),
                                showlegend=False,
                            ))
                        _fig_db.add_trace(go.Scatter(
                            x=_dbdf["entry"], y=_dbdf["company"],
                            mode="markers", name="Entry",
                            marker=dict(color=SLATE, size=12, symbol="circle"),
                        ))
                        _fig_db.add_trace(go.Scatter(
                            x=_dbdf["current"], y=_dbdf["company"],
                            mode="markers", name="Current",
                            marker=dict(color=NAVY, size=12, symbol="circle"),
                        ))
                        _fig_db.update_layout(
                            height=max(300, len(_db_rows) * 35 + 80),
                            plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(l=0, r=0, t=10, b=0),
                            font=dict(family="Arial", color=NAVY, size=10),
                            xaxis=dict(tickformat=",.1f", ticksuffix="x", gridcolor=BORDER),
                            legend=dict(orientation="h", y=-0.15),
                        )
                        st.plotly_chart(_fig_db, use_container_width=True)

            elif _t1_sel in _HORIZ_BAR_METRICS and _t1_src == "fs":
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(f'<div class="section-header">{_t1_sel} — Ranked</div>',
                            unsafe_allow_html=True)
                _hr_data = []
                for cname in _t1_companies:
                    fsub = fs_filtered[fs_filtered["company_name"] == cname]
                    if fsub.empty or _t1_col not in fsub.columns: continue
                    v = fsub.iloc[0][_t1_col]
                    if pd.notna(v):
                        _hr_data.append({"company": cname, "value": float(v)})
                if _hr_data:
                    _hrdf = pd.DataFrame(_hr_data).sort_values("value")
                    _fig_hr = go.Figure(go.Bar(
                        x=_hrdf["value"], y=_hrdf["company"], orientation="h",
                        marker_color=[SEA_GREEN if v >= 2.0 else XANTHOUS if v >= 1.0 else RED_FLAG
                                      for v in _hrdf["value"]],
                        text=_hrdf["value"].apply(_t1_fmt), textposition="outside",
                    ))
                    _fig_hr.update_layout(
                        height=max(300, len(_hr_data) * 30 + 60),
                        plot_bgcolor="white", paper_bgcolor="white",
                        margin=dict(l=0, r=80, t=10, b=0),
                        font=dict(family="Arial", color=NAVY, size=10),
                        xaxis=dict(gridcolor=BORDER),
                    )
                    st.plotly_chart(_fig_hr, use_container_width=True)

            elif _t1_src in ("fs", "flags"):
                st.info("This metric is a point-in-time value — period trend chart not available.")
            else:
                st.info(f"Chart not available for {_t1_sel}.")

        else:
            st.info("No data available for the selected metric and filter.")


    # ---- TAB 2: By Company Trends — classic metrics × companies snapshot ----
    with po_tab2:

        # ----------------------------------------------------------------
        # METRIC DEFINITIONS shared with tab 1 additional charts
        # ----------------------------------------------------------------
        ALL_METRIC_DEFS = [
            ("Entry TEV",               "entry_tev",               "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry Net Sales",         "entry_revenue",            "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry EBITDA",            "entry_adj_ebitda",         "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry Net Debt",          "entry_net_debt",           "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry TEV / Net Sales",   "entry_tev_to_revenue",     "fs",    format_multiple, False, "LTM at Entry — Ratios"),
            ("Entry TEV / EBITDA",      "entry_tev_to_ebitda",      "fs",    format_multiple, False, "LTM at Entry — Ratios"),
            ("Entry Net Debt / EBITDA", "entry_net_leverage",       "fs",    format_multiple, False, "LTM at Entry — Ratios"),
            ("Current TEV",             "current_tev",              "fs",    format_millions, False, "LTM Current — $USD"),
            ("LTM Net Sales",           "ltm_revenue",              "q",     format_millions, False, "LTM Current — $USD"),
            ("LTM EBITDA",              "ltm_adj_ebitda",           "q",     format_millions, False, "LTM Current — $USD"),
            ("Current Net Debt",        "net_debt",                 "q",     format_millions, False, "LTM Current — $USD"),
            ("Current TEV / Net Sales", "tev_to_revenue",           "fs",    format_multiple, False, "LTM Current — Ratios"),
            ("Current TEV / EBITDA",    "tev_to_ebitda",            "fs",    format_multiple, False, "LTM Current — Ratios"),
            ("Current Net Debt / EBITDA","net_leverage",            "q",     format_multiple, False, "LTM Current — Ratios"),
            ("Total Cost",              "entry_tev",                "fs",    format_millions, False, "Valuation"),
            ("Gross MOI",               "gross_moi",                "fs",    format_multiple, False, "Valuation"),
            ("Gross IRR",               "gross_irr",                "fs",    format_pct,      True,  "Valuation"),
            ("Floating Rate Debt",      "floating_rate_debt",       "q",     format_millions, False, "Credit Agreement"),
            ("Fixed Rate Debt",         "fixed_rate_debt",          "q",     format_millions, False, "Credit Agreement"),
            ("PIK Debt",                "pik_debt",                 "q",     format_millions, False, "Credit Agreement"),
            ("Total Gross Debt",        "total_gross_debt",         "q",     format_millions, False, "Credit Agreement"),
            ("Cash",                    "cash",                     "q",     format_millions, False, "Credit Agreement"),
            ("Net Debt",                "net_debt",                 "q",     format_millions, False, "Credit Agreement"),
            ("LTM Credit Agmt. EBITDA", "credit_agreement_ebitda",  "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Adj. EBITDA",         "adj_ebitda",               "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Cash Interest (Gross)","cash_interest_expense",   "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Capex (Excl. M&A)",   "capex",                    "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Δ NWC",               "change_in_nwc",            "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Cash Taxes",          "cash_taxes",               "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Mandatory Pmts",      "mandatory_principal",      "q",     format_millions, False, "Debt Ratio Inputs"),
            ("Total Net Leverage",      "net_leverage",             "q",     format_multiple, False, "Debt Ratios"),
            ("Total Gross Leverage",    "gross_leverage",           "q",     format_multiple, False, "Debt Ratios"),
            ("Sr. Secured Leverage",    "senior_secured_leverage",  "q",     format_multiple, False, "Debt Ratios"),
            ("Interest Coverage",       "interest_coverage",        "q",     format_multiple, False, "Debt Ratios"),
            ("Debt Service Coverage",   "debt_service_coverage",    "q",     format_multiple, False, "Debt Ratios"),
            ("LTM Free Cash Flow",      "free_cash_flow",           "q",     format_millions, False, "Debt Ratios"),
            ("LTM Revenue",             "ltm_revenue",              "q",     format_millions, False, "Operating"),
            ("Rev Growth (YoY)",        "revenue_yoy",              "flags", format_pct,      True,  "Operating"),
            ("EBITDA Margin",           "adj_ebitda_margin_pct",    "q",     format_pct,      True,  "Operating"),
            ("Gross Profit",            "gross_profit",             "q",     format_millions, False, "Operating"),
            ("Gross Margin %",          "gross_margin_pct",         "q",     format_pct,      True,  "Operating"),
        ]

        metric_labels   = [d[0] for d in ALL_METRIC_DEFS]
        metric_lookup   = {d[0]: d for d in ALL_METRIC_DEFS}
        categories      = list(dict.fromkeys(d[5] for d in ALL_METRIC_DEFS))

        period_mode = tab_period

        # Build period-labeled quarterly data
        def _period_label(df, mode):
            df = df.copy()
            df["cash_flow_date"] = pd.to_datetime(df["cash_flow_date"], errors="coerce")
            # Filter to correct period type using the period column
            if "period" in df.columns:
                pf = {"Quarterly": "Quarterly", "Yearly": "Annual", "Monthly": "Monthly"}.get(mode, "Quarterly")
                df = df[df["period"] == pf]
            # Assign display label
            if mode == "Monthly":
                df["_plabel"] = df["cash_flow_date"].dt.strftime("%b %Y")
            elif mode == "Yearly":
                df["_plabel"] = df["cash_flow_date"].dt.strftime("%Y-%m")
            else:
                df["_plabel"] = (df["period_label"] if "period_label" in df.columns
                                 else df["cash_flow_date"].dt.to_period("Q").astype(str))
            return df

        q_prep = _period_label(q_filt, period_mode) if not q_filt.empty else pd.DataFrame()

        if not q_prep.empty:
            all_periods = (q_prep.sort_values("cash_flow_date")["_plabel"]
                           .drop_duplicates().tolist())
        else:
            all_periods = []

        companies_ord = sorted(fs_filtered["company_name"].unique().tolist())

        # ----------------------------------------------------------------
        # PERIOD SELECTBOX — pick which period snapshot to show
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">Investment Summary — KPI View</div>',
                    unsafe_allow_html=True)
        st.caption("Select a period to see a snapshot of all KPIs across every company for that period.")

        sel_col_left, sel_col_right = st.columns([2, 5])
        with sel_col_left:
            if all_periods:
                selected_period = st.selectbox(
                    "Period",
                    options=list(reversed(all_periods)),   # most recent first
                    key="t2_period_select",
                    label_visibility="collapsed"
                )
            else:
                selected_period = None
                st.info("No period data available.")

        # Helper: get value for one company for the selected period
        def _get_snap_val(cname, metric_def):
            lbl, col, src, fmt, is_pct, cat = metric_def
            if src == "q":
                if q_prep.empty or selected_period is None: return None
                sub = q_prep[(q_prep["company_name"] == cname) &
                             (q_prep["_plabel"] == selected_period)]
                if sub.empty: return None
                sub = sub.sort_values("cash_flow_date")
                for try_col in [f"ltm_{col}", col]:
                    if try_col in sub.columns:
                        v = sub.iloc[-1][try_col]
                        if not pd.isna(v): return v
                return None
            elif src == "fs":
                sub = fs_filtered[fs_filtered["company_name"] == cname]
                if sub.empty or col not in sub.columns: return None
                v = sub.iloc[0][col]
                return None if pd.isna(v) else v
            elif src == "flags":
                sub = flags_filtered[flags_filtered["company_name"] == cname]
                if sub.empty or col not in sub.columns: return None
                v = sub.iloc[0][col]
                return None if pd.isna(v) else v
            return None

        # Helper: get flag colour for a value given its flag column
        FLAG_COL_MAP = {
            "revenue_yoy":           "revenue_growth_flag",
            "adj_ebitda_margin_pct": "ebitda_margin_flag",
            "net_leverage":          "net_leverage_flag",
            "interest_coverage":     "interest_coverage_flag",
        }

        def _get_flag_color(cname, q_col):
            flag_col = FLAG_COL_MAP.get(q_col)
            if not flag_col: return None
            sub = flags_filtered[flags_filtered["company_name"] == cname]
            if sub.empty or flag_col not in sub.columns: return None
            return sub.iloc[0][flag_col]

        # ----------------------------------------------------------------
        # SNAPSHOT TABLE: metrics as rows, companies as columns
        # ----------------------------------------------------------------
        if companies_ord:
            snap_rows = []
            for lbl, col, src, fmt, is_pct, cat in ALL_METRIC_DEFS:
                row = {"KPI": lbl}
                for cname in companies_ord:
                    val = _get_snap_val(cname, (lbl, col, src, fmt, is_pct, cat))
                    row[cname] = fmt(val) if val is not None and not pd.isna(val) else "—"
                    row[f"__flag_{cname}"] = _get_flag_color(cname, col)
                snap_rows.append(row)

            snap_df = pd.DataFrame(snap_rows)
            flag_cols_hidden = [c for c in snap_df.columns if c.startswith("__flag_")]
            disp_df = snap_df.drop(columns=flag_cols_hidden).set_index("KPI")

            def _style_snap(row):
                out = []
                for cname in row.index:
                    fval = snap_df.loc[snap_df["KPI"] == row.name,
                                       f"__flag_{cname}"].values[0] \
                           if f"__flag_{cname}" in snap_df.columns else None
                    clr = ""
                    if fval == "Red":    clr = f"color:{RED_FLAG};font-weight:600"
                    elif fval == "Yellow": clr = "color:#B7860B;font-weight:600"
                    elif fval == "Green":  clr = f"color:{SEA_GREEN};font-weight:600"
                    out.append(clr)
                return out

            try:
                styled_snap = disp_df.style.apply(_style_snap, axis=1)
            except Exception:
                styled_snap = disp_df.style

            st.dataframe(styled_snap, use_container_width=True,
                         height=min(700, len(snap_rows) * 35 + 50))
            st.caption(f"Showing period: **{selected_period}** · "
                       f"Flag colours apply to Revenue Growth, EBITDA Margin, Net Leverage, Interest Coverage")

        # ----------------------------------------------------------------
        # Period-over-period chart driven by metric selectbox
        # ----------------------------------------------------------------
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Period-over-Period Chart</div>',
                    unsafe_allow_html=True)

        active_metric = st.selectbox(
            "Select metric for chart",
            sorted(metric_labels),
            key="t2_chart_metric_select",
            label_visibility="visible"
        )

        mdef = metric_lookup[active_metric]
        _, m_col, m_src, m_fmt, m_is_pct, _ = mdef

        display_periods = all_periods[-12:] if len(all_periods) > 12 else all_periods

        def _get_val(cname, period, metric_def):
            lbl, col, src, fmt, is_pct, cat = metric_def
            if src == "q":
                if q_prep.empty: return None
                sub = q_prep[(q_prep["company_name"] == cname) & (q_prep["_plabel"] == period)]
                if sub.empty: return None
                sub = sub.sort_values("cash_flow_date")
                for try_col in [f"ltm_{col}", col]:
                    if try_col in sub.columns:
                        v = sub.iloc[-1][try_col]
                        if not pd.isna(v): return v
                return None
            elif src == "fs":
                sub = fs_filtered[fs_filtered["company_name"] == cname]
                if sub.empty or col not in sub.columns: return None
                v = sub.iloc[0][col]
                return None if pd.isna(v) else v
            elif src == "flags":
                sub = flags_filtered[flags_filtered["company_name"] == cname]
                if sub.empty or col not in sub.columns: return None
                v = sub.iloc[0][col]
                return None if pd.isna(v) else v

        # Resolve actual column to use for chart (prefer ltm_ prefixed)
        _m_actual_col = f"ltm_{m_col}" if (not q_prep.empty and f"ltm_{m_col}" in q_prep.columns) else m_col

        if m_src == "q" and not q_prep.empty and _m_actual_col in q_prep.columns:
            kpi_ts = q_prep[["company_name", "_plabel", "cash_flow_date", _m_actual_col]].dropna(subset=[_m_actual_col]).copy()
            kpi_ts = kpi_ts.sort_values("cash_flow_date")
            kpi_ts["_prev"] = kpi_ts.groupby("company_name")[_m_actual_col].shift(1)
            kpi_ts["_chg"]  = kpi_ts[_m_actual_col] - kpi_ts["_prev"]
            kpi_ts = kpi_ts.dropna(subset=["_chg"])
            if display_periods:
                kpi_ts = kpi_ts[kpi_ts["_plabel"].isin(display_periods)]

            if not kpi_ts.empty:
                fig_pop = go.Figure()
                for j, cname in enumerate(companies_ord):
                    co_ts = kpi_ts[kpi_ts["company_name"] == cname]
                    if co_ts.empty: continue
                    fig_pop.add_trace(go.Bar(
                        x=co_ts["_plabel"], y=co_ts["_chg"],
                        name=cname,
                        marker_color=COMPANY_COLORS[j % len(COMPANY_COLORS)],
                    ))
                fig_pop.update_layout(
                    height=360, barmode="group",
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    legend=dict(font=dict(size=9), orientation="h", y=-0.25),
                    xaxis=dict(tickangle=-45, gridcolor=BORDER),
                    yaxis=dict(tickformat=".0%" if m_is_pct else "$,.0f",
                               gridcolor=BORDER, title=f"Δ {active_metric}"),
                )
                st.plotly_chart(fig_pop, use_container_width=True)
                st.caption(f"Period-over-period change in {active_metric}.")
            else:
                st.info("Not enough periods to compute period-over-period change.")
        elif m_src in ("fs", "flags"):
            # Static snapshot — bar chart
            fs_vals = [{"Company": c, "Value": _get_val(c, None, mdef)}
                       for c in companies_ord]
            fs_vals = [r for r in fs_vals if r["Value"] is not None]
            if fs_vals:
                fv_df = pd.DataFrame(fs_vals).sort_values("Value")
                fig_fs = go.Figure(go.Bar(
                    x=fv_df["Value"], y=fv_df["Company"], orientation="h",
                    marker_color=NAVY,
                    text=fv_df["Value"].apply(m_fmt), textposition="outside"
                ))
                tick_fmt = ".2f" if "MOI" in active_metric or "Leverage" in active_metric else "$,.0f"
                fig_fs.update_layout(
                    height=max(280, len(fv_df) * 28),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=80, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat=tick_fmt, gridcolor=BORDER),
                )
                st.plotly_chart(fig_fs, use_container_width=True)
                st.caption(f"{active_metric} — latest snapshot (static, no time series).")
            # --- LTM at Entry — Fund Currency ($USD) ---
            ("Entry TEV",               "entry_tev",               "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry Net Sales",         "entry_revenue",            "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry EBITDA",            "entry_adj_ebitda",         "fs",    format_millions, False, "LTM at Entry — $USD"),
            ("Entry Net Debt",          "entry_net_debt",           "fs",    format_millions, False, "LTM at Entry — $USD"),
            # --- LTM at Entry — Ratios ---
            ("Entry TEV / Net Sales",   "entry_tev_to_revenue",     "fs",    format_multiple, False, "LTM at Entry — Ratios"),
            ("Entry TEV / EBITDA",      "entry_tev_to_ebitda",      "fs",    format_multiple, False, "LTM at Entry — Ratios"),
            ("Entry Net Debt / EBITDA", "entry_net_leverage",       "fs",    format_multiple, False, "LTM at Entry — Ratios"),
            # --- Exit / LTM Current — Fund Currency ($USD) ---
            ("Current TEV",             "current_tev",              "fs",    format_millions, False, "LTM Current — $USD"),
            ("LTM Net Sales",           "ltm_revenue",              "q",     format_millions, False, "LTM Current — $USD"),
            ("LTM EBITDA",              "ltm_adj_ebitda",           "q",     format_millions, False, "LTM Current — $USD"),
            ("Current Net Debt",        "net_debt",                 "q",     format_millions, False, "LTM Current — $USD"),
            # --- Exit / LTM Current — Ratios ---
            ("Current TEV / Net Sales", "tev_to_revenue",           "fs",    format_multiple, False, "LTM Current — Ratios"),
            ("Current TEV / EBITDA",    "tev_to_ebitda",            "fs",    format_multiple, False, "LTM Current — Ratios"),
            ("Current Net Debt / EBITDA","net_leverage",            "q",     format_multiple, False, "LTM Current — Ratios"),
            # --- Valuation ---
            ("Total Cost",              "entry_tev",                "fs",    format_millions, False, "Valuation"),
            ("Gross MOI",               "gross_moi",                "fs",    format_multiple, False, "Valuation"),
            ("Gross IRR",               "gross_irr",                "fs",    format_pct,      True,  "Valuation"),
            # --- Credit Agreement — Total Outstanding Debt ---
            ("Floating Rate Debt",      "floating_rate_debt",       "q",     format_millions, False, "Credit Agreement"),
            ("Fixed Rate Debt",         "fixed_rate_debt",          "q",     format_millions, False, "Credit Agreement"),
            ("PIK Debt",                "pik_debt",                 "q",     format_millions, False, "Credit Agreement"),
            ("Total Gross Debt",        "total_gross_debt",         "q",     format_millions, False, "Credit Agreement"),
            ("Cash",                    "cash",                     "q",     format_millions, False, "Credit Agreement"),
            ("Net Debt",                "net_debt",                 "q",     format_millions, False, "Credit Agreement"),
            # --- Relevant Info for Debt Ratios ---
            ("LTM Credit Agmt. EBITDA", "credit_agreement_ebitda",  "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Adj. EBITDA",         "adj_ebitda",               "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Cash Interest (Gross)","cash_interest_expense",    "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Capex (Excl. M&A)",   "capex",                    "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Δ NWC",               "change_in_nwc",            "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Cash Taxes",          "cash_taxes",               "q",     format_millions, False, "Debt Ratio Inputs"),
            ("LTM Mandatory Pmts",      "mandatory_principal",      "q",     format_millions, False, "Debt Ratio Inputs"),
            # --- Debt Ratios & Metrics ---
            ("Total Net Leverage",      "net_leverage",             "q",     format_multiple, False, "Debt Ratios"),
            ("Total Gross Leverage",    "gross_leverage",           "q",     format_multiple, False, "Debt Ratios"),
            ("Sr. Secured Leverage",    "senior_secured_leverage",  "q",     format_multiple, False, "Debt Ratios"),
            ("Interest Coverage",       "interest_coverage",        "q",     format_multiple, False, "Debt Ratios"),
            ("Debt Service Coverage",   "debt_service_coverage",    "q",     format_multiple, False, "Debt Ratios"),
            ("LTM Free Cash Flow",      "free_cash_flow",           "q",     format_millions, False, "Debt Ratios"),
            # --- Core Operating KPIs (always useful) ---
            ("LTM Revenue",             "ltm_revenue",              "q",     format_millions, False, "Operating"),
            ("Rev Growth (YoY)",        "revenue_yoy",              "flags", format_pct,      True,  "Operating"),
            ("EBITDA Margin",           "adj_ebitda_margin_pct",    "q",     format_pct,      True,  "Operating"),
            ("Gross Profit",            "gross_profit",             "q",     format_millions, False, "Operating"),
            ("Gross Margin %",          "gross_margin_pct",         "q",     format_pct,      True,  "Operating"),
        # ================================================================
        # ADDITIONAL CHARTS — Tab 2
        # ================================================================
        st.markdown("<hr style='border:1px solid #E0E4EA;margin:28px 0 20px 0;'>",
                    unsafe_allow_html=True)

        # Helper: get latest quarterly value per company for a given column
        def _latest_q(col):
            if q_prep.empty or col not in q_prep.columns:
                return pd.DataFrame()
            return (q_prep.sort_values("cash_flow_date")
                          .groupby("company_name")[[col, "cash_flow_date", "_plabel"]]
                          .last()
                          .reset_index()
                          .dropna(subset=[col]))

        # Helper: get time-series for a column, one row per company × period
        def _ts_q(col):
            if q_prep.empty or col not in q_prep.columns:
                return pd.DataFrame()
            return (q_prep[["company_name", "_plabel", "cash_flow_date", col]]
                    .dropna(subset=[col])
                    .sort_values("cash_flow_date")
                    .copy())

        CHART_H      = 380
        CHART_H_TALL = max(300, len(companies_ord) * 28 + 60)

        # ----------------------------------------------------------------
        # 1. Revenue & EBITDA by Company (grouped bar, latest period)
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">Revenue & EBITDA by Company — Latest Period</div>',
                    unsafe_allow_html=True)

        rev_df  = _latest_q("revenue")
        ebit_df = _latest_q("adj_ebitda")

        if not rev_df.empty or not ebit_df.empty:
            from plotly.subplots import make_subplots as _msp
            all_co = sorted(set(
                rev_df["company_name"].tolist() + ebit_df["company_name"].tolist()
            ))
            fig_re = go.Figure()
            rev_vals  = [rev_df.set_index("company_name")["revenue"].get(c, None) for c in all_co]
            ebit_vals = [ebit_df.set_index("company_name")["adj_ebitda"].get(c, None) for c in all_co]

            fig_re.add_trace(go.Bar(
                name="LTM Revenue", x=all_co, y=rev_vals,
                marker_color=NAVY, opacity=0.85,
                text=[format_millions(v) for v in rev_vals],
                textposition="outside", textfont=dict(size=8)
            ))
            fig_re.add_trace(go.Bar(
                name="LTM Adj. EBITDA", x=all_co, y=ebit_vals,
                marker_color=SKY, opacity=0.9,
                text=[format_millions(v) for v in ebit_vals],
                textposition="outside", textfont=dict(size=8)
            ))
            fig_re.update_layout(
                height=CHART_H, barmode="group",
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                legend=dict(orientation="h", y=-0.18, font=dict(size=10)),
                yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
                xaxis=dict(tickangle=-30),
            )
            st.plotly_chart(fig_re, use_container_width=True)
        else:
            st.info("Revenue / EBITDA data not available.")

        # ----------------------------------------------------------------
        # 2. Total Revenue vs. Budgeted Revenue by Company
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">Total Revenue vs. Budgeted Revenue by Company</div>',
                    unsafe_allow_html=True)

        # Check for budget column in quarterly data
        budget_col = next(
            (c for c in ([] if q_prep.empty else q_prep.columns)
             if "budget" in c.lower() or "budgeted" in c.lower()),
            None
        )
        if budget_col and not q_prep.empty:
            bud_rev = _latest_q("revenue").merge(
                _latest_q(budget_col), on="company_name", suffixes=("_act", "_bud")
            )
            if not bud_rev.empty:
                bud_co = bud_rev["company_name"].tolist()
                fig_bud = go.Figure()
                fig_bud.add_trace(go.Bar(
                    name="Actual Revenue", x=bud_co,
                    y=bud_rev["revenue"].tolist(), marker_color=NAVY
                ))
                fig_bud.add_trace(go.Bar(
                    name="Budgeted Revenue", x=bud_co,
                    y=bud_rev[budget_col].tolist(), marker_color=XANTHOUS,
                    opacity=0.7
                ))
                fig_bud.update_layout(
                    height=CHART_H, barmode="group",
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=20, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    legend=dict(orientation="h", y=-0.18),
                    yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
                    xaxis=dict(tickangle=-30),
                )
                st.plotly_chart(fig_bud, use_container_width=True)
            else:
                st.info("No companies have both actual and budget revenue data.")
        else:
            st.markdown(f"""
            <div style="background:#F8F9FA;border:1px dashed #CCCCCC;border-radius:6px;
                        padding:24px;text-align:center;">
                <div style="font-size:13px;font-weight:700;color:#999;font-family:Arial;">
                    Budgeted Revenue data not yet available
                </div>
                <div style="font-size:11px;color:#BBBBBB;font-family:Arial;margin-top:6px;">
                    Add a <code>budgeted_revenue</code> column to financials_quarterly.csv
                    to enable this chart
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ----------------------------------------------------------------
        # 3. EBITDA Contribution by Company as % of Total
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">EBITDA Contribution by Company — % of Portfolio Total</div>',
                    unsafe_allow_html=True)

        ebit_latest = _latest_q("adj_ebitda")
        if not ebit_latest.empty:
            total_ebitda_port = ebit_latest["adj_ebitda"].sum()
            ebit_latest = ebit_latest.copy()
            ebit_latest["pct"] = ebit_latest["adj_ebitda"] / total_ebitda_port
            ebit_latest = ebit_latest.sort_values("pct", ascending=True)

            colors_contrib = [
                SEA_GREEN if v >= 0 else RED_FLAG
                for v in ebit_latest["adj_ebitda"]
            ]
            fig_contrib = go.Figure(go.Bar(
                x=ebit_latest["pct"],
                y=ebit_latest["company_name"],
                orientation="h",
                marker_color=colors_contrib,
                text=[f"{v*100:.1f}%" for v in ebit_latest["pct"]],
                textposition="outside",
                customdata=ebit_latest["adj_ebitda"].tolist(),
                hovertemplate="<b>%{y}</b><br>EBITDA: $%{customdata:.1f}M<br>Share: %{text}<extra></extra>",
            ))
            fig_contrib.update_layout(
                height=CHART_H_TALL,
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=80, t=20, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                xaxis=dict(tickformat=".0%", gridcolor=BORDER,
                           title="% of Portfolio EBITDA"),
            )
            st.plotly_chart(fig_contrib, use_container_width=True)
            st.caption(f"Portfolio total LTM Adj. EBITDA: {format_millions(total_ebitda_port)}")
        else:
            st.info("EBITDA data not available.")

        # ----------------------------------------------------------------
        # 4. Gross IRR by Company
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">Gross IRR by Company</div>',
                    unsafe_allow_html=True)

        if not fs_filtered.empty and "gross_irr" in fs_filtered.columns:
            irr_df = (fs_filtered[["company_name", "gross_irr"]]
                      .dropna(subset=["gross_irr"])
                      .sort_values("gross_irr", ascending=True))
            if not irr_df.empty:
                irr_colors = [
                    SEA_GREEN if v > 0.20 else XANTHOUS if v > 0.10 else RED_FLAG
                    for v in irr_df["gross_irr"]
                ]
                fig_irr = go.Figure(go.Bar(
                    x=irr_df["gross_irr"],
                    y=irr_df["company_name"],
                    orientation="h",
                    marker_color=irr_colors,
                    text=[format_pct(v) for v in irr_df["gross_irr"]],
                    textposition="outside",
                ))
                fig_irr.add_vline(x=0.20, line_dash="dot", line_color=SEA_GREEN,
                                   annotation_text="20% target")
                fig_irr.update_layout(
                    height=CHART_H_TALL,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=80, t=20, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat=".0%", gridcolor=BORDER),
                )
                st.plotly_chart(fig_irr, use_container_width=True)
            else:
                st.info("No Gross IRR data available.")
        else:
            st.info("Gross IRR not available — add gross_irr to fund_summary.csv.")

        # ----------------------------------------------------------------
        # 5. Interest Coverage Ratio by Company — trend over time
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">Interest Coverage Ratio by Company</div>',
                    unsafe_allow_html=True)

        ic_ts = _ts_q("interest_coverage")
        if not ic_ts.empty:
            col_line, col_bar = st.columns([3, 2])

            with col_line:
                # Line chart — trend per company over periods
                fig_ic_line = go.Figure()
                for j, cname in enumerate(companies_ord):
                    co = ic_ts[ic_ts["company_name"] == cname]
                    if co.empty:
                        continue
                    fig_ic_line.add_trace(go.Scatter(
                        x=co["_plabel"], y=co["interest_coverage"],
                        name=cname, mode="lines+markers",
                        line=dict(color=COMPANY_COLORS[j % len(COMPANY_COLORS)], width=1.5),
                        marker=dict(size=4),
                    ))
                fig_ic_line.add_hline(y=3.0, line_dash="dash", line_color=SEA_GREEN,
                                       annotation_text="3.0x Green")
                fig_ic_line.add_hline(y=2.0, line_dash="dot", line_color=XANTHOUS,
                                       annotation_text="2.0x Watch")
                fig_ic_line.add_hline(y=0, line_color=RED_FLAG, line_width=0.5)
                fig_ic_line.update_layout(
                    height=CHART_H,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    legend=dict(font=dict(size=8), orientation="h", y=-0.28),
                    xaxis=dict(tickangle=-45),
                    yaxis=dict(tickformat=".1f", ticksuffix="x", gridcolor=BORDER,
                               title="Interest Coverage"),
                )
                st.plotly_chart(fig_ic_line, use_container_width=True)

            with col_bar:
                # Latest snapshot horizontal bar
                ic_latest = (_ts_q("interest_coverage")
                             .sort_values("cash_flow_date")
                             .groupby("company_name")["interest_coverage"]
                             .last().reset_index()
                             .sort_values("interest_coverage", ascending=True))
                ic_colors = [
                    SEA_GREEN if v > 3 else XANTHOUS if v > 2 else RED_FLAG
                    for v in ic_latest["interest_coverage"]
                ]
                fig_ic_bar = go.Figure(go.Bar(
                    x=ic_latest["interest_coverage"],
                    y=ic_latest["company_name"],
                    orientation="h",
                    marker_color=ic_colors,
                    text=[f"{v:.1f}x" for v in ic_latest["interest_coverage"]],
                    textposition="outside",
                ))
                fig_ic_bar.add_vline(x=3.0, line_dash="dash", line_color=SEA_GREEN)
                fig_ic_bar.add_vline(x=2.0, line_dash="dot",  line_color=XANTHOUS)
                fig_ic_bar.update_layout(
                    height=CHART_H_TALL,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=80, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat=".1f", ticksuffix="x", gridcolor=BORDER,
                               title="Latest"),
                )
                st.plotly_chart(fig_ic_bar, use_container_width=True)
        else:
            st.info("Interest Coverage data not available in quarterly data.")

        # ----------------------------------------------------------------
        # 6. Net Debt by Company — trend + latest snapshot
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">Net Debt by Company</div>',
                    unsafe_allow_html=True)

        nd_ts = _ts_q("net_debt")
        if not nd_ts.empty:
            col_nd1, col_nd2 = st.columns([3, 2])

            with col_nd1:
                fig_nd_line = go.Figure()
                for j, cname in enumerate(companies_ord):
                    co = nd_ts[nd_ts["company_name"] == cname]
                    if co.empty:
                        continue
                    fig_nd_line.add_trace(go.Scatter(
                        x=co["_plabel"], y=co["net_debt"],
                        name=cname, mode="lines+markers",
                        line=dict(color=COMPANY_COLORS[j % len(COMPANY_COLORS)], width=1.5),
                        marker=dict(size=4),
                    ))
                fig_nd_line.update_layout(
                    height=CHART_H,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    legend=dict(font=dict(size=8), orientation="h", y=-0.28),
                    xaxis=dict(tickangle=-45),
                    yaxis=dict(tickformat="$,.0f", gridcolor=BORDER, title="Net Debt ($M)"),
                )
                st.plotly_chart(fig_nd_line, use_container_width=True)

            with col_nd2:
                nd_latest = (nd_ts.sort_values("cash_flow_date")
                                  .groupby("company_name")["net_debt"]
                                  .last().reset_index()
                                  .sort_values("net_debt", ascending=False))
                nd_colors = [
                    RED_FLAG if v > 0 else SEA_GREEN for v in nd_latest["net_debt"]
                ]
                fig_nd_bar = go.Figure(go.Bar(
                    x=nd_latest["net_debt"],
                    y=nd_latest["company_name"],
                    orientation="h",
                    marker_color=nd_colors,
                    text=[format_millions(v) for v in nd_latest["net_debt"]],
                    textposition="outside",
                ))
                fig_nd_bar.update_layout(
                    height=CHART_H_TALL,
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=80, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat="$,.0f", gridcolor=BORDER, title="Latest ($M)"),
                )
                st.plotly_chart(fig_nd_bar, use_container_width=True)
        else:
            # Fall back to fund summary if net_debt in quarterly isn't available
            if not fs_filtered.empty and "net_debt" in fs_filtered.columns:
                nd_fs = (fs_filtered[["company_name", "net_debt"]]
                         .dropna(subset=["net_debt"])
                         .sort_values("net_debt", ascending=False))
                fig_nd_fs = go.Figure(go.Bar(
                    x=nd_fs["net_debt"], y=nd_fs["company_name"],
                    orientation="h",
                    marker_color=[RED_FLAG if v > 0 else SEA_GREEN for v in nd_fs["net_debt"]],
                    text=[format_millions(v) for v in nd_fs["net_debt"]],
                    textposition="outside",
                ))
                fig_nd_fs.update_layout(
                    height=CHART_H_TALL, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=80, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
                )
                st.plotly_chart(fig_nd_fs, use_container_width=True)
            else:
                st.info("Net Debt data not available.")

        # ----------------------------------------------------------------
        # 7. EBITDA Growth vs. Multiple Expansion / Compression
        #    Scatter: x = EBITDA growth (entry → current), y = TEV/EBITDA change
        #    Bubble size = current TEV
        # ----------------------------------------------------------------
        st.markdown('<div class="section-header">EBITDA Growth vs. Multiple Expansion / Compression</div>',
                    unsafe_allow_html=True)
        st.caption("x-axis: EBITDA growth since entry  ·  y-axis: TEV/EBITDA multiple change (positive = expansion)  ·  bubble size = current TEV")

        scatter_cols_needed = {
            "entry_adj_ebitda", "entry_tev_to_ebitda",
            "current_tev", "tev_to_ebitda", "overall_flag"
        }
        ebitda_latest = _latest_q("adj_ebitda")
        has_scatter = (
            not fs_filtered.empty
            and scatter_cols_needed.issubset(set(fs_filtered.columns))
            and not ebitda_latest.empty
        )

        if has_scatter:
            sc_df = fs_filtered[list(scatter_cols_needed | {"company_name"})].copy()
            sc_df = sc_df.merge(
                ebitda_latest[["company_name", "adj_ebitda"]],
                on="company_name", how="left"
            )
            sc_df = sc_df.dropna(
                subset=["entry_adj_ebitda", "entry_tev_to_ebitda",
                        "tev_to_ebitda", "current_tev"]
            )
            # EBITDA growth = (current - entry) / |entry|
            sc_df["ebitda_growth"] = (
                (sc_df["adj_ebitda"] - sc_df["entry_adj_ebitda"])
                / sc_df["entry_adj_ebitda"].abs()
            )
            # Multiple change = current TEV/EBITDA − entry TEV/EBITDA
            sc_df["multiple_chg"] = sc_df["tev_to_ebitda"] - sc_df["entry_tev_to_ebitda"]

            color_map = {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}
            fig_scat = go.Figure()

            for flag_val, grp in sc_df.groupby("overall_flag"):
                fig_scat.add_trace(go.Scatter(
                    x=grp["ebitda_growth"],
                    y=grp["multiple_chg"],
                    mode="markers+text",
                    name=flag_val,
                    text=grp["company_name"],
                    textposition="top center",
                    textfont=dict(size=8),
                    marker=dict(
                        size=grp["current_tev"].fillna(1000).apply(
                            lambda v: max(8, min(50, v / 500))
                        ),
                        color=color_map.get(flag_val, SLATE),
                        opacity=0.75,
                        line=dict(width=1, color="white"),
                    ),
                ))

            # Quadrant lines
            fig_scat.add_hline(y=0, line_color=SLATE, line_width=1)
            fig_scat.add_vline(x=0, line_color=SLATE, line_width=1)

            # Quadrant labels
            for (x, y, txt) in [
                (0.6,  4,   "↑ Organic + Multiple"),
                (-0.3, 4,   "↑ Multiple only"),
                (0.6, -4,   "↑ Organic, ↓ Multiple"),
                (-0.3,-4,   "↓ Both"),
            ]:
                fig_scat.add_annotation(
                    x=x, y=y, text=txt,
                    showarrow=False,
                    font=dict(size=9, color=SLATE),
                    xref="x", yref="y"
                )

            fig_scat.update_layout(
                height=460,
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=20, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                legend=dict(font=dict(size=9), orientation="h", y=-0.12),
                xaxis=dict(
                    tickformat=".0%", gridcolor=BORDER,
                    title="EBITDA Growth (Entry → Current)",
                    zeroline=False,
                ),
                yaxis=dict(
                    tickformat=".1f", ticksuffix="x", gridcolor=BORDER,
                    title="TEV/EBITDA Multiple Change (turns)",
                    zeroline=False,
                ),
            )
            st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.markdown(f"""
            <div style="background:#F8F9FA;border:1px dashed #CCCCCC;border-radius:6px;
                        padding:24px;text-align:center;">
                <div style="font-size:13px;font-weight:700;color:#999;font-family:Arial;">
                    Entry vs. Current valuation data not yet available
                </div>
                <div style="font-size:11px;color:#BBBBBB;font-family:Arial;margin-top:6px;">
                    Add entry_adj_ebitda, entry_tev_to_ebitda, tev_to_ebitda
                    to fund_summary.csv to enable this chart
                </div>
            </div>
            """, unsafe_allow_html=True)


    # ---- TAB 3: Company Alerts — Active Portfolio Companies ----
    with po_tab3:
        hdr_col, btn_col = st.columns([6, 1])
        with hdr_col:
            st.markdown('<div class="section-header">Active Portfolio Companies</div>',
                        unsafe_allow_html=True)
        with btn_col:
            if st.button("View All Flags →", key="goto_flags_from_tab3"):
                st.session_state["page"] = "flags_alerts"
                st.rerun()

        companies_tab3 = fs_filtered.sort_values(
            "overall_flag", key=lambda x: x.map({"Red": 0, "Yellow": 1, "Green": 2})
        )
        card_cols = st.columns(3)
        for i, (_, row) in enumerate(companies_tab3.iterrows()):
            col       = card_cols[i % 3]
            cname     = row.get("company_name", "")
            rev_yoy   = row.get("revenue_yoy")
            rev_color = SEA_GREEN if pd.notna(rev_yoy) and rev_yoy > 0 else RED_FLAG
            yoy_str   = format_pct(rev_yoy) if pd.notna(rev_yoy) else "—"
            inv_date  = row.get("investment_date", "")
            try:
                inv_year = str(pd.to_datetime(inv_date).year)
            except Exception:
                inv_year = "—"

            # Build flag detail tooltip
            _flag_details = []
            _flag_map = {
                "revenue_growth_flag":    ("Rev Growth",    format_pct(row.get("revenue_yoy"))),
                "ebitda_margin_flag":     ("EBITDA Margin", format_pct(row.get("ltm_adj_ebitda_margin"))),
                "net_leverage_flag":      ("Net Leverage",  format_multiple(row.get("net_leverage"))),
                "interest_coverage_flag": ("Int. Coverage", format_multiple(row.get("interest_coverage"))),
            }
            for fk, (flbl, fval) in _flag_map.items():
                fstatus = row.get(fk, "")
                if fstatus in ("Red", "Yellow"):
                    _flag_details.append(f"{fstatus} — {flbl}: {fval}")
            _tooltip = " | ".join(_flag_details) if _flag_details else "No alerts triggered"

            col.markdown(f"""
            <div class="company-card" title="{_tooltip}" style="cursor:help;">
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <div>
                        <div class="company-name">{cname}</div>
                        <div class="company-sector">{row.get("sector","")} · Acq. {inv_year}</div>
                    </div>
                    {flag_badge(row.get("overall_flag",""))}
                </div>
                <div style="margin-top:10px; display:flex; gap:14px; flex-wrap:wrap;">
                    <div><span style="font-size:13px;font-weight:700;color:{NAVY};">
                        {format_millions(row.get("ltm_revenue"))}</span><br>
                        <span style="font-size:10px;color:{SLATE};">LTM Rev</span></div>
                    <div><span style="font-size:13px;font-weight:700;color:{NAVY};">
                        {format_multiple(row.get("net_leverage"))}</span><br>
                        <span style="font-size:10px;color:{SLATE};">Net Lev</span></div>
                    <div><span style="font-size:13px;font-weight:700;color:{NAVY};">
                        {format_pct(row.get("ltm_adj_ebitda_margin"))}</span><br>
                        <span style="font-size:10px;color:{SLATE};">EBITDA Mgn</span></div>
                    <div><span style="font-size:13px;font-weight:700;color:{rev_color};">
                        {yoy_str}</span><br>
                        <span style="font-size:10px;color:{SLATE};">Rev Growth</span></div>
                </div>
                {f'<div style="margin-top:8px;font-size:9px;color:{RED_FLAG};font-family:Arial;">⚠ {_tooltip}</div>' if _flag_details else ''}
            </div>
            """, unsafe_allow_html=True)

            btn_c1, btn_c2 = col.columns(2)
            if btn_c1.button("View Company Detail", key=f"t3_detail_{i}_{cname}",
                              use_container_width=True):
                st.session_state["page"]             = "company_detail"
                st.session_state["selected_company"] = cname
                for k in ["drill_page", "drill_company", "drill_metric"]:
                    st.session_state.pop(k, None)
                st.rerun()
            if btn_c2.button("View Company Alerts", key=f"t3_alerts_{i}_{cname}",
                              use_container_width=True):
                st.session_state["page"]              = "flags_alerts"
                st.session_state["flag_filter_company"] = cname
                st.rerun()


        v_col1, v_col2 = st.columns(2)

        with v_col1:
            st.markdown('<div class="section-header">Value by Investment (Current TEV)</div>',
                        unsafe_allow_html=True)
            tev_df = fs_filtered.dropna(subset=["current_tev"]).sort_values(
                "current_tev", ascending=True)
            if not tev_df.empty:
                fig_tev = go.Figure(go.Bar(
                    x=tev_df["current_tev"], y=tev_df["company_name"],
                    orientation="h", marker_color=NAVY,
                    text=tev_df["current_tev"].apply(format_millions),
                    textposition="outside"
                ))
                fig_tev.update_layout(
                    height=max(280, len(tev_df) * 28),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=60, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat="$,.0f", gridcolor=BORDER)
                )
                st.plotly_chart(fig_tev, use_container_width=True)

        with v_col2:
            st.markdown('<div class="section-header">MOIC by Investment</div>',
                        unsafe_allow_html=True)
            moi_df = fs_filtered.dropna(subset=["gross_moi"]).sort_values(
                "gross_moi", ascending=True)
            if not moi_df.empty:
                moi_df["bar_color"] = moi_df["gross_moi"].apply(
                    lambda x: SEA_GREEN if x > 2.0 else XANTHOUS if x > 1.5 else RED_FLAG)
                fig_moi = go.Figure(go.Bar(
                    x=moi_df["gross_moi"], y=moi_df["company_name"],
                    orientation="h",
                    marker_color=moi_df["bar_color"].tolist(),
                    text=moi_df["gross_moi"].apply(lambda x: f"{x:.2f}x"),
                    textposition="outside"
                ))
                fig_moi.add_vline(x=1.0, line_dash="dash", line_color=RED_FLAG,
                                   annotation_text="1.0x")
                fig_moi.add_vline(x=2.0, line_dash="dot",  line_color=SEA_GREEN,
                                   annotation_text="2.0x")
                fig_moi.update_layout(
                    height=max(280, len(moi_df) * 28),
                    plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=60, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    xaxis=dict(tickformat=".2f", gridcolor=BORDER)
                )
                st.plotly_chart(fig_moi, use_container_width=True)

        # Invested Capital — pending Investran
        st.markdown('<div class="section-header">Invested Capital by Investment (Cost Basis)</div>',
                    unsafe_allow_html=True)

        # Use entry_tev as proxy for invested capital until Investran data available
        ic_df = fs_filtered.dropna(subset=["entry_tev"]).sort_values("entry_tev", ascending=True)
        if not ic_df.empty:
            fig_ic = go.Figure(go.Bar(
                x=ic_df["entry_tev"], y=ic_df["company_name"],
                orientation="h", marker_color=SLATE,
                text=ic_df["entry_tev"].apply(format_millions),
                textposition="outside",
                name="Entry TEV (Cost Proxy)"
            ))
            fig_ic.update_layout(
                height=max(280, len(ic_df) * 28),
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=60, t=10, b=0),
                font=dict(family="Arial", color=NAVY, size=10),
                xaxis=dict(tickformat="$,.0f", gridcolor=BORDER)
            )
            st.plotly_chart(fig_ic, use_container_width=True)
            st.caption("** Using Entry TEV as cost proxy — replace with Invested Capital from Investran when available")



# ---------------------------------------------------------------------------
# Page 2: Fund Summary
# ---------------------------------------------------------------------------

def page_fund_summary():
    render_page_header("Fund – Coming Soon")

    st.markdown(f"""
    <div style="background:#F8F9FA; border:2px dashed #CCCCCC; border-radius:10px;
                padding:60px 40px; text-align:center; margin-top:40px;">
        <div style="font-size:36px; margin-bottom:16px;">🚧</div>
        <div style="font-size:22px; font-weight:700; color:#999999; font-family:Arial;
                    margin-bottom:10px;">Fund Analytics — Coming Soon</div>
        <div style="font-size:14px; color:#BBBBBB; font-family:Arial;">
            Fund-level performance metrics, capital flow analysis, TVPI/DPI/RVPI,
            and Investran data integration will be available here.
        </div>
    </div>
    """, unsafe_allow_html=True)


    # Old fund summary content will be re-enabled when Coming Soon is released

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

    # LTM Revenue & EBITDA time-series trend
    quarterly = load_quarterly(selected)
    if not quarterly.empty:
        st.markdown('<div class="section-header">LTM Revenue & EBITDA Trend</div>',
                    unsafe_allow_html=True)

        _co_ov_period_col, _co_ov_range_col, _ = st.columns([2, 3, 3])
        with _co_ov_period_col:
            _co_ov_mode = st.radio(
                "Period",
                ["Monthly", "Quarterly"],
                horizontal=True,
                key=f"co_ov_period_{selected}",
                label_visibility="collapsed",
            )
        _ov_period_map = {"Monthly": "Monthly", "Quarterly": "Quarterly"}
        if "period" in quarterly.columns:
            quarterly_ov = quarterly[quarterly["period"] == _ov_period_map[_co_ov_mode]].copy()
        else:
            quarterly_ov = quarterly.copy()
        quarterly_ov["cash_flow_date"] = pd.to_datetime(quarterly_ov["cash_flow_date"], errors="coerce")
        quarterly_ov = quarterly_ov.sort_values("cash_flow_date")

        _default_months = 12 if _co_ov_mode == "Monthly" else 24
        _min_date = quarterly_ov["cash_flow_date"].min()
        _max_date = quarterly_ov["cash_flow_date"].max()
        _default_start = max(_max_date - pd.DateOffset(months=_default_months), _min_date)

        with _co_ov_range_col:
            _date_range = st.date_input(
                "Date range",
                value=(_default_start.date(), _max_date.date()),
                min_value=_min_date.date(),
                max_value=_max_date.date(),
                key=f"co_ov_daterange_{selected}",
                label_visibility="collapsed",
            )

        if isinstance(_date_range, (list, tuple)) and len(_date_range) == 2:
            quarterly_ov = quarterly_ov[
                (quarterly_ov["cash_flow_date"] >= pd.Timestamp(_date_range[0])) &
                (quarterly_ov["cash_flow_date"] <= pd.Timestamp(_date_range[1]))
            ]

        if not quarterly_ov.empty:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            # revenue column = LTM Net Sales (Actual) from updated view
            _rev = quarterly_ov["revenue"].combine_first(quarterly_ov.get("net_sales", pd.Series(dtype=float)))
            fig.add_trace(go.Bar(
                x=quarterly_ov["period_label"], y=_rev,
                name="LTM Net Sales ($M)", marker_color=NAVY, opacity=0.8
            ), secondary_y=False)
            fig.add_trace(go.Bar(
                x=quarterly_ov["period_label"], y=quarterly_ov["adj_ebitda"],
                name="LTM Adj. EBITDA ($M)", marker_color=SLATE, opacity=0.8
            ), secondary_y=False)
            _margin_df = quarterly_ov[["period_label", "adj_ebitda"]].copy()
            _margin_df["_rev"] = _rev.values
            _margin_df["margin"] = _margin_df["adj_ebitda"] / _margin_df["_rev"].replace(0, float("nan"))
            _margin_df = _margin_df.dropna(subset=["margin"])
            fig.add_trace(go.Scatter(
                x=_margin_df["period_label"], y=_margin_df["margin"],
                name="EBITDA Margin %", mode="lines+markers",
                line=dict(color=XANTHOUS, width=2), marker=dict(size=5),
                connectgaps=True,
            ), secondary_y=True)
            fig.update_layout(
                height=420, plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0), barmode="group",
                legend=dict(orientation="h", y=-0.18, font=dict(size=10)),
                font=dict(family="Arial", color=NAVY, size=10)
            )
            fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False)
            fig.update_yaxes(tickformat=".0%", secondary_y=True)
            fig.update_xaxes(tickangle=-45, tickmode="linear", dtick=1, tickfont=dict(size=9))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No {_co_ov_mode} data available for this company in the selected date range.")

        # Net Leverage trend
        col_lev, col_margin = st.columns(2)

        with col_lev:
            st.markdown(f'<div class="section-header">Net Leverage — {_co_ov_mode}</div>',
                        unsafe_allow_html=True)
            lev_df = quarterly_ov.dropna(subset=["net_leverage"])
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
                    height=340, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    yaxis=dict(title="Net Leverage (x)", gridcolor=BORDER)
                )
                fig3.update_xaxes(tickangle=-45, tickmode="linear", dtick=1,
                                  tickfont=dict(size=8))
                st.plotly_chart(fig3, use_container_width=True)

        with col_margin:
            st.markdown(f'<div class="section-header">EBITDA Margin % — {_co_ov_mode}</div>',
                        unsafe_allow_html=True)
            mgn_df = quarterly_ov.dropna(subset=["adj_ebitda_margin_pct"])
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
                    fill="tozeroy", fillcolor="rgba(63,102,128,0.1)",
                    connectgaps=True,
                ))
                fig4.update_layout(
                    height=340, plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=0, r=0, t=10, b=0),
                    font=dict(family="Arial", color=NAVY, size=10),
                    yaxis=dict(tickformat=".0%", gridcolor=BORDER)
                )
                fig4.update_xaxes(tickangle=-45, tickmode="linear", dtick=1,
                                  tickfont=dict(size=8))
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
    # Pre-select view if arriving from a navigation button
    _init_mode = st.session_state.pop("flags_view_mode_init", None)
    _view_options = ["Portfolio KPIs", "Company KPIs", "Scorecard Table", "Consumer KPIs"]
    _default_idx  = _view_options.index(_init_mode) if _init_mode in _view_options else 0
    view_mode = st.radio(
        "View",
        _view_options,
        index=_default_idx,
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
    # VIEW 1: Portfolio KPIs
    # -----------------------------------------------------------------------
    if view_mode == "Portfolio KPIs":

        # Calculation methodology — collapsible reference table
        with st.expander("Flag Calculation Methodology", expanded=True):
            st.markdown(
                f'<div style="font-size:12px;color:{SLATE};font-family:Arial;margin-bottom:8px;">'
                "Each flag is calculated from LTM financials pulled from 73 Strings. "
                "Thresholds are applied portfolio-wide and shown below."
                "</div>",
                unsafe_allow_html=True
            )
            methodology = [
                {"Metric": "Revenue Growth (YoY)",
                 "Calculation": "(LTM Revenue - Prior Year Revenue) / Prior Year Revenue",
                 "Green": "> 10%", "Yellow": "0 - 10%", "Red": "< 0%"},
                {"Metric": "EBITDA Margin",
                 "Calculation": "LTM Adj. EBITDA / LTM Net Sales",
                 "Green": "> 18%", "Yellow": "10 - 18%", "Red": "< 10%"},
                {"Metric": "Net Leverage",
                 "Calculation": "Net Debt / LTM Credit Agreement EBITDA",
                 "Green": "< 5.0x", "Yellow": "5.0 - 6.0x", "Red": "> 6.0x"},
                {"Metric": "Interest Coverage",
                 "Calculation": "LTM Adj. EBITDA / LTM Cash Interest Expense",
                 "Green": "> 3.0x", "Yellow": "2.0 - 3.0x", "Red": "< 2.0x"},
                {"Metric": "Overall Flag",
                 "Calculation": "Worst of the four individual flags above",
                 "Green": "All green", "Yellow": "Any yellow, no red", "Red": "Any red flag"},
            ]
            meth_df = pd.DataFrame(methodology).rename(columns={
                "Green": "🟢 Green", "Yellow": "🟡 Yellow", "Red": "🔴 Red"
            }).set_index("Metric")
            st.dataframe(meth_df, use_container_width=True)
            st.caption(
                "Net Debt = Total Gross Debt - Cash  ·  LTM = Last Twelve Months  ·  "
                "Data source: 73 Strings API → SQL Server → CSV export"
            )

        # Flag hover definitions
        FLAG_HOVER = {
            "revenue_growth_flag": {
                "label": "Revenue Growth (YoY)",
                "calc":  "(LTM Revenue - PY Revenue) / PY Revenue",
                "green": "> 10%", "yellow": "0-10%", "red": "< 0%",
            },
            "ebitda_margin_flag": {
                "label": "EBITDA Margin",
                "calc":  "LTM Adj. EBITDA / LTM Net Sales",
                "green": "> 18%", "yellow": "10-18%", "red": "< 10%",
            },
            "net_leverage_flag": {
                "label": "Net Leverage",
                "calc":  "Net Debt / LTM Credit Agreement EBITDA",
                "green": "< 5.0x", "yellow": "5.0-6.0x", "red": "> 6.0x",
            },
            "interest_coverage_flag": {
                "label": "Interest Coverage",
                "calc":  "LTM Adj. EBITDA / LTM Cash Interest Expense",
                "green": "> 3.0x", "yellow": "2.0-3.0x", "red": "< 2.0x",
            },
        }

        def ai_flag_summary(cname, row):
            key = f"ai_flag_summary_{cname}"
            if key in st.session_state:
                return st.session_state[key]
            try:
                from ai import ask_claude, build_portfolio_context
                ctx = build_portfolio_context()
                prompt = (
                    f"In 1-2 sentences, explain the key driver behind {cname}'s flag status. "
                    f"Revenue growth: {format_pct(row.get('revenue_yoy'))}, "
                    f"EBITDA margin: {format_pct(row.get('ltm_adj_ebitda_margin'))}, "
                    f"Net leverage: {format_multiple(row.get('net_leverage'))}, "
                    f"Interest coverage: {format_multiple(row.get('interest_coverage'))}. "
                    "Be specific and concise — no preamble."
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

            FLAG_METRIC_DEFS = [
                ("revenue_growth_flag",    "revenue_yoy",             "Rev Growth YoY",  format_pct),
                ("ebitda_margin_flag",     "ltm_adj_ebitda_margin",   "EBITDA Margin",   format_pct),
                ("net_leverage_flag",      "net_leverage",            "Net Leverage",    format_multiple),
                ("interest_coverage_flag", "interest_coverage",       "Int. Coverage",   format_multiple),
            ]

            for _, row in df.iterrows():
                cname    = row["company_name"]
                inv_year = "—"
                if not fs.empty and "investment_date" in fs.columns:
                    fs_row = fs[fs["company_name"] == cname]
                    if not fs_row.empty:
                        try:
                            inv_year = str(pd.to_datetime(fs_row.iloc[0]["investment_date"]).year)
                        except Exception:
                            pass

                exp_label = (
                    f"{flag_emoji(row['overall_flag'])}  {cname}  |  "
                    f"Acq. {inv_year}  |  "
                    f"Net Lev: {format_multiple(row.get('net_leverage'))}  |  "
                    f"Rev: {format_pct(row.get('revenue_yoy'))}  |  "
                    f"EBITDA Mgn: {format_pct(row.get('ltm_adj_ebitda_margin'))}"
                )

                with st.expander(exp_label):

                    # --- Top row: Revenue + EBITDA absolute, then 4 flag metric cards ---
                    top_cols = st.columns(6)
                    top_cols[0].metric("LTM Revenue",
                                       format_millions(row.get("ltm_revenue")))
                    top_cols[1].metric("LTM Adj. EBITDA",
                                       format_millions(row.get("ltm_adj_ebitda")))

                    for i, (fk, vk, lbl, fmt) in enumerate(FLAG_METRIC_DEFS):
                        fval  = str(row.get(fk, "") or "")
                        val   = row.get(vk)
                        fclr  = {"Red": RED_FLAG, "Yellow": XANTHOUS,
                                 "Green": SEA_GREEN}.get(fval, SLATE)
                        h     = FLAG_HOVER.get(fk, {})
                        tip   = (
                            h.get("label", lbl) + "\n"
                            "Calc: " + h.get("calc", "") + "\n"
                            "Green: " + h.get("green", "") + "  "
                            "Yellow: " + h.get("yellow", "") + "  "
                            "Red: " + h.get("red", "")
                        )
                        val_str = fmt(val) if val is not None and not pd.isna(val) else "—"
                        top_cols[i + 2].markdown(
                            f'<div title="{tip}" style="'
                            f'background:white;border:1px solid {BORDER};'
                            f'border-left:4px solid {fclr};border-radius:4px;'
                            f'padding:8px 10px;cursor:help;">'
                            f'<div style="font-size:18px;font-weight:700;'
                            f'color:{fclr};font-family:Arial;">{val_str}</div>'
                            f'<div style="font-size:10px;color:{SLATE};'
                            f'font-family:Arial;margin-top:2px;">{lbl}</div>'
                            f'<div style="font-size:9px;color:{fclr};'
                            f'font-family:Arial;font-weight:600;">'
                            f'{flag_emoji(fval)} {fval}</div>'
                            f'</div>',
                            unsafe_allow_html=True
                        )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- Macro & News inline ---
                    with st.expander("Macro & News", expanded=False):
                        try:
                            from db import load_news
                            news_df = load_news(cname)
                            if news_df is not None and not news_df.empty:
                                for _, nrow in news_df.head(3).iterrows():
                                    pub   = str(nrow.get("published", ""))[:10]
                                    ntitle = nrow.get("title", "")
                                    link  = nrow.get("link", "#")
                                    src   = nrow.get("source", "")
                                    st.markdown(
                                        f"**[{ntitle}]({link})**  \n"
                                        f'<span style="font-size:10px;color:{SLATE};">'
                                        f"{src} · {pub}</span>",
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.caption("No recent news. Run news_pipeline.py to fetch articles.")
                        except Exception:
                            st.caption("News unavailable.")

                    # --- AI Summary ---
                    ai_col, btn_col = st.columns([4, 1])
                    with btn_col:
                        if st.button("AI Summary", key=f"ai_sum_{cname}",
                                     use_container_width=True):
                            with st.spinner("Generating..."):
                                st.session_state.pop(f"ai_flag_summary_{cname}", None)
                                ai_flag_summary(cname, row)
                            st.rerun()
                    with ai_col:
                        summary = st.session_state.get(f"ai_flag_summary_{cname}", "")
                        if summary:
                            st.markdown(
                                f'<div style="background:{LIGHT_BG};'
                                f'border-left:3px solid {NAVY};padding:8px 10px;'
                                f'border-radius:4px;font-size:12px;color:{NAVY};'
                                f'font-family:Arial;"><b>AI:</b> {summary}</div>',
                                unsafe_allow_html=True
                            )

                    st.markdown("<br>", unsafe_allow_html=True)

                    # --- Navigation buttons ---
                    ac = st.columns(5)
                    if ac[0].button("View Company Detail",
                                    key=f"goto_co_{cname}",
                                    use_container_width=True):
                        st.session_state["page"]             = "company_detail"
                        st.session_state["selected_company"] = cname
                        st.rerun()
                    for metric_name, mc_btn in zip(
                        ["Net Leverage", "EBITDA Margin", "Rev Growth", "Gross Margin"],
                        ac[1:]
                    ):
                        if mc_btn.button(metric_name,
                                         key=f"flag_drill_{cname}_{metric_name}",
                                         use_container_width=True):
                            set_drill("flags", company=cname, metric=metric_name)
                            st.rerun()

        # -----------------------------------------------------------------------
        # COLOR FILTER — replaces hardcoded red/yellow/green sections
        # -----------------------------------------------------------------------
        color_filter = st.radio(
            "Filter by flag color",
            ["All", "🔴 Red", "🟡 Yellow", "🟢 Green"],
            horizontal=True,
            key="fa_color_filter",
            label_visibility="collapsed"
        )

        if color_filter == "🔴 Red":
            display_df = red
            section_color = RED_FLAG
        elif color_filter == "🟡 Yellow":
            display_df = yellow
            section_color = "#B7860B"
        elif color_filter == "🟢 Green":
            display_df = green
            section_color = SEA_GREEN
        else:
            display_df = flags_filtered
            section_color = NAVY

        if display_df.empty:
            st.info("No alerts match the current filter.")
        else:
            # Tile grid — 3 per row
            FLAG_METRIC_LABELS = [
                ("net_leverage_flag",   "net_leverage",           "Net Lev",    format_multiple),
                ("revenue_growth_flag", "revenue_yoy",            "Rev Growth", format_pct),
                ("ebitda_margin_flag",  "ltm_adj_ebitda_margin",  "EBITDA Mgn", format_pct),
                ("interest_coverage_flag", "interest_coverage",   "Int. Cov",   format_multiple),
            ]
            tile_cols = st.columns(3)
            for idx, (_, row) in enumerate(display_df.sort_values(
                "overall_flag", key=lambda x: x.map({"Red": 0, "Yellow": 1, "Green": 2})
            ).iterrows()):
                col = tile_cols[idx % 3]
                cname   = row.get("company_name", "")
                overall = row.get("overall_flag", "")
                fclr    = {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}.get(overall, SLATE)

                # Build one primary alert label per company (worst metric)
                primary_alert = "—"
                for fk, vk, lbl, fmt in FLAG_METRIC_LABELS:
                    if str(row.get(fk, "")) == overall:
                        val = row.get(vk)
                        if val is not None and not pd.isna(val):
                            primary_alert = f"{lbl}: {fmt(val)}"
                        break

                col.markdown(f"""
                <div style="background:white; border:1px solid {BORDER};
                            border-left:4px solid {fclr}; border-radius:6px;
                            padding:12px 14px; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;
                                margin-bottom:6px;">
                        <span style="font-size:13px; font-weight:700; color:{NAVY};
                                     font-family:Arial;">{cname}</span>
                        <span style="font-size:10px; font-weight:700; color:{fclr};
                                     font-family:Arial;">{flag_emoji(overall)} {overall}</span>
                    </div>
                    <div style="font-size:12px; color:{fclr}; font-family:Arial;
                                font-weight:600;">{primary_alert}</div>
                    <div style="font-size:10px; color:{SLATE}; font-family:Arial; margin-top:4px;">
                        Rev: {format_pct(row.get("revenue_yoy"))} &nbsp;|&nbsp;
                        Net Lev: {format_multiple(row.get("net_leverage"))} &nbsp;|&nbsp;
                        EBITDA Mgn: {format_pct(row.get("ltm_adj_ebitda_margin"))}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                btn_c1, btn_c2 = col.columns(2)
                if btn_c1.button("Detail", key=f"tile_detail_{cname}_{idx}",
                                  use_container_width=True):
                    st.session_state["page"]             = "company_detail"
                    st.session_state["selected_company"] = cname
                    st.rerun()
                if btn_c2.button("Alerts", key=f"tile_alerts_{cname}_{idx}",
                                  use_container_width=True):
                    st.session_state["page"]              = "flags_alerts"
                    st.session_state["flag_filter_company"] = cname
                    st.rerun()



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

    # -----------------------------------------------------------------------
    # VIEW 4: Consumer KPIs  (moved from standalone page)
    # -----------------------------------------------------------------------
    if view_mode == "Consumer KPIs":
        try:
            from pages_extra import page_consumer_kpis
            page_consumer_kpis()
        except Exception as exc:
            st.error(f"Consumer KPIs error: {exc}")


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
        elif page == "sop_training":
            from page_sop import page_sop
            page_sop()
        elif page == "export_ppt":
            from export_ppt import page_export
            page_export()

    if ai_open and ai_col is not None:
        with ai_col:
            render_ai_panel()


if __name__ == "__main__":
    main()
