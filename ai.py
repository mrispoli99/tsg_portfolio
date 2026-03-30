"""
ai.py — Claude-powered portfolio analyst
"""

import json
import streamlit as st
import anthropic
import pandas as pd
from db import (
    load_fund_summary, load_ltm_snapshot, load_flags,
    load_quarterly, load_yoy_growth, format_millions,
    format_multiple, format_pct
)


@st.cache_resource
def get_client():
    return anthropic.Anthropic(api_key=st.secrets["anthropic"]["api_key"])


def build_portfolio_context() -> str:
    """Build a concise data context string for Claude."""
    fs   = load_fund_summary()
    ltm  = load_ltm_snapshot()
    flags = load_flags()

    # Summarise fund-level
    total_tev     = fs["current_tev"].sum()
    avg_leverage  = fs["net_leverage"].mean()
    red_count     = (flags["overall_flag"] == "Red").sum()
    yellow_count  = (flags["overall_flag"] == "Yellow").sum()
    green_count   = (flags["overall_flag"] == "Green").sum()

    # Company summaries
    companies = []
    for _, row in fs.iterrows():
        companies.append({
            "company":        row.get("company_name"),
            "sector":         row.get("sector"),
            "investment_date":str(row.get("investment_date", ""))[:10],
            "security_type":  row.get("security_type"),
            "ownership":      row.get("ownership_structure"),
            "entry_tev":      round(row["entry_tev"], 1) if pd.notna(row.get("entry_tev")) else None,
            "current_tev":    round(row["current_tev"], 1) if pd.notna(row.get("current_tev")) else None,
            "gross_moi":      round(row["gross_moi"], 2) if pd.notna(row.get("gross_moi")) else None,
            "ltm_revenue":    round(row["ltm_revenue"], 1) if pd.notna(row.get("ltm_revenue")) else None,
            "ltm_adj_ebitda": round(row["ltm_adj_ebitda"], 1) if pd.notna(row.get("ltm_adj_ebitda")) else None,
            "ebitda_margin":  round(row["ltm_adj_ebitda_margin"] * 100, 1) if pd.notna(row.get("ltm_adj_ebitda_margin")) else None,
            "net_leverage":   round(row["net_leverage"], 1) if pd.notna(row.get("net_leverage")) else None,
            "revenue_yoy":    round(row["revenue_yoy"] * 100, 1) if pd.notna(row.get("revenue_yoy")) else None,
            "flag":           row.get("overall_flag"),
        })

    context = f"""
You are an expert private equity portfolio analyst at TSG Consumer Partners.
You have access to the following portfolio data (all financial values in $M):

FUND SUMMARY:
- Active companies: {len(fs)}
- Total TEV: ${total_tev:.0f}M
- Avg Net Leverage: {avg_leverage:.1f}x
- Flags: {red_count} Red, {yellow_count} Yellow, {green_count} Green

PORTFOLIO COMPANIES:
{json.dumps(companies, indent=2)}

KPI BENCHMARKS (TSG thresholds):
- Revenue Growth: Green >10%, Yellow 0-10%, Red <0%
- EBITDA Margin: Green >18%, Yellow 10-18%, Red <10%  
- Net Leverage: Green <5x, Yellow 5-6x, Red >6x
- Interest Coverage: Green >3x, Yellow 2-3x, Red <2x

When answering:
- Be concise and direct — lead with the key insight
- Use specific numbers from the data
- Flag any concerns clearly
- Format numbers as $XM for dollars, X.Xx for multiples, X% for percentages
- If asked for a narrative or memo bullets, write in professional PE analyst style
"""
    return context


def build_company_context(company_name: str) -> str:
    """Build detailed context for a single company."""
    quarterly = load_quarterly(company_name)
    growth    = load_yoy_growth(company_name)
    flags     = load_flags()

    company_flags = flags[flags["company_name"] == company_name]
    flag_row = company_flags.iloc[0] if len(company_flags) > 0 else None

    # Last 8 quarters
    recent = quarterly.tail(8)
    trend_data = []
    for _, row in recent.iterrows():
        trend_data.append({
            "period":        row.get("period_label"),
            "revenue":       round(row["revenue"], 1) if pd.notna(row.get("revenue")) else None,
            "adj_ebitda":    round(row["adj_ebitda"], 1) if pd.notna(row.get("adj_ebitda")) else None,
            "ebitda_margin": round(row["adj_ebitda_margin_pct"] * 100, 1) if pd.notna(row.get("adj_ebitda_margin_pct")) else None,
            "net_leverage":  round(row["net_leverage"], 1) if pd.notna(row.get("net_leverage")) else None,
        })

    # Latest YoY
    latest_growth = growth.tail(1).iloc[0] if len(growth) > 0 else None

    context = f"""
You are an expert PE analyst at TSG Consumer Partners reviewing {company_name}.

CURRENT KPI STATUS:
"""
    if flag_row is not None:
        context += f"""
- Overall Flag: {flag_row.get('overall_flag')}
- LTM Revenue: ${flag_row.get('ltm_revenue', 0):.1f}M
- LTM Adj. EBITDA: ${flag_row.get('ltm_adj_ebitda', 0):.1f}M
- LTM EBITDA Margin: {flag_row.get('ltm_adj_ebitda_margin', 0)*100:.1f}%
- Net Leverage: {flag_row.get('net_leverage', 0):.1f}x
- Revenue YoY: {flag_row.get('revenue_yoy', 0)*100:.1f}%
- Revenue Flag: {flag_row.get('revenue_growth_flag')}
- EBITDA Margin Flag: {flag_row.get('ebitda_margin_flag')}
- Net Leverage Flag: {flag_row.get('net_leverage_flag')}
"""

    context += f"""
QUARTERLY TREND (last 8 quarters):
{json.dumps(trend_data, indent=2)}
"""

    if latest_growth is not None:
        context += f"""
LATEST YoY GROWTH:
- Revenue YoY: {latest_growth.get('revenue_yoy', 0)*100:.1f}%
- EBITDA YoY: {latest_growth.get('ebitda_yoy', 0)*100:.1f}%
"""

    context += """
Answer questions about this company with specific data references.
For memo bullets, use professional PE style: lead with the headline metric,
follow with the driver, note the benchmark comparison.
"""
    return context


def ask_claude(question: str, context: str, history: list) -> str:
    """Send a question to Claude with portfolio context and chat history."""
    client = get_client()

    messages = []
    # Include last 6 messages of history for conversational context
    for h in history[-6:]:
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": question})

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1500,
        system=context,
        messages=messages,
    )
    return response.content[0].text


def build_company_context_with_news(company_name: str) -> str:
    """Build company context including recent news headlines."""
    base_context = build_company_context(company_name)

    try:
        from db import load_news
        news_df = load_news(company_name)
        if not news_df.empty:
            headlines = []
            for _, row in news_df.head(10).iterrows():
                pub = str(row.get("published", ""))[:10]
                headlines.append(f"- [{pub}] {row.get('title','')} ({row.get('source','')})")
            news_section = "\n\nRECENT NEWS (last 30 days):\n" + "\n".join(headlines)
            base_context += news_section
    except Exception:
        pass

    return base_context


def build_portfolio_context_with_news() -> str:
    """Build portfolio context including recent news across all companies."""
    base_context = build_portfolio_context()

    try:
        from db import load_news
        news_df = load_news()
        if not news_df.empty:
            headlines = []
            for _, row in news_df.head(20).iterrows():
                pub = str(row.get("published", ""))[:10]
                headlines.append(
                    f"- [{pub}] {row.get('company_name','')} — {row.get('title','')} ({row.get('source','')})"
                )
            news_section = "\n\nRECENT PORTFOLIO NEWS (last 30 days):\n" + "\n".join(headlines)
            base_context += news_section
    except Exception:
        pass

    return base_context
