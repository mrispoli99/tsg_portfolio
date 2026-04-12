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
        import pandas as _pd2
        quarterly_all["cash_flow_date"] = _pd2.to_datetime(quarterly_all["cash_flow_date"], errors="coerce")
        _q_cutoff = _pd2.Timestamp.now() - _pd2.DateOffset(years=3)
        quarterly_all = quarterly_all[quarterly_all["cash_flow_date"] >= _q_cutoff]
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
    except Exception as exc:
        st.info(f"News not available: {exc}")
        return

    if news_df is None or (hasattr(news_df, "empty") and news_df.empty):
        st.info(f"No recent news found for {company_name}.")
        st.caption("To enable news: run news_pipeline.py on your VM, "
                   "then re-export CSVs with export_to_csv.py.")
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

# Flag threshold explanations for Income Statement hover tooltips
IS_FLAG_RULES = {
    "Revenue":      ("🟢 >10% YoY growth", "🟡 0–10% growth", "🔴 Negative growth"),
    "EBITDA":       ("🟢 >10% YoY growth", "🟡 0–10% growth", "🔴 Declining"),
    "Gross Profit": ("🟢 >10% YoY growth", "🟡 0–10% growth", "🔴 Declining"),
    "default":      ("🟢 Improved >10%",   "🟡 Changed 0–10%", "🔴 Declined >10%"),
}


def _is_flag(delta_pct, attr_name: str) -> tuple:
    """Return (emoji, explanation) for an IS line item delta."""
    if delta_pct is None:
        return "⚪", "Insufficient data for comparison"
    rules = IS_FLAG_RULES.get(attr_name, IS_FLAG_RULES["default"])
    if delta_pct > 0.10:
        return "🟢", rules[0]
    elif delta_pct >= 0:
        return "🟡", rules[1]
    elif delta_pct >= -0.10:
        return "🟡", rules[2]
    else:
        return "🔴", rules[2]


def render_income_statement(company_name: str, compare_mode: str = "Prior Year"):
    label_map = {"Prior Year": "Prior Year", "Prior Quarter": "Prior Quarter"}
    cmp_label = label_map.get(compare_mode, "Prior Year")
    st.markdown(f'<div class="section-header">Income Statement — LTM vs {cmp_label}</div>',
                unsafe_allow_html=True)

    df = load_income_statement_ltm(company_name)

    if df.empty:
        st.info("No income statement data available for this company.")
        return

    # For Prior Quarter mode — shift comparison columns if available
    if compare_mode == "Prior Quarter" and "py_value" in df.columns:
        # Use quarterly data for QoQ comparison if possible
        try:
            qdf = load_quarterly(company_name)
            if not qdf.empty:
                qdf = qdf.sort_values("cash_flow_date")
                # Map attribute names to quarterly columns
                col_map = {
                    "Revenue": "revenue", "Net Sales": "revenue",
                    "Adj. EBITDA": "adj_ebitda", "Gross Profit": "gross_profit",
                    "Net Leverage": "net_leverage",
                }
                latest  = qdf.iloc[-1]
                prior_q = qdf.iloc[-2] if len(qdf) >= 2 else None
                for attr, qcol in col_map.items():
                    if prior_q is not None and qcol in qdf.columns:
                        mask = df["attribute_name"].str.contains(attr, case=False, na=False)
                        if mask.any():
                            pq_val = prior_q[qcol]
                            df.loc[mask, "py_value"] = pq_val
                            df.loc[mask, "delta"]    = df.loc[mask, "ltm_value"] - pq_val
                            df.loc[mask, "delta_pct"] = (
                                df.loc[mask, "delta"] / pq_val if pq_val else None)
        except Exception:
            pass  # Fall back to prior year data

    st.caption(f"Flags compare LTM vs {cmp_label}. 🟢 Improved >10% · 🟡 Changed 0–10% · 🔴 Declined >10%")

    for tag in IS_TAG_ORDER:
        tag_df = df[df["tag"] == tag].copy()
        if tag_df.empty:
            continue

        with st.expander(f"**{tag}**", expanded=(tag == "Income Statement")):
            rows = []
            tooltips = []
            for _, row in tag_df.iterrows():
                ltm       = row["ltm_value"]
                py        = row["py_value"]
                delta     = row["delta"]
                delta_pct = row["delta_pct"]
                attr      = str(row["attribute_name"])

                flag_emoji_str, flag_explanation = _is_flag(delta_pct, attr)
                tooltips.append(flag_explanation)

                rows.append({
                    "Line Item": attr,
                    "LTM ($M)":  f"{ltm:,.1f}" if ltm is not None else "—",
                    "PY ($M)":   f"{py:,.1f}"  if py  is not None else "—",
                    "Δ $M":      f"{delta:+,.1f}" if delta is not None else "—",
                    "Δ %":       f"{delta_pct*100:+.1f}%" if delta_pct is not None else "—",
                    "Flag":      flag_emoji_str,
                    "Flag Meaning": flag_explanation,
                })

            display_df = pd.DataFrame(rows)

            def color_flag_is(val):
                if "🟢" in str(val): return f"color: {SEA_GREEN}; font-weight: 700"
                if "🟡" in str(val): return f"color: #B7860B; font-weight: 700"
                if "🔴" in str(val): return f"color: {RED_FLAG}; font-weight: 700"
                return ""

            styled = (display_df.set_index("Line Item")
                                 .style.map(color_flag_is, subset=["Flag"]))
            st.dataframe(styled, use_container_width=True,
                         height=min(450, len(rows) * 38 + 40))


# ---------------------------------------------------------------------------
# Enhanced Company Detail Page
# ---------------------------------------------------------------------------

def page_company_detail_enhanced():
    from ui import render_page_header
    render_page_header("Company Detail")

    companies = get_company_list()
    if not companies:
        st.info("No company data available.")
        return

    # Pre-select from session state (set by "View Detail" button on Portfolio Overview)
    # Important: read once and don't overwrite on every render — only update when
    # the selectbox itself changes, not on every rerun
    default_company = st.session_state.get("selected_company", companies[0])
    if default_company not in companies:
        default_company = companies[0]
    default_idx = companies.index(default_company)

    selected = st.selectbox(
        "Select Company", companies,
        index=default_idx,
        label_visibility="collapsed",
        key="company_detail_select"
    )

    # Only update session state when user explicitly changes the selectbox
    if selected != st.session_state.get("selected_company"):
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

        # KPI strip — plain tiles for absolute metrics, colored flag cards for flagged metrics
        abs_cols = st.columns(4)
        abs_kpis = [
            (format_millions(flag_row.get("ltm_revenue")),     "LTM Revenue"),
            (format_millions(flag_row.get("ltm_adj_ebitda")),  "LTM EBITDA"),
            (format_pct(flag_row.get("ltm_gross_margin")),     "Gross Margin"),
            (format_multiple(flag_row.get("net_leverage")),    "Net Leverage"),
        ]
        for col, (val, label) in zip(abs_cols, abs_kpis):
            col.markdown(kpi_card(val, label), unsafe_allow_html=True)

        # Colored flag cards for the 4 flagged metrics
        FLAG_CARD_DEFS = [
            ("revenue_growth_flag",    "revenue_yoy",           "Rev Growth YoY",  format_pct,
             "Green >10% · Yellow 0–10% · Red <0%",   "(LTM Rev − PY Rev) / PY Rev"),
            ("ebitda_margin_flag",     "ltm_adj_ebitda_margin", "EBITDA Margin",   format_pct,
             "Green >18% · Yellow 10–18% · Red <10%", "LTM Adj. EBITDA / LTM Net Sales"),
            ("net_leverage_flag",      "net_leverage",          "Net Leverage",    format_multiple,
             "Green <5x · Yellow 5–6x · Red >6x",     "Net Debt / LTM Credit Agreement EBITDA"),
            ("interest_coverage_flag", "interest_coverage",     "Int. Coverage",   format_multiple,
             "Green >3x · Yellow 2–3x · Red <2x",     "LTM Adj. EBITDA / LTM Cash Interest"),
        ]
        flag_card_cols = st.columns(4)
        for col, (fk, vk, lbl, fmt, thresh, calc) in zip(flag_card_cols, FLAG_CARD_DEFS):
            fval    = str(flag_row.get(fk, "") or "")
            val     = flag_row.get(vk)
            fclr    = {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}.get(fval, SLATE)
            val_str = fmt(val) if val is not None and not pd.isna(val) else "—"
            tip     = f"{lbl}\nCalc: {calc}\nThresholds: {thresh}"
            col.markdown(
                f'<div title="{tip}" style="background:white;border:1px solid {BORDER};' 
                f'border-left:4px solid {fclr};border-radius:4px;padding:8px 10px;cursor:help;">' 
                f'<div style="font-size:18px;font-weight:700;color:{fclr};font-family:Arial;">{val_str}</div>' 
                f'<div style="font-size:10px;color:{SLATE};font-family:Arial;margin-top:2px;">{lbl}</div>' 
                f'<div style="font-size:9px;color:{fclr};font-family:Arial;font-weight:600;">' 
                f'{flag_emoji(fval)} {fval}</div>' 
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Sub-tabs within company detail
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Company Overview",
        "Company-Specific Analysis",
        "Valuation",
        "KPI Metric Alerts",
        "Macro & News",
        "General Information",
    ])

    with tab1:
        quarterly = load_quarterly(selected)
        # Limit to most recent 3 years
        if not quarterly.empty and "cash_flow_date" in quarterly.columns:
            import pandas as _pd
            quarterly = quarterly.copy()
            quarterly["cash_flow_date"] = _pd.to_datetime(quarterly["cash_flow_date"], errors="coerce")
            _cutoff = _pd.Timestamp.now() - _pd.DateOffset(years=3)
            quarterly = quarterly[quarterly["cash_flow_date"] >= _cutoff]
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

        # ----------------------------------------------------------------
        # KPI SUMMARY TABLE — KPIs as rows, periods as columns
        # with Δ% change column per period, for this company only
        # ----------------------------------------------------------------
        st.markdown("<hr style='border:1px solid #E0E4EA;margin:28px 0 16px 0;'>",
                    unsafe_allow_html=True)
        st.markdown('<div class="section-header">KPI Summary — Period View</div>',
                    unsafe_allow_html=True)

        # Reload full quarterly (not 3yr-filtered) for period label building
        q_all_co = load_quarterly(selected)
        if not q_all_co.empty and "cash_flow_date" in q_all_co.columns:
            import pandas as _pd2
            q_all_co = q_all_co.copy()
            q_all_co["cash_flow_date"] = _pd2.to_datetime(q_all_co["cash_flow_date"], errors="coerce")
            _co_cutoff = _pd2.Timestamp.now() - _pd2.DateOffset(years=3)
            q_all_co = q_all_co[q_all_co["cash_flow_date"] >= _co_cutoff]

        # Period mode selector — sits above this section only
        _pm_col, _ = st.columns([2, 5])
        with _pm_col:
            co_period_mode = st.radio(
                "Period",
                ["Quarterly", "Monthly", "Yearly"],
                horizontal=True,
                key=f"co_period_mode_{selected}",
                label_visibility="visible"
            )

        if not q_all_co.empty:
            # Filter to the correct period type FIRST — critical to avoid mixing
            # quarterly, monthly, and annual rows (which share the same columns but
            # have different magnitudes for non-LTM fields).
            if "period" in q_all_co.columns:
                _period_type_map = {"Quarterly": "Quarterly", "Monthly": "Monthly", "Yearly": "Annual"}
                q_all_co = q_all_co[q_all_co["period"] == _period_type_map.get(co_period_mode, "Quarterly")]

            # Build period label per mode
            if co_period_mode == "Monthly":
                q_all_co["_plabel"] = q_all_co["cash_flow_date"].dt.strftime("%b %Y")
            elif co_period_mode == "Yearly":
                q_all_co["_plabel"] = q_all_co["cash_flow_date"].dt.year.astype(str)
            else:
                q_all_co["_plabel"] = (q_all_co["period_label"]
                                       if "period_label" in q_all_co.columns
                                       else q_all_co["cash_flow_date"].dt.to_period("Q").astype(str))

            # Sorted unique period labels
            all_co_periods = (q_all_co.sort_values("cash_flow_date")["_plabel"]
                              .drop_duplicates().tolist())

            # KPI definitions for this table
            # (display_label, column, format_fn, is_pct, threshold_fn)
            # threshold_fn: given value, returns "Red"|"Yellow"|"Green"|None
            CO_KPI_DEFS = [
                ("LTM Revenue ($M)",       "ltm_revenue",               format_millions, False,
                    None),
                ("LTM Adj. EBITDA ($M)",   "ltm_adj_ebitda",            format_millions, False,
                    None),
                ("EBITDA Margin %",         "ltm_adj_ebitda_margin_pct", format_pct,      True,
                    lambda v: "Green" if v > 0.18 else "Yellow" if v > 0.10 else "Red"),
                ("Gross Profit ($M)",       "ltm_gross_profit",          format_millions, False,
                    None),
                ("Gross Margin %",          "ltm_gross_margin_pct",      format_pct,      True,
                    None),
                ("Net Leverage",            "net_leverage",          format_multiple, False,
                    lambda v: "Green" if v < 5 else "Yellow" if v < 6 else "Red"),
                ("Interest Coverage",       "interest_coverage",     format_multiple, False,
                    lambda v: "Green" if v > 3 else "Yellow" if v > 2 else "Red"),
                ("Debt Svc Coverage",       "debt_service_coverage", format_multiple, False,
                    lambda v: "Green" if v > 2.5 else "Yellow" if v > 1.2 else "Red"),
                ("Net Debt ($M)",           "net_debt",              format_millions, False,
                    None),
                ("Total Gross Debt ($M)",   "total_gross_debt",      format_millions, False,
                    None),
                ("Free Cash Flow ($M)",     "free_cash_flow",        format_millions, False,
                    lambda v: "Green" if v > 0 else "Red"),
                ("LTM Capex ($M)",          "capex",                 format_millions, False,
                    None),
            ]

            # Active KPI state (drives the chart below)
            _kpi_key = f"co_active_kpi_{selected}"
            if _kpi_key not in st.session_state:
                st.session_state[_kpi_key] = CO_KPI_DEFS[0][0]
            active_co_kpi = st.session_state[_kpi_key]

            # Build pivot: rows = KPIs, cols = periods + Δ%
            # The CSV already contains pre-calculated LTM figures.
            # For each period, take the most recent row (latest cash_flow_date)
            # — this handles multiple rows in the same period correctly.
            pivot_rows = []
            raw_vals   = {}

            for lbl, col, fmt, is_pct, thresh_fn in CO_KPI_DEFS:
                if col not in q_all_co.columns:
                    continue
                row = {"KPI": lbl}
                raw_vals[lbl] = {}
                prev_val = None

                for p in all_co_periods:
                    sub = q_all_co[q_all_co["_plabel"] == p]
                    if sub.empty:
                        val = None
                    else:
                        # Most recent LTM value within the period
                        v = sub.sort_values("cash_flow_date").iloc[-1][col]
                        val = None if pd.isna(v) else float(v)

                    raw_vals[lbl][p] = val
                    row[p] = fmt(val) if val is not None else "—"

                    # Δ% vs prior period
                    if prev_val is not None and val is not None and prev_val != 0:
                        chg = (val - prev_val) / abs(prev_val)
                        row[f"Δ {p}"] = f"{chg*100:+.1f}%"
                    else:
                        row[f"Δ {p}"] = "—"
                    prev_val = val

                pivot_rows.append(row)

            if pivot_rows:
                pivot_df = pd.DataFrame(pivot_rows).set_index("KPI")
                delta_cols = [c for c in pivot_df.columns if c.startswith("Δ ")]

                def _co_style(row):
                    """Colour Δ columns and highlight the active KPI row."""
                    styles = []
                    for col_name in row.index:
                        is_active = (row.name == active_co_kpi)
                        if is_active:
                            bg  = "background-color:#071733;"
                            fw  = "font-weight:700;"
                            clr = "color:#FFFFFF;"
                        else:
                            bg  = ""
                            fw  = ""
                            clr = ""
                        if not is_active and col_name.startswith("Δ "):
                            s = str(row[col_name])
                            if s.startswith("+"): clr = f"color:{SEA_GREEN};"
                            elif s.startswith("-"): clr = f"color:{RED_FLAG};"
                        styles.append(bg + fw + clr)
                    return styles

                try:
                    styled_co = pivot_df.style.apply(_co_style, axis=1)
                except Exception:
                    styled_co = pivot_df.style

                st.dataframe(styled_co, use_container_width=True,
                             height=min(550, len(pivot_rows) * 38 + 50))
                st.caption(f"KPIs for **{selected}** · {co_period_mode} periods · "
                           f"Δ% = change vs prior period · click a row to select metric")

                # ----------------------------------------------------------------
                # METRIC SELECTOR — buttons to pick which KPI drives the chart
                # ----------------------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-header">Select Metric for Chart Below</div>',
                            unsafe_allow_html=True)

                # Inject CSS so active button is navy + white text, inactive is
                # white + navy text with a border — both always clearly readable.
                st.markdown("""
                <style>
                .kpi-btn-active > div > button {
                    background-color: #071733 !important;
                    color: #FFFFFF !important;
                    border: 2px solid #071733 !important;
                    font-weight: 700 !important;
                    border-radius: 6px !important;
                }
                .kpi-btn-inactive > div > button {
                    background-color: #FFFFFF !important;
                    color: #071733 !important;
                    border: 1px solid #CBD3DE !important;
                    font-weight: 400 !important;
                    border-radius: 6px !important;
                }
                .kpi-btn-inactive > div > button:hover {
                    background-color: #F4F6F9 !important;
                    border-color: #071733 !important;
                }
                </style>
                """, unsafe_allow_html=True)

                kpi_names_avail = [r["KPI"] for r in pivot_rows]
                btn_cols = st.columns(min(len(kpi_names_avail), 4))
                for i, kpi_lbl in enumerate(kpi_names_avail):
                    is_active_btn = (kpi_lbl == active_co_kpi)
                    css_class = "kpi-btn-active" if is_active_btn else "kpi-btn-inactive"
                    with btn_cols[i % 4]:
                        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
                        if st.button(kpi_lbl,
                                     key=f"co_kpi_btn_{selected}_{kpi_lbl}",
                                     use_container_width=True):
                            st.session_state[_kpi_key] = kpi_lbl
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                # ----------------------------------------------------------------
                # PERIOD-OVER-PERIOD CHART — for the selected KPI, this company only
                # ----------------------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f'<div class="section-header">{active_co_kpi} — Period-over-Period</div>',
                    unsafe_allow_html=True
                )

                # Find the column and format for the active KPI
                active_def = next(
                    (d for d in CO_KPI_DEFS if d[0] == active_co_kpi), None
                )
                if active_def and active_def[1] in q_all_co.columns:
                    _, a_col, a_fmt, a_is_pct, a_thresh = active_def
                    ts = (q_all_co[["_plabel", "cash_flow_date", a_col]]
                          .dropna(subset=[a_col])
                          .sort_values("cash_flow_date")
                          .copy())

                    if len(ts) >= 2:
                        # Bar = absolute value, line overlay = Δ% change
                        ts["_prev"] = ts[a_col].shift(1)
                        ts["_chg_pct"] = ((ts[a_col] - ts["_prev"]) /
                                          ts["_prev"].abs()).where(
                            ts["_prev"].notna() & (ts["_prev"] != 0))

                        bar_colors = []
                        for v in ts[a_col]:
                            if a_thresh:
                                flag = a_thresh(v)
                                bar_colors.append(
                                    {"Green": SEA_GREEN, "Yellow": XANTHOUS,
                                     "Red": RED_FLAG}.get(flag, NAVY)
                                )
                            else:
                                bar_colors.append(NAVY)

                        from plotly.subplots import make_subplots as _msp2
                        fig_co_kpi = _msp2(specs=[[{"secondary_y": True}]])

                        # Primary axis — absolute values as bars
                        fig_co_kpi.add_trace(
                            go.Bar(
                                x=ts["_plabel"], y=ts[a_col],
                                name=active_co_kpi,
                                marker_color=bar_colors,
                                opacity=0.85,
                            ),
                            secondary_y=False
                        )

                        # Secondary axis — Δ% as line
                        fig_co_kpi.add_trace(
                            go.Scatter(
                                x=ts["_plabel"], y=ts["_chg_pct"],
                                name="Δ% vs Prior",
                                mode="lines+markers",
                                line=dict(color=XANTHOUS, width=2),
                                marker=dict(size=5),
                            ),
                            secondary_y=True
                        )

                        tick_fmt_primary = ".0%" if a_is_pct else "$,.0f"
                        fig_co_kpi.update_layout(
                            height=340,
                            plot_bgcolor="white", paper_bgcolor="white",
                            margin=dict(l=0, r=0, t=10, b=0),
                            font=dict(family="Arial", color=NAVY, size=10),
                            legend=dict(orientation="h", y=-0.22, font=dict(size=10)),
                            xaxis=dict(tickangle=-45, gridcolor=BORDER),
                            barmode="overlay",
                        )
                        fig_co_kpi.update_yaxes(
                            tickformat=tick_fmt_primary,
                            gridcolor=BORDER,
                            secondary_y=False
                        )
                        fig_co_kpi.update_yaxes(
                            tickformat="+.0%",
                            title_text="Δ% vs Prior Period",
                            secondary_y=True,
                            showgrid=False,
                        )
                        st.plotly_chart(fig_co_kpi, use_container_width=True)
                        st.caption(
                            f"Bars = {active_co_kpi} absolute value · "
                            f"Line = period-over-period % change"
                        )
                    else:
                        st.info("Not enough periods to show period-over-period change.")
                else:
                    st.info(f"{active_co_kpi} data not available in quarterly records.")
            else:
                st.info("No KPI data available for this company.")
        else:
            st.info("No quarterly data available for this company.")

    with tab2:
        st.markdown(f"""
        <div style="background:#F8F9FA; border:2px dashed #CCCCCC; border-radius:10px;
                    padding:60px 40px; text-align:center; margin-top:20px;">
            <div style="font-size:28px; margin-bottom:12px;">🔬</div>
            <div style="font-size:18px; font-weight:700; color:#999999; font-family:Arial;
                        margin-bottom:8px;">Company-Specific Analysis — Coming Soon</div>
            <div style="font-size:13px; color:#BBBBBB; font-family:Arial;">
                Deep-dive company analytics and custom analysis views will be available here.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.markdown(f"""
        <div style="background:#F8F9FA; border:2px dashed #CCCCCC; border-radius:10px;
                    padding:60px 40px; text-align:center; margin-top:20px;">
            <div style="font-size:28px; margin-bottom:12px;">📊</div>
            <div style="font-size:18px; font-weight:700; color:#999999; font-family:Arial;
                        margin-bottom:8px;">Valuation — Coming Soon</div>
            <div style="font-size:13px; color:#BBBBBB; font-family:Arial;">
                Company valuation metrics, MOIC, IRR, and comparable analysis will appear here.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-header">Credit & Performance Flag Scorecard</div>',
                    unsafe_allow_html=True)

        # Threshold explanations — shown as hover context
        ALERT_THRESHOLDS = {
            "Net Debt / EBITDA":      ("< 2.0x",  "2.0–4.0x",  "4.0–6.0x",  "> 6.0x",  "Net Debt ÷ LTM Credit Agreement EBITDA"),
            "Gross Debt / EBITDA":    ("< 3.0x",  "3.0–5.0x",  "5.0–7.0x",  "> 7.0x",  "Total Gross Debt ÷ LTM Credit Agreement EBITDA"),
            "Sr. Secured / EBITDA":   ("< 2.0x",  "2.0–3.5x",  "3.5–5.0x",  "> 5.0x",  "Senior Secured Debt ÷ LTM EBITDA"),
            "Interest Coverage":      ("> 4.0x",  "2.5–4.0x",  "1.5–2.5x",  "< 1.5x",  "LTM Adj. EBITDA ÷ LTM Cash Interest Expense"),
            "Debt Service Coverage":  ("> 2.5x",  "1.8–2.5x",  "1.2–1.8x",  "< 1.2x",  "(LTM EBITDA − Capex) ÷ (Interest + Principal)"),
            "Free Cash Flow":         ("Strong+", "Positive",  "0–Slight−", "< 0",     "LTM EBITDA − Capex − ΔNWC − Cash Taxes"),
            "EBITDA Margin":          ("> 30%",   "20–30%",    "10–20%",    "< 10%",   "LTM Adj. EBITDA ÷ LTM Net Sales"),
            "TEV / Revenue":          ("< 1.5x",  "1.5–3.0x",  "3.0–5.0x",  "> 5.0x",  "Total Enterprise Value ÷ LTM Net Sales"),
            "TEV / EBITDA":           ("< 6.0x",  "6.0–10.0x", "10.0–16.0x","> 16.0x", "Total Enterprise Value ÷ LTM EBITDA"),
            "MOIC":                   ("> 2.5x",  "1.5–2.5x",  "1.0–1.5x",  "< 1.0x",  "(Realized + Unrealized Value) ÷ Total Cost"),
            "Cash / Gross Debt":      ("> 20%",   "10–20%",    "5–10%",     "< 5%",    "Cash ÷ Total Gross Debt"),
            "Floating Rate Debt %":   ("< 20%",   "20–50%",    "50–80%",    "> 80%",   "Floating Rate Debt ÷ Total Gross Debt"),
        }

        with st.expander("Flag Thresholds & Calculation Methodology", expanded=True):
            thresh_rows = []
            for metric, (best, green, yellow, red, calc) in ALERT_THRESHOLDS.items():
                thresh_rows.append({
                    "Metric":      metric,
                    "Calculation": calc,
                    "⭐ Best":     best,
                    "🟢 Green":    green,
                    "🟡 Yellow":   yellow,
                    "🔴 Red":      red,
                })
            st.dataframe(pd.DataFrame(thresh_rows).set_index("Metric"),
                         use_container_width=True)

        try:
            from db import load_portfolio_flags
            from page_portfolio_flags import render_company_scorecard
            flags_df    = load_portfolio_flags()
            company_row = flags_df[flags_df["company_name"] == selected]
            if not flags_df.empty and not company_row.empty:
                render_company_scorecard(company_row.iloc[0])
            elif flags_df.empty:
                st.info("portfolio_flags.csv not found. Run export_to_csv.py to generate it.")
            else:
                st.info(f"No flag data found for {selected}.")
        except Exception as exc:
            st.warning(f"Could not load flag scorecard: {exc}")

    with tab5:
        st.markdown('<div class="section-header">Macro & News</div>',
                    unsafe_allow_html=True)

        # CapIQ market comps placeholder
        st.markdown(f"""
        <div style="background:#F8F9FA; border:1px dashed #CCCCCC; border-radius:6px;
                    padding:20px 24px; margin-bottom:16px;">
            <div style="font-size:13px; font-weight:700; color:#999; font-family:Arial;
                        margin-bottom:4px;">📈 Market Comps (CapIQ)</div>
            <div style="font-size:12px; color:#BBBBBB; font-family:Arial;">
                CapIQ market comparables integration coming soon. Public peer multiples,
                sector benchmarks, and trading comps will appear here.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Macro context
        macro_sector = info_row.get("client_sector", "") if info_row is not None else ""
        if macro_sector:
            st.markdown(f"""
            <div style="background:{LIGHT_BG}; border-left:3px solid {SLATE};
                        border-radius:4px; padding:10px 14px; margin-bottom:12px;
                        font-size:12px; color:{NAVY}; font-family:Arial;">
                <b>Sector:</b> {macro_sector} —
                Macro data integration (CapIQ comps, sector benchmarks) coming soon.
            </div>
            """, unsafe_allow_html=True)
        try:
            render_news_section(selected)
        except Exception as exc:
            st.info(f"News not available: {exc}")

    with tab6:
        if info_row is None:
            st.info("Company profile data not available in company_master.csv.")
        elif True:
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
                def fmt_pct_val(v):
                    try: return f"{float(v)*100:.1f}%" if v and str(v) not in ("None","nan","") else None
                    except: return str(v) if v else None

                gov_fields = [
                    ("Security Type",         info_row.get("security_type")),
                    ("Ownership",             info_row.get("ownership_structure")),
                    ("Fund Ownership (Entry)",fmt_pct_val(info_row.get("fund_ownership_entry_pct"))),
                    ("Fund Ownership (Current)",fmt_pct_val(info_row.get("fund_current_ownership_pct"))),
                    ("TSG Controlled (Entry)",fmt_pct_val(info_row.get("tsg_controlled_entry_pct"))),
                    ("Board Seats",           info_row.get("board_seats")),
                    ("Cov-Lite",              info_row.get("cov_lite")),
                    ("Covenant Details",      info_row.get("cov_lite_description")),
                    ("Funds",                 info_row.get("funds")),
                    ("FX to USD (Entry)",     info_row.get("fx_to_usd_entry")),
                    ("FX to USD (Current)",   info_row.get("fx_to_usd_current")),
                    ("Restricted List",       info_row.get("restricted_list")),
                    ("Info Rights",           info_row.get("information_rights")),
                    ("Exit Type",             info_row.get("exit_type")),
                    ("Valuation Method",      info_row.get("valuation_methodology")),
                ]
                for label, val in gov_fields:
                    if val and str(val) not in ("None", "nan", ""):
                        st.markdown(f"**{label}:** {val}")

