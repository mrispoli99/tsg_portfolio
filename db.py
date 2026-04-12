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

    # Detect format: wide (has metric columns directly) vs long (has attribute_name column)
    long_format_indicators = {"attribute_name", "metric_name", "attribute", "metric"}
    is_long = bool(long_format_indicators & set(df.columns.str.lower()))

    if not is_long:
        # Already wide — return as-is
        return df

    # -----------------------------------------------------------------------
    # PIVOT long → wide
    # Identify key columns by common names
    # -----------------------------------------------------------------------
    cols_lower = {c.lower(): c for c in df.columns}

    # Company identifier
    company_col = next((cols_lower[k] for k in
                        ["company_name", "company", "entity_name", "name"]
                        if k in cols_lower), None)

    # Date column
    date_col = next((cols_lower[k] for k in
                     ["cash_flow_date", "period_date", "date", "period_end"]
                     if k in cols_lower), None)

    # Attribute / metric name column
    attr_col = next((cols_lower[k] for k in
                     ["attribute_name", "metric_name", "attribute", "metric"]
                     if k in cols_lower), None)

    # Value column
    val_col = next((cols_lower[k] for k in
                    ["value", "amount", "val", "metric_value"]
                    if k in cols_lower), None)

    # Frequency column (Monthly / Quarterly / Annual)
    freq_col = next((cols_lower[k] for k in
                     ["frequency", "freq", "period_type"]
                     if k in cols_lower), None)

    # as_of_date — use most recent snapshot per company/period/metric
    as_of_col = next((cols_lower[k] for k in
                      ["as_of_date", "as_of", "snapshot_date", "report_date"]
                      if k in cols_lower), None)

    if not all([company_col, date_col, attr_col, val_col]):
        st.warning("financials_quarterly.csv appears to be long-format but required "
                   "columns (company, date, attribute_name, value) could not be identified. "
                   f"Columns found: {list(df.columns)}")
        return df

    # Parse dates
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if as_of_col:
        df[as_of_col] = pd.to_datetime(df[as_of_col], errors="coerce")

    # Ensure value is numeric
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")

    # -----------------------------------------------------------------------
    # Map verbose attribute names → short column names
    # Add any additional mappings that match your SQL view's attribute_name values
    # -----------------------------------------------------------------------
    ATTR_MAP = {
        # Revenue / Net Sales
        "ltm net sales (actual) (datasheet)":   "revenue",
        "ltm net sales (actual)":               "revenue",
        "ltm revenue (actual)":                 "revenue",
        "ltm net sales":                        "revenue",
        "ltm revenue":                          "revenue",
        "net sales":                            "revenue",
        "revenue":                              "revenue",

        # EBITDA
        "ltm adj. ebitda (actual) (datasheet)": "adj_ebitda",
        "ltm adj. ebitda (actual)":             "adj_ebitda",
        "ltm adj ebitda (actual)":              "adj_ebitda",
        "ltm adjusted ebitda":                  "adj_ebitda",
        "ltm adj. ebitda":                      "adj_ebitda",
        "ltm adj ebitda":                       "adj_ebitda",
        "adj. ebitda":                          "adj_ebitda",
        "adj ebitda":                           "adj_ebitda",
        "ebitda (at entry) (datasheet)":        "entry_adj_ebitda",
        "ltm ebitda (at entry) (datasheet)":    "entry_adj_ebitda",
        "ltm ebitda (at entry)":                "entry_adj_ebitda",

        # Gross Profit
        "ltm gross profit (actual)":            "gross_profit",
        "ltm gross profit":                     "gross_profit",
        "gross profit":                         "gross_profit",

        # Net Leverage
        "total net leverage":                   "net_leverage",
        "net leverage":                         "net_leverage",
        "net debt / ebitda":                    "net_leverage",

        # Gross Leverage
        "total gross leverage":                 "gross_leverage",
        "gross debt / ebitda":                  "gross_leverage",

        # Senior Secured Leverage
        "senior secured leverage":              "senior_secured_leverage",
        "sr. secured / ebitda":                 "senior_secured_leverage",

        # Interest Coverage
        "interest coverage ratio":              "interest_coverage",
        "interest coverage":                    "interest_coverage",
        "ltm interest coverage":                "interest_coverage",

        # Debt Service Coverage
        "debt service coverage ratio":          "debt_service_coverage",
        "debt service coverage":                "debt_service_coverage",

        # Margins
        "ltm ebitda margin":                    "adj_ebitda_margin_pct",
        "ebitda margin":                        "adj_ebitda_margin_pct",
        "ltm gross margin":                     "gross_margin_pct",
        "gross margin":                         "gross_margin_pct",

        # Debt / Balance Sheet
        "total gross debt":                     "total_gross_debt",
        "gross debt":                           "total_gross_debt",
        "net debt":                             "net_debt",
        "cash":                                 "cash",
        "floating rate debt":                   "floating_rate_debt",
        "fixed rate debt":                      "fixed_rate_debt",
        "pik debt":                             "pik_debt",
        "senior secured debt":                  "senior_secured_debt",

        # Cash Flow / Other
        "ltm free cash flow":                   "free_cash_flow",
        "free cash flow":                       "free_cash_flow",
        "ltm capex":                            "capex",
        "capex":                                "capex",
        "ltm cash interest expense":            "cash_interest_expense",
        "cash interest expense":                "cash_interest_expense",
        "ltm cash taxes":                       "cash_taxes",
        "cash taxes":                           "cash_taxes",
        "ltm change in nwc":                    "change_in_nwc",
        "change in nwc":                        "change_in_nwc",
        "ltm mandatory principal payments":     "mandatory_principal",

        # Credit Agreement EBITDA
        "ltm credit agreement ebitda":          "credit_agreement_ebitda",
        "credit agreement ebitda":              "credit_agreement_ebitda",

        # Revenue YoY
        "revenue growth (yoy)":                 "revenue_yoy",
        "revenue yoy":                          "revenue_yoy",
        "yoy revenue growth":                   "revenue_yoy",

        # TEV multiples
        "tev / revenue":                        "tev_to_revenue",
        "tev / net sales":                      "tev_to_revenue",
        "tev / ebitda":                         "tev_to_ebitda",
    }

    # Normalise attribute names and map
    df["_attr_norm"] = df[attr_col].str.strip().str.lower()
    df["_col_name"]  = df["_attr_norm"].map(ATTR_MAP)

    # Keep only mapped rows (drop unmapped metrics)
    mapped = df[df["_col_name"].notna()].copy()

    if mapped.empty:
        st.warning(
            "financials_quarterly.csv is long-format but none of the attribute_name values "
            "matched the expected mapping. Check that attribute names match the ATTR_MAP in db.py. "
            f"Sample values: {df['_attr_norm'].unique()[:10].tolist()}"
        )
        return df

    # If multiple as_of snapshots exist, keep only the most recent per
    # company / date / attribute so we get one clean value per cell
    group_cols = [company_col, date_col, "_col_name"]
    if as_of_col:
        mapped = (mapped.sort_values(as_of_col)
                        .groupby(group_cols, as_index=False)
                        .last())
    else:
        mapped = (mapped.sort_values(date_col)
                        .groupby(group_cols, as_index=False)
                        .last())

    # Pivot to wide format
    wide = mapped.pivot_table(
        index=[company_col, date_col],
        columns="_col_name",
        values=val_col,
        aggfunc="last"
    ).reset_index()
    wide.columns.name = None

    # Rename company and date columns to standard names
    wide = wide.rename(columns={company_col: "company_name", date_col: "cash_flow_date"})

    # Add period_label (quarter string) for compatibility
    wide["cash_flow_date"] = pd.to_datetime(wide["cash_flow_date"], errors="coerce")
    wide["period_label"] = wide["cash_flow_date"].dt.to_period("Q").astype(str)

    # Add frequency label if available
    if freq_col and freq_col in mapped.columns:
        freq_map = (mapped.groupby([company_col, date_col])[freq_col]
                          .last().reset_index()
                          .rename(columns={company_col: "company_name",
                                           date_col:    "cash_flow_date"}))
        freq_map["cash_flow_date"] = pd.to_datetime(freq_map["cash_flow_date"], errors="coerce")
        wide = wide.merge(freq_map, on=["company_name", "cash_flow_date"], how="left")

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
