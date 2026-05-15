"""
corepower_visuals.py
====================
Three bespoke visual charts for the Core Power Company-Specific Analysis tab:

  1. TTM Adj. EBITDA Since Investment
     — Rolling 12-month Management EBITDA from entry (Apr 2019) to latest,
       plotted as a bar chart at quarterly intervals.
       COVID trough annotated. Entry-case underwriting line overlaid.

  2. Revenue Mix (Stacked Bar)
     — Monthly stacked bar: Yoga (member + non-member) / Retail / Franchise.
       Non-member revenue broken out as a separate segment on top.
       Rolling 12-month window, togglable to show full history since entry.

  3. Studio-Level P&L Waterfall
     — Single selected month: Revenue → minus Labor → minus Occupancy →
       minus Programming → minus Other OpEx → minus Regional OH →
       = Studio Contribution.
       Rendered as a classic waterfall (green=positive, red=cost step, navy=totals).

All functions accept a pre-filtered DataFrame from load_company_kpis_all()
and return nothing — they render directly into Streamlit.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ── Brand colours (match the rest of the app) ────────────────────────────────
NAVY      = "#071733"
SLATE     = "#3F6680"
SKY       = "#A8CFDE"
XANTHOUS  = "#F3B51F"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
BORDER    = "#E0E4EA"
LIGHT_BG  = "#F4F6F9"
CELADON   = "#85D7B0"
PURPLE    = "#7C5CBF"

# Entry date — CorePower investment closed April 2019
ENTRY_DATE = pd.Timestamp("2019-04-01")

# TSG underwriting case Adj. EBITDA targets (from board materials)
# Format: (quarter_end_date, underwriting_value_$M)
UNDERWRITING_TARGETS = [
    (pd.Timestamp("2019-12-31"), 29.0),
    (pd.Timestamp("2020-12-31"), 39.0),   # pre-COVID case
    (pd.Timestamp("2022-12-31"), 47.0),
]


# ---------------------------------------------------------------------------
# Helper: load and roll up monthly Management EBITDA to TTM
# ---------------------------------------------------------------------------

def _load_ttm_ebitda(kpis_df: pd.DataFrame) -> pd.DataFrame:
    """
    From the full company_kpis DataFrame (already filtered to Core Power),
    pull monthly Management EBITDA and compute rolling 12-month (TTM) sum.
    Returns DataFrame with columns: cash_flow_date, monthly_ebitda, ttm_ebitda, label
    """
    sub = (
        kpis_df[
            (kpis_df["attribute_name"] == "Management EBITDA") &
            (kpis_df["period"] == "Monthly")
        ]
        .sort_values("cash_flow_date")
        .copy()
    )
    if sub.empty:
        return pd.DataFrame()

    sub = sub.rename(columns={"true_up_value": "monthly_ebitda"})
    sub["ttm_ebitda"] = sub["monthly_ebitda"].rolling(12, min_periods=12).sum()
    sub["label"] = sub["cash_flow_date"].dt.strftime("%b-%y")
    return sub[["cash_flow_date", "monthly_ebitda", "ttm_ebitda", "label"]]


# ---------------------------------------------------------------------------
# Chart 1 — TTM Management EBITDA Since Investment
# ---------------------------------------------------------------------------

def render_ttm_ebitda_since_investment(kpis_df: pd.DataFrame, period_mode: str = "Quarterly"):
    """
    Bar chart of TTM Management EBITDA at each quarter-end since investment.
    Bars are coloured: red=negative, navy=positive.
    Key annotations: COVID trough, first positive TTM, latest value.
    Optional underwriting case overlay (dashed line).
    """
    st.markdown(
        '<div class="section-header-co">TTM Adj. EBITDA Since Investment</div>',
        unsafe_allow_html=True,
    )

    ttm = _load_ttm_ebitda(kpis_df)
    if ttm.empty:
        st.info("Management EBITDA monthly data not available.")
        return

    # Filter plot points based on period_mode:
    #   Monthly   — every month-end (shows granular TTM progression)
    #   Quarterly — quarter-ends only (Mar/Jun/Sep/Dec)
    #   Annual    — December only (year-end TTM)
    ttm_all = ttm.dropna(subset=["ttm_ebitda"]).copy()
    if period_mode == "Monthly":
        ttm_q = ttm_all.copy()
    elif period_mode == "Annual":
        ttm_q = ttm_all[ttm_all["cash_flow_date"].dt.month == 12].copy()
    else:
        ttm_q = ttm_all[ttm_all["cash_flow_date"].dt.month.isin([3, 6, 9, 12])].copy()

    if ttm_q.empty:
        st.info("Insufficient data to compute TTM EBITDA.")
        return

    # Toggle: full history vs. recent window
    _toggle_key = "cpy_ttm_full_history"
    _full = st.toggle("Show full history since investment", value=True, key=_toggle_key)
    if not _full:
        _window_years = {"Monthly": 2, "Annual": 10, "Quarterly": 3}
        _cutoff = ttm_q["cash_flow_date"].max() - pd.DateOffset(
            years=_window_years.get(period_mode, 3)
        )
        ttm_q = ttm_q[ttm_q["cash_flow_date"] >= _cutoff]

    vals   = ttm_q["ttm_ebitda"].tolist()
    labels = ttm_q["label"].tolist()
    colors = [RED_FLAG if v < 0 else NAVY for v in vals]

    fig = go.Figure()

    # Main bars
    fig.add_trace(go.Bar(
        x=labels, y=vals,
        marker_color=colors,
        opacity=0.88,
        text=[f"${v:.0f}M" for v in vals],
        textposition="outside",
        textfont=dict(size=8, color=NAVY),
        name="TTM Mgmt. EBITDA",
        cliponaxis=False,
    ))

    # Zero line
    fig.add_hline(y=0, line_width=1.5, line_color=SLATE)

    # Key annotations
    _trough_row = ttm_q.loc[ttm_q["ttm_ebitda"].idxmin()]
    _latest_row = ttm_q.iloc[-1]

    # COVID trough
    if _trough_row["ttm_ebitda"] < 0:
        fig.add_annotation(
            x=_trough_row["label"],
            y=_trough_row["ttm_ebitda"],
            text="COVID trough",
            showarrow=True, arrowhead=2, arrowcolor=RED_FLAG,
            font=dict(size=9, color=RED_FLAG),
            bgcolor="white", bordercolor=RED_FLAG, borderwidth=1,
            ay=40, ax=0,
        )

    # First positive quarter (turning point)
    _positive = ttm_q[ttm_q["ttm_ebitda"] > 0]
    if len(_positive) > 0:
        _turn_row = _positive.iloc[0]
        if _turn_row["label"] != _latest_row["label"]:
            fig.add_annotation(
                x=_turn_row["label"],
                y=_turn_row["ttm_ebitda"],
                text="First positive TTM",
                showarrow=True, arrowhead=2, arrowcolor=SEA_GREEN,
                font=dict(size=9, color=SEA_GREEN),
                bgcolor="white", bordercolor=SEA_GREEN, borderwidth=1,
                ay=-36, ax=0,
            )

    # Remove underwriting overlay — no longer shown
    fig.update_layout(
        height=420,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=30, b=40),
        font=dict(family="Arial", color=NAVY, size=10),
        legend=dict(
            orientation="h", y=-0.18, x=0,
            font=dict(size=10), bgcolor="rgba(0,0,0,0)"
        ),
        yaxis=dict(
            title="TTM Mgmt. EBITDA ($M)",
            gridcolor=BORDER,
            zeroline=False,
            tickformat="$,.0f",
        ),
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=9),
            gridcolor=BORDER,
        ),
        bargap=0.25,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    _period_note = {
        "Monthly":   "every month-end",
        "Quarterly": "quarter-ends",
        "Annual":    "year-ends (December)",
    }.get(period_mode, "quarter-ends")
    st.caption(
        f"TTM = trailing twelve months (rolling 12-month sum of monthly Management EBITDA). "
        f"Plotted at {_period_note}."
    )

    # ── Data table below chart ────────────────────────────────────────────────
    # Mirrors the format from Michelle's email:
    #   Row 1: TTM TSG Underwriting Case Adj. EBITDA ($M) — placeholder, always blank
    #   Row 2: TTM Cash Revenue ($M)                      — rolling 12m Member Cash Revenue
    #   Row 3: TTM Adj. EBITDA Margin %                   — rolling 12m Mgmt EBITDA / Revenue
    #   Row 4: Net Debt ($M)                              — from financials_quarterly

    # Build quarterly time series for the table columns (same x-axis as chart)
    _monthly = kpis_df[kpis_df["period"] == "Monthly"].copy()

    # TTM Cash Revenue — rolling 12m sum of Member Cash Revenue
    _mcr = (_monthly[_monthly["attribute_name"] == "Member Cash Revenue"]
            .sort_values("cash_flow_date")
            .set_index("cash_flow_date")["true_up_value"])
    _mcr_ttm = _mcr.rolling(12, min_periods=12).sum()

    # TTM Revenue (for margin calc) — rolling 12m Total Studio Revenue
    _rev = (_monthly[_monthly["attribute_name"] == "Total Studio Revenue"]
            .sort_values("cash_flow_date")
            .set_index("cash_flow_date")["true_up_value"])
    _rev_ttm = _rev.rolling(12, min_periods=12).sum()

    # TTM EBITDA margin — Mgmt EBITDA TTM / Revenue TTM
    _ebitda = (_monthly[_monthly["attribute_name"] == "Management EBITDA"]
               .sort_values("cash_flow_date")
               .set_index("cash_flow_date")["true_up_value"])
    _ebitda_ttm = _ebitda.rolling(12, min_periods=12).sum()
    _margin_ttm = (_ebitda_ttm / _rev_ttm * 100).where(_rev_ttm > 0)

    # Net Debt — from the kpis_df quarterly column (passed via financials_quarterly merge)
    # Use Net Debt (Global) monthly attribute if available
    _nd = (_monthly[_monthly["attribute_name"] == "Net Debt (Global)"]
           .sort_values("cash_flow_date")
           .set_index("cash_flow_date")["true_up_value"])

    def _fmt_m(v):
        """Format as integer $M or blank."""
        try:
            f = float(v)
            if pd.isna(f):
                return ""
            return f"{f:.0f}"
        except Exception:
            return ""

    def _fmt_pct(v):
        try:
            f = float(v)
            if pd.isna(f):
                return ""
            return f"{f:.0f}%"
        except Exception:
            return ""

    # Build table columns based on period_mode
    # TTM bars always show at quarter-ends, but the table columns follow period_mode
    if period_mode == "Monthly":
        # Show last 18 months
        _all_dates = _monthly[_monthly["attribute_name"] == "Management EBITDA"].sort_values("cash_flow_date")["cash_flow_date"]
        _col_dates  = _all_dates.tail(18).tolist()
        _col_labels = [d.strftime("%b-%y") for d in _col_dates]
    elif period_mode == "Annual":
        # Show year-ends since investment
        _col_dates  = [d for d in ttm_q["cash_flow_date"].tolist() if pd.Timestamp(d).month == 12]
        _col_labels = [pd.Timestamp(d).strftime("Dec-%y") for d in _col_dates]
    else:
        # Quarterly (default) — same as the chart x-axis
        _col_labels = ttm_q["label"].tolist()
        _col_dates  = ttm_q["cash_flow_date"].tolist()

    def _nearest(series, date):
        """Get the series value at or before the given date."""
        sub = series[series.index <= date]
        return sub.iloc[-1] if not sub.empty else float("nan")

    _rows = [
        ("TTM TSG Underwriting Case Adj. EBITDA ($M)", [""] * len(_col_dates)),  # always blank
        ("TTM Cash Revenue ($M)",    [_fmt_m(_nearest(_mcr_ttm,    d)) for d in _col_dates]),
        ("TTM Adj. EBITDA Margin %", [_fmt_pct(_nearest(_margin_ttm, d)) for d in _col_dates]),
        ("Net Debt ($M)",            [_fmt_m(_nearest(_nd,          d)) for d in _col_dates]),
    ]

    # Render as a styled HTML table matching the board-deck format
    _header_cells = "".join(
        f'<th style="padding:5px 10px; font-size:10px; font-weight:600; color:{NAVY}; '
        f'text-align:center; border-bottom:2px solid {NAVY}; white-space:nowrap;">{lbl}</th>'
        for lbl in _col_labels
    )
    _table_html = f"""
    <div style="overflow-x:auto; margin-top:4px;">
    <table style="width:100%; border-collapse:collapse; font-family:Arial; font-size:11px;">
        <thead>
            <tr>
                <th style="padding:5px 10px; font-size:10px; font-weight:600; color:{NAVY};
                           text-align:left; border-bottom:2px solid {NAVY}; min-width:240px;">
                </th>
                {_header_cells}
            </tr>
        </thead>
        <tbody>
    """
    for _ri, (_row_label, _row_vals) in enumerate(_rows):
        _bg     = "#F8F9FA" if _ri % 2 == 0 else "white"
        _italic = " font-style:italic; color:#AAAAAA;" if _row_label.startswith("TTM TSG") else ""
        _cells  = "".join(
            f'<td style="padding:5px 10px; text-align:center; border-bottom:1px solid {BORDER};'
            f'color:{SLATE};">{v}</td>'
            for v in _row_vals
        )
        _table_html += (
            f'<tr style="background:{_bg};">'
            f'<td style="padding:5px 10px; font-weight:500; color:{NAVY};{_italic}'
            f'border-bottom:1px solid {BORDER};">{_row_label}</td>'
            f'{_cells}</tr>'
        )
    _table_html += "</tbody></table></div>"
    st.markdown(_table_html, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Chart 2 — Monthly Revenue Mix (Stacked Bar)
# ---------------------------------------------------------------------------

def render_revenue_mix(kpis_df: pd.DataFrame, period_mode: str = "Quarterly"):
    """
    Stacked bar chart breaking revenue into segments.
    period_mode controls whether Monthly, Quarterly, or Annual rows are used.
    """
    st.markdown(
        f'<div class="section-header-co">{period_mode} Revenue Mix</div>',
        unsafe_allow_html=True,
    )

    # Map period_mode to the period tag used in company_kpis.csv
    _period_map = {"Monthly": "Monthly", "Quarterly": "Quarterly", "Annual": "Annual"}
    _period_tag = _period_map.get(period_mode, "Quarterly")
    monthly = kpis_df[kpis_df["period"] == _period_tag].copy()

    _SEGMENTS = [
        ("Yoga",                    "Yoga",                     NAVY,     0.90),
        ("Non-Member Revenue",      "Non-Member Cash Revenue",  SKY,      0.90),
        ("Retail",                  "Retail",                   CELADON,  0.90),
        ("Franchise & Royalties",   "Franchise and Royalties",  XANTHOUS, 0.90),
    ]

    # Build wide pivot: date × segment
    rows = {}
    for label, attr, _, _ in _SEGMENTS:
        sub = monthly[monthly["attribute_name"] == attr].set_index("cash_flow_date")["true_up_value"]
        rows[label] = sub

    wide = pd.DataFrame(rows).sort_index()
    if wide.empty:
        st.info("Revenue mix data not available.")
        return

    # Date range selector
    _min_d = wide.index.min()
    _max_d = wide.index.max()
    _default_start = max(_min_d, _max_d - pd.DateOffset(months=24))

    _rc1, _rc2 = st.columns([3, 4])
    with _rc1:
        _range = st.date_input(
            "Date range",
            value=(_default_start.date(), _max_d.date()),
            min_value=_min_d.date(),
            max_value=_max_d.date(),
            key="cpy_rev_mix_range",
            label_visibility="collapsed",
        )
    if isinstance(_range, (list, tuple)) and len(_range) == 2:
        wide = wide[
            (wide.index >= pd.Timestamp(_range[0])) &
            (wide.index <= pd.Timestamp(_range[1]))
        ]

    if wide.empty:
        st.info("No data in selected range.")
        return

    x_labels = wide.index.strftime("%b-%y").tolist()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    for label, attr, color, opacity in _SEGMENTS:
        if label not in wide.columns:
            continue
        y = wide[label].fillna(0).tolist()
        fig.add_trace(
            go.Bar(
                x=x_labels, y=y,
                name=label,
                marker_color=color,
                opacity=opacity,
            ),
            secondary_y=False,
        )

    # Total Studio Revenue as a line overlay
    total_sub = kpis_df[
        (kpis_df["period"] == _period_tag) &
        (kpis_df["attribute_name"] == "Total Studio Revenue")
    ].set_index("cash_flow_date")["true_up_value"]
    total_sub = total_sub[
        (total_sub.index >= wide.index.min()) &
        (total_sub.index <= wide.index.max())
    ].sort_index()
    if not total_sub.empty:
        fig.add_trace(
            go.Scatter(
                x=total_sub.index.strftime("%b-%y").tolist(),
                y=total_sub.values.tolist(),
                mode="lines+markers",
                name="Total Studio Revenue",
                line=dict(color=SLATE, width=1.5, dash="dot"),
                marker=dict(size=4),
            ),
            secondary_y=True,
        )

    fig.update_layout(
        height=380,
        barmode="stack",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=10, b=40),
        font=dict(family="Arial", color=NAVY, size=10),
        legend=dict(
            orientation="h", y=-0.22, x=0,
            font=dict(size=10), bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(tickangle=-45, tickfont=dict(size=9), gridcolor=BORDER),
        yaxis=dict(title="Revenue ($M)", gridcolor=BORDER, tickformat="$,.0f"),
        yaxis2=dict(title="Total Revenue ($M)", gridcolor=BORDER,
                    tickformat="$,.0f", overlaying="y", side="right",
                    showgrid=False),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(
        "Yoga = member + non-member yoga class revenue (LTM reported). "
        "Non-Member shown separately where available. "
        "Dotted line = Total Studio Revenue cross-check."
    )


# ---------------------------------------------------------------------------
# Chart 3 — Studio-Level P&L Waterfall
# ---------------------------------------------------------------------------

def render_studio_pl_waterfall(kpis_df: pd.DataFrame, period_mode: str = "Quarterly"):
    """
    Waterfall chart for a single selected period showing the studio P&L bridge.
    period_mode controls which period granularity is used.
    """
    _period_map = {"Monthly": "Monthly", "Quarterly": "Quarterly", "Annual": "Annual"}
    _period_tag = _period_map.get(period_mode, "Quarterly")
    monthly = kpis_df[kpis_df["period"] == _period_tag].copy()

    _REQUIRED = [
        "Total Studio Revenue", "Labor", "Occupancy (Cash Rent and NNN)",
        "Programming", "Other OPEX", "Studio Contribution",
    ]
    _OPTIONAL_COSTS = [
        ("Regional OH",     "Regional Overhead"),
        ("Regional Sales",  "Regional Sales Overhead"),
        ("Regional Ops",    "Regional Operating Overhead"),
    ]

    _req_dates = None
    for attr in _REQUIRED:
        _dates = set(
            monthly[monthly["attribute_name"] == attr]["cash_flow_date"].dt.strftime("%Y-%m-%d")
        )
        _req_dates = _dates if _req_dates is None else _req_dates & _dates
    _req_dates = sorted(_req_dates or [])

    if not _req_dates:
        return  # No complete data — show nothing silently

    # Only render header once we know data exists
    st.markdown(
        '<div class="section-header-co">Studio-Level P&L Waterfall</div>',
        unsafe_allow_html=True,
    )

    # Period selector — default to latest
    _sel_col, _ = st.columns([2, 5])
    with _sel_col:
        _period_labels = {
            d: pd.Timestamp(d).strftime("%B %Y") for d in _req_dates
        }
        _selected_period_label = st.selectbox(
            f"Select {period_mode} period",
            options=list(_period_labels.values())[::-1],
            key=f"cpy_waterfall_period_{period_mode}",
            label_visibility="collapsed",
        )
    # Map back to date string
    _selected_date = next(
        d for d, l in _period_labels.items() if l == _selected_period_label
    )
    _ts = pd.Timestamp(_selected_date)

    def _get(attr):
        row = monthly[
            (monthly["attribute_name"] == attr) &
            (monthly["cash_flow_date"] == _ts)
        ]
        return float(row["true_up_value"].values[0]) if not row.empty else None

    rev   = _get("Total Studio Revenue")
    labor = _get("Labor")
    occ   = _get("Occupancy (Cash Rent and NNN)")
    prog  = _get("Programming")
    other = _get("Other OPEX")
    sc    = _get("Studio Contribution")

    if rev is None or sc is None:
        st.info(f"Incomplete data for {_selected_period_label}.")
        return

    # Pull optional regional OH items and combine
    reg_oh_total = 0.0
    reg_oh_parts = []
    for label, attr in _OPTIONAL_COSTS:
        val = _get(attr)
        if val is not None and abs(val) > 0.001:
            reg_oh_total += val
            reg_oh_parts.append(f"{label}: ${val:.2f}M")

    # Retail COGS estimate (Rev - Member - NonMember - Franchise ≈ Retail rev; Retail GM% available)
    retail_rev = _get("Retail") or 0.0
    retail_gm  = _get("Retail Gross Margin") or 0.0  # stored as decimal ~0.08-0.18
    retail_cogs = retail_rev * (1.0 - retail_gm) if retail_gm > 0 else 0.0

    # Build waterfall steps
    # Each step: (label, value, type)
    #   type: "absolute"=total bar, "relative"=delta bar
    steps = [
        ("Total Studio\nRevenue",   rev,   "absolute"),
        ("Labor",                  -labor if labor else 0, "relative"),
        ("Occupancy",              -occ   if occ   else 0, "relative"),
        ("Programming",            -prog  if prog  else 0, "relative"),
        ("Other OpEx",             -other if other else 0, "relative"),
    ]
    if retail_cogs > 0.05:
        steps.append(("Retail COGS",  -retail_cogs, "relative"))
    if reg_oh_total > 0.05:
        steps.append(("Regional OH",  -reg_oh_total, "relative"))

    steps.append(("Studio\nContribution", sc, "absolute"))

    step_labels = [s[0] for s in steps]
    step_vals   = [s[1] for s in steps]
    step_types  = [s[2] for s in steps]

    # Waterfall: compute running base for relative bars
    _base = []
    _running = 0.0
    for val, typ in zip(step_vals, step_types):
        if typ == "absolute":
            _base.append(0)
            _running = val
        else:
            if val < 0:
                _base.append(_running + val)
            else:
                _base.append(_running)
            _running += val

    # Colours
    _bar_colors = []
    for val, typ in zip(step_vals, step_types):
        if typ == "absolute":
            _bar_colors.append(NAVY if val > 0 else RED_FLAG)
        else:
            _bar_colors.append(RED_FLAG if val < 0 else SEA_GREEN)

    fig = go.Figure()

    # Invisible base bars (for stacking effect)
    fig.add_trace(go.Bar(
        x=step_labels,
        y=_base,
        marker_color="rgba(0,0,0,0)",
        showlegend=False,
        hoverinfo="skip",
    ))

    # Visible bars
    _abs_vals = [abs(v) for v in step_vals]
    fig.add_trace(go.Bar(
        x=step_labels,
        y=_abs_vals,
        marker_color=_bar_colors,
        opacity=0.88,
        text=[f"${v:+.1f}M" if t == "relative" else f"${abs(v):.1f}M"
              for v, t in zip(step_vals, step_types)],
        textposition="outside",
        textfont=dict(size=10, color=NAVY),
        showlegend=False,
        cliponaxis=False,
    ))

    # Connector lines between bars
    _connector_x = []
    _connector_y = []
    _prev_top = 0.0
    for i, (val, typ) in enumerate(zip(step_vals, step_types)):
        if typ == "absolute":
            _prev_top = val
        else:
            _next_base = _base[i]
            _connector_x.extend([step_labels[i - 1], step_labels[i], None])
            _connector_y.extend([_prev_top, _next_base + abs(val) if val < 0 else _next_base, None])
            _prev_top = _next_base + abs(val) if val < 0 else _next_base + val

    # Studio contribution % annotation
    sc_pct = (sc / rev * 100) if rev else 0
    _margin_note = f"Studio Contribution Margin: {sc_pct:.1f}%"

    fig.update_layout(
        height=420,
        barmode="stack",
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=0, r=0, t=40, b=10),
        font=dict(family="Arial", color=NAVY, size=10),
        title=dict(
            text=f"{_selected_period_label}  ·  {_margin_note}",
            font=dict(size=12, color=SLATE),
            x=0, xanchor="left",
        ),
        yaxis=dict(
            title="$M",
            gridcolor=BORDER,
            tickformat="$,.1f",
            range=[min(0, min(_base) - 1), max(step_vals) * 1.25],
        ),
        xaxis=dict(tickfont=dict(size=10), gridcolor=BORDER),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Small data table below the chart for the selected period
    _table_rows = []
    for label, val, typ in zip(step_labels, step_vals, step_types):
        _clean_label = label.replace("\n", " ")
        if typ == "absolute":
            _table_rows.append({"Item": _clean_label, "$M": f"${abs(val):.2f}M", "% of Revenue": f"{abs(val)/rev*100:.1f}%"})
        else:
            _table_rows.append({"Item": _clean_label, "$M": f"(${abs(val):.2f}M)", "% of Revenue": f"{abs(val)/rev*100:.1f}%"})

    with st.expander("View data table", expanded=False):
        if reg_oh_parts:
            st.caption("Regional OH = " + " + ".join(reg_oh_parts))
        st.dataframe(
            pd.DataFrame(_table_rows).set_index("Item"),
            use_container_width=True,
        )


# ---------------------------------------------------------------------------
# Master render function — called from pages_extra tab2
# ---------------------------------------------------------------------------

def render_corepower_visuals(kpis_df: pd.DataFrame, period_mode: str = "Quarterly"):
    """
    Entry point: renders all three Core Power bespoke charts in sequence.
    kpis_df should be the full company_kpis_all() DataFrame
    already filtered to Core Power (or the full dataset — filtering is done here).
    period_mode: "Monthly" | "Quarterly" | "Annual"
    """
    # Ensure we only have Core Power data
    if "company_name" in kpis_df.columns:
        kpis_df = kpis_df[kpis_df["company_name"] == "Core Power"].copy()

    # Ensure date column is parsed
    if not kpis_df.empty:
        kpis_df["cash_flow_date"] = pd.to_datetime(kpis_df["cash_flow_date"], errors="coerce")

    if kpis_df.empty:
        st.info("No Core Power KPI data available. Ensure company_kpis.csv is up to date.")
        return

    st.markdown(
        """
        <style>
        .section-header-co {
            font-size: 11px;
            font-weight: 600;
            color: #888;
            font-family: Arial;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            border-bottom: 1px solid #E0E4EA;
            padding-bottom: 5px;
            margin: 20px 0 12px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # TTM EBITDA always uses monthly data — TTM rolling sum requires monthly granularity
    render_ttm_ebitda_since_investment(kpis_df, period_mode)
    st.markdown("<hr style='border-color:#E0E4EA; margin:24px 0;'>", unsafe_allow_html=True)
    render_revenue_mix(kpis_df, period_mode)
    st.markdown("<hr style='border-color:#E0E4EA; margin:24px 0;'>", unsafe_allow_html=True)
    render_studio_pl_waterfall(kpis_df, period_mode)
