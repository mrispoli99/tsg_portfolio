"""
export_to_csv.py
================
Exports all dashboard SQL views to CSV files.
Run this on your VM whenever you want to refresh the demo data.

Output: data/ folder (committed to GitHub, read by Streamlit)

Usage:
    python export_to_csv.py
"""

import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# --- Import config from your pipeline folder ---
# Run this from your TSGPortfolio root folder where config.py lives
try:
    import config
    SERVER   = config.SQL_SERVER
    DATABASE = config.SQL_DATABASE
    USERNAME = config.SQL_USERNAME
    PASSWORD = config.SQL_PASSWORD
    DRIVER   = getattr(config, "SQL_DRIVER", "ODBC Driver 17 for SQL Server")
except ImportError:
    # Fallback — fill these in manually if running standalone
    SERVER   = "TSGSQL"
    DATABASE = "tsgPortfolio"
    USERNAME = "your_username"
    PASSWORD = "your_password"
    DRIVER   = "ODBC Driver 17 for SQL Server"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("export_csv")

# Output folder — inside the dashboard directory
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "tsg_dashboard", "data")

# Views to export — (filename, query)
EXPORTS = [
    ("portfolio_overview.csv",
     "SELECT * FROM dbo.vw_portfolio_overview"),
     
    ("entry_vs_current.csv",
     "SELECT * FROM dbo.vw_entry_vs_current"),

    ("fund_summary.csv",
     "SELECT * FROM dbo.vw_fund_summary WHERE company_name NOT LIKE '%Test%' ORDER BY current_tev DESC"),

    ("company_master.csv",
     "SELECT * FROM dbo.vw_company_master WHERE company_name NOT LIKE '%Test%' ORDER BY company_name"),

    ("flags_and_alerts.csv",
     "SELECT * FROM dbo.vw_flags_and_alerts WHERE company_name NOT LIKE '%Test%' ORDER BY overall_flag, company_name"),

    ("ltm_snapshot.csv",
     "SELECT * FROM dbo.vw_ltm_snapshot WHERE company_name NOT LIKE '%Test%' ORDER BY ltm_revenue DESC"),

    ("financials_quarterly.csv",
     """SELECT * FROM dbo.vw_financials_quarterly
        WHERE company_name NOT LIKE '%Test%'
        ORDER BY company_name, cash_flow_date"""),

    # Month-level view for the Monthly period toggle.
    # True monthly filers (e.g. ATI) get one row per calendar month;
    # quarterly-only companies pass through their quarterly rows unchanged
    # with period_granularity='Quarterly' so the dashboard can show a note.
    ("financials_monthly.csv",
     """SELECT * FROM dbo.vw_financials_monthly
        WHERE company_name NOT LIKE '%Test%'
        ORDER BY company_name, cash_flow_date"""),

    ("financials_annual.csv",
     """SELECT * FROM dbo.vw_financials_annual
        WHERE company_name NOT LIKE '%Test%'
        ORDER BY company_name, cash_flow_date"""),

    ("yoy_growth.csv",
     """SELECT * FROM dbo.vw_yoy_growth
        WHERE company_name NOT LIKE '%Test%'
        ORDER BY company_name, cash_flow_date"""),

    ("portfolio_flags.csv",
     "SELECT * FROM dbo.vw_portfolio_flags WHERE company_name NOT LIKE '%Test%' ORDER BY red_flag_count DESC"),

    ("company_kpis.csv",
     """SELECT * FROM dbo.vw_company_kpis
        WHERE company_name NOT LIKE '%Test%'
        ORDER BY company_name, attribute_name, cash_flow_date"""),

    ("company_news.csv",
     """SELECT TOP 500 company_name, title, summary, published, link, source
        FROM dbo.ts_company_news
        WHERE company_name NOT LIKE '%Test%'
        ORDER BY published DESC"""),
]


def get_engine():
    conn_str = (
        f"mssql+pyodbc://{USERNAME}:{quote_plus(PASSWORD)}"
        f"@{SERVER}/{DATABASE}"
        f"?driver={DRIVER.replace(' ', '+')}"
        f"&TrustServerCertificate=yes"
    )
    return create_engine(conn_str, fast_executemany=False)


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    engine = get_engine()

    logger.info("=== CSV Export START ===")
    logger.info(f"Output directory: {OUTPUT_DIR}")

    total_rows = 0
    for filename, query in EXPORTS:
        try:
            df = pd.read_sql(query, engine)

            # Strip timezone from datetime columns (CSV doesn't support tz-aware)
            for col in df.select_dtypes(include=["datetimetz", "datetime64[ns, UTC]"]).columns:
                df[col] = df[col].dt.tz_localize(None)

            output_path = os.path.join(OUTPUT_DIR, filename)
            df.to_csv(output_path, index=False)
            logger.info(f"  ✓ {filename:<35} {len(df):>6} rows")
            total_rows += len(df)

        except Exception as exc:
            logger.warning(f"  ✗ {filename:<35} FAILED: {exc}")

    logger.info(f"=== CSV Export DONE — {total_rows} total rows written to {OUTPUT_DIR} ===")
    logger.info("Next: commit the data/ folder to GitHub and redeploy Streamlit")


if __name__ == "__main__":
    run()
