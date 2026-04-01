"""
pages_extra.py
==============
Additional dashboard pages:
  - Consumer KPIs
  - Company News
  - Updated Company Detail with income statement drill-down
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from db import (
    load_flags, load_ltm_snapshot, load_quarterly, load_yoy_growth,
    load_company_master, load_news, load_income_statement_ltm,
    load_consumer_kpis, get_company_list,
    format_millions, format_multiple, format_pct, flag_color, flag_emoji
)
from ai import build_company_context_with_news, ask_claude

# TSG Brand Colors
NAVY      = "#071733"
SLATE     = "#3F6680"
SKY       = "#A8CFDE"
XANTHOUS  = "#F3B51F"
CELADON   = "#85D7B0"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
LIGHT_BG  = "#F4F6F9"
BORDER    = "#E0E4EA"

# Tags to show in income statement drill-down, in order
IS_TAG_ORDER = [
    "Income Statement",
    "KPI",
    "Ratio Analysis",
    "Covenant",
    "Balance Sheet",
    "Cash Flow",
    "Valuation",
]


def flag_badge(flag: str) -> str:
    css = {"Red": "flag-red", "Yellow": "flag-yellow", "Green": "flag-green"}.get(flag, "")
    return f'<span class="metric-pill {css}">{flag_emoji(flag)} {flag}</span>'


def kpi_card(value, label, delta="", delta_color=SLATE):
    return f"""
    <div class="kpi-card">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {"" if not delta else f'<div class="kpi-delta" style="color:{delta_color};">{delta}</div>'}
    </div>
    """


# ---------------------------------------------------------------------------
# Consumer KPIs Page
# ---------------------------------------------------------------------------

def page_consumer_kpis():
    from ui import render_page_header
    render_page_header("Consumer KPIs")

    kpi_df = load_consumer_kpis()

    if kpi_df.empty:
        st.info("No KPI data available. KPI attributes will appear here once data is loaded.")
        return

    # Get unique KPI names
    kpi_names = sorted(kpi_df["attribute_name"].unique().tolist())

    # Filters
    col_f1, col_f2 = st.columns([2, 3])
    with col_f1:
        selected_kpi = st.selectbox("Select KPI", kpi_names)
    with col_f2:
        companies = sorted(kpi_df["company_name"].unique().tolist())
        selected_companies = st.multiselect("Filter Companies", companies, default=companies)

    if not selected_kpi:
        return

    filtered = kpi_df[
        (kpi_df["attribute_name"] == selected_kpi) &
        (kpi_df["company_name"].isin(selected_companies))
    ].sort_values("true_up_value", ascending=True)

    if filtered.empty:
        st.info(f"No data available for {selected_kpi}")
        return

    st.markdown(f'<div class="section-header">{selected_kpi} — Latest Quarter by Company</div>',
                unsafe_allow_html=True)

    # Horizontal bar chart
    flags_df = load_flags()[["company_name", "overall_flag"]]
    merged   = filtered.merge(flags_df, on="company_name", how="left")
    merged["flag_color"] = merged["overall_flag"].map(
        {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}
    ).fillna(SLATE)

    fig = go.Figure(go.Bar(
        x=merged["true_up_value"],
        y=merged["company_name"],
        orientation="h",
        marker_color=merged["flag_color"].tolist(),
        text=merged["true_up_value"].apply(
            lambda x: f"{x:.1f}%" if abs(x) < 10 else f"{x:,.1f}"
        ),
        textposition="outside",
    ))
    fig.update_layout(
        height=max(300, len(merged) * 35),
        plot_bgcolor="white", paper_bgcolor="white",
        margin=dict(l=0, r=60, t=10, b=0),
        font=dict(family="Arial", color=NAVY, size=11),
        xaxis=dict(gridcolor=BORDER),
        yaxis=dict(tickfont=dict(size=11)),
    )
    st.plotly_chart(fig, use_container_width=True)

    # KPI trend over time for selected companies
    st.markdown(f'<div class="section-header">{selected_kpi} — Quarterly Trend</div>',
                unsafe_allow_html=True)

    # Pull time series from quarterly view
    quarterly_all = pd.DataFrame()
    for company in selected_companies[:6]:  # Limit to 6 for readability
        try:
            q = load_quarterly(company)
            # Try to find this KPI in the quarterly data
            # KPIs are stored as separate attributes; check if column exists
            kpi_col_map = {
                "Revenue (Global)":          "revenue",
                "EBITDA (Global)":           "ebitda_global",
                "Adj. EBITDA (Global)":      "adj_ebitda_global",
                "Total Debt / EBITDA (Global)": "net_leverage",
                "Gross Margin (Global)":     "gross_margin_global",
                "EBITDA / (Interest+Principal)": "interest_coverage",
            }
            col = kpi_col_map.get(selected_kpi)
            if col and col in q.columns:
                sub = q[["period_label", "cash_flow_date", col]].dropna()
                sub["company_name"] = company
                sub = sub.rename(columns={col: "value"})
                quarterly_all = pd.concat([quarterly_all, sub])
        except Exception:
            pass

    if not quarterly_all.empty:
        quarterly_all = quarterly_all.sort_values("cash_flow_date")
        fig2 = px.line(
            quarterly_all, x="period_label", y="value",
            color="company_name",
            color_discrete_sequence=[NAVY, SLATE, SKY, XANTHOUS, CELADON, SEA_GREEN],
            markers=True,
            labels={"period_label": "", "value": selected_kpi, "company_name": "Company"},
        )
        fig2.update_layout(
            height=320, plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(family="Arial", color=NAVY, size=10),
            legend=dict(orientation="h", y=-0.2),
            xaxis=dict(tickangle=-45),
            yaxis=dict(gridcolor=BORDER),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Full KPI heatmap — all KPIs x all companies (latest values)
    st.markdown('<div class="section-header">Full KPI Scorecard — All Companies</div>',
                unsafe_allow_html=True)

    pivot = kpi_df[kpi_df["company_name"].isin(selected_companies)].pivot_table(
        index="attribute_name", columns="company_name", values="true_up_value", aggfunc="last"
    )

    if not pivot.empty:
        # Format values
        display_pivot = pivot.copy()
        for col in display_pivot.columns:
            display_pivot[col] = display_pivot[col].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) and abs(x) < 10
                else f"{x:,.1f}" if pd.notna(x)
                else "—"
            )
        st.dataframe(display_pivot, use_container_width=True, height=400)


# ---------------------------------------------------------------------------
# Company News Section (used inside Company Detail)
# ---------------------------------------------------------------------------

def render_news_section(company_name: str):
    st.markdown(f'<div class="section-header">Recent News — {company_name}</div>',
                unsafe_allow_html=True)

    try:
        news_df = load_news(company_name)
    except Exception:
        st.info("News table not yet created. Run news_schema.sql and then news_pipeline.py.")
        return

    if news_df.empty:
        st.info(f"No recent news found for {company_name}. Run news_pipeline.py to fetch articles.")
        return

    for _, row in news_df.iterrows():
        pub = str(row.get("published", ""))[:10]
        title   = row.get("title", "")
        summary = row.get("summary", "")
        link    = row.get("link", "")
        source  = row.get("source", "")

        st.markdown(f"""
        <div style="background:white; border:1px solid {BORDER}; border-left:3px solid {SLATE};
                    border-radius:4px; padding:10px 14px; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:start;">
                <a href="{link}" target="_blank"
                   style="font-size:13px; font-weight:600; color:{NAVY};
                          font-family:Arial; text-decoration:none;">
                    {title}
                </a>
                <span style="font-size:10px; color:{SLATE}; font-family:Arial;
                             white-space:nowrap; margin-left:12px;">{pub}</span>
            </div>
            <div style="font-size:11px; color:{SLATE}; font-family:Arial; margin-top:4px;">
                {source} {"— " + summary[:150] + "..." if summary else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Income Statement Drill-Down (Company Detail)
# ---------------------------------------------------------------------------

def render_income_statement(company_name: str):
    st.markdown('<div class="section-header">Income Statement — LTM vs Prior Year</div>',
                unsafe_allow_html=True)

    df = load_income_statement_ltm(company_name)

    if df.empty:
        st.info("No income statement data available for this company.")
        return

    # Display by tag group
    for tag in IS_TAG_ORDER:
        tag_df = df[df["tag"] == tag].copy()
        if tag_df.empty:
            continue

        with st.expander(f"**{tag}**", expanded=(tag == "Income Statement")):
            rows = []
            for _, row in tag_df.iterrows():
                ltm = row["ltm_value"]
                py  = row["py_value"]
                delta = row["delta"]
                delta_pct = row["delta_pct"]

                # Flag delta
                if delta_pct is not None:
                    if delta_pct > 0.10:
                        flag = "🟢"
                    elif delta_pct > 0:
                        flag = "🟡"
                    elif delta_pct > -0.10:
                        flag = "🟡"
                    else:
                        flag = "🔴"
                else:
                    flag = "⚪"

                rows.append({
                    "Line Item":    row["attribute_name"],
                    "LTM ($M)":     f"{ltm:,.1f}" if ltm is not None else "—",
                    "PY ($M)":      f"{py:,.1f}"  if py  is not None else "—",
                    "Δ $M":         f"{delta:+,.1f}" if delta is not None else "—",
                    "Δ %":          f"{delta_pct*100:+.1f}%" if delta_pct is not None else "—",
                    "Flag":         flag,
                })

            display_df = pd.DataFrame(rows)
            st.dataframe(display_df.set_index("Line Item"),
                         use_container_width=True,
                         height=min(400, len(rows) * 38 + 40))


# ---------------------------------------------------------------------------
# Enhanced Company Detail Page
# ---------------------------------------------------------------------------

def page_company_detail_enhanced():
    from ui import render_page_header
    render_page_header("Company Detail")

    companies  = get_company_list()
    # Pre-select from session state (set by "View Detail" button on Portfolio Overview)
    default_company = st.session_state.get("selected_company", companies[0] if companies else None)
    default_idx     = companies.index(default_company) if default_company in companies else 0
    selected   = st.selectbox("Select Company", companies,
                               index=default_idx, label_visibility="collapsed")
    # Update session state so it persists
    st.session_state["selected_company"] = selected

    if not selected:
        return

    flags        = load_flags()
    company_flag = flags[flags["company_name"] == selected]
    flag_row     = company_flag.iloc[0] if len(company_flag) > 0 else None
    master       = load_company_master()
    company_info = master[master["company_name"] == selected]
    info_row     = company_info.iloc[0] if len(company_info) > 0 else None

    # Company header card
    if flag_row is not None:
        overall = flag_row.get("overall_flag", "")
        sector  = info_row.get("client_sector", "") if info_row is not None else ""
        inv_date = str(info_row.get("investment_date", ""))[:10] if info_row is not None else ""
        security = info_row.get("security_type", "") if info_row is not None else ""
        ownership = info_row.get("ownership_structure", "") if info_row is not None else ""
        geo      = info_row.get("geography", "") if info_row is not None else ""
        hq       = info_row.get("headquarters", "") if info_row is not None else ""

        st.markdown(f"""
        <div style="background:white; border:1px solid {BORDER}; border-radius:6px;
                    padding:16px 20px; margin-bottom:16px;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="background:{NAVY}; color:white; padding:10px 16px;
                                border-radius:4px; font-weight:700; font-family:Arial; font-size:18px;">
                        {selected[:2].upper()}
                    </div>
                    <div>
                        <div style="font-size:22px; font-weight:700; color:{NAVY}; font-family:Arial;">
                            {selected}
                        </div>
                        <div style="font-size:12px; color:{SLATE}; font-family:Arial; margin-top:2px;">
                            {sector} · {geo[:25] if geo else ""} · Entry {inv_date}
                            &nbsp;|&nbsp; {security} &nbsp;|&nbsp; {ownership}
                            &nbsp;|&nbsp; HQ: {hq}
                        </div>
                    </div>
                </div>
                <div>{flag_badge(overall)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # KPI strip
        kpi_cols = st.columns(7)
        kpis = [
            (format_millions(flag_row.get("ltm_revenue")),        "LTM Revenue"),
            (format_millions(flag_row.get("ltm_ebitda")),          "LTM EBITDA"),
            (format_pct(flag_row.get("ltm_adj_ebitda_margin")),    "EBITDA Margin"),
            (format_pct(flag_row.get("ltm_gross_margin")),         "Gross Margin"),
            (format_multiple(flag_row.get("net_leverage")),         "Net Leverage"),
            (format_pct(flag_row.get("revenue_yoy")),               "Rev Growth YoY"),
            (format_pct(flag_row.get("ebitda_yoy")),                "EBITDA Growth YoY"),
        ]
        for col, (val, label) in zip(kpi_cols, kpis):
            col.markdown(kpi_card(val, label), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Sub-tabs within company detail
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Financials", "📋 Income Statement", "🚦 Credit Flags", "📰 News", "🤖 AI Analyst", "ℹ️ Overview"
    ])

    with tab1:
        quarterly = load_quarterly(selected)
        if not quarterly.empty:
            # Revenue & EBITDA trend
            st.markdown('<div class="section-header">Revenue & EBITDA Trend</div>',
                        unsafe_allow_html=True)
            from plotly.subplots import make_subplots
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            rev = quarterly["revenue"].combine_first(quarterly["net_sales"])
            fig.add_trace(go.Bar(x=quarterly["period_label"], y=rev,
                                  name="Revenue ($M)", marker_color=NAVY, opacity=0.8),
                          secondary_y=False)
            fig.add_trace(go.Bar(x=quarterly["period_label"], y=quarterly["adj_ebitda"],
                                  name="Adj. EBITDA ($M)", marker_color=SLATE, opacity=0.8),
                          secondary_y=False)
            margin = quarterly["adj_ebitda"] / rev.replace(0, float("nan"))
            fig.add_trace(go.Scatter(x=quarterly["period_label"], y=margin,
                                      name="EBITDA Margin %", mode="lines+markers",
                                      line=dict(color=XANTHOUS, width=2)),
                          secondary_y=True)
            fig.update_layout(height=300, plot_bgcolor="white", paper_bgcolor="white",
                               margin=dict(l=0,r=0,t=10,b=0), barmode="group",
                               legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
                               font=dict(family="Arial", color=NAVY, size=10))
            fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False)
            fig.update_yaxes(tickformat=".0%", secondary_y=True)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            # Leverage and Margin side by side
            col_lev, col_mgn = st.columns(2)
            with col_lev:
                st.markdown('<div class="section-header">Net Leverage</div>',
                            unsafe_allow_html=True)
                lev_df = quarterly.dropna(subset=["net_leverage"])
                if not lev_df.empty:
                    fig3 = go.Figure()
                    fig3.add_hline(y=6.0, line_dash="dash", line_color=RED_FLAG,
                                   annotation_text="6.0x Covenant")
                    fig3.add_hline(y=5.0, line_dash="dot", line_color=XANTHOUS,
                                   annotation_text="5.0x Watch")
                    fig3.add_trace(go.Bar(
                        x=lev_df["period_label"], y=lev_df["net_leverage"],
                        marker_color=[RED_FLAG if v > 6 else XANTHOUS if v > 5 else NAVY
                                      for v in lev_df["net_leverage"]]
                    ))
                    fig3.update_layout(height=240, plot_bgcolor="white",
                                        paper_bgcolor="white",
                                        margin=dict(l=0,r=0,t=10,b=0),
                                        font=dict(family="Arial", color=NAVY, size=10),
                                        yaxis=dict(gridcolor=BORDER))
                    fig3.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig3, use_container_width=True)

            with col_mgn:
                st.markdown('<div class="section-header">EBITDA Margin %</div>',
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
                        fill="tozeroy", fillcolor="rgba(63,102,128,0.1)"
                    ))
                    fig4.update_layout(height=240, plot_bgcolor="white",
                                        paper_bgcolor="white",
                                        margin=dict(l=0,r=0,t=10,b=0),
                                        font=dict(family="Arial", color=NAVY, size=10),
                                        yaxis=dict(tickformat=".0%", gridcolor=BORDER))
                    fig4.update_xaxes(tickangle=-45)
                    st.plotly_chart(fig4, use_container_width=True)

    with tab2:
        render_income_statement(selected)

    with tab3:
        st.markdown('<div class="section-header">Credit & Performance Flag Scorecard</div>',
                    unsafe_allow_html=True)
        try:
            from page_portfolio_flags import render_company_scorecard, load_portfolio_flags
            flags_df = load_portfolio_flags()
            company_row = flags_df[flags_df["company_name"] == selected]
            if not company_row.empty:
                render_company_scorecard(company_row.iloc[0])
            else:
                st.info("Run vw_portfolio_flags.sql in SSMS to enable credit flags.")
        except Exception as exc:
            st.info(f"Credit flags not available: {exc}")

    with tab4:
        render_news_section(selected)

    with tab5:
        st.markdown('<div class="section-header">AI Analyst</div>',
                    unsafe_allow_html=True)

        chat_key = f"chat_v2_{selected}"
        if chat_key not in st.session_state:
            st.session_state[chat_key] = []

        context = build_company_context_with_news(selected)

        prompts = [
            f"Summarize {selected}'s performance in 3 bullet points",
            f"What are the key risks for {selected}?",
            f"Write a board memo update for {selected}",
            f"How does recent news affect the outlook for {selected}?",
        ]
        cols = st.columns(4)
        for col, prompt in zip(cols, prompts):
            if col.button(prompt, key=f"v2_prompt_{prompt[:20]}", use_container_width=True):
                st.session_state[chat_key].append({"role": "user", "content": prompt})
                with st.spinner("Analysing..."):
                    response = ask_claude(prompt, context, st.session_state[chat_key][:-1])
                st.session_state[chat_key].append({"role": "assistant", "content": response})

        for msg in st.session_state[chat_key]:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">{msg["content"]}</div>',
                            unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-assistant">{msg["content"]}</div>',
                            unsafe_allow_html=True)

        user_input = st.chat_input(f"Ask anything about {selected}...")
        if user_input:
            st.session_state[chat_key].append({"role": "user", "content": user_input})
            with st.spinner("Analysing..."):
                response = ask_claude(user_input, context, st.session_state[chat_key][:-1])
            st.session_state[chat_key].append({"role": "assistant", "content": response})
            st.rerun()

    with tab6:
        if info_row is not None:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="section-header">Company Profile</div>',
                            unsafe_allow_html=True)
                fields = [
                    ("Sector",           info_row.get("client_sector")),
                    ("Geography",        info_row.get("geography")),
                    ("Investment Date",  str(info_row.get("investment_date",""))[:10]),
                    ("Investment Status",info_row.get("investment_status")),
                    ("Currency",         info_row.get("currency")),
                    ("Fiscal Year End",  info_row.get("fiscal_year_end")),
                    ("Headquarters",     info_row.get("headquarters")),
                    ("Business Model",   info_row.get("business_model")),
                    ("Product/Service",  info_row.get("product_or_service")),
                    ("Website",          info_row.get("website")),
                ]
                for label, val in fields:
                    if val and str(val) not in ("None", "nan", ""):
                        st.markdown(f"**{label}:** {val}")
            with c2:
                st.markdown('<div class="section-header">Governance</div>',
                            unsafe_allow_html=True)
                gov_fields = [
                    ("Security Type",    info_row.get("security_type")),
                    ("Ownership",        info_row.get("ownership_structure")),
                    ("Board Seats",      info_row.get("board_seats")),
                    ("Cov-Lite",         info_row.get("cov_lite")),
                    ("Covenant Details", info_row.get("cov_lite_description")),
                    ("Funds",            info_row.get("funds")),
                    ("Restricted List",  info_row.get("restricted_list")),
                    ("Info Rights",      info_row.get("information_rights")),
                    ("Exit Type",        info_row.get("exit_type")),
                    ("Valuation Method", info_row.get("valuation_methodology")),
                ]
                for label, val in gov_fields:
                    if val and str(val) not in ("None", "nan", ""):
                        st.markdown(f"**{label}:** {val}")
