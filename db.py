"""
db.py — CSV-only data loaders for Streamlit Cloud demo
No database, no SQL, no Azure, no ODBC. Just reads CSV files from data/
"""

import pandas as pd
import streamlit as st
from pathlib import Path

# CSVs sit in the same directory as db.py (repo root)
DATA_DIR = Path(__file__).parent


def _csv(filename: str) -> pd.DataFrame:
    path = DATA_DIR / filename
    if not path.exists():
        st.warning(f"Data file not found: `{filename}` (looked in `{DATA_DIR}`)")
        return pd.DataFrame()
    # Try encodings in order — SQL Server / Excel exports are often latin-1 or cp1252
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, low_memory=False, encoding=encoding)
            for col in df.columns:
                if any(x in col.lower() for x in ["date", "published"]):
                    try:
                        df[col] = pd.to_datetime(df[col], errors="coerce")
                    except Exception:
                        pass
            return df
        except UnicodeDecodeError:
            continue
    # Last resort: ignore undecodable bytes
    df = pd.read_csv(path, low_memory=False, encoding="latin-1", errors="replace")
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
def load_entry_vs_current() -> pd.DataFrame:
    return _csv("entry_vs_current.csv")

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
    df = _csv("financials_quarterly.csv")
    if df.empty:
        return df

    # ------------------------------------------------------------------
    # Detect long vs wide format
    # ------------------------------------------------------------------
    long_indicators = {"attribute_name", "metric_name", "attribute", "metric"}
    is_long = bool(long_indicators & set(c.lower() for c in df.columns))

    if not is_long:
        return df   # Already wide — return as-is

    # ------------------------------------------------------------------
    # LONG FORMAT (ts_entity_financials style):
    # Columns: company_name, period, tag, attribute_name,
    #          cash_flow_date, as_of_date, true_up_value, ...
    #
    # Strategy:
    #  1. Keep most recent as_of_date per (company, period_type,
    #     cash_flow_date, attribute_name)
    #  2. Pivot attribute_name → columns
    #  3. Return one row per (company_name, period, cash_flow_date)
    #     so the app can filter by period type exactly
    # ------------------------------------------------------------------

    # Normalise column names
    col_map = {c: c.lower().replace(" ", "_") for c in df.columns}
    df = df.rename(columns=col_map)

    # Identify key columns
    company_col  = next((c for c in df.columns if c in
                         ("company_name", "company", "entity_name")), None)
    attr_col     = next((c for c in df.columns if c in
                         ("attribute_name", "metric_name", "attribute")), None)
    val_col      = next((c for c in df.columns if c in
                         ("true_up_value", "value", "amount", "val")), None)
    date_col     = next((c for c in df.columns if c in
                         ("cash_flow_date", "period_date", "date")), None)
    as_of_col    = next((c for c in df.columns if c in
                         ("as_of_date", "as_of", "snapshot_date")), None)
    period_col   = next((c for c in df.columns if c in
                         ("period", "frequency", "period_type", "freq")), None)

    if not all([company_col, attr_col, val_col, date_col]):
        st.warning(f"Cannot parse financials CSV. Columns: {list(df.columns)}")
        return df

    # Filter to Actual version only — exclude At-Entry and Budget
    if "version" in df.columns:
        df = df[df["version"] == "Actual"]
    if as_of_col:
        df[as_of_col] = pd.to_datetime(df[as_of_col], errors="coerce")
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")

    # ------------------------------------------------------------------
    # Map attribute names → short column names
    # ------------------------------------------------------------------
    ATTR_MAP = {
        # ---- LTM Revenue (use Valuation LTM Revenue — correct pre-calc LTM) ----
        "valuation ltm revenue":                        "revenue",

        # ---- LTM EBITDA ----
        "ltm adj. ebitda (global)":                     "adj_ebitda",
        "valuation ltm ebitda":                         "adj_ebitda",

        # ---- Gross Profit / Margins ----
        "gross profit":                                 "gross_profit",
        "gross margin (global)":                        "gross_margin_pct",
        "adj. ebitda margin %":                         "adj_ebitda_margin_pct",
        "ebitda margin %":                              "adj_ebitda_margin_pct",

        # ---- Leverage / Coverage ratios ----
        "total net leverage (global)":                  "net_leverage",
        "net debt / ebitda (global)":                   "net_leverage",
        "total debt / ebitda (global)":                 "net_leverage",
        "total gross leverage (global)":                "gross_leverage",
        "senior secured gross leverage (global)":       "senior_secured_leverage",
        "interest coverage ratio (global)":             "interest_coverage",
        "ebitda / interest expense":                    "interest_coverage",
        "debt service coverage ratio (global)":         "debt_service_coverage",
        "ebitda / (interest+principal)":                "debt_service_coverage",

        # ---- Net Debt / Debt components ----
        "net debt (global)":                            "net_debt",
        "valuation net debt":                           "net_debt",
        "total gross debt (global)":                    "total_gross_debt",
        "floating rate debt (global)":                  "floating_rate_debt",
        "fixed rate debt (global)":                     "fixed_rate_debt",
        "pik debt (global)":                            "pik_debt",
        "other debt (global)":                          "other_debt",
        "senior secured portion (gross) (global)":      "senior_secured_debt",
        "unrestricted cash (global)":                   "cash",
        "cash (global)":                                "cash",

        # ---- LTM Cash Flow items ----
        "ltm credit agreement adj. ebitda (global)":    "credit_agreement_ebitda",
        "ltm free cash flow (global)":                  "free_cash_flow",
        "ltm capex (excl. m&a purchase capex) (global)":"capex",
        "ltm cash interest expense (gross) (global)":   "cash_interest_expense",
        "ltm cash taxes (including distributions) (global)": "cash_taxes",
        "ltm increase / decrease in nwc (global)":      "change_in_nwc",
        "ltm mandatory principal payments (global)":    "mandatory_principal",

        # ---- Valuation / TEV ----
        "total enterprise value (tev)":                 "current_tev",
        "tev / net sales (global)":                     "tev_to_revenue",
        "tev / ebitda (global)":                        "tev_to_ebitda",

        # ---- Returns / Growth ----
        "gross moi":                                    "gross_moi",
        "gross irr":                                    "gross_irr",
        "revenue growth %":                             "revenue_yoy",
        "adj. ebitda growth %":                         "ebitda_growth",
        "total cost basis":                             "total_cost",
        "unrealized value":                             "unrealized_value",
        "realized proceeds":                            "realized_proceeds",
        "total realized & unrealized value":            "total_value",
    }

    df["_attr_norm"] = df[attr_col].str.strip().str.lower()
    df["_col_name"]  = df["_attr_norm"].map(ATTR_MAP)

    # Keep only rows we know how to map
    mapped = df[df["_col_name"].notna()].copy()

    if mapped.empty:
        # Show unmapped attribute names to help debugging
        sample = df["_attr_norm"].unique()[:15].tolist()
        st.warning(f"No attribute names matched the mapping. Sample values: {sample}")
        return df

    # ------------------------------------------------------------------
    # Deduplicate: keep most recent as_of_date per
    # (company, period_type, cash_flow_date, attribute)
    # ------------------------------------------------------------------
    group_keys = [company_col, date_col, "_col_name"]
    if period_col:
        group_keys.insert(1, period_col)
    if as_of_col:
        mapped = (mapped.sort_values(as_of_col)
                        .groupby(group_keys, as_index=False)
                        .last())
    else:
        mapped = mapped.groupby(group_keys, as_index=False).last()

    # ------------------------------------------------------------------
    # Pivot to wide: one row per (company, period_type, cash_flow_date)
    # ------------------------------------------------------------------
    pivot_index = [company_col, date_col]
    if period_col:
        pivot_index.insert(1, period_col)

    wide = mapped.pivot_table(
        index=pivot_index,
        columns="_col_name",
        values=val_col,
        aggfunc="last"
    ).reset_index()
    wide.columns.name = None

    # Standardise column names
    rename = {company_col: "company_name", date_col: "cash_flow_date"}
    if period_col:
        rename[period_col] = "period"
    wide = wide.rename(columns=rename)

    wide["cash_flow_date"] = pd.to_datetime(wide["cash_flow_date"], errors="coerce")

    # period_label for Quarterly grouping compatibility
    wide["period_label"] = wide["cash_flow_date"].dt.to_period("Q").astype(str)

    return wide.sort_values(["company_name", "cash_flow_date"])

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
