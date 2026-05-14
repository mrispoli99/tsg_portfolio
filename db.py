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
    """
    Load flags_and_alerts.csv and backfill two columns that the SQL view
    leaves null for most companies:

      revenue_yoy      — pulled from yoy_growth.csv (latest period per company)
      ltm_gross_margin — pulled from financials_quarterly.csv (latest gross_margin_pct)
      ltm_gross_profit — pulled from financials_quarterly.csv (latest gross_profit)

    All other columns come from flags_and_alerts.csv unchanged.
    """
    df = _csv("flags_and_alerts.csv")
    if df.empty:
        return df

    # ── Backfill revenue_yoy from yoy_growth.csv ─────────────────────────
    try:
        yoy = _csv("yoy_growth.csv")
        if not yoy.empty and "revenue_yoy" in yoy.columns:
            yoy["cash_flow_date"] = pd.to_datetime(yoy["cash_flow_date"], errors="coerce")
            # Latest non-null revenue_yoy per company
            latest_yoy = (
                yoy[yoy["revenue_yoy"].notna()]
                .sort_values("cash_flow_date")
                .groupby("company_name", as_index=False)
                .last()[["company_name", "revenue_yoy"]]
                .rename(columns={"revenue_yoy": "_yoy_fill"})
            )
            df = df.merge(latest_yoy, on="company_name", how="left")
            # Only fill where flags CSV has null
            null_mask = df["revenue_yoy"].isna()
            df.loc[null_mask, "revenue_yoy"] = df.loc[null_mask, "_yoy_fill"]
            df = df.drop(columns=["_yoy_fill"])
    except Exception:
        pass

    # ── Backfill gross_margin and gross_profit from financials_quarterly.csv ─
    try:
        q = _csv("financials_quarterly.csv")
        if not q.empty:
            q["cash_flow_date"] = pd.to_datetime(q["cash_flow_date"], errors="coerce")
            gm_cols = [c for c in ["gross_margin_pct", "gross_profit"] if c in q.columns]
            if gm_cols:
                latest_q = (
                    q[q[gm_cols[0]].notna() if gm_cols else [True] * len(q)]
                    .sort_values("cash_flow_date")
                    .groupby("company_name", as_index=False)
                    .last()[["company_name"] + gm_cols]
                )
                # Rename to match flags column names
                rename_map = {
                    "gross_margin_pct": "ltm_gross_margin",
                    "gross_profit":     "ltm_gross_profit",
                }
                latest_q = latest_q.rename(columns={
                    c: rename_map[c] for c in gm_cols if c in rename_map
                })
                fill_cols = [rename_map[c] for c in gm_cols if c in rename_map]

                df = df.merge(
                    latest_q[["company_name"] + fill_cols].rename(
                        columns={c: f"_{c}_fill" for c in fill_cols}
                    ),
                    on="company_name", how="left"
                )
                for c in fill_cols:
                    fill_col = f"_{c}_fill"
                    if c not in df.columns:
                        df[c] = None
                    null_mask = df[c].isna()
                    df.loc[null_mask, c] = df.loc[null_mask, fill_col]
                    df = df.drop(columns=[fill_col])
    except Exception:
        pass

    return df

@st.cache_data
def load_ltm_snapshot() -> pd.DataFrame:
    return _csv("ltm_snapshot.csv")

def _prep_financials(df: pd.DataFrame, period_value: str) -> pd.DataFrame:
    """
    Normalise a wide-format financials CSV so the app always sees the same
    standard columns regardless of which view file was loaded.

    period_value : the fallback string for the 'period' column
                   ('Quarterly' | 'Annual' | 'Monthly')
    """
    if df.empty:
        return df

    df = df.copy()
    df["cash_flow_date"] = pd.to_datetime(df["cash_flow_date"], errors="coerce")

    # ── Normalise the period column ──────────────────────────────────────
    # Monthly view uses 'period_granularity' instead of 'period'
    if "period" not in df.columns:
        if "period_granularity" in df.columns:
            df = df.rename(columns={"period_granularity": "period"})
        else:
            df["period"] = period_value

    # ── Ensure period_label exists ───────────────────────────────────────
    if "period_label" not in df.columns:
        d = df["cash_flow_date"]
        if period_value == "Quarterly":
            df["period_label"] = "Q" + d.dt.quarter.astype(str) + " " + d.dt.year.astype(str)
        elif period_value == "Monthly":
            df["period_label"] = d.dt.strftime("%b %Y")
        else:  # Annual
            df["period_label"] = d.dt.year.astype(str)

    return df.sort_values(["company_name", "cash_flow_date"])


@st.cache_data
def load_quarterly_all() -> pd.DataFrame:
    """Load all three period granularities and return them stacked."""
    frames = []

    q = _csv("financials_quarterly.csv")
    if not q.empty:
        frames.append(_prep_financials(q, "Quarterly"))

    m = _csv("financials_monthly.csv")
    if not m.empty:
        frames.append(_prep_financials(m, "Monthly"))

    a = _csv("financials_annual.csv")
    if not a.empty:
        frames.append(_prep_financials(a, "Annual"))

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    combined["cash_flow_date"] = pd.to_datetime(combined["cash_flow_date"], errors="coerce")
    return combined.sort_values(["company_name", "cash_flow_date"])

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

@st.cache_data
def load_company_kpis_all() -> pd.DataFrame:
    """Load the long-format company-specific KPI data."""
    df = _csv("company_kpis.csv")
    if df.empty:
        return df
    df["cash_flow_date"] = pd.to_datetime(df["cash_flow_date"], errors="coerce")
    if "period" not in df.columns:
        df["period"] = "Quarterly"
    return df.sort_values(["company_name", "attribute_name", "cash_flow_date"])


def load_company_kpis(company_name: str, attributes: list, period: str = "Quarterly") -> pd.DataFrame:
    """
    Return a wide-format DataFrame for one company's configured KPIs.

    For attributes that only exist as Monthly data (e.g. Classes / Day,
    Average Membership Price), automatically aggregates to the requested
    granularity rather than returning empty:
      - Quarterly: last monthly value in each calendar quarter
      - Annual:    last monthly value in each calendar year
      - Monthly:   pass-through as-is
    """
    df = load_company_kpis_all()
    if df.empty:
        return pd.DataFrame()

    co_df = df[df["company_name"] == company_name].copy()
    if co_df.empty:
        return pd.DataFrame()

    # Split attributes into those that have data at the requested period
    # and those that only have monthly data (need aggregation)
    frames = []

    for attr in attributes:
        attr_df = co_df[co_df["attribute_name"] == attr].copy()
        if attr_df.empty:
            continue

        available_periods = set(attr_df["period"].unique())

        if period in available_periods:
            # Has data at the requested granularity — use directly
            frames.append(attr_df[attr_df["period"] == period][
                ["cash_flow_date", "attribute_name", "true_up_value"]
            ])
        elif "Monthly" in available_periods and period in ("Quarterly", "Annual"):
            # Only monthly data available — aggregate up
            monthly = attr_df[attr_df["period"] == "Monthly"].copy()
            monthly = monthly.sort_values("cash_flow_date")
            if period == "Quarterly":
                monthly["_gkey"] = (
                    monthly["cash_flow_date"].dt.year.astype(str) + "Q" +
                    monthly["cash_flow_date"].dt.quarter.astype(str)
                )
            else:  # Annual
                monthly["_gkey"] = monthly["cash_flow_date"].dt.year.astype(str)
            # Keep last monthly row per quarter/year (most recent value)
            agg = (monthly.sort_values("cash_flow_date")
                          .drop_duplicates(subset=["_gkey"], keep="last")
                          .drop(columns=["_gkey"]))
            frames.append(agg[["cash_flow_date", "attribute_name", "true_up_value"]])
        # else: no usable data for this attribute — skip

    if not frames:
        return pd.DataFrame()

    sub = pd.concat(frames, ignore_index=True)

    # Pivot to wide format
    pivot = (sub.pivot_table(
                index="cash_flow_date",
                columns="attribute_name",
                values="true_up_value",
                aggfunc="last")
               .reset_index()
               .sort_values("cash_flow_date"))

    # Add period_label
    if period == "Monthly":
        pivot["period_label"] = pivot["cash_flow_date"].dt.strftime("%b %Y")
    elif period == "Annual":
        pivot["period_label"] = pivot["cash_flow_date"].dt.strftime("%Y")
    else:
        pivot["period_label"] = (
            "Q" + pivot["cash_flow_date"].dt.quarter.astype(str)
            + " " + pivot["cash_flow_date"].dt.year.astype(str)
        )

    return pivot


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