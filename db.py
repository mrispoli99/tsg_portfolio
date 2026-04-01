"""
db.py — Data loaders for TSG Portfolio Dashboard
=================================================
Supports two modes controlled by DATA_SOURCE environment variable
or automatic detection:

  MODE 1 — CSV (default when no DB secrets present)
    Reads from data/ folder — used for Streamlit Cloud demo deployment
    No database connection needed

  MODE 2 — SQL Server (when db secrets are present)
    Reads live from SQL Server views — used for VM / Azure App Service

Switch by setting environment variable:
    DATA_SOURCE=csv   → always use CSV files
    DATA_SOURCE=sql   → always use SQL Server
    (unset)           → auto-detect based on whether db secrets exist
"""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from pathlib import Path

# Path to CSV files — data/ folder sits next to this file
DATA_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# Mode detection
# ---------------------------------------------------------------------------

def _use_csv() -> bool:
    """Determine whether to use CSV or SQL mode."""
    override = os.environ.get("DATA_SOURCE", "").lower()
    if override == "csv":
        return True
    if override == "sql":
        return False
    # Auto-detect: use CSV if no database secrets are configured
    try:
        _ = st.secrets["database"]["server"]
        return False  # secrets exist → use SQL
    except Exception:
        return True   # no secrets → use CSV


# ---------------------------------------------------------------------------
# Secret helper (SQL mode only)
# ---------------------------------------------------------------------------

def get_secret(key: str, section: str = None) -> str:
    vault_url = os.environ.get("AZURE_KEYVAULT_URL")
    if vault_url:
        try:
            from azure.keyvault.secrets import SecretClient
            from azure.identity import DefaultAzureCredential
            client = SecretClient(vault_url=vault_url,
                                  credential=DefaultAzureCredential())
            prefix_map = {"database": "db", "auth": "auth", "anthropic": "anthropic"}
            prefix = prefix_map.get(section, section) if section else ""
            secret_name = f"{prefix}-{key}" if prefix else key
            return client.get_secret(secret_name).value
        except Exception:
            pass
    if section:
        return st.secrets[section][key]
    return st.secrets[key]


# ---------------------------------------------------------------------------
# SQL Engine (SQL mode only)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_engine():
    server   = get_secret("server",   "database")
    database = get_secret("database", "database")
    username = get_secret("username", "database")
    password = get_secret("password", "database")

    import pyodbc
    available = [d for d in pyodbc.drivers() if "SQL Server" in d]
    driver = sorted(available)[-1] if available else "ODBC Driver 17 for SQL Server"

    conn_str = (
        f"mssql+pyodbc://{username}:{quote_plus(password)}"
        f"@{server}/{database}"
        f"?driver={driver.replace(' ', '+')}"
        f"&TrustServerCertificate=yes"
        f"&Encrypt=yes"
        f"&Connection+Timeout=30"
    )

    try:
        engine = create_engine(conn_str, fast_executemany=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"""
**Database connection failed.**
Driver: `{driver}` | Server: `{server}` | Database: `{database}`
Error: `{str(e)}`
        """)
        st.stop()


# ---------------------------------------------------------------------------
# CSV loaders
# ---------------------------------------------------------------------------

def _csv(filename: str) -> pd.DataFrame:
    """Load a CSV file from the data/ folder."""
    path = DATA_DIR / filename
    if not path.exists():
        st.error(f"Data file not found: `{path}`. Run `export_to_csv.py` on your VM first.")
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    # Parse date columns automatically
    for col in df.columns:
        if any(x in col.lower() for x in ["date", "published", "fetched"]):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass
    return df


# ---------------------------------------------------------------------------
# Data loaders — auto-switch between CSV and SQL
# ---------------------------------------------------------------------------

@st.cache_data(ttl=86400)
def load_portfolio_overview() -> pd.DataFrame:
    if _use_csv():
        return _csv("portfolio_overview.csv")
    return pd.read_sql("SELECT * FROM dbo.vw_portfolio_overview", get_engine())


@st.cache_data(ttl=86400)
def load_fund_summary() -> pd.DataFrame:
    if _use_csv():
        return _csv("fund_summary.csv")
    return pd.read_sql(
        "SELECT * FROM dbo.vw_fund_summary WHERE company_name NOT LIKE '%Test%' ORDER BY current_tev DESC",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_company_master() -> pd.DataFrame:
    if _use_csv():
        return _csv("company_master.csv")
    return pd.read_sql(
        "SELECT * FROM dbo.vw_company_master WHERE company_name NOT LIKE '%Test%' ORDER BY company_name",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_flags() -> pd.DataFrame:
    if _use_csv():
        return _csv("flags_and_alerts.csv")
    return pd.read_sql(
        "SELECT * FROM dbo.vw_flags_and_alerts WHERE company_name NOT LIKE '%Test%' ORDER BY overall_flag, company_name",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_ltm_snapshot() -> pd.DataFrame:
    if _use_csv():
        return _csv("ltm_snapshot.csv")
    return pd.read_sql(
        "SELECT * FROM dbo.vw_ltm_snapshot WHERE company_name NOT LIKE '%Test%' ORDER BY ltm_revenue DESC",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_quarterly(company_name: str = None) -> pd.DataFrame:
    if _use_csv():
        df = _csv("financials_quarterly.csv")
        if company_name and not df.empty:
            df = df[df["company_name"] == company_name]
        return df
    if company_name:
        query = """
            SELECT * FROM dbo.vw_financials_quarterly
            WHERE company_name = :name
            ORDER BY cash_flow_date
        """
        return pd.read_sql(text(query), get_engine(), params={"name": company_name})
    return pd.read_sql(
        "SELECT * FROM dbo.vw_financials_quarterly WHERE company_name NOT LIKE '%Test%' ORDER BY company_name, cash_flow_date",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_yoy_growth(company_name: str = None) -> pd.DataFrame:
    if _use_csv():
        df = _csv("yoy_growth.csv")
        if company_name and not df.empty:
            df = df[df["company_name"] == company_name]
        return df
    if company_name:
        query = """
            SELECT * FROM dbo.vw_yoy_growth
            WHERE company_name = :name
            ORDER BY cash_flow_date
        """
        return pd.read_sql(text(query), get_engine(), params={"name": company_name})
    return pd.read_sql(
        "SELECT * FROM dbo.vw_yoy_growth WHERE company_name NOT LIKE '%Test%' ORDER BY company_name, cash_flow_date",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_news(company_name: str = None) -> pd.DataFrame:
    if _use_csv():
        df = _csv("company_news.csv")
        if company_name and not df.empty:
            df = df[df["company_name"] == company_name].head(20)
        return df
    if company_name:
        query = """
            SELECT TOP 20 company_name, title, summary, published, link, source
            FROM dbo.ts_company_news
            WHERE company_name = :name
            ORDER BY published DESC
        """
        return pd.read_sql(text(query), get_engine(), params={"name": company_name})
    return pd.read_sql(
        "SELECT TOP 100 * FROM dbo.ts_company_news ORDER BY published DESC",
        get_engine()
    )


@st.cache_data(ttl=86400)
def load_income_statement_ltm(company_name: str) -> pd.DataFrame:
    if _use_csv():
        # Build LTM vs PY from the quarterly CSV
        df = load_quarterly(company_name)
        if df.empty:
            return pd.DataFrame()

        # Numeric columns only
        value_cols = [c for c in df.columns
                      if df[c].dtype in ["float64", "float32", "int64"]
                      and c not in ["fiscal_year", "fiscal_quarter"]]

        df = df.sort_values("cash_flow_date", ascending=False)
        ltm_df = df.head(4)
        py_df  = df.iloc[4:8]

        rows = []
        for col in value_cols:
            ltm_val = ltm_df[col].sum() if not ltm_df[col].isna().all() else None
            py_val  = py_df[col].sum()  if not py_df[col].isna().all()  else None
            if ltm_val is None and py_val is None:
                continue
            delta     = (ltm_val - py_val) if ltm_val and py_val else None
            delta_pct = (delta / abs(py_val)) if delta and py_val and py_val != 0 else None
            rows.append({
                "attribute_name": col.replace("_", " ").title(),
                "tag":            "Income Statement",
                "ltm_value":      ltm_val,
                "py_value":       py_val,
                "delta":          delta,
                "delta_pct":      delta_pct,
            })
        return pd.DataFrame(rows)

    query = """
    WITH ranked AS (
        SELECT f.company_id, f.attribute_name, f.tag, f.cash_flow_date, f.true_up_value,
            ROW_NUMBER() OVER (
                PARTITION BY f.company_id, f.attribute_name,
                             YEAR(f.cash_flow_date), DATEPART(QUARTER, f.cash_flow_date)
                ORDER BY f.cash_flow_date DESC
            ) AS rn
        FROM dbo.ts_entity_financials f
        JOIN dbo.ts_entities e ON e.entity_id = f.company_id
        WHERE e.name = :name AND f.version = 'Actual' AND f.period = 'Quarterly'
          AND f.true_up_value IS NOT NULL
    ),
    deduped AS (SELECT * FROM ranked WHERE rn = 1),
    numbered AS (
        SELECT attribute_name, tag, true_up_value, cash_flow_date,
            ROW_NUMBER() OVER (PARTITION BY attribute_name ORDER BY cash_flow_date DESC) AS qrank
        FROM deduped
    )
    SELECT attribute_name, tag,
        SUM(CASE WHEN qrank <= 4 THEN true_up_value ELSE 0 END) AS ltm_value,
        SUM(CASE WHEN qrank BETWEEN 5 AND 8 THEN true_up_value ELSE 0 END) AS py_value
    FROM numbered WHERE qrank <= 8
    GROUP BY attribute_name, tag
    HAVING SUM(CASE WHEN qrank <= 4 THEN true_up_value ELSE 0 END) <> 0
    ORDER BY tag, attribute_name
    """
    df = pd.read_sql(text(query), get_engine(), params={"name": company_name})
    if not df.empty:
        df["delta"]     = df["ltm_value"] - df["py_value"]
        df["delta_pct"] = df.apply(
            lambda r: r["delta"] / abs(r["py_value"])
            if r["py_value"] and r["py_value"] != 0 else None, axis=1
        )
    return df


@st.cache_data(ttl=86400)
def load_consumer_kpis() -> pd.DataFrame:
    if _use_csv():
        # Derive from quarterly data — pivot numeric cols as KPIs
        df = load_quarterly()
        if df.empty:
            return pd.DataFrame()
        kpi_cols = ["revenue", "adj_ebitda", "net_leverage",
                    "interest_coverage", "gross_margin_pct", "adj_ebitda_margin_pct"]
        rows = []
        for col in kpi_cols:
            if col not in df.columns:
                continue
            latest = df.sort_values("cash_flow_date").groupby("company_name").last().reset_index()
            sub = latest[["company_name", "cash_flow_date", col]].dropna(subset=[col])
            sub["attribute_name"] = col.replace("_", " ").title()
            sub = sub.rename(columns={col: "true_up_value"})
            sub["tag"] = "KPI"
            rows.append(sub[["company_name", "attribute_name", "cash_flow_date",
                              "true_up_value", "tag"]])
        return pd.concat(rows) if rows else pd.DataFrame()

    query = """
    WITH ranked AS (
        SELECT e.name AS company_name, f.attribute_name, f.tag, f.cash_flow_date,
               f.true_up_value,
               ROW_NUMBER() OVER (
                   PARTITION BY f.company_id, f.attribute_name
                   ORDER BY f.cash_flow_date DESC
               ) AS rn
        FROM dbo.ts_entity_financials f
        JOIN dbo.ts_entities e ON e.entity_id = f.company_id
        WHERE f.version = 'Actual' AND f.period = 'Quarterly'
          AND f.tag = 'KPI' AND f.true_up_value IS NOT NULL
          AND e.type = 'Portfolio Company'
    )
    SELECT company_name, attribute_name, cash_flow_date, true_up_value
    FROM ranked WHERE rn = 1
    ORDER BY company_name, attribute_name
    """
    return pd.read_sql(text(query), get_engine())


def get_company_list() -> list:
    df = load_company_master()
    return sorted(df["company_name"].dropna().tolist())


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def format_millions(val, decimals=1):
    if val is None or pd.isna(val):
        return "—"
    if abs(val) >= 1000:
        return f"${val/1000:.{decimals}f}B"
    return f"${val:.{decimals}f}M"


def format_multiple(val, decimals=1):
    if val is None or pd.isna(val):
        return "—"
    return f"{val:.{decimals}f}x"


def format_pct(val, decimals=1):
    if val is None or pd.isna(val):
        return "—"
    return f"{val*100:.{decimals}f}%"


def flag_color(flag: str) -> str:
    return {"Red": "#C0392B", "Yellow": "#F3B51F", "Green": "#06865C"}.get(flag, "#888888")


def flag_emoji(flag: str) -> str:
    return {"Red": "🔴", "Yellow": "🟡", "Green": "🟢"}.get(flag, "⚪")
