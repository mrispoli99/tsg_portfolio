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
from ai import build_company_context, ask_claude

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

    # Filter to datasheet KPIs only
    kpi_df = kpi_df[kpi_df["attribute_name"].str.contains("datasheet", case=False, na=False)].copy()

    if kpi_df.empty:
        st.info("No datasheet KPIs found. Ensure attributes with 'datasheet' in the name are loaded.")
        return

    # Create a clean display label by stripping "datasheet" (and surrounding punctuation/spaces)
    import re
    kpi_df["display_name"] = kpi_df["attribute_name"].apply(
        lambda x: re.sub(r"[\s\-–_]*datasheet[\s\-–_]*", " ", x, flags=re.IGNORECASE).strip(" -–_")
    )

    # Get unique KPI names (use display_name for UI, attribute_name for filtering)
    name_map = kpi_df[["attribute_name", "display_name"]].drop_duplicates().set_index("display_name")["attribute_name"].to_dict()
    kpi_names = sorted(name_map.keys())

    # Filters
    col_f1, col_f2 = st.columns([2, 3])
    with col_f1:
        selected_display = st.selectbox("Select KPI", kpi_names)
    with col_f2:
        companies = sorted(kpi_df["company_name"].unique().tolist())
        selected_companies = st.multiselect("Filter Companies", companies, default=companies)

    if not selected_display:
        return

    selected_kpi = name_map.get(selected_display, selected_display)

    filtered = kpi_df[
        (kpi_df["attribute_name"] == selected_kpi) &
        (kpi_df["company_name"].isin(selected_companies))
    ].sort_values("true_up_value", ascending=True)

    if filtered.empty:
        st.info(f"No data available for {selected_display}")
        return

    st.markdown(f'<div class="section-header">{selected_display} — Most Recent LTM by Company</div>',
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

    # Full KPI scorecard — all datasheet KPIs x all companies (latest values), display names as rows
    st.markdown('<div class="section-header">Full KPI Scorecard — All Companies</div>',
                unsafe_allow_html=True)

    pivot_data = kpi_df[kpi_df["company_name"].isin(selected_companies)].copy()
    pivot_data["display_name"] = pivot_data["attribute_name"].apply(
        lambda x: re.sub(r"[\s\-–_]*datasheet[\s\-–_]*", " ", x, flags=re.IGNORECASE).strip(" -–_")
    )
    pivot = pivot_data.pivot_table(
        index="display_name", columns="company_name", values="true_up_value", aggfunc="last"
    )

    if not pivot.empty:
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
# Categorized AI Summary for Company-Specific Analysis tab
# Splits output into Financials / Operational / Liquidity / Financing sections.
# Operational section always uses manual notes (no 73s data source).
# ---------------------------------------------------------------------------

def _render_ai_summary_categorized(company: str, df: pd.DataFrame,
                                   kpi_cards: list, kpi_charts: list):
    """
    Render a 4-section AI summary:
      Financials  — auto-generated from data
      Operational — manual notes field (no structured data source)
      Liquidity   — auto-generated from data
      Financing   — auto-generated from data
    """
    try:
        from page_company_kpis import _build_kpi_context, _fmt
        from ai import ask_claude
    except ImportError as e:
        st.info(f"AI module not available: {e}")
        return

    session_key   = f"csa_ai_summary_{company}"
    chat_key      = f"csa_ai_chat_{company}"
    ops_notes_key = f"csa_ops_notes_{company}"

    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    SYSTEM = (
        "You are a private equity analyst at TSG Consumer Partners. "
        "Analyze ONLY the data and context explicitly provided. Never invent numbers. "
        "If a metric is absent, write 'not available'. "
        "Format dollar values as '$X.XM'. Always cite the period for each data point. "
        "CRITICAL FORMATTING RULE: You MUST use exactly these four section headers on their own "
        "lines, with no markdown formatting around them — no asterisks, no hashes, no bold:\n"
        "FINANCIALS:\n"
        "OPERATIONAL:\n"
        "LIQUIDITY:\n"
        "FINANCING:\n"
        "Each section header must be on its own line, followed immediately by bullet points. "
        "Do not add any other headers, bold text, or markdown formatting anywhere in your response."
    )

    context = _build_kpi_context(company, df, kpi_cards, kpi_charts)

    # ── Context Notes — collapsable, above AI sections ───────────────────────
    _notes_saved    = st.session_state.get(ops_notes_key, "")
    _files_key      = f"csa_uploaded_files_{company}"
    _files_text_key = f"csa_files_text_{company}"
    if _files_key not in st.session_state:
        st.session_state[_files_key] = []
    if _files_text_key not in st.session_state:
        st.session_state[_files_text_key] = {}

    _has_context = bool(_notes_saved.strip() or st.session_state[_files_text_key])
    _expander_label = "📎 Context Notes & Files" + (" ✓" if _has_context else "")

    with st.expander(_expander_label, expanded=False):
        st.caption(
            "Add any notes or upload files to give the AI additional context — "
            "board updates, management commentary, press releases, earnings transcripts, etc. "
            "Saved content is synthesized into all four AI summary sections."
        )

        _notes_input = st.text_area(
            "Notes",
            value=_notes_saved,
            placeholder=(
                "Paste any context here — operational updates, key themes from board meetings, "
                "management commentary, financing developments, competitive dynamics, etc."
            ),
            height=130,
            key=f"csa_notes_input_{company}",
            label_visibility="visible",
        )

        _uploaded = st.file_uploader(
            "Upload files",
            type=["pdf", "txt", "csv", "docx", "md"],
            accept_multiple_files=True,
            key=f"csa_file_upload_{company}",
            help="PDF, TXT, CSV, DOCX, or Markdown. Text is extracted and added to AI context.",
        )

        if _uploaded:
            for _f in _uploaded:
                if _f.name not in st.session_state[_files_text_key]:
                    try:
                        _raw_bytes = _f.read()
                        _ext = _f.name.rsplit(".", 1)[-1].lower()
                        if _ext == "pdf":
                            try:
                                import pypdf as _pypdf
                                _reader = _pypdf.PdfReader(__import__("io").BytesIO(_raw_bytes))
                                _txt = "\n".join(
                                    p.extract_text() or "" for p in _reader.pages
                                )
                            except Exception:
                                _txt = _raw_bytes.decode("utf-8", errors="ignore")
                        elif _ext == "docx":
                            try:
                                import docx as _docx
                                _doc = _docx.Document(__import__("io").BytesIO(_raw_bytes))
                                _txt = "\n".join(p.text for p in _doc.paragraphs)
                            except Exception:
                                _txt = _raw_bytes.decode("utf-8", errors="ignore")
                        else:
                            _txt = _raw_bytes.decode("utf-8", errors="ignore")
                        st.session_state[_files_text_key][_f.name] = _txt[:15000]
                    except Exception as _fe:
                        st.warning(f"Could not read {_f.name}: {_fe}")

        if st.session_state[_files_text_key]:
            st.markdown("**Loaded files:**")
            for _fname, _ftxt in list(st.session_state[_files_text_key].items()):
                _fcol1, _fcol2 = st.columns([5, 1])
                with _fcol1:
                    st.caption(f"📄 {_fname} — {len(_ftxt):,} chars extracted")
                with _fcol2:
                    if st.button("✕", key=f"csa_del_file_{company}_{_fname}",
                                 use_container_width=True):
                        del st.session_state[_files_text_key][_fname]
                        st.session_state.pop(session_key, None)
                        st.rerun()

        _save_col, _ = st.columns([1, 6])
        with _save_col:
            if st.button("Save", key=f"csa_notes_save_{company}", use_container_width=True):
                st.session_state[ops_notes_key] = _notes_input
                st.session_state.pop(session_key, None)
                st.rerun()

    # Build combined extra context from notes + files — done AFTER expander renders
    _all_extra_context = ""
    _saved_notes = st.session_state.get(ops_notes_key, "")
    if _saved_notes.strip():
        _all_extra_context += f"\n\nADDITIONAL CONTEXT (notes added by team):\n{_saved_notes.strip()}"
    for _fname, _ftxt in st.session_state[_files_text_key].items():
        _all_extra_context += f"\n\n--- UPLOADED FILE: {_fname} ---\n{_ftxt.strip()}"

    # Inject all extra context before the cache check
    if _all_extra_context:
        context += _all_extra_context

    # ── Auto-generate on first load ───────────────────────────────────────────
    if session_key not in st.session_state:
        with st.spinner("Generating summary..."):
            try:
                _has_extra = bool(_all_extra_context.strip())
                _operational_instruction = (
                    "OPERATIONAL:\n"
                    "- 2-3 bullets synthesizing the additional context notes and files provided. "
                    "Focus on operational highlights, management themes, and qualitative developments. "
                    "If no additional context was provided, write a single bullet: 'No operational notes provided.'"
                    if _has_extra else
                    "OPERATIONAL:\n"
                    "- No operational notes provided."
                )
                prompt = (
                    f"Using the data and context provided, write a structured performance summary "
                    f"for {company}. Your response MUST contain exactly these four section headers "
                    f"on their own lines, with no markdown or bold formatting:\n\n"
                    f"FINANCIALS:\n"
                    f"- 2-3 bullets on revenue trajectory, EBITDA, and margin trends\n\n"
                    f"{_operational_instruction}\n\n"
                    f"LIQUIDITY:\n"
                    f"- 2 bullets drawing specifically on: LTM Free Cash Flow, Cash Balance, "
                    f"Debt Service Coverage Ratio, and any covenant data available. "
                    f"If these metrics are not in the data, say so explicitly.\n\n"
                    f"FINANCING:\n"
                    f"- 2 bullets on leverage level, debt composition (fixed vs. floating), "
                    f"and any notable credit dynamics\n\n"
                    f"Do not use asterisks, bold, hashes, or any other markdown around the section "
                    f"headers. Write the headers exactly as shown above."
                )
                summary = ask_claude(prompt, context + "\n\n" + SYSTEM, [])
                st.session_state[session_key] = summary
                st.session_state[chat_key] = [
                    {"role": "user",      "content": prompt},
                    {"role": "assistant", "content": summary},
                ]
            except Exception as e:
                st.session_state[session_key] = f"Could not generate summary: {e}"

    # ── Render the four sections ──────────────────────────────────────────────
    raw = st.session_state.get(session_key, "")

    import re as _re
    _sections = {"FINANCIALS": "", "OPERATIONAL": "", "LIQUIDITY": "", "FINANCING": ""}
    _current  = None
    for _line in raw.splitlines():
        _clean = _re.sub(r"[*#_`]", "", _line).strip().upper().rstrip(":").strip()
        if _clean in _sections:
            _current = _clean
            continue
        if _current:
            _content_line = _re.sub(r"\*\*(.+?)\*\*", r"\1", _line)
            _sections[_current] += _content_line + "\n"

    if not any(v.strip() for v in _sections.values()):
        _sections["FINANCIALS"] = raw

    _SECTION_COLORS = {
        "FINANCIALS":  NAVY,
        "OPERATIONAL": SEA_GREEN,
        "LIQUIDITY":   SLATE,
        "FINANCING":   XANTHOUS,
    }

    # Financials
    st.markdown(f"""
    <div style="border-left:3px solid {_SECTION_COLORS['FINANCIALS']}; padding:8px 14px;
                margin-bottom:10px; background:#F8F9FA; border-radius:0 4px 4px 0;">
        <div style="font-size:11px; font-weight:700; color:{_SECTION_COLORS['FINANCIALS']};
                    font-family:Arial; text-transform:uppercase; letter-spacing:0.6px;
                    margin-bottom:6px;">Financials</div>
        <div style="font-size:12px; color:{NAVY}; font-family:Arial; white-space:pre-wrap;">{_sections["FINANCIALS"].strip() or "—"}</div>
    </div>
    """, unsafe_allow_html=True)

    # Operational — AI-generated from notes and files
    _op_content = _sections["OPERATIONAL"].strip()
    _op_note    = "" if _op_content and _op_content != "No operational notes provided." else (
        '<span style="font-size:10px; font-weight:400; color:#AAAAAA; margin-left:8px;">'
        '(add notes above to populate)</span>'
    )
    st.markdown(f"""
    <div style="border-left:3px solid {_SECTION_COLORS['OPERATIONAL']}; padding:8px 14px;
                margin-bottom:10px; background:#F8F9FA; border-radius:0 4px 4px 0;">
        <div style="font-size:11px; font-weight:700; color:{_SECTION_COLORS['OPERATIONAL']};
                    font-family:Arial; text-transform:uppercase; letter-spacing:0.6px;
                    margin-bottom:6px;">Operational{_op_note}</div>
        <div style="font-size:12px; color:{NAVY}; font-family:Arial; white-space:pre-wrap;">{_op_content or "—"}</div>
    </div>
    """, unsafe_allow_html=True)

    # Liquidity
    st.markdown(f"""
    <div style="border-left:3px solid {_SECTION_COLORS['LIQUIDITY']}; padding:8px 14px;
                margin-bottom:10px; background:#F8F9FA; border-radius:0 4px 4px 0;">
        <div style="font-size:11px; font-weight:700; color:{_SECTION_COLORS['LIQUIDITY']};
                    font-family:Arial; text-transform:uppercase; letter-spacing:0.6px;
                    margin-bottom:6px;">Liquidity</div>
        <div style="font-size:12px; color:{NAVY}; font-family:Arial; white-space:pre-wrap;">{_sections["LIQUIDITY"].strip() or "—"}</div>
    </div>
    """, unsafe_allow_html=True)

    # Financing
    st.markdown(f"""
    <div style="border-left:3px solid {_SECTION_COLORS['FINANCING']}; padding:8px 14px;
                margin-bottom:10px; background:#F8F9FA; border-radius:0 4px 4px 0;">
        <div style="font-size:11px; font-weight:700; color:{_SECTION_COLORS['FINANCING']};
                    font-family:Arial; text-transform:uppercase; letter-spacing:0.6px;
                    margin-bottom:6px;">Financing</div>
        <div style="font-size:12px; color:{NAVY}; font-family:Arial; white-space:pre-wrap;">{_sections["FINANCING"].strip() or "—"}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Regenerate button ─────────────────────────────────────────────────────
    _reg_col, _ = st.columns([1, 5])
    with _reg_col:
        if st.button("↺ Regenerate", key=f"csa_regen_{company}", use_container_width=True):
            st.session_state.pop(session_key, None)
            st.rerun()

    # ── Follow-up chat ────────────────────────────────────────────────────────
    st.caption("Ask follow-up questions — answers are grounded in the data above only.")
    for _msg in st.session_state[chat_key][2:]:
        if _msg["role"] == "user":
            st.markdown(f"> {_msg['content']}")
        else:
            st.markdown(_msg["content"])

    _user_q = st.chat_input(
        f"Ask about {company}…",
        key=f"csa_chat_input_{company}"
    )
    if _user_q:
        st.session_state[chat_key].append({"role": "user", "content": _user_q})
        with st.spinner("Thinking..."):
            try:
                _resp = ask_claude(
                    _user_q,
                    context + "\n\n" + SYSTEM,  # context already has notes + files injected
                    st.session_state[chat_key][:-1],
                )
            except Exception as _e:
                _resp = f"Error: {_e}"
        st.session_state[chat_key].append({"role": "assistant", "content": _resp})
        st.rerun()


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

    # ── Pull fund summary row for Investment Update card ──────────────────────
    from db import load_fund_summary, load_ltm_snapshot
    _fs  = load_fund_summary()
    _ltm = load_ltm_snapshot()
    _fs_row  = _fs[_fs["company_name"] == selected].iloc[0]  if len(_fs[_fs["company_name"] == selected])  > 0 else None
    _ltm_row = _ltm[_ltm["company_name"] == selected].iloc[0] if len(_ltm[_ltm["company_name"] == selected]) > 0 else None

    def _inv_fmt(val, decimals=1):
        """Format investment values — show as $XM/$XB, or '—' if missing."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return "—"
        try:
            v = float(val)
            if abs(v) >= 1000:
                return f"${v/1000:.{decimals}f}B"
            return f"${v:.{decimals}f}M"
        except Exception:
            return str(val)

    # Investment Update card values
    _inv_date   = str(info_row.get("investment_date", ""))[:10] if info_row is not None else "—"
    # Format investment date as "Month YYYY"
    try:
        import datetime as _dt
        _inv_date_fmt = _dt.datetime.strptime(_inv_date, "%Y-%m-%d").strftime("%B %Y")
    except Exception:
        _inv_date_fmt = _inv_date

    _total_cost  = _inv_fmt(_ltm_row.get("total_cost") if _ltm_row is not None else None)
    _security    = info_row.get("security_type", "") if info_row is not None else ""
    _ownership   = info_row.get("ownership_structure", "") if info_row is not None else ""
    _fund_own    = _fs_row.get("fund_current_ownership_pct") if _fs_row is not None else None
    _tsg_own     = _fs_row.get("tsg_controlled_current_pct") if _fs_row is not None else None
    _struct_str  = str(_security or "").strip()
    if _ownership and str(_ownership).strip() not in ("", "nan", "None"):
        _struct_str += f" / {_ownership}" if _struct_str else str(_ownership)
    if _fund_own and not (isinstance(_fund_own, float) and pd.isna(_fund_own)):
        try:
            _struct_str += f" ({float(_fund_own)*100:.0f}% ownership)"
        except Exception:
            pass

    _val_method  = info_row.get("valuation_methodology", "") if info_row is not None else ""
    if not _val_method or str(_val_method).strip() in ("", "nan", "None"):
        _val_method = "—"

    # Last available quarter's value — Total Realized & Unrealized Value
    # Filter to Quarterly rows to avoid Monthly/Annual mixing in the delta calc.
    # Falls back to all rows if Quarterly filter leaves nothing.
    _last_val_label = "Latest Quarter Value"
    _last_val_str   = "—"
    try:
        _qdf = load_quarterly(selected)
        if not _qdf.empty and "total_value" in _qdf.columns:
            _qdf["cash_flow_date"] = pd.to_datetime(_qdf["cash_flow_date"], errors="coerce")
            # Try Quarterly only first; fall back to all if empty
            if "period" in _qdf.columns:
                _qdf_q = _qdf[_qdf["period"] == "Quarterly"].dropna(subset=["total_value"])
                _qdf   = _qdf_q if not _qdf_q.empty else _qdf.dropna(subset=["total_value"])
            else:
                _qdf = _qdf.dropna(subset=["total_value"])
            _qdf = _qdf.sort_values("cash_flow_date")
            if not _qdf.empty:
                _latest_row    = _qdf.iloc[-1]
                _latest_val    = float(_latest_row["total_value"])
                _latest_period = str(_latest_row.get("period_label", "")).strip()
                _last_val_label = f"{_latest_period} Value" if _latest_period else "Latest Quarter Value"
                _last_val_str   = _inv_fmt(_latest_val)
                if len(_qdf) >= 2:
                    _prior_val = float(_qdf.iloc[-2]["total_value"])
                    _delta     = _latest_val - _prior_val
                    _sign      = "+" if _delta >= 0 else ""
                    _last_val_str += f" ({_sign}{_inv_fmt(_delta)} vs. prior quarter)"
    except Exception:
        pass

    # Company header card — stacked layout: identity on top, Investment Update below
    if flag_row is not None:
        overall   = flag_row.get("overall_flag", "")
        sector    = info_row.get("client_sector", "") if info_row is not None else ""
        inv_date  = str(info_row.get("investment_date", ""))[:10] if info_row is not None else ""
        security  = info_row.get("security_type", "") if info_row is not None else ""
        ownership = info_row.get("ownership_structure", "") if info_row is not None else ""
        geo       = info_row.get("geography", "") if info_row is not None else ""
        hq        = info_row.get("headquarters", "") if info_row is not None else ""

        # Build subtitle — suppress any null/nan fields cleanly
        def _clean(v):
            return str(v).strip() if v and str(v).strip() not in ("", "nan", "None", "NaN") else ""
        _sub = []
        if _clean(sector):   _sub.append(_clean(sector))
        if _clean(geo):      _sub.append(_clean(geo)[:30])
        if _clean(inv_date): _sub.append(f"Entry {inv_date}")
        _pipes = []
        if _clean(hq):       _pipes.append(f"HQ: {_clean(hq)}")
        _subtitle_line = " · ".join(_sub)
        if _pipes:
            _subtitle_line += " &nbsp;|&nbsp; " + " &nbsp;|&nbsp; ".join(_pipes)

        st.markdown(f"""
        <div style="background:white; border:1px solid {BORDER}; border-radius:6px;
                    padding:16px 20px; margin-bottom:16px;">
            <!-- Top row: company identity + flag badge -->
            <div style="display:flex; align-items:center; justify-content:space-between;
                        margin-bottom:14px;">
                <div style="display:flex; align-items:center; gap:14px;">
                    <div style="background:{NAVY}; color:white; padding:10px 16px;
                                border-radius:4px; font-weight:700; font-family:Arial;
                                font-size:18px; flex-shrink:0;">
                        {selected[:2].upper()}
                    </div>
                    <div>
                        <div style="font-size:22px; font-weight:700; color:{NAVY}; font-family:Arial;">
                            {selected}
                        </div>
                        <div style="font-size:12px; color:{SLATE}; font-family:Arial; margin-top:2px;">
                            {_subtitle_line}
                        </div>
                    </div>
                </div>
                <div>{flag_badge(overall)}</div>
            </div>
            <!-- Investment Update card — below company name, left-aligned -->
            <div style="border:1px solid {BORDER}; border-radius:6px; overflow:hidden;
                        max-width:420px; font-family:Arial; font-size:12px;">
                <div style="background:{NAVY}; color:white; font-weight:700;
                            font-size:12px; padding:7px 14px; letter-spacing:0.3px;">
                    Investment Update
                </div>
                <table style="width:100%; border-collapse:collapse;">
                    <tr style="border-bottom:1px solid {BORDER};">
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA; width:45%;">Investment Date:</td>
                        <td style="padding:6px 12px; color:{SLATE};">{_inv_date_fmt}</td>
                    </tr>
                    <tr style="border-bottom:1px solid {BORDER};">
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA;">Aggregate Investment:</td>
                        <td style="padding:6px 12px; color:{SLATE};">{_total_cost}</td>
                    </tr>
                    <tr style="border-bottom:1px solid {BORDER};">
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA;">Valuation Methodology:</td>
                        <td style="padding:6px 12px; color:{SLATE};">{_val_method}</td>
                    </tr>
                    <tr style="border-bottom:1px solid {BORDER};">
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA;">{_last_val_label}:</td>
                        <td style="padding:6px 12px; color:{SLATE}; font-style:italic;">{_last_val_str}</td>
                    </tr>
                    <tr style="border-bottom:1px solid {BORDER};">
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA;">Exit Date:</td>
                        <td style="padding:6px 12px; color:#AAAAAA; font-style:italic;">—</td>
                    </tr>
                    <tr style="border-bottom:1px solid {BORDER};">
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA;">Exit Type:</td>
                        <td style="padding:6px 12px; color:#AAAAAA; font-style:italic;">—</td>
                    </tr>
                    <tr>
                        <td style="padding:6px 12px; font-weight:600; color:{NAVY};
                                   background:#F8F9FA;">MOI Forecast:</td>
                        <td style="padding:6px 12px; color:#AAAAAA; font-style:italic;">—</td>
                    </tr>
                </table>
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
        # Build period label strings for the flag cards
        _as_of = flag_row.get("as_of_date")
        try:
            _as_of_ts  = pd.to_datetime(_as_of)
            _as_of_lbl = _as_of_ts.strftime("%b %Y")
            _py_lbl    = (_as_of_ts - pd.DateOffset(years=1)).strftime("%b %Y")
            _yoy_period_lbl  = f"{_as_of_lbl} vs. {_py_lbl}"
            _curr_period_lbl = _as_of_lbl
        except Exception:
            _yoy_period_lbl  = ""
            _curr_period_lbl = ""

        flag_card_cols = st.columns(4)
        for col, (fk, vk, lbl, fmt, thresh, calc) in zip(flag_card_cols, FLAG_CARD_DEFS):
            fval    = str(flag_row.get(fk, "") or "")
            val     = flag_row.get(vk)
            fclr    = {"Red": RED_FLAG, "Yellow": XANTHOUS, "Green": SEA_GREEN}.get(fval, SLATE)
            val_str = fmt(val) if val is not None and not pd.isna(val) else "—"
            tip     = f"{lbl}\nCalc: {calc}\nThresholds: {thresh}"
            # Period sub-label — YoY metrics show "Dec 2025 vs. Dec 2024", others show "Dec 2025"
            _plbl = _yoy_period_lbl if "yoy" in vk.lower() or "growth" in vk.lower() else _curr_period_lbl
            col.markdown(
                f'<div title="{tip}" style="background:white;border:1px solid {BORDER};'
                f'border-left:4px solid {fclr};border-radius:4px;padding:8px 10px;cursor:help;">'
                f'<div style="font-size:18px;font-weight:700;color:{fclr};font-family:Arial;">{val_str}</div>'
                f'<div style="font-size:10px;color:{SLATE};font-family:Arial;margin-top:2px;">{lbl}</div>'
                f'<div style="font-size:9px;color:#AAAAAA;font-family:Arial;margin-top:1px;">{_plbl}</div>'
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
        # Parse dates
        if not quarterly.empty and "cash_flow_date" in quarterly.columns:
            import pandas as _pd
            quarterly = quarterly.copy()
            quarterly["cash_flow_date"] = _pd.to_datetime(quarterly["cash_flow_date"], errors="coerce")

        # ----------------------------------------------------------------
        # PERIOD SELECTOR — applies to ALL charts and the datasheet table
        # ----------------------------------------------------------------
        _pm_col, _ = st.columns([3, 5])
        with _pm_col:
            co_period_mode = st.radio(
                "Period",
                ["Quarterly", "Monthly", "Yearly"],
                horizontal=True,
                key=f"co_period_mode_{selected}",
                label_visibility="collapsed",
            )

        # Filter all data to selected period type only
        _period_type_map = {"Quarterly": "Quarterly", "Monthly": "Monthly", "Yearly": "Annual"}
        _pf_val = _period_type_map.get(co_period_mode, "Quarterly")
        if not quarterly.empty and "period" in quarterly.columns:
            quarterly = quarterly[quarterly["period"] == _pf_val].copy()

        # Apply rolling window — sized by period mode so all granularities show enough data
        if not quarterly.empty:
            _window_years = {"Quarterly": 3, "Monthly": 2, "Yearly": 10}
            _cutoff = _pd.Timestamp.now() - _pd.DateOffset(years=_window_years.get(co_period_mode, 3))
            quarterly = quarterly[quarterly["cash_flow_date"] >= _cutoff]

        if not quarterly.empty:
            # Revenue & EBITDA trend — LTM values per period (time series)
            st.markdown('<div class="section-header">LTM Revenue & EBITDA Trend</div>',
                        unsafe_allow_html=True)
            from plotly.subplots import make_subplots
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            # revenue and adj_ebitda columns now hold LTM Net Sales and LTM Adj. EBITDA
            rev = quarterly["revenue"].combine_first(quarterly["net_sales"])
            _margin_s = (quarterly["adj_ebitda"] / rev.replace(0, float("nan")))
            _margin_df = pd.DataFrame({
                "period_label": quarterly["period_label"],
                "margin": _margin_s
            }).dropna()
            fig.add_trace(go.Bar(x=quarterly["period_label"], y=rev,
                                  name="LTM Net Sales ($M)", marker_color=NAVY, opacity=0.8),
                          secondary_y=False)
            fig.add_trace(go.Bar(x=quarterly["period_label"], y=quarterly["adj_ebitda"],
                                  name="LTM Adj. EBITDA ($M)", marker_color=SLATE, opacity=0.8),
                          secondary_y=False)
            fig.add_trace(go.Scatter(x=_margin_df["period_label"], y=_margin_df["margin"],
                                      name="EBITDA Margin %", mode="lines+markers",
                                      line=dict(color=XANTHOUS, width=2),
                                      connectgaps=True),
                          secondary_y=True)
            fig.update_layout(height=420, plot_bgcolor="white", paper_bgcolor="white",
                               margin=dict(l=0, r=0, t=10, b=0), barmode="group",
                               legend=dict(orientation="h", y=-0.18, font=dict(size=10)),
                               font=dict(family="Arial", color=NAVY, size=10))
            fig.update_yaxes(tickformat="$,.0f", gridcolor=BORDER, secondary_y=False)
            fig.update_yaxes(tickformat=".0%", secondary_y=True)
            fig.update_xaxes(tickangle=-45, tickmode="linear", dtick=1, tickfont=dict(size=9))
            st.plotly_chart(fig, use_container_width=True)

            # Leverage and Margin side by side
            col_lev, col_mgn = st.columns(2)
            with col_lev:
                st.markdown(f'<div class="section-header">Net Leverage — {co_period_mode}</div>',
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
                    fig3.update_layout(height=340, plot_bgcolor="white",
                                        paper_bgcolor="white",
                                        margin=dict(l=0,r=0,t=10,b=0),
                                        font=dict(family="Arial", color=NAVY, size=10),
                                        yaxis=dict(gridcolor=BORDER))
                    fig3.update_xaxes(tickangle=-45, tickmode="linear", dtick=1,
                                      tickfont=dict(size=8))
                    st.plotly_chart(fig3, use_container_width=True)

            with col_mgn:
                st.markdown(f'<div class="section-header">EBITDA Margin % — {co_period_mode}</div>',
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
                        fill="tozeroy", fillcolor="rgba(63,102,128,0.1)",
                        connectgaps=True,
                    ))
                    fig4.update_layout(height=340, plot_bgcolor="white",
                                        paper_bgcolor="white",
                                        margin=dict(l=0,r=0,t=10,b=0),
                                        font=dict(family="Arial", color=NAVY, size=10),
                                        yaxis=dict(tickformat=".0%", gridcolor=BORDER))
                    fig4.update_xaxes(tickangle=-45, tickmode="linear", dtick=1,
                                      tickfont=dict(size=8))
                    st.plotly_chart(fig4, use_container_width=True)

        # ----------------------------------------------------------------
        # COMPANY DATASHEET — KPIs as rows, periods as columns
        # ----------------------------------------------------------------
        st.markdown("<hr style='border:1px solid #E0E4EA;margin:28px 0 16px 0;'>",
                    unsafe_allow_html=True)
        st.markdown('<div class="section-header">Company Datasheet</div>',
                    unsafe_allow_html=True)

        # Reload full data (no 3yr cutoff) for the datasheet table — reuse period filter
        q_all_co = load_quarterly(selected)
        if not q_all_co.empty and "cash_flow_date" in q_all_co.columns:
            import pandas as _pd2
            q_all_co = q_all_co.copy()
            q_all_co["cash_flow_date"] = _pd2.to_datetime(q_all_co["cash_flow_date"], errors="coerce")
            _co_cutoff = _pd2.Timestamp.now() - _pd2.DateOffset(years=3)
            q_all_co = q_all_co[q_all_co["cash_flow_date"] >= _co_cutoff]

        if not q_all_co.empty:
            # Filter to the correct period type
            if "period" in q_all_co.columns:
                _pf_map2 = {"Quarterly": "Quarterly", "Monthly": "Monthly", "Yearly": "Annual"}
                q_all_co = q_all_co[q_all_co["period"] == _pf_map2.get(co_period_mode, "Quarterly")]

            # Build period label per mode
            if co_period_mode == "Monthly":
                q_all_co["_plabel"] = q_all_co["cash_flow_date"].dt.strftime("%b %Y")
            elif co_period_mode == "Yearly":
                q_all_co["_plabel"] = q_all_co["cash_flow_date"].dt.strftime("%Y")
            else:
                q_all_co["_plabel"] = (q_all_co["period_label"].astype(str)
                                       if "period_label" in q_all_co.columns
                                       else q_all_co["cash_flow_date"].dt.to_period("Q").astype(str))

            # Sorted unique period labels
            all_co_periods = (q_all_co.sort_values("cash_flow_date")["_plabel"]
                              .drop_duplicates().tolist())

            # KPI definitions mapped to column names in the updated Datasheet views
            # (display_label, column, format_fn, is_pct, threshold_fn)
            CO_KPI_DEFS = [
                # LTM Income
                ("LTM Net Sales ($M)",                  "revenue",                  format_millions,  False, None),
                ("LTM Adj. EBITDA ($M)",                "adj_ebitda",               format_millions,  False, None),
                ("LTM EBITDA (Actual) ($M)",            "ltm_ebitda_actual",        format_millions,  False, None),
                ("LTM Credit Agreement EBITDA ($M)",    "ltm_credit_agreement_ebitda", format_millions, False, None),
                # LTM Margins (derived)
                ("EBITDA Margin %",                     "adj_ebitda_margin_pct",    format_pct,       True,
                    lambda v: "Green" if v > 0.18 else "Yellow" if v > 0.10 else "Red"),
                # LTM Cash Flow
                ("LTM Free Cash Flow ($M)",             "ltm_free_cash_flow",       format_millions,  False,
                    lambda v: "Green" if v > 0 else "Red"),
                ("LTM Capex ($M)",                      "ltm_capex",                format_millions,  False, None),
                ("LTM Cash Interest Expense ($M)",      "ltm_cash_interest",        format_millions,  False, None),
                ("LTM Cash Taxes ($M)",                 "ltm_cash_taxes",           format_millions,  False, None),
                ("LTM Δ NWC ($M)",                     "ltm_change_nwc",           format_millions,  False, None),
                ("LTM Mandatory Principal Pmts ($M)",   "ltm_principal_payments",   format_millions,  False, None),
                # Debt & Balance Sheet
                ("Cash ($M)",                           "cash",                     format_millions,  False, None),
                ("Net Debt (Actual) ($M)",              "net_debt",                 format_millions,  False, None),
                ("Net Debt (Credit Agreement) ($M)",    "net_debt_credit_agreement",format_millions,  False, None),
                ("Total Gross Debt ($M)",               "total_gross_debt",         format_millions,  False, None),
                ("Floating Rate Debt ($M)",             "floating_rate_debt",       format_millions,  False, None),
                ("Fixed Rate Debt ($M)",                "fixed_rate_debt",          format_millions,  False, None),
                ("PIK Debt ($M)",                       "pik_debt",                 format_millions,  False, None),
                ("Senior Secured Portion ($M)",         "senior_secured_debt",      format_millions,  False, None),
                ("Other Debt ($M)",                     "other_debt",               format_millions,  False, None),
                # Leverage & Coverage
                ("Net Debt / EBITDA",                   "net_leverage",             format_multiple,  False,
                    lambda v: "Green" if v < 5 else "Yellow" if v < 6 else "Red"),
                ("Total Gross Leverage",                "gross_leverage",           format_multiple,  False, None),
                ("Total Net Leverage",                  "total_net_leverage",       format_multiple,  False, None),
                ("Senior Secured Gross Leverage",       "senior_secured_leverage",  format_multiple,  False, None),
                ("Interest Coverage Ratio",             "interest_coverage",        format_multiple,  False,
                    lambda v: "Green" if v > 3 else "Yellow" if v > 2 else "Red"),
                ("Debt Service Coverage Ratio",         "debt_service_coverage",    format_multiple,  False,
                    lambda v: "Green" if v > 1.8 else "Yellow" if v > 1.2 else "Red"),
                # Valuation
                ("TEV (Actual) ($M)",                   "tev",                      format_millions,  False, None),
                ("TEV / EBITDA",                        "tev_to_ebitda",            format_multiple,  False, None),
                ("TEV / Net Sales",                     "tev_to_revenue",           format_multiple,  False, None),
                # Returns & Ownership
                ("Gross MOI",                           "gross_moi",                format_multiple,  False, None),
                ("Gross IRR",                           "gross_irr",                format_pct,       True,  None),
                ("Total Cost ($M)",                     "total_cost",               format_millions,  False, None),
                ("Unrealized Value ($M)",               "unrealized_value",         format_millions,  False, None),
                ("Realized Proceeds ($M)",              "realized_proceeds",        format_millions,  False, None),
                ("Total Realized & Unrealized ($M)",    "total_value",              format_millions,  False, None),
                ("Fund Current Ownership %",            "fund_current_ownership",   format_pct,       True,  None),
                ("Fund Ownership at Entry %",           "fund_ownership_at_entry",  format_pct,       True,  None),
                ("TSG Controlled Ownership %",          "tsg_current_ownership",    format_pct,       True,  None),
                ("TSG Ownership at Entry %",            "tsg_ownership_at_entry",   format_pct,       True,  None),
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
                        # Use exact column as specified in CO_KPI_DEFS — no ltm_ prefix guessing.
                        # Take last non-null value (duplicate rows per period exist in the data).
                        if col in sub.columns:
                            non_null = sub[col].dropna()
                            val = float(non_null.iloc[-1]) if not non_null.empty else None
                        else:
                            val = None

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
                # CHART — chart type per spec, with date range selector
                # ----------------------------------------------------------------
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f'<div class="section-header">{active_co_kpi} — Trend</div>',
                    unsafe_allow_html=True
                )

                # Date range selector
                _chart_min = q_all_co["cash_flow_date"].min()
                _chart_max = q_all_co["cash_flow_date"].max()
                _default_months = 12 if co_period_mode == "Monthly" else 24
                _chart_default_start = max(_chart_min, _chart_max - pd.DateOffset(months=_default_months))
                _dr_col, _ = st.columns([3, 4])
                with _dr_col:
                    _chart_range = st.date_input(
                        "Date range",
                        value=(_chart_default_start.date(), _chart_max.date()),
                        min_value=_chart_min.date(),
                        max_value=_chart_max.date(),
                        key=f"co_chart_range_{selected}_{active_co_kpi}",
                        label_visibility="collapsed",
                    )

                q_chart_filtered = q_all_co.copy()
                if isinstance(_chart_range, (list, tuple)) and len(_chart_range) == 2:
                    q_chart_filtered = q_chart_filtered[
                        (q_chart_filtered["cash_flow_date"] >= pd.Timestamp(_chart_range[0])) &
                        (q_chart_filtered["cash_flow_date"] <= pd.Timestamp(_chart_range[1]))
                    ]

                # Chart type mapping
                _CO_MULTILINE = {
                    "LTM Revenue ($M)", "LTM Adj. EBITDA ($M)", "Gross Profit ($M)",
                    "Gross Margin %", "EBITDA Margin %", "LTM Free Cash Flow ($M)", "LTM Capex ($M)",
                }
                _CO_GROUPED_BAR = {"Net Leverage", "Interest Coverage",
                                   "Net Debt ($M)", "Total Gross Debt ($M)"}

                # Find the column and format for the active KPI
                active_def = next(
                    (d for d in CO_KPI_DEFS if d[0] == active_co_kpi), None
                )
                if active_def and active_def[1] in q_chart_filtered.columns:
                    _, a_col, a_fmt, a_is_pct, a_thresh = active_def
                    ts = (q_chart_filtered[["_plabel", "cash_flow_date", a_col]]
                          .dropna(subset=[a_col])
                          .sort_values("cash_flow_date")
                          .drop_duplicates(subset=["_plabel"], keep="last")
                          .copy())

                    if len(ts) >= 1:
                        tick_fmt = ".0%" if a_is_pct else "$,.0f"

                        if active_co_kpi in _CO_GROUPED_BAR:
                            # Grouped/colored bar chart
                            bar_colors = []
                            for v in ts[a_col]:
                                if a_thresh:
                                    fl = a_thresh(v)
                                    bar_colors.append(
                                        {"Green": SEA_GREEN, "Yellow": XANTHOUS,
                                         "Red": RED_FLAG}.get(fl, NAVY))
                                else:
                                    bar_colors.append(NAVY)
                            fig_co_kpi = go.Figure(go.Bar(
                                x=ts["_plabel"], y=ts[a_col],
                                marker_color=bar_colors, opacity=0.85, name=active_co_kpi,
                            ))
                            fig_co_kpi.update_layout(
                                height=400, plot_bgcolor="white", paper_bgcolor="white",
                                margin=dict(l=0, r=0, t=10, b=0),
                                font=dict(family="Arial", color=NAVY, size=10),
                                xaxis=dict(tickangle=-45, tickmode="linear", dtick=1,
                                           tickfont=dict(size=9), gridcolor=BORDER),
                                yaxis=dict(tickformat=tick_fmt, gridcolor=BORDER),
                            )
                        else:
                            # Line chart (default for all LTM metrics)
                            line_color = (
                                {"Green": SEA_GREEN, "Yellow": XANTHOUS, "Red": RED_FLAG}
                                .get(a_thresh(ts[a_col].iloc[-1]), NAVY)
                                if a_thresh and not ts.empty else NAVY
                            )
                            fig_co_kpi = go.Figure(go.Scatter(
                                x=ts["_plabel"], y=ts[a_col],
                                mode="lines+markers", name=active_co_kpi,
                                line=dict(color=line_color, width=2),
                                marker=dict(size=6),
                                connectgaps=True,
                                fill="tozeroy",
                                fillcolor=f"rgba(7,23,51,0.07)",
                            ))
                            fig_co_kpi.update_layout(
                                height=400, plot_bgcolor="white", paper_bgcolor="white",
                                margin=dict(l=0, r=0, t=10, b=0),
                                font=dict(family="Arial", color=NAVY, size=10),
                                xaxis=dict(tickangle=-45, tickmode="linear", dtick=1,
                                           tickfont=dict(size=9), gridcolor=BORDER),
                                yaxis=dict(tickformat=tick_fmt, gridcolor=BORDER),
                            )

                        st.plotly_chart(fig_co_kpi, use_container_width=True)
                    else:
                        st.info("Not enough data in the selected date range.")
                else:
                    st.info(f"{active_co_kpi} data not available in quarterly records.")
            else:
                st.info("No KPI data available for this company.")
        else:
            st.info("No quarterly data available for this company.")

    with tab2:
        # ── Company-Specific Analysis: pulls from page_company_kpis ─────────────
        try:
            from page_company_kpis import (
                _fmt, _delta_str, _make_bar_chart, _make_line_chart,
                _build_kpi_context, _render_ai_summary,
                CHART_COLORS, NAVY as KPI_NAVY, SLATE as KPI_SLATE,
                BORDER as KPI_BORDER, LIGHT_BG as KPI_LIGHT_BG,
            )
            from company_kpi_config import COMPANY_KPI_CONFIG
            from db import load_company_kpis, load_company_kpis_all

            # ── Period selector ──────────────────────────────────────────────
            _p_col, _ = st.columns([3, 5])
            with _p_col:
                _period_mode = st.radio(
                    "Period",
                    ["Monthly", "Quarterly", "Annual"],
                    index=1,
                    horizontal=True,
                    key=f"csa_period_{selected}",
                    label_visibility="collapsed",
                )

            if selected not in COMPANY_KPI_CONFIG:
                st.info(f"No Company-Specific Analysis configured for {selected} yet.")
            else:
                cfg        = COMPANY_KPI_CONFIG[selected]
                kpi_cards  = cfg.get("kpi_cards", [])
                kpi_charts = cfg.get("kpi_charts", [])
                all_attrs  = list({k["attribute"] for k in kpi_cards + kpi_charts})
                df_kpi     = load_company_kpis(selected, all_attrs, _period_mode)

                # ── Supplement with financials_quarterly for Datasheet attrs ──
                # Some attributes (Net Leverage, TEV, etc.) live in
                # financials_quarterly.csv, not company_kpis.csv.
                # Map them in so KPI cards don't show NaN.
                _QUARTERLY_FALLBACK = {
                    "Net Debt / EBITDA (Datasheet)": "net_leverage",
                    "LTM Free Cash Flow (Datasheet)": "ltm_free_cash_flow",
                    "Cash (Datasheet)":               "cash",
                    "Debt Service Coverage Ratio (Datasheet)": "debt_service_coverage",
                    "Fixed Rate Debt (Datasheet)":    "fixed_rate_debt",
                    "Floating Rate Debt (Datasheet)": "floating_rate_debt",
                    "Total Gross Debt (Datasheet)":   "total_gross_debt",
                    "LTM Net Sales (Actual) (Datasheet)": "revenue",
                    "LTM Adj. EBITDA (Datasheet)":    "adj_ebitda",
                }
                _missing_attrs = [
                    a for a in all_attrs
                    if a in _QUARTERLY_FALLBACK and (
                        df_kpi.empty or a not in df_kpi.columns or
                        df_kpi[a].isna().all()
                    )
                ]
                if _missing_attrs:
                    try:
                        _q_fin = load_quarterly(selected)
                        if not _q_fin.empty:
                            _q_fin = _q_fin.copy()
                            _q_fin["cash_flow_date"] = pd.to_datetime(
                                _q_fin["cash_flow_date"], errors="coerce"
                            )
                            _ptype = {"Monthly": "Monthly", "Quarterly": "Quarterly",
                                      "Annual": "Annual"}.get(_period_mode, "Quarterly")
                            if "period" in _q_fin.columns:
                                _q_fin = _q_fin[_q_fin["period"] == _ptype]
                            _q_fin = _q_fin.sort_values("cash_flow_date")
                            # Add period_label if missing
                            if "period_label" not in _q_fin.columns:
                                _q_fin["period_label"] = (
                                    "Q" + _q_fin["cash_flow_date"].dt.quarter.astype(str)
                                    + " " + _q_fin["cash_flow_date"].dt.year.astype(str)
                                )
                            for _attr in _missing_attrs:
                                _qcol = _QUARTERLY_FALLBACK[_attr]
                                if _qcol in _q_fin.columns:
                                    if df_kpi.empty:
                                        # Build df_kpi from quarterly financials
                                        df_kpi = _q_fin[
                                            ["cash_flow_date", "period_label"]
                                        ].drop_duplicates().copy()
                                    # Merge the column in by date
                                    _src = _q_fin[["cash_flow_date", _qcol]].drop_duplicates(
                                        "cash_flow_date", keep="last"
                                    )
                                    if _attr not in df_kpi.columns:
                                        df_kpi = df_kpi.merge(
                                            _src.rename(columns={_qcol: _attr}),
                                            on="cash_flow_date", how="left"
                                        )
                    except Exception:
                        pass

                if df_kpi.empty:
                    st.info(f"No {_period_mode} KPI data found for {selected}. "
                            f"Ensure company_kpis.csv is up to date.")
                else:
                    # ── KPI cards ────────────────────────────────────────────
                    _latest = df_kpi.sort_values("cash_flow_date").iloc[-1]
                    _prev_rows = df_kpi.sort_values("cash_flow_date")
                    _prev = _prev_rows.iloc[-2] if len(_prev_rows) >= 2 else None

                    # ── Deduplicate to one row per display period ─────────────
                    if _period_mode == "Quarterly" and not df_kpi.empty:
                        df_kpi = (df_kpi
                                  .sort_values("cash_flow_date")
                                  .assign(_qkey=lambda d: (
                                      d["cash_flow_date"].dt.year.astype(str) + "Q" +
                                      d["cash_flow_date"].dt.quarter.astype(str)
                                  ))
                                  .drop_duplicates(subset=["_qkey"], keep="last")
                                  .drop(columns=["_qkey"])
                                  .reset_index(drop=True))
                        df_kpi["period_label"] = (
                            "Q" + df_kpi["cash_flow_date"].dt.quarter.astype(str)
                            + " " + df_kpi["cash_flow_date"].dt.year.astype(str)
                        )
                        _latest   = df_kpi.sort_values("cash_flow_date").iloc[-1]
                        _prev_rows = df_kpi.sort_values("cash_flow_date")
                        _prev     = _prev_rows.iloc[-2] if len(_prev_rows) >= 2 else None

                    # Build dynamic section header: "Latest Period: Q3 2025 vs. Q2 2025"
                    _cur_lbl  = str(_latest.get("period_label", "")).strip() if "period_label" in _latest.index else ""
                    _prev_lbl = str(_prev.get("period_label", "")).strip() if _prev is not None and "period_label" in _prev.index else ""
                    if _cur_lbl and _prev_lbl:
                        _period_header = f"Latest Period: {_cur_lbl} vs. {_prev_lbl}"
                    elif _cur_lbl:
                        _period_header = f"Latest Period: {_cur_lbl}"
                    else:
                        _period_header = "Latest Period"
                    st.markdown(f'<div class="section-header-co">{_period_header}</div>',
                                unsafe_allow_html=True)

                    _card_cols = st.columns(len(kpi_cards)) if kpi_cards else []
                    for _i, _card in enumerate(kpi_cards):
                        _attr     = _card["attribute"]
                        _fmt_str  = _card["format"]
                        _label    = _card["label"]
                        # Use last non-NaN value — handles sparse attributes
                        # (e.g. Net Leverage only populated at quarter-end)
                        _sorted = df_kpi.sort_values("cash_flow_date")
                        if _attr in _sorted.columns:
                            _non_null = _sorted[_sorted[_attr].notna()]
                            _val  = _non_null[_attr].iloc[-1] if not _non_null.empty else None
                            _pval = _non_null[_attr].iloc[-2] if len(_non_null) >= 2 else None
                        else:
                            _val, _pval = None, None
                        _delta, _dcol = _delta_str(_val, _pval, _fmt_str)
                        with _card_cols[_i]:
                            st.markdown(f"""
                            <div class="kpi-card-co">
                                <div class="label">{_label}</div>
                                <div class="value">{_fmt(_val, _fmt_str)}</div>
                                <div class="delta" style="color:{_dcol};">{_delta}&nbsp;</div>
                            </div>
                            """, unsafe_allow_html=True)

                    # ── AI Summary ───────────────────────────────────────────
                    st.markdown('<div class="section-header-co">AI Summary</div>',
                                unsafe_allow_html=True)
                    _render_ai_summary_categorized(selected, df_kpi, kpi_cards, kpi_charts)

                    st.markdown("<hr style='border-color:#E0E4EA; margin:24px 0;'>",
                                unsafe_allow_html=True)

                    # ── Core Power bespoke visuals ───────────────────────────
                    # Three dedicated charts (TTM EBITDA, Revenue Mix, Waterfall)
                    # rendered before the standard KPI grid.
                    if selected == "Core Power":
                        try:
                            from corepower_visuals import render_corepower_visuals
                            from db import load_company_kpis_all
                            _cp_all = load_company_kpis_all()
                            render_corepower_visuals(_cp_all, _period_mode)
                            st.markdown(
                                "<hr style='border-color:#E0E4EA; margin:28px 0 20px 0;'>",
                                unsafe_allow_html=True,
                            )
                        except Exception as _cpe:
                            st.warning(f"Core Power visuals error: {_cpe}")

                    # ── Charts: grouped by theme for Core Power ──────────────
                    # For Core Power, organise charts into themed sections.
                    # For all other companies, render as 2-col grid (existing behaviour).
                    _is_core_power = (selected == "Core Power")

                    if _is_core_power:
                        _CHART_GROUPS = [
                            ("Revenue Mix", [
                                "Total Studio Revenue", "Member Cash Revenue",
                                "Non-Member Revenue", "Membership Revenue",
                                "Corporate & Franchise Rev", "Retail Revenue",
                                "Retail Gross Margin", "Franchise & Royalties",
                            ]),
                            ("Studio Economics", [
                                "Studio Contribution", "Studio Contribution ex-Occ",
                                "Studio Contribution ex-SLR", "Studio Expense ex-Rent",
                                "Labor", "Occupancy (Cash Rent)", "Programming",
                                "Pre-Opening Expense",
                            ]),
                            ("Operating Metrics", [
                                "Avg Membership Price", "Attendance / Studio (Mem)",
                                "Attendance / Studio (Non-Mem)", "Classes / Day",
                            ]),
                            ("Liquidity & Debt", [
                                "LTM Free Cash Flow", "Cash Balance",
                                "Debt Service Coverage", "Net Leverage Trend",
                                "Floating Rate Debt", "Fixed Rate Debt",
                            ]),
                        ]
                        # Build a label→config lookup
                        _chart_by_label = {c["label"]: c for c in kpi_charts}
                        # Dedup chart data: one row per period label
                        _chart_df = (df_kpi
                                     .sort_values("cash_flow_date")
                                     .drop_duplicates(subset=["period_label"], keep="last")
                                     .tail(12))

                        for _group_name, _group_labels in _CHART_GROUPS:
                            _group_charts = [_chart_by_label[l] for l in _group_labels
                                             if l in _chart_by_label]
                            if not _group_charts:
                                continue
                            st.markdown(f'<div class="section-header-co">{_group_name}</div>',
                                        unsafe_allow_html=True)
                            for _row_start in range(0, len(_group_charts), 2):
                                _pair = _group_charts[_row_start: _row_start + 2]
                                _gcols = st.columns(2)
                                for _ci, _cc in enumerate(_pair):
                                    _attr  = _cc["attribute"]
                                    _fmt_c = _cc["format"]
                                    _lbl   = _cc["label"]
                                    _ctype = _cc.get("chart", "bar")
                                    _color = CHART_COLORS[(_row_start + _ci) % len(CHART_COLORS)]
                                    with _gcols[_ci]:
                                        _has = (_attr in _chart_df.columns
                                                and _chart_df[_attr].notna().any())
                                        st.markdown(
                                            f'<div class="chart-card-co">'
                                            f'<div class="chart-title-co">{_lbl}</div></div>',
                                            unsafe_allow_html=True
                                        )

                                        # Per-period comment input (stored in session state)
                                        _comment_key = f"chart_comments_{selected}_{_attr}"
                                        if _comment_key not in st.session_state:
                                            st.session_state[_comment_key] = {}

                                        if not _has:
                                            st.caption(f"No data for '{_attr}'")
                                            continue

                                        if _ctype == "line":
                                            _fig = _make_line_chart(_chart_df, _attr, _lbl, _fmt_c, _color)
                                        else:
                                            _fig = _make_bar_chart(_chart_df, _attr, _lbl, _fmt_c, _color)

                                        # Overlay annotations from saved comments
                                        _comments = st.session_state[_comment_key]
                                        if _comments and _attr in _chart_df.columns:
                                            for _period, _note in _comments.items():
                                                if _note:
                                                    _fig.add_annotation(
                                                        x=_period, y=0,
                                                        text=f"💬 {_note[:30]}{'…' if len(_note)>30 else ''}",
                                                        showarrow=True, arrowhead=2,
                                                        arrowcolor=KPI_SLATE,
                                                        font=dict(size=9, color=KPI_SLATE),
                                                        bgcolor="white",
                                                        bordercolor=KPI_SLATE,
                                                        borderwidth=1,
                                                        yref="paper", yanchor="bottom", ay=-40
                                                    )

                                        st.plotly_chart(_fig, use_container_width=True,
                                                        config={"displayModeBar": False})

                                        # Comment input
                                        with st.expander("Add comment", expanded=False):
                                            _avail_periods = (
                                                _chart_df["period_label"].dropna().tolist()
                                                if "period_label" in _chart_df.columns else []
                                            )
                                            if _avail_periods:
                                                _sel_period = st.selectbox(
                                                    "Period",
                                                    _avail_periods,
                                                    key=f"cmt_period_{selected}_{_attr}",
                                                    label_visibility="collapsed",
                                                )
                                                _cmt_text = st.text_input(
                                                    "Comment",
                                                    value=st.session_state[_comment_key].get(_sel_period, ""),
                                                    key=f"cmt_text_{selected}_{_attr}_{_sel_period}",
                                                    placeholder="Add a note for this period…",
                                                    label_visibility="collapsed",
                                                )
                                                if st.button("Save", key=f"cmt_save_{selected}_{_attr}_{_sel_period}",
                                                             use_container_width=False):
                                                    st.session_state[_comment_key][_sel_period] = _cmt_text
                                                    st.rerun()
                    else:
                        # ── Standard 2-column grid for all other companies ────
                        st.markdown('<div class="section-header-co">Trend Charts</div>',
                                    unsafe_allow_html=True)
                        _chart_df = (df_kpi
                                     .sort_values("cash_flow_date")
                                     .drop_duplicates(subset=["period_label"], keep="last")
                                     .tail(12))
                        for _row_start in range(0, len(kpi_charts), 2):
                            _pair = kpi_charts[_row_start: _row_start + 2]
                            _gcols = st.columns(2)
                            for _ci, _cc in enumerate(_pair):
                                _attr  = _cc["attribute"]
                                _fmt_c = _cc["format"]
                                _lbl   = _cc["label"]
                                _ctype = _cc.get("chart", "bar")
                                _color = CHART_COLORS[(_row_start + _ci) % len(CHART_COLORS)]
                                with _gcols[_ci]:
                                    _has = (_attr in _chart_df.columns
                                            and _chart_df[_attr].notna().any())
                                    st.markdown(
                                        f'<div class="chart-card-co">'
                                        f'<div class="chart-title-co">{_lbl}</div></div>',
                                        unsafe_allow_html=True
                                    )
                                    if not _has:
                                        st.caption(f"No data for '{_attr}'")
                                        continue
                                    if _ctype == "line":
                                        _fig = _make_line_chart(_chart_df, _attr, _lbl, _fmt_c, _color)
                                    else:
                                        _fig = _make_bar_chart(_chart_df, _attr, _lbl, _fmt_c, _color)
                                    st.plotly_chart(_fig, use_container_width=True,
                                                    config={"displayModeBar": False})

        except Exception as _exc:
            st.error(f"Company-Specific Analysis error: {_exc}")

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

        # Threshold explanations — auto-collapsed by default
        ALERT_THRESHOLDS = {
            "Net Debt / EBITDA":      ("< 2.0x",  "2.0–4.0x",  "4.0–6.0x",  "> 6.0x",  "Net Debt ÷ LTM Credit Agreement EBITDA"),
            "Gross Debt / EBITDA":    ("< 3.0x",  "3.0–5.0x",  "5.0–7.0x",  "> 7.0x",  "Total Gross Debt (Datasheet) ÷ LTM Credit Agreement EBITDA"),
            "Sr. Secured / EBITDA":   ("< 2.0x",  "2.0–3.5x",  "3.5–5.0x",  "> 5.0x",  "Senior Secured Portion (Gross) (Datasheet) ÷ LTM EBITDA"),
            "Interest Coverage":      ("> 4.0x",  "2.5–4.0x",  "1.5–2.5x",  "< 1.5x",  "LTM Adj. EBITDA ÷ LTM Cash Interest Expense"),
            "Debt Service Coverage":  ("> 2.5x",  "1.8–2.5x",  "1.2–1.8x",  "< 1.2x",  "(LTM EBITDA − Capex) ÷ (Interest + Principal)"),
            "Free Cash Flow":         ("Strong+", "Positive",  "0–Slight−", "< 0",     "LTM EBITDA − Capex − ΔNWC − Cash Taxes"),
            "EBITDA Margin":          ("> 30%",   "20–30%",    "10–20%",    "< 10%",   "LTM Adj. EBITDA ÷ LTM Net Sales"),
            "TEV / Revenue":          ("< 1.5x",  "1.5–3.0x",  "3.0–5.0x",  "> 5.0x",  "Total Enterprise Value ÷ LTM Net Sales"),
            "TEV / EBITDA":           ("< 6.0x",  "6.0–10.0x", "10.0–16.0x","> 16.0x", "Total Enterprise Value ÷ LTM EBITDA"),
            "MOIC":                   ("> 2.5x",  "1.5–2.5x",  "1.0–1.5x",  "< 1.0x",  "(Realized + Unrealized Value) ÷ Total Cost"),
            "Cash / Gross Debt":      ("> 20%",   "10–20%",    "5–10%",     "< 5%",    "Cash ÷ Total Gross Debt (Datasheet)"),
            "Floating Rate Debt %":   ("< 20%",   "20–50%",    "50–80%",    "> 80%",   "Floating Rate Debt (Datasheet) ÷ Total Gross Debt (Datasheet)"),
        }

        with st.expander("Flag Thresholds & Calculation Methodology", expanded=False):
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
                _flag_row = company_row.iloc[0].copy()

                # ── Supplement missing metrics from financials_quarterly ────────
                # Gross Debt/EBITDA, Sr. Secured/EBITDA, Cash/Gross Debt,
                # Floating Rate % — all null in portfolio_flags.csv but
                # available in financials_quarterly.csv
                try:
                    _q_supp = load_quarterly(selected)
                    if not _q_supp.empty and "period" in _q_supp.columns:
                        _q_supp = (_q_supp[_q_supp["period"] == "Quarterly"]
                                   .sort_values("cash_flow_date"))
                        _ql = _q_supp.dropna(subset=["total_gross_debt"]).iloc[-1] if not _q_supp.empty else None
                        if _ql is not None:
                            _ltm_ebitda = float(_ql.get("adj_ebitda") or 0)
                            _gross_debt = float(_ql.get("total_gross_debt") or 0)
                            _sr_sec     = float(_ql.get("senior_secured_debt") or 0)
                            _cash       = float(_ql.get("cash") or 0)
                            _float_debt = float(_ql.get("floating_rate_debt") or 0)
                            _as_of      = str(_ql.get("period_label", ""))

                            # Gross Debt / EBITDA
                            if pd.isna(_flag_row.get("gross_leverage")) and _ltm_ebitda:
                                _flag_row["gross_leverage"] = _gross_debt / _ltm_ebitda
                            # Sr. Secured / EBITDA
                            if pd.isna(_flag_row.get("senior_secured_leverage")) and _ltm_ebitda:
                                _flag_row["senior_secured_leverage"] = _sr_sec / _ltm_ebitda
                            # Cash / Gross Debt
                            if pd.isna(_flag_row.get("cash_to_debt")) and _gross_debt:
                                _flag_row["cash_to_debt"] = _cash / _gross_debt
                            # Floating Rate %
                            if pd.isna(_flag_row.get("floating_rate_pct")) and _gross_debt:
                                _flag_row["floating_rate_pct"] = _float_debt / _gross_debt

                            # Show period being referenced
                            st.caption(f"Metrics as of **{_as_of}** · supplemented from quarterly financials where portfolio_flags.csv is null")
                except Exception:
                    pass

                render_company_scorecard(_flag_row)
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
        # News — coming soon
        st.markdown(f"""
        <div style="background:#F8F9FA; border:1px dashed #CCCCCC; border-radius:6px;
                    padding:20px 24px; margin-bottom:16px;">
            <div style="font-size:13px; font-weight:700; color:#999; font-family:Arial;
                        margin-bottom:4px;">📰 Company News</div>
            <div style="font-size:12px; color:#BBBBBB; font-family:Arial;">
                News feed coming soon.
            </div>
        </div>
        """, unsafe_allow_html=True)

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

