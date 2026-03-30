"""
db.py — Database connection and cached data loaders
"""

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


@st.cache_resource
def get_engine():
    s = st.secrets["database"]

    # Detect available ODBC driver — Streamlit Cloud (Linux) may differ from Windows
    import pyodbc
    available = [d for d in pyodbc.drivers() if "SQL Server" in d]
    driver = sorted(available)[-1] if available else s.get("driver", "ODBC Driver 17 for SQL Server")

    conn_str = (
        f"mssql+pyodbc://{s['username']}:{quote_plus(s['password'])}"
        f"@{s['server']}/{s['database']}"
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

Driver detected: `{driver}`
Server: `{s.get("server", "not set")}`
Database: `{s.get("database", "not set")}`
Error: `{str(e)}`

**Things to check:**
1. SQL Server firewall — allow connections from `0.0.0.0/0` (all IPs) or Streamlit Cloud IPs
2. Server name in secrets matches your Azure SQL server exactly (include `.database.windows.net`)
3. Username / password correct
4. Encrypt + TrustServerCertificate settings on your SQL Server
        """)
        st.stop()


@st.cache_data(ttl=3600)
def load_portfolio_overview() -> pd.DataFrame:
    return pd.read_sql("SELECT * FROM dbo.vw_portfolio_overview", get_engine())


@st.cache_data(ttl=3600)
def load_fund_summary() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM dbo.vw_fund_summary ORDER BY current_tev DESC",
        get_engine()
    )


@st.cache_data(ttl=3600)
def load_company_master() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM dbo.vw_company_master ORDER BY company_name",
        get_engine()
    )


@st.cache_data(ttl=3600)
def load_flags() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM dbo.vw_flags_and_alerts ORDER BY overall_flag, company_name",
        get_engine()
    )


@st.cache_data(ttl=3600)
def load_ltm_snapshot() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT * FROM dbo.vw_ltm_snapshot ORDER BY ltm_revenue DESC",
        get_engine()
    )


@st.cache_data(ttl=3600)
def load_quarterly(company_name: str = None) -> pd.DataFrame:
    if company_name:
        query = """
            SELECT * FROM dbo.vw_financials_quarterly
            WHERE company_name = :name
            ORDER BY cash_flow_date
        """
        return pd.read_sql(text(query), get_engine(), params={"name": company_name})
    return pd.read_sql(
        "SELECT * FROM dbo.vw_financials_quarterly ORDER BY company_name, cash_flow_date",
        get_engine()
    )


@st.cache_data(ttl=3600)
def load_yoy_growth(company_name: str = None) -> pd.DataFrame:
    if company_name:
        query = """
            SELECT * FROM dbo.vw_yoy_growth
            WHERE company_name = :name
            ORDER BY cash_flow_date
        """
        return pd.read_sql(text(query), get_engine(), params={"name": company_name})
    return pd.read_sql(
        "SELECT * FROM dbo.vw_yoy_growth ORDER BY company_name, cash_flow_date",
        get_engine()
    )


def get_company_list() -> list:
    df = load_company_master()
    return sorted(df["company_name"].dropna().tolist())


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


@st.cache_data(ttl=86400)
def load_news(company_name: str = None) -> pd.DataFrame:
    """Load news articles — optionally filtered to one company."""
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
    """
    Build LTM vs Prior Year income statement for a company.
    Uses last 4 quarters (LTM) vs the 4 quarters before that (PY).
    Returns one row per attribute with LTM value, PY value, delta, delta%.
    """
    query = """
    WITH ranked AS (
        SELECT
            f.attribute_name,
            f.tag,
            f.cash_flow_date,
            f.true_up_value,
            ROW_NUMBER() OVER (
                PARTITION BY f.company_id, f.attribute_name,
                             YEAR(f.cash_flow_date), DATEPART(QUARTER, f.cash_flow_date)
                ORDER BY f.cash_flow_date DESC
            ) AS rn
        FROM dbo.ts_entity_financials f
        JOIN dbo.ts_entities e ON e.entity_id = f.company_id
        WHERE e.name   = :name
          AND f.version = 'Actual'
          AND f.period  = 'Quarterly'
          AND f.true_up_value IS NOT NULL
    ),
    deduped AS (
        SELECT * FROM ranked WHERE rn = 1
    ),
    numbered AS (
        SELECT
            attribute_name, tag, true_up_value, cash_flow_date,
            ROW_NUMBER() OVER (
                PARTITION BY attribute_name
                ORDER BY cash_flow_date DESC
            ) AS qrank
        FROM deduped
    )
    SELECT
        attribute_name,
        tag,
        SUM(CASE WHEN qrank <= 4 THEN true_up_value ELSE 0 END)     AS ltm_value,
        SUM(CASE WHEN qrank BETWEEN 5 AND 8 THEN true_up_value ELSE 0 END) AS py_value
    FROM numbered
    WHERE qrank <= 8
    GROUP BY attribute_name, tag
    HAVING SUM(CASE WHEN qrank <= 4 THEN true_up_value ELSE 0 END) <> 0
        OR SUM(CASE WHEN qrank BETWEEN 5 AND 8 THEN true_up_value ELSE 0 END) <> 0
    ORDER BY tag, attribute_name
    """
    df = pd.read_sql(text(query), get_engine(), params={"name": company_name})
    if not df.empty:
        df["delta"]    = df["ltm_value"] - df["py_value"]
        df["delta_pct"] = df.apply(
            lambda r: r["delta"] / abs(r["py_value"])
            if r["py_value"] and r["py_value"] != 0 else None, axis=1
        )
    return df


@st.cache_data(ttl=86400)
def load_consumer_kpis() -> pd.DataFrame:
    """
    Load all Consumer KPI attributes (tag = 'KPI') across all companies,
    latest quarter only.
    """
    query = """
    WITH ranked AS (
        SELECT
            e.name AS company_name,
            e.entity_id,
            f.attribute_name,
            f.tag,
            f.cash_flow_date,
            f.true_up_value,
            ROW_NUMBER() OVER (
                PARTITION BY f.company_id, f.attribute_name
                ORDER BY f.cash_flow_date DESC
            ) AS rn
        FROM dbo.ts_entity_financials f
        JOIN dbo.ts_entities e ON e.entity_id = f.company_id
        WHERE f.version = 'Actual'
          AND f.period  = 'Quarterly'
          AND f.tag     = 'KPI'
          AND f.true_up_value IS NOT NULL
          AND e.type    = 'Portfolio Company'
    )
    SELECT company_name, attribute_name, cash_flow_date, true_up_value
    FROM ranked
    WHERE rn = 1
    ORDER BY company_name, attribute_name
    """
    return pd.read_sql(text(query), get_engine())
