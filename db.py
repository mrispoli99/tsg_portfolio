"""
db.py — CSV-only data loaders for Streamlit Cloud demo
No database, no SQL, no Azure, no ODBC. Just reads CSV files from data/
"""

import pandas as pd
import streamlit as st
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def _csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        st.error(f"Missing data file: {filename}. Run export_to_csv.py on your VM.")
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    for col in df.columns:
        if any(x in col.lower() for x in ["date", "published"]):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass
    return df


@st.cache_data
def load_portfolio_overview() -> pd.DataFrame:
    return _csv("portfolio_overview.csv")

@st.cache_data
def load_fund_summary() -> pd.DataFrame:
    return _csv("fund_summary.csv")

@st.cache_data
def load_company_master() -> pd.DataFrame:
    return _csv("company_master.csv")

@st.cache_data
def load_flags() -> pd.DataFrame:
    return _csv("flags_and_alerts.csv")

@st.cache_data
def load_ltm_snapshot() -> pd.DataFrame:
    return _csv("ltm_snapshot.csv")

@st.cache_data
def load_quarterly_all() -> pd.DataFrame:
    return _csv("financials_quarterly.csv")

def load_quarterly(company_name: str = None) -> pd.DataFrame:
    df = load_quarterly_all()
    if company_name and not df.empty:
        df = df[df["company_name"] == company_name]
    return df

@st.cache_data
def load_yoy_all() -> pd.DataFrame:
    return _csv("yoy_growth.csv")

def load_yoy_growth(company_name: str = None) -> pd.DataFrame:
    df = load_yoy_all()
    if company_name and not df.empty:
        df = df[df["company_name"] == company_name]
    return df

@st.cache_data
def load_news_all() -> pd.DataFrame:
    return _csv("company_news.csv")

def load_news(company_name: str = None) -> pd.DataFrame:
    df = load_news_all()
    if company_name and not df.empty:
        df = df[df["company_name"] == company_name].head(20)
    return df

@st.cache_data
def load_portfolio_flags() -> pd.DataFrame:
    return _csv("portfolio_flags.csv")

def load_income_statement_ltm(company_name: str) -> pd.DataFrame:
    df = load_quarterly(company_name)
    if df.empty:
        return pd.DataFrame()
    skip = {"fiscal_year", "fiscal_quarter", "company_id"}
    value_cols = [c for c in df.columns
                  if df[c].dtype in ["float64", "float32", "int64"]
                  and c not in skip]
    df = df.sort_values("cash_flow_date", ascending=False)
    ltm_df = df.head(4)
    py_df  = df.iloc[4:8]
    rows = []
    for col in value_cols:
        ltm_val = ltm_df[col].sum() if not ltm_df[col].isna().all() else None
        py_val  = py_df[col].sum()  if not py_df[col].isna().all()  else None
        if not ltm_val and not py_val:
            continue
        delta     = (ltm_val - py_val) if ltm_val and py_val else None
        delta_pct = (delta / abs(py_val)) if delta and py_val else None
        rows.append({
            "attribute_name": col.replace("_", " ").title(),
            "tag":            "Income Statement",
            "ltm_value":      ltm_val,
            "py_value":       py_val,
            "delta":          delta,
            "delta_pct":      delta_pct,
        })
    return pd.DataFrame(rows)

def load_consumer_kpis() -> pd.DataFrame:
    df = load_quarterly_all()
    if df.empty:
        return pd.DataFrame()
    kpi_cols = ["revenue", "adj_ebitda", "net_leverage",
                "interest_coverage", "gross_margin_pct", "adj_ebitda_margin_pct"]
    rows = []
    for col in [c for c in kpi_cols if c in df.columns]:
        latest = (df.sort_values("cash_flow_date")
                    .groupby("company_name").last().reset_index())
        sub = latest[["company_name", "cash_flow_date", col]].dropna(subset=[col])
        sub = sub.copy()
        sub["attribute_name"] = col.replace("_", " ").title()
        sub["true_up_value"]  = sub[col]
        sub["tag"]            = "KPI"
        rows.append(sub[["company_name", "attribute_name",
                          "cash_flow_date", "true_up_value"]])
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

def get_company_list() -> list:
    df = load_company_master()
    return sorted(df["company_name"].dropna().tolist())

# Auth helper — reads from st.secrets if available, else open access for demo
def check_auth_password(entered: str) -> bool:
    try:
        return entered == st.secrets["auth"]["password"]
    except Exception:
        return True  # no secrets configured = open demo mode

# Formatting helpers
def format_millions(val, decimals=1):
    if val is None or pd.isna(val): return "—"
    if abs(val) >= 1000: return f"${val/1000:.{decimals}f}B"
    return f"${val:.{decimals}f}M"

def format_multiple(val, decimals=1):
    if val is None or pd.isna(val): return "—"
    return f"{val:.{decimals}f}x"

def format_pct(val, decimals=1):
    if val is None or pd.isna(val): return "—"
    return f"{val*100:.{decimals}f}%"

def flag_color(flag: str) -> str:
    return {"Red": "#C0392B", "Yellow": "#F3B51F", "Green": "#06865C"}.get(flag, "#888888")

def flag_emoji(flag: str) -> str:
    return {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(flag, "⚪")

# Stub — not needed in CSV mode
def get_engine():
    st.error("SQL mode not available in demo deployment.")
    st.stop()

def get_secret(key, section=None):
    if section:
        return st.secrets[section][key]
    return st.secrets[key]
