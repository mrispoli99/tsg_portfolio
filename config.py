"""
73 Strings → SQL Server Pipeline Configuration
================================================
Edit these values before running any pipeline.
"""

# -------------------------------------------------------------------
# 73 Strings API credentials
# -------------------------------------------------------------------
API_SUBSCRIPTION_KEY = "e01db4d6108d4894b90a34bf32cd5812"
USER_ID              = "d8454ba6-618f-442b-af0f-5ee58460d0d7"          # UUID from 73 Strings
ORG_ID               = "952e0f6d-6c58-42bf-bd6f-56c3393d09de"           # UUID from 73 Strings

# -------------------------------------------------------------------
# SQL Server connection
# -------------------------------------------------------------------
SQL_SERVER   = "TSGSQL"
SQL_DATABASE = "TSGPortfolio"
SQL_USERNAME = "tsguser"
SQL_PASSWORD = "MMzsjg12778!!"
SQL_DRIVER   = "ODBC Driver 17 for SQL Server"     # or 18


# Connection string (built automatically; override if needed)
SQL_CONN_STR = (
    f"mssql+pyodbc://{SQL_USERNAME}:{SQL_PASSWORD}"
    f"@{SQL_SERVER}/{SQL_DATABASE}"
    f"?driver={SQL_DRIVER.replace(' ', '+')}"
)
 
# -------------------------------------------------------------------
# API base URLs
# -------------------------------------------------------------------
BASE_ASSET_INFO      = "https://api-accord-usprod2-73strings.azure-api.net/assetinfo"
BASE_FINANCIAL_DATA  = "https://api-accord-usprod2-73strings.azure-api.net/financial-data"
BASE_QUALITATIVE     = "https://api-accord-usprod2-73strings.azure-api.net/qualitative-data"
BASE_TRANSACTIONS    = "https://api-accord-usprod2-73strings.azure-api.net/transactions"
 
# -------------------------------------------------------------------
# Pipeline behaviour
# -------------------------------------------------------------------
REQUEST_TIMEOUT_SEC  = 60      # per API call
PAGE_SIZE            = 100     # transactions page size (max 100)
BATCH_SIZE           = 50      # entity IDs per financial-data request
LOG_LEVEL            = "INFO"  # DEBUG | INFO | WARNING | ERROR
 
# Financial data pull window (set None to omit from request)
FINANCIAL_START_DATE = "2015-01-01"   # adjust if your data goes further back
FINANCIAL_END_DATE   = None           # None = today
FINANCIAL_CURRENCY   = "USD"
FINANCIAL_UNITS      = "Millions"
FINANCIAL_PERIOD_TYPE = None   # e.g. "Annual" | "Quarterly" | None
 
# Qualitative data pull window
QUAL_START_DATE = None
QUAL_END_DATE   = None
 