"""
company_kpi_config.py
=====================
Per-company KPI configuration for the Company-Specific KPI page.

Each company entry has:
  - "kpi_cards": up to 4 metrics shown as summary tiles at the top
  - "kpi_charts": metrics shown as time-series charts in the 2-column grid

Format per metric:
  {
    "label":     display name shown in UI
    "attribute": exact attribute_name from ts_entity_financials
    "format":    "millions" | "pct" | "multiple" | "number" | "thousands"
    "chart":     "bar" | "line"   (charts only)
  }

Format meanings:
  millions  -> $X.XM / $X.XB
  pct       -> X.X%
  multiple  -> X.Xx
  number    -> integer (e.g. job count, unit count)
  thousands -> $XXXk
"""

COMPANY_KPI_CONFIG = {

    # ----------------------------------------------------------------
    # Wrench Group
    # KPIs from portco slides: HVAC Install/Service, Plumbing, Electrical,
    # Water, Insulation revenue & GP splits; job counts; avg ticket prices
    # ----------------------------------------------------------------
    "Wrench Group": {
        "kpi_cards": [
            {"label": "Total Revenue",            "attribute": "Total Revenue",                  "format": "millions"},
            {"label": "Adj. EBITDA (excl. GF)",   "attribute": "PF Adjusted EBITDA",             "format": "millions"},
            {"label": "Gross Margin",             "attribute": "Contribution Margin",            "format": "pct"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "HVAC Install Revenue",     "attribute": "HVAC Install Revenue",           "format": "millions", "chart": "bar"},
            {"label": "HVAC Service Revenue",     "attribute": "HVAC Service Revenue",           "format": "millions", "chart": "bar"},
            {"label": "Plumbing Revenue",         "attribute": "Plumbing Revenue",               "format": "millions", "chart": "bar"},
            {"label": "Electrical Revenue",       "attribute": "Electrical Revenue",             "format": "millions", "chart": "bar"},
            {"label": "Total HVAC Revenue",       "attribute": "Total HVAC Revenue",             "format": "millions", "chart": "bar"},
            {"label": "HVAC Install Jobs",        "attribute": "Number of HVAC Install Jobs",    "format": "number",   "chart": "bar"},
            {"label": "HVAC Service Jobs",        "attribute": "Number of HVAC Service Jobs",    "format": "number",   "chart": "bar"},
            {"label": "Plumbing Jobs",            "attribute": "Number of Total Plumbing Jobs",  "format": "number",   "chart": "bar"},
            {"label": "Avg HVAC Install Ticket",  "attribute": "Average HVAC Install Ticket Price", "format": "thousands", "chart": "line"},
            {"label": "Avg HVAC Service Ticket",  "attribute": "Average HVAC Service Ticket Price", "format": "thousands", "chart": "line"},
            {"label": "Avg Plumbing Ticket",      "attribute": "Average Plumbing Ticket Price",  "format": "thousands", "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # Summer Fridays
    # KPIs from portco slides: Sephora sell-in/sell-thru, channel splits,
    # gross sales, gross margin
    # ----------------------------------------------------------------
    "Summer Fridays": {
        "kpi_cards": [
            {"label": "Net Sales",                "attribute": "Net Sales",                          "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                    "format": "millions"},
            {"label": "Gross Margin",             "attribute": "Gross Margin",                       "format": "pct"},
            {"label": "Sephora US+CAN Sell-Thru", "attribute": "Sephora US + CAN Sell-Thru",         "format": "millions"},
        ],
        "kpi_charts": [
            {"label": "Gross Sales",              "attribute": "Gross Sales",                        "format": "millions", "chart": "bar"},
            {"label": "Sephora US+CAN Sell In",   "attribute": "Sephora US + CAN Sell In",           "format": "millions", "chart": "bar"},
            {"label": "Sephora US+CAN Sell-Thru", "attribute": "Sephora US + CAN Sell-Thru",         "format": "millions", "chart": "bar"},
            {"label": "Sell In YoY Growth",       "attribute": "Sephora US + CAN Sell In YoY Growth (%)", "format": "pct", "chart": "line"},
            {"label": "Sell-Thru YoY Growth",     "attribute": "Sephora US + CAN Sell-Thru YoY Growth (%)", "format": "pct", "chart": "line"},
            {"label": "Domestic Revenue",         "attribute": "Domestic",                           "format": "millions", "chart": "bar"},
            {"label": "International Revenue",    "attribute": "International",                      "format": "millions", "chart": "bar"},
            {"label": "Sephora Revenue",          "attribute": "Sephora",                            "format": "millions", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Radiance Holdings
    # KPIs from portco slides: SSSG (Sola & Woodhouse), occupancy,
    # franchise vs corporate splits
    # ----------------------------------------------------------------
    "Radiance Holdings": {
        "kpi_cards": [
            {"label": "Revenue",                  "attribute": "Total Revenue",                  "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Total SSSG",               "attribute": "Total SSSG",                     "format": "pct"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Total SSSG",               "attribute": "Total SSSG",                     "format": "pct",      "chart": "line"},
            {"label": "Monetary SSSG",            "attribute": "Monetary (SSSG)",                "format": "pct",      "chart": "line"},
            {"label": "Total Occupancy",          "attribute": "Total Occupancy",                "format": "pct",      "chart": "line"},
            {"label": "Mature Total Occupancy",   "attribute": "Mature Total Occupancy",         "format": "pct",      "chart": "line"},
            {"label": "Mature Corp Occupancy",    "attribute": "Mature Corporate Occupancy",     "format": "pct",      "chart": "line"},
            {"label": "Mature Franchise Occupancy","attribute": "Mature Franchise Occupancy",    "format": "pct",      "chart": "line"},
            {"label": "Royalty Income",           "attribute": "Royalty Income",                 "format": "millions", "chart": "bar"},
            {"label": "Technology Fees",          "attribute": "Technology Fees",                "format": "millions", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Rough Country
    # KPIs from portco slides: Suspension vs Non-Suspension, channel
    # splits (DTC/Installer/Converter), product category revenue
    # ----------------------------------------------------------------
    "Rough Country": {
        "kpi_cards": [
            {"label": "Net Sales",                "attribute": "Net Sales",                      "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Gross Margin",             "attribute": "Gross Margin",                   "format": "pct"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Lift Kits & Susp.",        "attribute": "Lift Kits & Susp. Acc.",         "format": "millions", "chart": "bar"},
            {"label": "Shocks & Stabilizers",     "attribute": "Shocks & Stabilizers",           "format": "millions", "chart": "bar"},
            {"label": "Bed Covers",               "attribute": "Bed Covers",                     "format": "millions", "chart": "bar"},
            {"label": "Steps & Runningboard",     "attribute": "Steps & Runningboard",           "format": "millions", "chart": "bar"},
            {"label": "Wheels & Tires",           "attribute": "Wheels & Tires",                 "format": "millions", "chart": "bar"},
            {"label": "Bumpers",                  "attribute": "Bumpers",                        "format": "millions", "chart": "bar"},
            {"label": "Interior & Mats",          "attribute": "Interior & Mats",                "format": "millions", "chart": "bar"},
            {"label": "Installer Channel",        "attribute": "Installer",                      "format": "millions", "chart": "bar"},
            {"label": "Internet Seller",          "attribute": "Internet Seller",                "format": "millions", "chart": "bar"},
            {"label": "Employee Headcount",       "attribute": "Employee Headcount",             "format": "number",   "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # Mavis
    # KPIs from portco slides: SSSG, SL revenue, SL gross margin,
    # SL contribution margin, cash flow
    # ----------------------------------------------------------------
    "Mavis": {
        "kpi_cards": [
            {"label": "Total Sales",              "attribute": "Revenue, net",                   "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Gross Profit",             "attribute": "Gross Profit",                   "format": "millions"},
            {"label": "Net Leverage (excl. Pref)","attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Total Revenue",            "attribute": "Revenue, net",                   "format": "millions", "chart": "bar"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions", "chart": "bar"},
            {"label": "Adj. EBITDA Margin",       "attribute": "LTM Adj. EBITDA (Datasheet)",    "format": "pct",      "chart": "line"},
            {"label": "Gross Profit",             "attribute": "Gross Profit",                   "format": "millions", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Core Power
    # KPIs from portco slides: membership count, cash revenue,
    # studio contribution, attendance
    # ----------------------------------------------------------------
    "Core Power": {
        "kpi_cards": [
            {"label": "Cash Revenue",             "attribute": "Member Cash Revenue",            "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Management EBITDA",              "format": "millions"},
            {"label": "Studio Contribution",      "attribute": "Studio Contribution",            "format": "millions"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Total Revenue",            "attribute": "Total Studio Revenue",           "format": "millions", "chart": "bar"},
            {"label": "Membership Revenue",       "attribute": "Membership",                     "format": "millions", "chart": "bar"},
            {"label": "Retail Revenue",           "attribute": "Retail",                         "format": "millions", "chart": "bar"},
            {"label": "Studio Contribution",      "attribute": "Studio Contribution",            "format": "millions", "chart": "bar"},
            {"label": "Avg Membership Price",     "attribute": "Average Membership Price",       "format": "thousands","chart": "line"},
            {"label": "Attendance / Studio",      "attribute": "Attendance/Studio Member",       "format": "number",   "chart": "line"},
            {"label": "Classes / Day",            "attribute": "Classes / Day",                  "format": "number",   "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # Hempz
    # KPIs from portco slides: channel gross sales (Ulta, Target,
    # Walmart, Amazon, etc.), gross margin, sell-through by channel
    # ----------------------------------------------------------------
    "Hempz": {
        "kpi_cards": [
            {"label": "Net Revenues",             "attribute": "Net Revenues",                   "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Gross Profit",             "attribute": "Gross Profit after COGS",        "format": "millions"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Gross Sales",              "attribute": "Gross Sales",                    "format": "millions", "chart": "bar"},
            {"label": "Ulta Gross Sales",         "attribute": "Gross Sales - Ulta",             "format": "millions", "chart": "bar"},
            {"label": "Target Gross Sales",       "attribute": "Gross Sales - Target",           "format": "millions", "chart": "bar"},
            {"label": "Walmart Gross Sales",      "attribute": "Gross Sales - Walmart",          "format": "millions", "chart": "bar"},
            {"label": "Amazon Gross Sales",       "attribute": "Gross Sales - Amazon",           "format": "millions", "chart": "bar"},
            {"label": "Walgreens Gross Sales",    "attribute": "Gross Sales - Walgreens",        "format": "millions", "chart": "bar"},
            {"label": "International Gross Sales","attribute": "Gross Sales - International",    "format": "millions", "chart": "bar"},
            {"label": "Ulta Sales Dilution %",    "attribute": "LTM Sales Dilution % Ulta",      "format": "pct",      "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # Trinity Solar
    # KPIs from portco slides: contracts signed, installs, solar vs
    # roofing revenue, financing mix
    # ----------------------------------------------------------------
    "Trinity Solar": {
        "kpi_cards": [
            {"label": "Total Revenue",            "attribute": "Total Revenue",                  "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adj. EBITDA (Diligence)",        "format": "millions"},
            {"label": "Solar Installs",           "attribute": "Installs - Solar",               "format": "number"},
            {"label": "Contracts Signed (Solar)", "attribute": "Contracts Approved - Solar",     "format": "number"},
        ],
        "kpi_charts": [
            {"label": "Solar & Battery Revenue",  "attribute": "Solar & Battery Revenue",        "format": "millions", "chart": "bar"},
            {"label": "Roofing Revenue",          "attribute": "Roofing Revenue",                "format": "millions", "chart": "bar"},
            {"label": "Solar Installs",           "attribute": "Installs - Solar",               "format": "number",   "chart": "bar"},
            {"label": "Roofing Installs",         "attribute": "Installs - Roofing",             "format": "number",   "chart": "bar"},
            {"label": "Contracts Signed (Solar)", "attribute": "Contracts Approved - Solar",     "format": "number",   "chart": "bar"},
            {"label": "Solar Gross Profit",       "attribute": "Solar + Battery Gross Profit",   "format": "millions", "chart": "bar"},
            {"label": "Roofing Gross Profit",     "attribute": "Roofing Gross Profit",           "format": "millions", "chart": "bar"},
            {"label": "Sunnova % of Contracts",   "attribute": "Sunnova PPA/Lease (% of contracts signed)", "format": "pct", "chart": "line"},
            {"label": "IGS % of Contracts",       "attribute": "IGS PPA/Lease (% of contracts signed)", "format": "pct", "chart": "line"},
            {"label": "Watts Installed (MM)",     "attribute": "Total Watts Installed (MMs) - Solar", "format": "number", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Super Star Car Wash
    # KPIs from portco slides: SSSG, membership revenue, car counts,
    # unit count, 4-wall EBITDA
    # ----------------------------------------------------------------
    "Super Star": {
        "kpi_cards": [
            {"label": "Total Revenue",            "attribute": "Total Revenue",                  "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "4-Wall EBITDAR",           "attribute": "4-Wall EBITDAR",                 "format": "millions"},
            {"label": "Car Wash Count",           "attribute": "Car Wash Count",                 "format": "number"},
        ],
        "kpi_charts": [
            {"label": "Total Wash Revenue",       "attribute": "Total Wash Revenue",             "format": "millions", "chart": "bar"},
            {"label": "Membership Revenue",       "attribute": "Membership Revenue",             "format": "millions", "chart": "bar"},
            {"label": "Retail Revenue",           "attribute": "Retail Revenue",                 "format": "millions", "chart": "bar"},
            {"label": "Member Car Count",         "attribute": "Member Car Count",               "format": "number",   "chart": "bar"},
            {"label": "Total Car Count",          "attribute": "Car Count",                      "format": "number",   "chart": "bar"},
            {"label": "Memberships (ending)",     "attribute": "Memberships (ending)",           "format": "number",   "chart": "line"},
            {"label": "Car Wash Units",           "attribute": "Car Wash Count",                 "format": "number",   "chart": "line"},
            {"label": "4-Wall EBITDA",            "attribute": "4-Wall EBITDA",                  "format": "millions", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Thrive Pet Healthcare
    # KPIs from portco slides: SSSG, transactions, ACT (avg check),
    # DVM headcount, revenue by segment
    # ----------------------------------------------------------------
    "Thrive Pet Healthcare": {
        "kpi_cards": [
            {"label": "Net Revenue",              "attribute": "Net Revenue",                    "format": "millions"},
            {"label": "Mgmt Adj. EBITDA",         "attribute": "Mgmt Adjusted EBITDA",           "format": "millions"},
            {"label": "Transactions",             "attribute": "Transactions",                   "format": "number"},
            {"label": "DVM Headcount",            "attribute": "DVM Headcount - Ending",         "format": "number"},
        ],
        "kpi_charts": [
            {"label": "Gross Revenue",            "attribute": "Gross Revenue",                  "format": "millions", "chart": "bar"},
            {"label": "Product Revenue",          "attribute": "Product Revenue",                "format": "millions", "chart": "bar"},
            {"label": "Services Revenue",         "attribute": "Services Revenue",               "format": "millions", "chart": "bar"},
            {"label": "Membership Revenue",       "attribute": "Membership Revenue",             "format": "millions", "chart": "bar"},
            {"label": "Transactions",             "attribute": "Transactions",                   "format": "number",   "chart": "bar"},
            {"label": "Avg Check (ACT)",          "attribute": "ACT",                            "format": "thousands","chart": "line"},
            {"label": "DVM Headcount",            "attribute": "DVM Headcount - Ending",         "format": "number",   "chart": "line"},
            {"label": "4-Wall EBITDA Margin",     "attribute": "Mgmt Adjusted Operations EBITDA","format": "pct",      "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # Endeavor Schools
    # KPIs from portco slides: enrollment, TSG Valuation EBITDA,
    # SS revenue, school-level EBITDA, grant income
    # ----------------------------------------------------------------
    "Endeavor": {
        "kpi_cards": [
            {"label": "Revenue",                  "attribute": "Total Income",                   "format": "millions"},
            {"label": "TSG Valuation EBITDA",     "attribute": "PF Adj. EBITDA",                 "format": "millions"},
            {"label": "School-Level EBITDA",      "attribute": "School Level EBITDA",            "format": "millions"},
            {"label": "Grant Income",             "attribute": "Grants",                         "format": "millions"},
        ],
        "kpi_charts": [
            {"label": "Total Revenue",            "attribute": "Total Income",                   "format": "millions", "chart": "bar"},
            {"label": "Net Tuition Income",       "attribute": "Net Tuition Income",             "format": "millions", "chart": "bar"},
            {"label": "Grant Income",             "attribute": "Grants",                         "format": "millions", "chart": "bar"},
            {"label": "School-Level EBITDA",      "attribute": "School Level EBITDA",            "format": "millions", "chart": "bar"},
            {"label": "Adj. EBITDA",              "attribute": "Adj. EBITDA",                    "format": "millions", "chart": "bar"},
            {"label": "Net Leverage",             "attribute": "Net Leverage",                   "format": "multiple", "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # ATI Restoration
    # KPIs from portco slides: revenue by job type (Asbestos, Mold,
    # ReCon, Contents, ES), job counts
    # ----------------------------------------------------------------
    "ATI": {
        "kpi_cards": [
            {"label": "Total Revenue",            "attribute": "Total Revenue",                  "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Gross Profit",             "attribute": "Gross Profit",                   "format": "millions"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Asbestos Revenue",         "attribute": "Asbestos Revenue",               "format": "millions", "chart": "bar"},
            {"label": "Mold Revenue",             "attribute": "Mold Revenue",                   "format": "millions", "chart": "bar"},
            {"label": "ReCon Revenue",            "attribute": "ReCon Revenue",                  "format": "millions", "chart": "bar"},
            {"label": "Contents Revenue",         "attribute": "Contents Revenue",               "format": "millions", "chart": "bar"},
            {"label": "ES Revenue",               "attribute": "ES Revenue",                     "format": "millions", "chart": "bar"},
            {"label": "# Asbestos Jobs",          "attribute": "# Asb Jobs",                     "format": "number",   "chart": "bar"},
            {"label": "# Mold Jobs",              "attribute": "# Mold Jobs",                    "format": "number",   "chart": "bar"},
            {"label": "# ReCon Jobs",             "attribute": "# ReCon Jobs",                   "format": "number",   "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Legacy.com
    # KPIs from portco slides: revenue by channel (Tukios, Batesville,
    # Legacy Pro, ADN, Newspapers, Consumer)
    # ----------------------------------------------------------------
    "Legacy": {
        "kpi_cards": [
            {"label": "Total Revenue",            "attribute": "Total Revenue",                  "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA (Synergized) or Deemed per CA (Acquired Batesville)", "format": "millions"},
            {"label": "Gross Margin",             "attribute": "Product Margin",                 "format": "pct"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Tukios Revenue",           "attribute": "Revenue (Tukios)",               "format": "millions", "chart": "bar"},
            {"label": "Legacy Revenue",           "attribute": "Revenue (Legacy)",               "format": "millions", "chart": "bar"},
            {"label": "Media Revenue",            "attribute": "Revenue (Media Partners)",       "format": "millions", "chart": "bar"},
            {"label": "Batesville Revenue",       "attribute": "Revenue (Batesville White Label)","format": "millions", "chart": "bar"},
            {"label": "Tukios EBITDA",            "attribute": "EBITDA (Tukios)",                "format": "millions", "chart": "bar"},
            {"label": "Legacy EBITDA",            "attribute": "EBITDA (Legacy)",                "format": "millions", "chart": "bar"},
            {"label": "Tukios Gross Profit",      "attribute": "Gross Profit (Tukios)",          "format": "millions", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Cadogan Tate
    # KPIs from portco slides: revenue by service type (Storage,
    # Handling, White Glove, Commercial, FVP), LfL growth, by region
    # ----------------------------------------------------------------
    "Cadogan Tate": {
        "kpi_cards": [
            {"label": "Net Revenue",              "attribute": "Net Revenue",                    "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Gross Margin",             "attribute": "Gross profit %",                 "format": "pct"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Storage Revenue",          "attribute": "Storage",                        "format": "millions", "chart": "bar"},
            {"label": "Handling Revenue",         "attribute": "Handling",                       "format": "millions", "chart": "bar"},
            {"label": "White Glove Revenue",      "attribute": "White Glove",                    "format": "millions", "chart": "bar"},
            {"label": "Commercial Revenue",       "attribute": "Commercial",                     "format": "millions", "chart": "bar"},
            {"label": "UK Revenue",               "attribute": "UK Revenue",                     "format": "millions", "chart": "bar"},
            {"label": "US Revenue",               "attribute": "US Revenue",                     "format": "millions", "chart": "bar"},
            {"label": "France Revenue",           "attribute": "France Revenue",                 "format": "millions", "chart": "bar"},
            {"label": "Storage Gross Margin",     "attribute": "Storage GP%",                    "format": "pct",      "chart": "line"},
        ],
    },

    # ----------------------------------------------------------------
    # Revolut
    # KPIs from portco slides: MAU, revenue by segment (FX, Payments,
    # Subscriptions, Wealth, Credit)
    # ----------------------------------------------------------------
    "Revolut": {
        "kpi_cards": [
            {"label": "Revenue",                  "attribute": "Turnover",                       "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Monthly Active People",    "attribute": "Monthly Active People (#m)",     "format": "number"},
            {"label": "Monthly Active Businesses","attribute": "Monthly Active Businesses (#k)", "format": "number"},
        ],
        "kpi_charts": [
            {"label": "FX & Wealth Revenue",      "attribute": "FX & Wealth",                    "format": "millions", "chart": "bar"},
            {"label": "Payments Revenue",         "attribute": "Payments",                       "format": "millions", "chart": "bar"},
            {"label": "Subscriptions Revenue",    "attribute": "Subscriptions",                  "format": "millions", "chart": "bar"},
            {"label": "Credit Revenue",           "attribute": "Credit",                         "format": "millions", "chart": "bar"},
            {"label": "Monthly Active People",    "attribute": "Monthly Active People (#m)",     "format": "number",   "chart": "line"},
            {"label": "Monthly Active Businesses","attribute": "Monthly Active Businesses (#k)", "format": "number",   "chart": "line"},
            {"label": "Gross Profit",             "attribute": "Gross Profit",                   "format": "millions", "chart": "bar"},
        ],
    },

    # ----------------------------------------------------------------
    # Powerstop
    # KPIs from portco slides: channel revenue (Online Retail, WD),
    # product splits, gross margin
    # ----------------------------------------------------------------
    "Powerstop": {
        "kpi_cards": [
            {"label": "Net Sales",                "attribute": "Net Sales",                      "format": "millions"},
            {"label": "Adj. EBITDA",              "attribute": "Adjusted EBITDA",                "format": "millions"},
            {"label": "Gross Margin",             "attribute": "Gross Margin",                   "format": "pct"},
            {"label": "Net Leverage",             "attribute": "Net Debt / EBITDA (Datasheet)",  "format": "multiple"},
        ],
        "kpi_charts": [
            {"label": "Online Retailer Net Sales","attribute": "Net Sales (Online Retail)",      "format": "millions", "chart": "bar"},
            {"label": "WD Net Sales",             "attribute": "Net Sales (WD)",                 "format": "millions", "chart": "bar"},
            {"label": "Amazon Net Sales",         "attribute": "Amazon Net Sales (Online Retail)","format": "millions","chart": "bar"},
            {"label": "Rock Auto Net Sales",      "attribute": "Rock Auto Net Sales (Online Retail)", "format": "millions", "chart": "bar"},
            {"label": "Parts Authority (WD)",     "attribute": "Parts Authority Net Sales (WD)", "format": "millions", "chart": "bar"},
            {"label": "XL Parts | TPH (WD)",      "attribute": "XL Parts | TPH Net Sales (WD)", "format": "millions", "chart": "bar"},
            {"label": "Gross Profit",             "attribute": "Gross Profit",                   "format": "millions", "chart": "bar"},
            {"label": "Gross Margin %",           "attribute": "Gross Margin",                   "format": "pct",      "chart": "line"},
        ],
    },

}
