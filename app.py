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
    initial_sidebar_state="expanded",
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
    /* Page background */
    .stApp {{ background-color: {LIGHT_BG}; }}

    /* Header bar */
    .tsg-header {{
        background-color: {NAVY};
        padding: 14px 24px;
        border-radius: 6px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .tsg-header-title {{
        color: white;
        font-size: 20px;
        font-weight: 700;
        font-family: Arial, sans-serif;
        margin: 0;
    }}
    .tsg-header-subtitle {{
        color: {SKY};
        font-size: 13px;
        font-family: Arial, sans-serif;
        margin: 0;
    }}

    /* KPI cards */
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

    /* Company cards */
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

    /* Flag badges */
    .flag-red    {{ background: #FDECEA; color: {RED_FLAG}; border: 1px solid {RED_FLAG}; }}
    .flag-yellow {{ background: #FEF9E7; color: #B7860B;   border: 1px solid {XANTHOUS}; }}
    .flag-green  {{ background: #EAFAF1; color: {SEA_GREEN}; border: 1px solid {SEA_GREEN}; }}

    /* Section headers */
    .section-header {{
        font-size: 13px;
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

    /* Alert banner */
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

    /* Chat bubbles */
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

    /* Hide Streamlit default elements */
    #MainMenu {{ visibility: hidden; }}
    footer {{ visibility: hidden; }}
    .stDeployButton {{ display: none; }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {NAVY} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: white !important;
    }}
    [data-testid="stSidebar"] .stSelectbox label {{
        color: {SKY} !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
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
            if password == st.secrets["auth"]["password"]:
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
    st.markdown(f"""
    <div class="tsg-header">
        <div>
            <p class="tsg-header-title">TSG <span style="color:{SKY}; font-weight:400;">CONSUMER</span></p>
            <p class="tsg-header-subtitle">{subtitle}</p>
        </div>
        <div style="text-align:right;">
            <p style="color:{SKY}; font-size:12px; font-family:Arial; margin:0;">{title}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


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
    render_header("Portfolio Overview")

    overview = load_portfolio_overview().iloc[0]
    flags    = load_flags()
    ltm      = load_ltm_snapshot()
    fs       = load_fund_summary()

    # Alert banner for red flags
    red_companies = flags[flags["overall_flag"] == "Red"]["company_name"].tolist()
    if red_companies:
        issues = []
        for _, row in flags[flags["overall_flag"] == "Red"].iterrows():
            parts = []
            if row.get("net_leverage_flag") == "Red":
                parts.append(f"Net Lev {format_multiple(row.get('net_leverage'))}")
            if row.get("revenue_growth_flag") == "Red":
                parts.append(f"Rev Growth {format_pct(row.get('revenue_yoy'))}")
            if row.get("ebitda_margin_flag") == "Red":
                parts.append(f"EBITDA Margin {format_pct(row.get('ltm_adj_ebitda_margin'))}")
            issues.append(f"<b>{row['company_name']}</b>: {', '.join(parts)}")

        st.markdown(f"""
        <div class="alert-banner">
            🚨 <b>{len(red_companies)} Active Red Flag{"s" if len(red_companies) > 1 else ""}</b> —
            {" · ".join(issues)}
        </div>
        """, unsafe_allow_html=True)

    # Top KPI row
    red   = int(overview.get("red_flag_count", 0))
    yel   = int(overview.get("yellow_flag_count", 0))
    grn   = int(overview.get("green_flag_count", 0))

    cols = st.columns(6)
    cards = [
        (format_millions(overview.get("total_tev")),          "Total TEV",            ""),
        (format_millions(overview.get("total_ltm_revenue")),   "LTM Portfolio Revenue",""),
        (format_millions(overview.get("total_ltm_adj_ebitda")),"LTM Portfolio EBITDA", ""),
        (format_multiple(overview.get("avg_net_leverage_wtd")),"Avg Net Leverage",     "Weighted by TEV"),
        (format_pct(overview.get("avg_adj_ebitda_margin")),    "Avg EBITDA Margin",    ""),
        (f"🔴{red}  🟡{yel}  🟢{grn}",                        "KPI Flags",            f"{int(overview.get('active_company_count',0))} Companies"),
    ]
    for col, (val, label, delta) in zip(cols, cards):
        col.markdown(kpi_card(val, label, delta), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts row
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-header">Portfolio Revenue & EBITDA — LTM Trend</div>',
                    unsafe_allow_html=True)
        quarterly = load_quarterly()
        if not quarterly.empty:
            agg = quarterly.groupby("period_label").agg(
                revenue    = ("revenue", "sum"),
                adj_ebitda = ("adj_ebitda", "sum"),
                cash_flow_date = ("cash_flow_date", "max")
            ).reset_index().sort_values("cash_flow_date").tail(12)

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(
                x=agg["period_label"], y=agg["revenue"],
                name="Revenue ($M)", marker_color=SLATE, opacity=0.85
            ), secondary_y=False)
            fig.add_trace(go.Bar(
                x=agg["period_label"], y=agg["adj_ebitda"],
                name="Adj. EBITDA ($M)", marker_color=SKY, opacity=0.85
            ), secondary_y=False)
            margin = agg["adj_ebitda"] / agg["revenue"].replace(0, float("nan"))
            fig.add_trace(go.Scatter(
                x=agg["period_label"], y=margin,
                name="EBITDA Margin %", mode="lines+markers",
                line=dict(color=XANTHOUS, width=2),
                marker=dict(size=5)
            ), secondary_y=True)
            fig.update_layout(
                height=280, plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
                font=dict(family="Arial", color=NAVY, size=10),
                barmode="group"
            )
            fig.update_yaxes(tickformat="$,.0f", secondary_y=False,
                             gridcolor=BORDER, gridwidth=1)
            fig.update_yaxes(tickformat=".0%", secondary_y=True)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown('<div class="section-header">Portfolio by Sector</div>',
                    unsafe_allow_html=True)
        sector_data = fs.groupby("sector")["current_tev"].sum().reset_index()
        sector_data = sector_data.dropna().sort_values("current_tev", ascending=False)
        if not sector_data.empty:
            fig2 = px.pie(
                sector_data, values="current_tev", names="sector",
                hole=0.55,
                color_discrete_sequence=[NAVY, SLATE, SKY, XANTHOUS, CELADON,
                                          SEA_GREEN, MAGENTA, EGGPLANT]
            )
            fig2.update_traces(textposition="outside", textinfo="percent+label",
                               textfont_size=10)
            fig2.update_layout(
                height=280, showlegend=False,
                margin=dict(l=0, r=0, t=10, b=0),
                paper_bgcolor="white"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # Company cards grid
    st.markdown('<div class="section-header">Active Portfolio Companies</div>',
                unsafe_allow_html=True)

    companies = fs.sort_values("overall_flag",
                                key=lambda x: x.map({"Red": 0, "Yellow": 1, "Green": 2}))
    cols = st.columns(3)
    for i, (_, row) in enumerate(companies.iterrows()):
        col = cols[i % 3]
        rev_yoy = row.get("revenue_yoy")
        rev_yoy_str = f"{'▲' if rev_yoy and rev_yoy > 0 else '▼'} {format_pct(rev_yoy)} Rev" if pd.notna(rev_yoy) else ""

        col.markdown(f"""
        <div class="company-card">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <div>
                    <div class="company-name">{row.get('company_name','')}</div>
                    <div class="company-sector">{row.get('sector','')} · {row.get('geography','')[:20] if pd.notna(row.get('geography')) else ''}</div>
                </div>
                {flag_badge(row.get('overall_flag',''))}
            </div>
            <div style="margin-top:10px; display:flex; gap:16px; flex-wrap:wrap;">
                <div><span style="font-size:13px;font-weight:700;color:{NAVY};">{format_millions(row.get('ltm_revenue'))}</span><br><span style="font-size:10px;color:{SLATE};">LTM Rev</span></div>
                <div><span style="font-size:13px;font-weight:700;color:{NAVY};">{format_multiple(row.get('net_leverage'))}</span><br><span style="font-size:10px;color:{SLATE};">Net Lev</span></div>
                <div><span style="font-size:13px;font-weight:700;color:{NAVY};">{format_pct(row.get('ltm_adj_ebitda_margin'))}</span><br><span style="font-size:10px;color:{SLATE};">EBITDA Mgn</span></div>
                <div><span style="font-size:13px;font-weight:700;color:{'#06865C' if pd.notna(rev_yoy) and rev_yoy > 0 else RED_FLAG};">{format_pct(rev_yoy)}</span><br><span style="font-size:10px;color:{SLATE};">Rev Growth</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        company_name_val = row.get('company_name','')
        if col.button(f"View Detail →", key=f"drill_{company_name_val}", use_container_width=True):
            set_drill("overview", company=company_name_val)
            st.rerun()


# ---------------------------------------------------------------------------
# Page 2: Fund Summary
# ---------------------------------------------------------------------------

def page_fund_summary():
    render_header("Fund Summary")

    fs = load_fund_summary()

    st.markdown('<div class="section-header">TSG9 Investment Summary</div>',
                unsafe_allow_html=True)

    # Format for display
    display = fs[[
        "company_name", "sector", "investment_date", "security_type",
        "ownership_structure", "entry_tev", "current_tev", "gross_moi",
        "ltm_revenue", "ltm_adj_ebitda", "ltm_adj_ebitda_margin",
        "net_leverage", "revenue_yoy", "overall_flag"
    ]].copy()

    display["investment_date"] = pd.to_datetime(display["investment_date"]).dt.strftime("%b %Y")
    display["entry_tev"]   = display["entry_tev"].apply(lambda x: format_millions(x))
    display["current_tev"] = display["current_tev"].apply(lambda x: format_millions(x))
    display["gross_moi"]   = display["gross_moi"].apply(lambda x: format_multiple(x))
    display["ltm_revenue"] = display["ltm_revenue"].apply(lambda x: format_millions(x))
    display["ltm_adj_ebitda"] = display["ltm_adj_ebitda"].apply(lambda x: format_millions(x))
    display["ltm_adj_ebitda_margin"] = display["ltm_adj_ebitda_margin"].apply(lambda x: format_pct(x))
    display["net_leverage"] = display["net_leverage"].apply(lambda x: format_multiple(x))
    display["revenue_yoy"]  = display["revenue_yoy"].apply(lambda x: format_pct(x))
    display["overall_flag"] = display["overall_flag"].apply(lambda x: f"{flag_emoji(x)} {x}")

    display.columns = [
        "Company", "Sector", "Entry", "Security", "Ownership",
        "Entry TEV", "Current TEV", "Gross MOI",
        "LTM Revenue", "LTM EBITDA", "EBITDA Mgn",
        "Net Lev", "Rev Growth", "Flag"
    ]

    # Drill-down check
    if has_drill():
        d = get_drill()
        if d["page"] == "fund_summary" and d["company"]:
            drill_tev_history(d["company"])
            return

    st.dataframe(
        display.set_index("Company"),
        use_container_width=True,
        height=600,
    )
    st.caption("Click a company name below to drill into TEV & Valuation history:")
    raw2 = load_fund_summary()
    drill_cols = st.columns(5)
    for i, (_, row) in enumerate(raw2.iterrows()):
        if drill_cols[i % 5].button(row["company_name"], key=f"fs_drill_{row['company_name']}", use_container_width=True):
            set_drill("fund_summary", company=row["company_name"])
            st.rerun()

    # Scatter: Gross IRR vs MOI (using revenue growth as proxy)
    st.markdown('<div class="section-header">Current TEV vs EBITDA Margin</div>',
                unsafe_allow_html=True)
    raw = load_fund_summary()
    plot_df = raw.dropna(subset=["current_tev", "ltm_adj_ebitda_margin", "net_leverage"])

    if not plot_df.empty:
        plot_df["flag_color"] = plot_df["overall_flag"].map(
            {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}
        ).fillna(SLATE)
        fig = px.scatter(
            plot_df,
            x="ltm_adj_ebitda_margin",
            y="current_tev",
            size="ltm_revenue",
            color="overall_flag",
            color_discrete_map={"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN},
            hover_name="company_name",
            text="company_name",
            labels={
                "ltm_adj_ebitda_margin": "LTM EBITDA Margin",
                "current_tev": "Current TEV ($M)",
                "overall_flag": "Flag"
            },
            size_max=50,
        )
        fig.update_traces(textposition="top center", textfont_size=9)
        fig.update_layout(
            height=380, plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Arial", color=NAVY, size=10),
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(tickformat=".0%", gridcolor=BORDER),
            yaxis=dict(tickformat="$,.0f", gridcolor=BORDER),
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Page 3: Company Detail
# ---------------------------------------------------------------------------

def page_company_detail():
    render_header("Company Detail")

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
# Page 4: Flags & Alerts
# ---------------------------------------------------------------------------

def page_flags_alerts():
    render_header("Flags & Alerts")

    flags = load_flags()

    red    = flags[flags["overall_flag"] == "Red"]
    yellow = flags[flags["overall_flag"] == "Yellow"]
    green  = flags[flags["overall_flag"] == "Green"]

    # Summary counts
    cols = st.columns(3)
    cols[0].markdown(kpi_card(
        f"🔴 {len(red)}",
        "Red Flags",
        "Requires immediate attention",
        RED_FLAG
    ), unsafe_allow_html=True)
    cols[1].markdown(kpi_card(
        f"🟡 {len(yellow)}",
        "Yellow Flags",
        "Watch — worsening trend",
        "#B7860B"
    ), unsafe_allow_html=True)
    cols[2].markdown(kpi_card(
        f"🟢 {len(green)}",
        "Green — On Track",
        "Within acceptable thresholds",
        SEA_GREEN
    ), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Drill-down check
    if has_drill():
        d = get_drill()
        if d["page"] == "flags" and d["company"] and d["metric"]:
            drill_flag_metric(d["company"], d["metric"])
            return

    def render_flag_section(df, color, title):
        if df.empty:
            return
        st.markdown(f'<div class="section-header" style="color:{color};">{title}</div>',
                    unsafe_allow_html=True)
        for _, row in df.iterrows():
            with st.expander(
                f"{flag_emoji(row['overall_flag'])}  {row['company_name']}  |  "
                f"Net Lev: {format_multiple(row.get('net_leverage'))}  |  "
                f"Rev Growth: {format_pct(row.get('revenue_yoy'))}  |  "
                f"EBITDA Mgn: {format_pct(row.get('ltm_adj_ebitda_margin'))}"
            ):
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("LTM Revenue",     format_millions(row.get("ltm_revenue")))
                c2.metric("LTM Adj. EBITDA", format_millions(row.get("ltm_adj_ebitda")))
                c3.metric("EBITDA Margin",   format_pct(row.get("ltm_adj_ebitda_margin")))
                c4.metric("Net Leverage",    format_multiple(row.get("net_leverage")))
                c5.metric("Rev Growth YoY",  format_pct(row.get("revenue_yoy")))

                # Flag breakdown
                flag_cols = st.columns(4)
                flag_cols[0].markdown(
                    f"**Revenue Growth**<br>{flag_badge(row.get('revenue_growth_flag',''))}",
                    unsafe_allow_html=True)
                flag_cols[1].markdown(
                    f"**EBITDA Margin**<br>{flag_badge(row.get('ebitda_margin_flag',''))}",
                    unsafe_allow_html=True)
                flag_cols[2].markdown(
                    f"**Net Leverage**<br>{flag_badge(row.get('net_leverage_flag',''))}",
                    unsafe_allow_html=True)
                flag_cols[3].markdown(
                    f"**Interest Coverage**<br>{flag_badge(row.get('interest_coverage_flag',''))}",
                    unsafe_allow_html=True)
                # Drill-down buttons for each flagged metric
                st.markdown("**Drill into metric trend:**")
                drill_btn_cols = st.columns(4)
                for metric_name, btn_col in zip(
                    ["Net Leverage", "EBITDA Margin", "Revenue Growth", "Gross Margin"],
                    drill_btn_cols
                ):
                    if btn_col.button(metric_name, key=f"flag_drill_{row['company_name']}_{metric_name}", use_container_width=True):
                        set_drill("flags", company=row["company_name"], metric=metric_name)
                        st.rerun()

    render_flag_section(red,    RED_FLAG,  "🔴 RED — Covenant or Material Breach")
    render_flag_section(yellow, "#B7860B", "🟡 YELLOW — Watch List")
    render_flag_section(green,  SEA_GREEN, "🟢 GREEN — Notable Outperformers")

    # Benchmark scorecard
    st.markdown('<div class="section-header">Full KPI Benchmark Scorecard</div>',
                unsafe_allow_html=True)
    scorecard = flags[[
        "company_name", "ltm_revenue", "revenue_yoy",
        "ltm_adj_ebitda_margin", "net_leverage",
        "interest_coverage", "overall_flag",
        "revenue_growth_flag", "ebitda_margin_flag", "net_leverage_flag"
    ]].copy()
    scorecard["ltm_revenue"]           = scorecard["ltm_revenue"].apply(format_millions)
    scorecard["revenue_yoy"]           = scorecard["revenue_yoy"].apply(format_pct)
    scorecard["ltm_adj_ebitda_margin"] = scorecard["ltm_adj_ebitda_margin"].apply(format_pct)
    scorecard["net_leverage"]          = scorecard["net_leverage"].apply(format_multiple)
    scorecard["interest_coverage"]     = scorecard["interest_coverage"].apply(format_multiple)
    scorecard["overall_flag"]          = scorecard["overall_flag"].apply(
        lambda x: f"{flag_emoji(x)} {x}")
    scorecard.columns = [
        "Company", "LTM Revenue", "Rev Growth", "EBITDA Margin",
        "Net Leverage", "Int. Coverage", "Overall",
        "Rev Flag", "Margin Flag", "Lev Flag"
    ]
    st.dataframe(scorecard.set_index("Company"), use_container_width=True)


# ---------------------------------------------------------------------------
# Portfolio AI page
# ---------------------------------------------------------------------------

def page_portfolio_ai():
    render_header("Portfolio AI Analyst")

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
# Sidebar navigation
# ---------------------------------------------------------------------------

def render_sidebar():
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center; padding:20px 0 10px 0;">
            <p style="font-size:18px; font-weight:700; color:white;
                      font-family:Arial; margin:0;">
                TSG <span style="color:{SKY};">CONSUMER</span>
            </p>
            <p style="font-size:10px; color:{SKY}; margin:4px 0 0 0; font-family:Arial;">
                Portfolio Analytics
            </p>
        </div>
        <hr style="border-color:rgba(255,255,255,0.15); margin:10px 0;">
        """, unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            ["📊 Portfolio Overview",
             "📋 Fund Summary",
             "🏢 Company Detail",
             "🚨 Flags & Alerts",
             "📈 Consumer KPIs",
             "🤖 AI Analyst",
             "🚦 Portfolio Flags",
             "📤 Export to PPT"],
            label_visibility="collapsed"
        )

        st.markdown("<hr style='border-color:rgba(255,255,255,0.15); margin:20px 0;'>",
                    unsafe_allow_html=True)

        # Last refresh
        try:
            from sqlalchemy import text as sql_text
            with get_engine().connect() as conn:
                row = conn.execute(sql_text("""
                    SELECT TOP 1 finished_at, pipeline_name
                    FROM dbo.ts_pipeline_runs
                    WHERE status = 'SUCCESS'
                    ORDER BY finished_at DESC
                """)).fetchone()
                if row:
                    st.markdown(f"""
                    <p style="font-size:10px; color:{SKY}; font-family:Arial; margin:0;">
                        DATA AS OF<br>
                        <span style="color:white; font-weight:600;">
                            {str(row[0])[:16] if row[0] else 'Unknown'}
                        </span>
                    </p>
                    """, unsafe_allow_html=True)
        except Exception:
            pass

        if st.button("Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    return page


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not check_password():
        return

    # Pre-warm cache on startup
    load_portfolio_overview()
    load_fund_summary()
    load_flags()
    load_ltm_snapshot()
    load_company_master()

    page = render_sidebar()

    if page == "📊 Portfolio Overview":
        page_portfolio_overview()
    elif page == "📋 Fund Summary":
        page_fund_summary()
    elif page == "🏢 Company Detail":
        from pages_extra import page_company_detail_enhanced
        page_company_detail_enhanced()
    elif page == "🚨 Flags & Alerts":
        page_flags_alerts()
    elif page == "📈 Consumer KPIs":
        from pages_extra import page_consumer_kpis
        page_consumer_kpis()
    elif page == "🤖 AI Analyst":
        from ai import build_portfolio_context_with_news
        page_portfolio_ai()
    elif page == "🚦 Portfolio Flags":
        from page_portfolio_flags import page_portfolio_flags
        page_portfolio_flags()
    elif page == "📤 Export to PPT":
        from export_ppt import page_export
        page_export()


if __name__ == "__main__":
    main()
