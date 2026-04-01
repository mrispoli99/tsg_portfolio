"""
ui.py — Shared UI components used across all page modules.
Avoids circular imports by keeping these out of app.py.
"""

import streamlit as st

NAVY      = "#071733"
SLATE     = "#3F6680"
SKY       = "#A8CFDE"
XANTHOUS  = "#F3B51F"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
BORDER    = "#E0E4EA"


def render_page_header(title: str):
    st.markdown(f"""
    <div style="padding:12px 0 8px 0; border-bottom:1px solid {BORDER}; margin-bottom:16px;">
        <span style="font-size:18px; font-weight:700; color:{NAVY};
                     font-family:Arial;">{title}</span>
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str):
    st.markdown(
        f'<div class="section-header">{title}</div>',
        unsafe_allow_html=True
    )


def kpi_tile(value: str, label: str, delta: str = "", delta_color: str = SLATE) -> str:
    delta_html = (f'<div class="kpi-tile-delta" style="color:{delta_color};">{delta}</div>'
                  if delta else "")
    return f"""
    <div class="kpi-tile">
        <div class="kpi-tile-value">{value}</div>
        <div class="kpi-tile-label">{label}</div>
        {delta_html}
    </div>"""


def kpi_tile_pending(label: str, note: str = "** Pending Investran data") -> str:
    return f"""
    <div class="kpi-tile-pending">
        <div class="kpi-tile-pending-value">—</div>
        <div class="kpi-tile-pending-label">{label}</div>
        <div class="kpi-tile-pending-note">{note}</div>
    </div>"""


def flag_badge(flag: str) -> str:
    from db import flag_emoji
    css = {"Red": "flag-red", "Yellow": "flag-yellow", "Green": "flag-green"}.get(flag, "")
    return f'<span class="metric-pill {css}">{flag_emoji(flag)} {flag}</span>'
