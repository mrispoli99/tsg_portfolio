"""
page_sop.py — SOP / Training page
Renders the TSG 73s SOP content inline with full AI Q&A capability.
All content sourced from TSG_73s_SOP_v2.pdf.
"""

import streamlit as st
import pandas as pd

NAVY      = "#071733"
SLATE     = "#3F6680"
SKY       = "#A8CFDE"
XANTHOUS  = "#F3B51F"
SEA_GREEN = "#06865C"
RED_FLAG  = "#C0392B"
LIGHT_BG  = "#F4F6F9"
BORDER    = "#E0E4EA"
GOLD      = "#F3B51F"

# -----------------------------------------------------------------------
# SOP content structured from the PDF
# -----------------------------------------------------------------------

SOP_SECTIONS = {
    "Governance": {
        "Points of Contact": "contacts",
        "Roles & Responsibilities": "roles",
        "Definitions": "definitions",
        "Timeline & SLAs": "sla",
        "Escalation & Issues": "escalation",
        "Access & Permissions": "access",
    },
    "Metric Governance": {
        "Portfolio KPI Governance": "portfolio_kpi",
        "Company KPI Governance": "company_kpi",
        "Reporting Governance": "reporting_gov",
    },
    "Onboarding": {
        "Portfolio Companies": "onboard_portco",
        "Deal Team": "onboard_deal",
        "Senior Management": "onboard_mgmt",
        "Offshore Team": "onboard_offshore",
        "Vantage Non-Finance": "onboard_vantage",
    },
    "Platform Use": {
        "Creating New Companies": "new_company",
        "Data Request Cycle": "data_request",
        "Attribute Management": "attributes",
        "Formula Management": "formulas",
        "User Permissions": "user_permissions",
        "Decommissioning Companies": "decommission",
        "Ad Hoc & Restatements": "ad_hoc",
    },
}

CONTACTS_DATA = [
    ("Platform Strategy & Roadmap", "Vantage Finance", "Priya Emerson",
     "pemerson@tsgconsumer.com", "Own platform vision, roadmap, and governance",
     "New initiatives, roadmap questions"),
    ("Budget / Vendor Management", "Vantage Finance", "Priya Emerson",
     "pemerson@tsgconsumer.com", "Manage vendor relationship and SLAs",
     "Vendor performance concerns"),
    ("Trainings & Historical Implementation", "Vantage Finance",
     "Michelle Phan; Jess Collazo-Young",
     "mphan@; jyoung@tsgconsumer.com",
     "Lead onboarding and training; maintain materials",
     "New PortCo onboarding; training requests"),
    ("Data Processing & Validation", "Vantage Finance; Offshore Team",
     "Jess Collazo-Young", "jyoung@tsgconsumer.com",
     "Process, validate, and standardize submitted data",
     "Formatting issues, validation questions"),
    ("Reporting", "Vantage", "Michelle Phan; Matt Rispoli",
     "mphan@; mrispoli@tsgconsumer.com",
     "Implement reporting changes, ensure correct data model linkage",
     "Report revisions or format updates"),
    ("KPI Definitions & Logic", "Deal Team", "Dependent on Portfolio Company",
     "TBD", "Define and maintain KPI definitions and logic",
     "KPI changes, analytical discrepancies"),
    ("Platform Issues & Escalation", "Vantage Finance", "Jess Collazo-Young",
     "jyoung@tsgconsumer.com", "Analytical review and issue escalation",
     "Data discrepancies or anomalies"),
    ("Compliance Review", "TSG Compliance", "Drew Weilbacher",
     "dweilbacher@tsgconsumer.com", "Review investor-facing materials",
     "External distribution or material changes"),
]

SLA_DATA = [
    ("PortCo data submission", "PortCo Finance Contact", "10 business days",
     "High", "Day 1 → Offshore notifies Deal Team; Day 5 → Vantage Finance; Day 10 → Deal VP + MD"),
    ("Offshore data processing", "Offshore Team", "2 business days",
     "High", "Notify Vantage Finance if processing delayed beyond 2 days"),
    ("Deal Team analytical review", "Deal Team Associate", "5 business days",
     "Medium", "Vantage Finance follows up if not acknowledged within 3 days"),
    ("Reporting updates", "Vantage Finance", "Immediate / Automatic", "—", "—"),
    ("New user access (standard)", "Vantage Finance", "2 business days",
     "Medium", "Escalate to Vantage Finance if not actioned within SLA"),
    ("User offboarding", "Vantage Finance", "1 business day",
     "High", "Vantage Finance escalates immediately if missed"),
    ("IT ticket — critical", "Technology Lead", "1 business day",
     "High", "Escalate to Executive Sponsor if unresolved beyond SLA"),
    ("IT ticket — standard", "Technology Lead", "3 business days",
     "Medium", "Escalate to Executive Sponsor if unresolved beyond SLA"),
    ("KPI / formula change approval", "Vantage Finance", "5 business days",
     "Medium", "Requestor follows up after 5 days; escalate to Priya Emerson"),
    ("Restatement request processing", "Offshore Team", "5 business days",
     "Medium", "Vantage Finance approval must precede work"),
    ("New company onboarding", "Vantage Finance + Offshore", "~60 days",
     "Low", "Flag delays to Senior Management if Phase 9 not achieved within 75 days"),
]

DEFINITIONS_DATA = [
    ("Attribute", "Defined data field collected from portfolio companies. Represents a single metric, KPI, or data point such as Revenue, Net Debt, Customer Count."),
    ("Attribute (Custom)", "Company-specific attributes. Most attributes in 73Strings will be custom to TSG portfolio companies."),
    ("Attribute (Global)", "Attributes provided by 73Strings that are not editable in the system."),
    ("Entity", "A company or organization record in 73Strings. Configured with sector, currency, and fiscal year end."),
    ("RACI", "Responsibility assignment framework: Responsible (executes), Accountable (owns), Consulted (provides input), Informed (kept updated)."),
    ("PortCo", "Portfolio Company — an entity in which TSG has an active investment and that submits financial data through 73Strings."),
    ("Claude Data Model", "Centralized data model housed in Snowflake, containing KPI calculations, time-based logic, and source table relationships. Changes follow the same governance as KPI changes."),
    ("Flag / Alert", "A threshold breach or watch condition in the Claude Flags & Alerts dashboard. Severity: Red (critical), Yellow (watch), Green (on track)."),
]


def _raci_pills(r="", a="", c="", i=""):
    pills = []
    if r: pills.append(f'<span style="background:{NAVY};color:white;padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;">R: {r}</span>')
    if a: pills.append(f'<span style="background:{GOLD};color:{NAVY};padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;">A: {a}</span>')
    if c: pills.append(f'<span style="background:{SKY};color:{NAVY};padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;">C: {c}</span>')
    if i: pills.append(f'<span style="background:#EEE;color:{SLATE};padding:3px 10px;border-radius:12px;font-size:10px;font-weight:700;">I: {i}</span>')
    return '<div style="display:flex;gap:6px;flex-wrap:wrap;margin:10px 0;">' + "".join(pills) + "</div>"


def _section_header(title, breadcrumb=""):
    bc = f'<div style="font-size:10px;color:{SLATE};margin-bottom:6px;">{breadcrumb}</div>' if breadcrumb else ""
    return f"""
    {bc}
    <div style="font-size:17px;font-weight:700;color:{NAVY};font-family:Arial;
                margin-bottom:12px;padding-bottom:8px;border-bottom:2px solid {SKY};">
        {title}
    </div>
    """


def _info_box(text):
    return f"""
    <div style="background:{LIGHT_BG};border-left:3px solid {SKY};border-radius:0 6px 6px 0;
                padding:9px 12px;font-size:12px;color:{SLATE};line-height:1.6;margin:10px 0;">
        {text}
    </div>
    """


def _warn_box(text):
    return f"""
    <div style="background:#FFF8E8;border-left:3px solid {GOLD};border-radius:0 6px 6px 0;
                padding:9px 12px;font-size:12px;color:#7a5500;line-height:1.6;margin:10px 0;">
        ⚠️ {text}
    </div>
    """


def render_sop_contacts():
    st.markdown(_section_header("Platform Points of Contact", "Platform Governance"), unsafe_allow_html=True)
    st.markdown("Use this table to identify who to contact for each platform topic before escalating.", unsafe_allow_html=True)
    df = pd.DataFrame(CONTACTS_DATA, columns=["Topic","Team","Point of Contact","Email","Responsibility","When to Engage"])
    st.dataframe(df.set_index("Topic"), use_container_width=True)


def render_sop_roles():
    st.markdown(_section_header("Roles & Responsibilities", "Platform Governance"), unsafe_allow_html=True)
    st.markdown(_raci_pills("Offshore Team", "Vantage Finance", "TSG Finance; TSG Compliance", "Senior Management"), unsafe_allow_html=True)
    roles = [
        ("Owner & Governance", "Vantage & TSG Finance\n(Priya Emerson, Jessica Duran,\nMichelle Phan, Jess Collazo-Young)",
         "Own platform strategy, roadmap, and end-to-end monitoring process",
         "Manage vendor SLAs · oversee data governance · maintain SOPs · own approvals"),
        ("Data Accuracy & Upload", "Portfolio Company (Primary Finance Contact)",
         "Ensure accuracy and completeness of submitted financials",
         "Submit monthly data per KPIs · notify team of restatements or structural changes"),
        ("Data Processing & QA", "Offshore Team (Knowcraft)",
         "Validate, process, and standardize submitted data",
         "Identify anomalies · ensure clean ingestion · escalate material issues to Deal Team"),
        ("Analytical Review", "Deal Team Associates (with VP Support)",
         "Define KPI logic and conduct final data validation",
         "Review auto-calculated outputs · analyze results · escalate discrepancies"),
        ("Data Consumption", "Senior Management (MDs & Operating Partners)",
         "Review portfolio performance to inform strategic decisions",
         "Review Claude dashboards · monitor KPI and exception trends"),
    ]
    df = pd.DataFrame(roles, columns=["Role","Team","Core Responsibility","Key Activities"]).set_index("Role")
    st.dataframe(df, use_container_width=True)


def render_sop_definitions():
    st.markdown(_section_header("Definitions", "Platform Governance"), unsafe_allow_html=True)
    df = pd.DataFrame(DEFINITIONS_DATA, columns=["Term","Definition"]).set_index("Term")
    st.dataframe(df, use_container_width=True)


def render_sop_sla():
    st.markdown(_section_header("Timeline & SLA Expectations", "Platform Governance"), unsafe_allow_html=True)
    st.markdown(_warn_box("Confirm PowerBI refresh SLA and escalation thresholds with Vantage Finance before publishing externally."), unsafe_allow_html=True)
    df = pd.DataFrame(SLA_DATA, columns=["Process","Owner","Target SLA","Severity","Escalation"])
    def color_sev(val):
        if val == "High":   return f"color: {RED_FLAG}; font-weight: 700"
        if val == "Medium": return f"color: #8a6000; font-weight: 700"
        if val == "Low":    return f"color: {SEA_GREEN}; font-weight: 700"
        return ""
    st.dataframe(df.set_index("Process").style.map(color_sev, subset=["Severity"]),
                 use_container_width=True)


def render_sop_escalation():
    st.markdown(_section_header("Escalation & Issue Resolution", "Platform Governance"), unsafe_allow_html=True)
    st.markdown(_raci_pills("Issue Identifier; Offshore Team", "Vantage Finance", "TSG Finance; TSG Compliance", "Senior Management"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-bottom:8px;">Issue Identification & Logging</div>', unsafe_allow_html=True)
        for item in [
            "Reporting or KPI inaccuracies",
            "Data discrepancies or control failures",
            "Missed deadlines or process breakdowns",
            "External feedback identifying errors",
        ]:
            st.markdown(f"• {item}")
        st.markdown("**Documentation required:** Issue description, impacted report/KPI, preliminary materiality assessment, assigned owner, target resolution date, logged in Issue Tracker.")
    with col2:
        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-bottom:8px;">Escalation & Resolution</div>', unsafe_allow_html=True)
        for item in [
            "Material financial or investor impact",
            "SLA breach",
            "Repeated or systemic control failures",
        ]:
            st.markdown(f"• {item}")
        st.markdown("**Documentation required:** Root cause analysis, corrective action plan, impact assessment, resolution date in Issue Log, formal closure documentation.")


def render_sop_access():
    st.markdown(_section_header("Access & Permissions", "Platform Governance"), unsafe_allow_html=True)
    st.markdown(_raci_pills("Offshore Team; Vantage Finance", "Vantage Finance", "Vantage Finance; TSG Compliance", "Senior Management"), unsafe_allow_html=True)

    rows = [
        ("New User", "Written request from hiring manager or team lead via email", "Vantage Finance Review; TSG Compliance (if admin)", "Offshore Team"),
        ("User Offboarding", "Written confirmation from HR or manager that user should be deactivated", "Vantage Finance", "Offshore Team — 1 business day"),
        ("Role Change", "Email from team lead specifying requested permission update", "Vantage Finance", "Offshore Team"),
        ("PortCo User", "Request from deal team member with contact details", "Vantage Finance", "Offshore Team"),
    ]
    df = pd.DataFrame(rows, columns=["Request Type","Documentation Required","Approval","Execution"]).set_index("Request Type")
    st.dataframe(df, use_container_width=True)
    st.markdown(_info_box("Quarterly review of all user access performed by Vantage Finance. Admin access requires TSG Compliance review."), unsafe_allow_html=True)


def render_sop_portfolio_kpi():
    st.markdown(_section_header("Portfolio KPI Governance", "Metric Governance"), unsafe_allow_html=True)
    st.markdown("**Definition:** Portfolio Metrics are KPIs leveraged in the portfolio datasheet or for cross-portfolio review.")
    st.markdown(_raci_pills("Offshore Team; Vantage Finance", "Vantage Finance", "Vantage Finance; TSG Finance; TSG Compliance; Deal Team", "Senior Management"), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-bottom:8px;">Adding a Portfolio KPI</div>', unsafe_allow_html=True)
        for doc in ["Clear business definition", "Exact calculation logic (formula + system source)", "Reporting frequency", "Named owner", "Identified system of record", "Approved transformation logic", "Manual adjustment policy (if applicable)", "Entry in 73s Metric Dictionary"]:
            st.markdown(f"• {doc}")
        st.markdown(f"\n**Approvals required:** Vantage Finance · TSG Finance review · TSG Compliance (if investor-facing) · Logged in KPI Change Log")
    with col2:
        st.markdown(f'<div style="font-weight:700;color:{NAVY};margin-bottom:8px;">Execution & Controls</div>', unsafe_allow_html=True)
        for ctrl in ["Initial validation test performed", "Reconciliation to financial statements", "Version control applied", "First reporting cycle reviewed by Vantage Finance"]:
            st.markdown(f"• {ctrl}")


def render_sop_company_kpi():
    st.markdown(_section_header("Company KPI Governance", "Metric Governance"), unsafe_allow_html=True)
    st.markdown("**Definition:** Company KPIs are leveraged by the deal team or Vantage specific to that company.")
    st.markdown(_raci_pills("Offshore Team; Vantage Finance", "Vantage Finance", "Vantage Finance; TSG Finance; TSG Compliance; Deal Team", "Senior Management"), unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Adding a Company KPI", "Updating / Maintaining"])
    with tab1:
        for doc in ["Clear business definition", "Exact calculation logic (formula + system source)", "Reporting frequency", "Named owner", "Identified system of record", "Approved transformation logic", "Manual adjustment policy (if applicable)", "Entry in 73s Metric Dictionary"]:
            st.markdown(f"• {doc}")
        st.markdown("**Approvals:** Deal team lead approval · Vantage Finance review · Logged in KPI Change Log")
    with tab2:
        for doc in ["Written explanation of change", "Updated calculation logic (if applicable)", "Updated system mapping (if applicable)", "Impact assessment (if material)", "Updated entry in 73s Metric Dictionary"]:
            st.markdown(f"• {doc}")
        st.markdown("**Approvals:** Deal team lead approval · Vantage Finance approval · Logged in KPI Change Log")


def render_sop_reporting_gov():
    st.markdown(_section_header("Reporting Governance", "Metric Governance"), unsafe_allow_html=True)
    st.markdown("**Definition:** Controls and oversight for creation, modification, distribution, and maintenance of recurring portfolio, fund, and management reports.")
    st.markdown(_raci_pills("Offshore Team; Vantage Finance", "Vantage Finance", "Vantage Finance; TSG Finance; TSG Compliance; Deal Team", "Senior Management"), unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Adding a New Report", "Updating a Report"])
    with tab1:
        for doc in ["Business purpose and defined audience", "Data sources and KPI definitions", "Report owner, frequency, and distribution list", "Control procedures and storage location", "Entry added to Reporting Inventory"]:
            st.markdown(f"• {doc}")
        st.markdown("**Approvals:** Vantage Finance · TSG Finance review · TSG Compliance (if external) · Logged in Report Change Log")
    with tab2:
        for doc in ["Description of change and rationale", "Updated logic or data source documentation", "Impact assessment (if material)", "Updated Reporting Inventory and Change Log"]:
            st.markdown(f"• {doc}")
        st.markdown("**Approvals:** Vantage Finance · TSG Finance (if financial impact) · TSG Compliance (if external-facing)")


def _render_phase_table(phases):
    """Render an onboarding phase table."""
    df = pd.DataFrame(phases, columns=["Phase","Timing","Key Activities","Deal Team","Vantage Finance","Success Criteria"])
    st.dataframe(df.set_index("Phase"), use_container_width=True)


def render_sop_onboard_portco():
    st.markdown(_section_header("Onboarding: Portfolio Companies", "Platform Training & Materials"), unsafe_allow_html=True)
    phases = [
        ("Phase -1: Deal Team Prep",     "Variable (~3 mo.)", "Align on reporting expectations, define metrics/KPIs, assess systems, identify reporting owner", "R", "C", "Reporting framework agreed; formal 'ready for onboarding' signal sent"),
        ("Phase 0: Pre-Onboarding",      "Day 0–3",           "Confirm onboarding required, align internally on scope", "A", "R", "Decision to onboard, initial scope defined"),
        ("Phase 1: Internal Alignment",  "Day 0–5",           "Define cadence, data fields, historical scope, contacts, go-live date, escalation path", "A", "R", "All requirements documented; contacts + timeline confirmed"),
        ("Phase 2: Kickoff Scheduling",  "Day 5–10",          "Identify PortCo contact, schedule intro meeting, send pre-read materials", "R", "R", "Meeting scheduled; materials shared"),
        ("Phase 3: Kickoff Meeting",     "Day 7–14",          "Conduct walkthrough (tool, data, timing), align expectations, confirm next steps", "R", "R", "PortCo understands process; submission plan confirmed"),
        ("Phase 4: System Activation",   "Day 14–21",         "Send first automated request, confirm receipt, track submission", "C", "A", "First request delivered; submission initiated"),
        ("Phase 5: First Submission",    "Day 21–30",         "Receive data, validate, resolve discrepancies, finalize dataset", "C", "A", "Clean dataset; no critical errors"),
        ("Phase 6: Stabilization",       "Day 30–60",         "Repeat reporting cycle, monitor timeliness, reduce errors", "C", "A", "2nd successful submission; improved accuracy"),
        ("Phase 7: Steady-State",        "Ongoing",           "Monthly/quarterly reporting, issue tracking, performance monitoring", "C", "A", "On-time submissions; consistent data quality"),
        ("Phase 8: Escalation",          "Trigger-based",     "Escalate missed deadlines, poor data quality, non-responsiveness", "A", "R", "Issues resolved via Deal Team intervention"),
        ("Phase 9: Onboarding Complete", "~Day 60",           "Confirm independence, documentation complete, transition to BAU", "A", "R", "2 clean cycles; full handoff achieved"),
    ]
    _render_phase_table(phases)


def render_sop_onboard_deal():
    st.markdown(_section_header("Onboarding: Deal Team", "Platform Training & Materials"), unsafe_allow_html=True)
    phases = [
        ("Phase 0: Access & Setup",         "Day 0–2",   "Grant access to systems; confirm permissions", "R", "A", "User can log into all systems; no access issues"),
        ("Phase 1: Tool Orientation",       "Day 1–5",   "Walkthrough of platform (navigation, where data lives, reporting structure)", "R", "A", "User understands where to find key data"),
        ("Phase 2: Excel Plugin Training",  "Day 3–7",   "Install + train on Excel plug-in (data pulls, refreshes, templates)", "R", "A", "User can independently pull and refresh data in Excel"),
        ("Phase 3: Notifications & Workflow","Day 3–7",  "Configure notifications; explain reporting cadence", "R", "A", "Notifications set; user understands reporting flow"),
        ("Phase 4: Standard Reporting Review","Day 5–10","Walkthrough of standard outputs (portfolio dashboard, KPIs, historical trends)", "R", "A", "User can interpret core reporting outputs"),
        ("Phase 5: Valuation Workflow",     "Day 7–14",  "Train on updating valuation workbook using Excel plug-in", "R", "A", "User can update valuation file with live data"),
        ("Phase 6: Portfolio Datasheet Mgmt","Day 7–14", "Review auto-calculated portfolio datasheet; explain adjustments, overrides", "R", "A", "User can make adjustments correctly"),
        ("Phase 7: PowerBI Access",         "Day 7–14",  "Train on accessing dashboards, filtering, exporting, interpreting metrics", "R", "A", "User can navigate and extract insights"),
        ("Phase 8: Manual Reporting",       "Day 10–14", "Build custom analyses using Excel plug-in", "R", "A", "User can independently create custom reporting"),
        ("Phase 9: Validation & Certification","Day 10–14","Complete test case (update valuation + generate report + validate outputs)", "R", "A", "User demonstrates full workflow competency"),
        ("Phase 10: Post-Onboarding Review","Within 30d","Review updated valuation workbook; validate data integrity and linkage", "R", "A", "Workbook reviewed and approved; user certified"),
    ]
    _render_phase_table(phases)


def render_sop_onboard_mgmt():
    st.markdown(_section_header("Onboarding: Senior Management", "Platform Training & Materials"), unsafe_allow_html=True)
    phases = [
        ("Phase 0: Access & Setup",          "Day 0–2",  "Provide access to Claude dashboards and key reporting materials", "R", "A", "User can access all dashboards without friction"),
        ("Phase 1: Executive Reporting Overview","Day 1–5","Walkthrough of standard reporting (portfolio dashboards, KPIs, cadence)", "R", "A", "User knows what standard reporting exists"),
        ("Phase 2: KPI & Metric Framing",    "Day 1–5",  "High-level overview of key KPIs — definitions, what matters, how to interpret", "R", "A", "User understands core metrics and decision relevance"),
        ("Phase 3: Dashboard Navigation",    "Day 3–7",  "Focused walkthrough (filters, slicing, drilling into PortCos, exporting)", "R", "A", "User can quickly navigate and extract insights"),
        ("Phase 4: Data Context & Reliability","Day 3–7","High-level explanation of data sources, refresh cadence, key limitations", "R", "A", "User understands when to trust vs. question data"),
        ("Phase 5: Bespoke Reporting — Self-Service","Day 5–10","Overview of how to create custom views", "R", "A", "User can generate simple custom views independently"),
        ("Phase 6: Request Pathway",         "Day 5–10", "Define how to request new reporting (who to contact, turnaround)", "R", "A", "User knows how to efficiently request new analyses"),
        ("Phase 7: Decision Use Cases",      "Day 7–10", "Apply reporting to real scenarios (IC prep, board materials, performance reviews)", "R", "A", "User can leverage reporting in decision-making"),
        ("Phase 9: Ongoing Feedback Loop",   "Ongoing",  "Capture feedback on reporting gaps, new needs, and usability improvements", "R", "A", "Continuous improvement of reporting outputs"),
    ]
    _render_phase_table(phases)


def render_sop_onboard_offshore():
    st.markdown(_section_header("Onboarding: Offshore Team / Data Management", "Platform Training & Materials"), unsafe_allow_html=True)
    phases = [
        ("Phase 0: Access & Setup",         "Day 0–3",  "Grant access to systems, templates, and documentation; confirm permissions", "R", "A", "User can access all required systems and files"),
        ("Phase 1: Process Overview",       "Day 1–5",  "End-to-end walkthrough of reporting lifecycle (PortCo submission → validation → final reporting)", "R", "A", "User understands full workflow and their role"),
        ("Phase 2: Tool Training",          "Day 3–7",  "Hands-on training in the reporting tool (data ingestion, validation, tracking submissions)", "R", "A", "User can navigate and operate the tool independently"),
        ("Phase 3: Data Validation & QA",   "Day 5–10", "Train on validation rules (completeness, consistency, variance checks, tie-outs)", "R", "A", "User can identify and flag data issues accurately"),
        ("Phase 4: Issue Identification",   "Day 5–10", "Define issue types (minor vs critical), documentation standards, and triage process", "R", "A", "User can classify and prioritize issues correctly"),
        ("Phase 5: Escalation Protocol",    "Day 7–12", "Train on when/how to escalate to Deal Team and Vantage Finance (including SLAs)", "R", "A", "Issues escalated appropriately and on time"),
        ("Phase 6: Communication Standards","Day 7–12", "Establish communication guidelines (clear issue summaries, required details, follow-ups)", "R", "A", "Clear, concise communication with Deal Team"),
        ("Phase 7: Reporting Cycle Execution","Day 10–14","Execute a full mock or real reporting cycle (request → submission → validation → escalation)", "R", "A", "User completes full cycle with minimal supervision"),
        ("Phase 8: Documentation & Tracking","Day 10–14","Train on logging issues, tracking status, maintaining audit trail", "R", "A", "All work is documented and traceable"),
        ("Phase 9: Ongoing Operations",     "Ongoing",  "Monitor performance (timeliness, accuracy, issue rates), continuous improvement", "R", "A", "Consistent, high-quality execution of reporting cycles"),
    ]
    _render_phase_table(phases)


def render_sop_onboard_vantage():
    st.markdown(_section_header("Onboarding: Vantage Non-Finance", "Platform Training & Materials"), unsafe_allow_html=True)
    phases = [
        ("Phase 0: Access & Setup",         "Day 0–2",  "Grant access to reporting tools; confirm permissions", "R", "A", "User can access all dashboards and reporting materials"),
        ("Phase 1: Reporting Orientation",  "Day 1–5",  "Overview of reporting structure (portfolio KPIs, cadence, key outputs)", "R", "A", "User understands what reports exist and where to find them"),
        ("Phase 2: Dashboard Training",     "Day 3–7",  "Walkthrough of dashboards (navigation, filters, drill-downs, exporting)", "R", "A", "User can independently navigate and extract insights"),
        ("Phase 3: KPI & Metric Definitions","Day 3–7", "Review key metrics (definitions, calculation logic, limitations, common pitfalls)", "R", "A", "User understands how core KPIs are defined"),
        ("Phase 4: Data Flow & Source Context","Day 5–10","Explain how data is sourced (PortCo submissions, Excel plug-in, transformations)", "R", "A", "User understands where data comes from"),
        ("Phase 5: Data Reliability & Limitations","Day 5–10","Review known limitations (timing lags, manual adjustments, estimation areas)", "R", "A", "User can appropriately interpret and challenge data"),
        ("Phase 6: Standard Use Cases",     "Day 7–10", "Walkthrough of common use cases (portfolio reviews, IC prep, performance tracking)", "R", "A", "User can apply reports to real business decisions"),
        ("Phase 7: Self-Service Analysis",  "Day 7–14", "Training on exporting data and light analysis", "R", "A", "User can perform basic independent analysis"),
        ("Phase 8: Practical Application",  "Day 10–14","Complete a practical exercise (analyze a PortCo, pull KPIs, identify trends)", "R", "A", "User demonstrates ability to interpret and use data"),
        ("Phase 9: Ongoing Feedback Loop",  "Ongoing",  "Provide channel for questions, feedback, and continuous improvement", "R", "A", "User is engaged and provides feedback on reporting usefulness"),
    ]
    _render_phase_table(phases)


def render_sop_new_company():
    st.markdown(_section_header("Creating New Companies in 73Strings", "Platform Use"), unsafe_allow_html=True)
    st.markdown(_warn_box("Deal team lead written approval is required before entity creation begins. Approving lead name + email + confirmation checkbox must be completed on form submission."), unsafe_allow_html=True)
    steps = [
        ("1", "Receive Form 01 & get written approval", "Email deal team · await confirmation · save form to shared folder · log into 73Strings\nApprover: Deal Team Lead  ·  Notified: Jess Collazo-Young; Offshore Team"),
        ("2", "Click 'Create Entity' in 73S Monitor", "Admin only · navigate to 73S Monitor → Briefcase button (left toolbar) · panel opens on right"),
        ("3", "Define entity details — from Form 01", "Company identity: legal name, DBA, fund, sector, geography\nInvestment details: investment date, fiscal year end, reporting currency (USD), reporting frequency, expected first reporting period, TSG ownership %, security type"),
        ("4", "Define company profile", "After entity is created · navigate to Overview → Profile"),
        ("5", "Add contacts", "Navigate to Contacts tab · add key contacts from Form 01"),
        ("6", "Add company attributes and create lineage record", "Settings → Bulk Upload → Get All Templates → Attributes Template\nCopy/paste labels from: Income statement · Balance sheet · Cash flow (SOCF) · KPI supplement · Budget/forecast · Mgmt. adj. EBITDA bridge\nAppend '(SOCF)' to all cash flow labels before importing"),
    ]
    for num, title, detail in steps:
        with st.expander(f"Step {num}: {title}", expanded=True):
            for line in detail.split("\n"):
                st.markdown(line)


def render_sop_data_request():
    st.markdown(_section_header("Data Request Cycle", "Platform Use"), unsafe_allow_html=True)
    st.markdown("73S Monitor → My Portfolio → [PortCo] → Data Requests")
    steps = [
        ("1", "Create the data request", "73S Monitor → My Portfolio → [PortCo] → Data Requests → Create a request\nEntity: Company · Business unit: Consol · Mode of collection: Request Documents · Documents: All\nVersion: Annual budget → Budget · Financials → Actual · Forecasts → Forecast\nPeriod type: Quarterly · Due in: 10 days · Grace period: 0 (no extensions)"),
        ("2", "Schedule a recurring request", "After initial request is generated · click the radio button on the request → Schedule recurring request (lower right)\nFrequency: Monthly (or quarterly/annual if directed) · Condition: Ends after · Recurrence stop: 10"),
        ("3", "Request moves to Open (Status: Open)", "To cancel or edit: click the 3 dots to the left of the request and follow the prompts"),
        ("4", "Request fulfilled → moves to Under Review", "Map the financials to attributes following the same process as outlined in Step 6 of Creating New Companies\nOnce mapped, the request will automatically move to Closed"),
    ]
    for num, title, detail in steps:
        with st.expander(f"Step {num}: {title}", expanded=True):
            for line in detail.split("\n"):
                st.markdown(line)
    st.markdown(_info_box("Missed submission escalation: Day 1 → Offshore notifies Deal Team · Day 2 → Deal Team contacts PortCo · Day 5 → Escalate to Vantage Finance · Day 10 → Escalate to Deal VP and MD. All missed submissions must be documented in the Issue Tracker."), unsafe_allow_html=True)


def render_sop_attributes():
    st.markdown(_section_header("Attribute Management", "Platform Use"), unsafe_allow_html=True)
    st.markdown("Admin access only · 73S Monitor → Settings → Attribute Management · Audit log: Platform Audit Log")
    st.markdown(_warn_box("Cash flow attributes must always include '(SOCF)' in the attribute name. Statement suffixes: (BS) | (SOCF) | (IS) | (Cov)"), unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Adding Attributes", "Editing & Maintaining", "Retiring", "Quarterly Audit"])
    with tab1:
        scenarios = [
            ("1", "Label on multiple financial statements", "Suffix with statement tag in parentheses", '"Revolver (BS)", "Revolver (SOCF)"'),
            ("2", "Same label across multiple metric types", "Suffix with metric name", '"HVAC Install Revenue", "HVAC Install Gross Profit"'),
            ("3", "Same label across entities/channels", "Suffix with entity/channel identifier", '"Royalty Income (Sola Salons)", "Royalty Income (Woodhouse)"'),
            ("4", "Extra spaces, punctuation, formatting", "Adjust system name to be correct", '"A/R- Credit Cards" → "A/R - Credit Cards"'),
            ("5", 'Label uses "Less:", "(-)", "Add:"', "Strip prefix, then apply scenario 1", '"Less: Accum. Depreciation" → "Accum. Depreciation"'),
            ("6", "Same data point, new label (existing)", "Rename attribute — add old name as synonym", '"SLEBITDA" → "Studio Contribution"'),
            ("7", "Label changes over time (new/existing)", "Use most recent label — add prior as synonym", '"Net Loss" → "Net Income (Loss)"'),
        ]
        df = pd.DataFrame(scenarios, columns=["#","Scenario","Action","Example"]).set_index("#")
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.markdown("**When a PortCo renames a line item (Scenarios 6 & 7):**")
        for step in ["Draft email to deal team member (cc Vantage Finance) — include original name, updated name, supporting financials",
                     "Receive written approval from deal team and Vantage Finance",
                     "Do not make any changes in 73S until written approval is received",
                     "Rename attribute in 73S · add prior name as a synonym · update lineage record"]:
            st.markdown(f"• {step}")
        st.markdown("**Synonym management:** Navigate to attribute → open edit panel (pencil icon) → add old name in Synonym field. Review synonyms quarterly.")

    with tab3:
        st.markdown(_warn_box("Do not delete attributes — deletion affects reporting and other portfolio companies. Always inactivate instead."), unsafe_allow_html=True)
        for step in ["Obtain written approval from both Deal Team and Vantage Finance",
                     "Confirm attribute is not still in use — if so, resolve dependencies first",
                     "Use the edit icon (pencil) to mark as inactive — never the delete (trash) icon",
                     "Document reason in Metric Change Log · update KPIs Master · notify affected deal team members"]:
            st.markdown(f"• {step}")

    with tab4:
        for step in ["Offshore Team pulls the full attribute list from 73S each quarter",
                     "Reconcile against each PortCo's latest source financials",
                     "Flag any attribute with no data in 2+ consecutive periods",
                     "Review all synonyms for accuracy and no duplicate mapping conflicts",
                     "Document findings in Platform Audit Log",
                     "Vantage Finance reviews and approves all findings before any changes are implemented"]:
            st.markdown(f"• {step}")


def render_sop_formulas():
    st.markdown(_section_header("Formula Management", "Platform Use"), unsafe_allow_html=True)
    st.markdown("Admin access only · 73S Monitor → Settings → Formula Management · Change log: Metric Change Log")
    st.markdown(_raci_pills("Offshore Team; Vantage Finance", "Vantage Finance", "Vantage Finance; TSG Finance; Deal Team", "Senior Management"), unsafe_allow_html=True)
    st.markdown(_warn_box("Formula must not go live without written approval from Vantage Finance. Do not delete formulas — always inactivate."), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Creating a Formula", "Editing a Formula", "Retiring a Formula"])
    with tab1:
        for step in ["Apply naming conventions — use Title Case, unique/descriptive names (e.g. 'EBITDA Margin' not 'Formula 1'). For nested formulas, name parent to show dependency",
                     "Click 'Add Formula' — enter Formula Name, Formula expression, Applicable Entities (default all; deselect non-applicable), Description",
                     "Define calculator settings — Version: keep all · Period: keep all · Missing default values: always set to 0",
                     "For nested formulas: name parent formula to show dependency relationship · document full chain in Description field and KPIs Master",
                     "Pre-live validation: back-test against at least 2 prior periods · reconcile to source statements · confirm entity assignments · Vantage Finance written approval required",
                     "Log in Metric Change Log — effective date and approver name"]:
            st.markdown(f"• {step}")
    with tab2:
        for step in ["Edit via the pencil icon — Settings → Formula Management · locate formula → click edit icon",
                     "Do not delete — use edit only",
                     "Re-run pre-live validation (Step 5 above) after any edit",
                     "Re-confirm entity assignments after editing",
                     "Log the edit in Metric Change Log with effective date and approver"]:
            st.markdown(f"• {step}")
    with tab3:
        for step in ["Obtain written approval from both Deal Team and Vantage Finance",
                     "Confirm formula is not referenced in active reports, KPIs, or nested formulas",
                     "Use edit icon to mark as inactive — preserves audit trail and historical values",
                     "Update KPIs Master — retirement date and reason",
                     "Log in Metric Change Log"]:
            st.markdown(f"• {step}")


def render_sop_user_permissions():
    st.markdown(_section_header("User Permissions", "Platform Use"), unsafe_allow_html=True)
    st.markdown("73S — Initials Bubble (upper right) → User Access Management")
    steps = [
        ("1", "Click 'Add User' and define details", "73S → Initials Bubble → User Access Management → Add User → New User\nUser Name: Full name · Email: business email · User Type: 'User' unless known admin\nTools Access: Select all Product Tools except 73 Value - Credit"),
        ("2", "Configure entity access", "Under Entity, click dropdown next to POC → choose applicable PortCo(s)\nGrant read or write access under 73 Extract & Monitor and 73 Value - Equity\nTransaction section: nothing selected"),
        ("3", "Save and confirm", "User saved in User Access Management · confirm user receives welcome email from 73S"),
    ]
    for num, title, detail in steps:
        with st.expander(f"Step {num}: {title}", expanded=True):
            for line in detail.split("\n"):
                st.markdown(line)


def render_sop_decommission():
    st.markdown(_section_header("Decommissioning Companies", "Platform Use"), unsafe_allow_html=True)
    st.markdown("Admin access only · 73S Monitor → Briefcase button · Archive documentation: Platform Audit Log")
    st.markdown(_warn_box("Do not delete the entity — all historical data must be preserved. User permissions must be updated separately."), unsafe_allow_html=True)
    steps = [
        ("1", "Trigger & authorization", "Exit event confirmed by Deal Team and Vantage Finance\nWritten authorization required before any activity begins\nPortCo exit confirmed · Written auth — Vantage Finance · Written auth — Deal Team lead · Final reporting period closed & validated"),
        ("2", "System actions in 73S", "Admin only · 73S Monitor → Briefcase button\n• Cancel all open / scheduled recurring data requests\n• Inactivate PortCo user access\n• Set entity status to inactive — do not delete\n• Deselect all entity-specific formulas\n• Verify no cross-portfolio formulas affected"),
        ("3", "Documentation & notification", "• Log in Platform Audit Log — exit date, authorizing parties, final reporting period\n• Update KPIs Master → inactive status\n• Update Reporting Master → inactive status\n• Notify all users — access removed\n• Archive source financials & intake docs\n• Notify TSG Compliance if in investor-facing report"),
    ]
    for num, title, detail in steps:
        with st.expander(f"Step {num}: {title}", expanded=True):
            for line in detail.split("\n"):
                st.markdown(line)


def render_sop_ad_hoc():
    st.markdown(_section_header("Ad Hoc & Restatement Requests", "Platform Use"), unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Ad Hoc / One-Off Data Requests", "Restatement Requests"])

    with tab1:
        st.markdown("**Form 03 — Submit Ad Hoc Data Request**")
        st.markdown("Approver: Deal Team Lead · Notified: Vantage Finance · Assigned to: Offshore Team")
        st.markdown("**Required fields:** Portfolio company · Fund · Data version (Actual/Budget/Forecast) · Reporting period · Statements/data requested · Business justification · Data needed by (date)")
        st.markdown("**Statements to select:** Income statement · Balance sheet · Cash flow statement · KPI supplement · Mgmt. EBITDA bridge")
        st.markdown(_warn_box("Grace period is 0 — escalation begins immediately on due date. Day 1: Offshore Team notifies Deal Team · Day 2: Deal Team contacts PortCo · Day 5: Escalate to Vantage Finance · Day 10: Escalate to Deal VP and MD"), unsafe_allow_html=True)

    with tab2:
        st.markdown("**Form 04 — Submit Restatement Request**")
        st.markdown("Approver: Vantage Finance · Notified: Deal Team · Assigned to: Offshore Team")
        st.markdown(_warn_box("Offshore Team must not begin any restatement activity until Vantage Finance has approved the scope."), unsafe_allow_html=True)
        for step in ["Deal Team submits written restatement request to Vantage Finance",
                     "Vantage Finance reviews and approves scope",
                     "Offshore Team creates new data request labeled: 'Restatement – [PortCo] – [Period]'",
                     "Receive, validate, and import corrected data — supersedes original · document in Metric Change Log",
                     "Re-validate all impacted outputs (KPIs, reports, dashboards)",
                     "If investor-facing material is affected, Senior Management must be informed before closing"]:
            st.markdown(f"• {step}")


RENDER_MAP = {
    "contacts":       render_sop_contacts,
    "roles":          render_sop_roles,
    "definitions":    render_sop_definitions,
    "sla":            render_sop_sla,
    "escalation":     render_sop_escalation,
    "access":         render_sop_access,
    "portfolio_kpi":  render_sop_portfolio_kpi,
    "company_kpi":    render_sop_company_kpi,
    "reporting_gov":  render_sop_reporting_gov,
    "onboard_portco": render_sop_onboard_portco,
    "onboard_deal":   render_sop_onboard_deal,
    "onboard_mgmt":   render_sop_onboard_mgmt,
    "onboard_offshore":render_sop_onboard_offshore,
    "onboard_vantage":render_sop_onboard_vantage,
    "new_company":    render_sop_new_company,
    "data_request":   render_sop_data_request,
    "attributes":     render_sop_attributes,
    "formulas":       render_sop_formulas,
    "user_permissions":render_sop_user_permissions,
    "decommission":   render_sop_decommission,
    "ad_hoc":         render_sop_ad_hoc,
}


# -----------------------------------------------------------------------
# SOP full text for AI Q&A context
# -----------------------------------------------------------------------

SOP_AI_CONTEXT = """
TSG Consumer Partners — Platform SOP Summary (TSG 73s SOP v2, March 2026)

POINTS OF CONTACT:
- Platform Strategy & Roadmap: Priya Emerson (Vantage Finance)
- Budget/Vendor: Priya Emerson
- Trainings & Implementation: Michelle Phan, Jess Collazo-Young
- Data Processing & Validation: Jess Collazo-Young
- Reporting: Michelle Phan, Matt Rispoli
- KPI Definitions: Deal Team (company-specific)
- Platform Issues & Escalation: Jess Collazo-Young
- Compliance Review: Drew Weilbacher

KEY SLAs:
- PortCo data submission: 10 business days (escalate Day 1 → 5 → 10)
- Offshore data processing: 2 business days
- Deal Team review: 5 business days
- New user setup: 2 days (standard), 5 days (admin)
- User offboarding: 1 business day (High severity)
- KPI/formula change approval: 5 business days
- New company onboarding: ~60 days (2 clean reporting cycles)

GOVERNANCE:
- All KPI additions require: business definition, calculation logic, frequency, owner, system of record, KPI Change Log entry
- Portfolio KPIs require Vantage Finance + TSG Finance + TSG Compliance approvals
- Company KPIs require Deal Team Lead + Vantage Finance approvals
- All formula changes require written Vantage Finance approval before go-live
- Do not delete attributes or formulas — always inactivate to preserve audit trail

RACI (default):
- R: Offshore Team, Vantage Finance
- A: Vantage Finance
- C: Vantage Finance, TSG Finance, TSG Compliance, Deal Team
- I: Senior Management

73 STRINGS CONVENTIONS:
- Cash flow attributes must include "(SOCF)" suffix
- Statement suffixes: (BS) | (SOCF) | (IS) | (Cov)
- Formula names: Title Case, unique, descriptive
- Nested formulas: name parent to show dependency (e.g. "LTM EBITDA" feeds "LTM EBITDA Margin")
- Never use "Default" checkbox for formulas

ESCALATION PATH (data issues):
Day 1: Offshore notifies Deal Team
Day 5: Escalate to Vantage Finance
Day 10: Deal Team VP + MD

ONBOARDING (PortCo):
Phase -1 to Phase 9 (~60 days total, 2 clean reporting cycles required for certification)
"""


# -----------------------------------------------------------------------
# Main page function
# -----------------------------------------------------------------------

def page_sop():
    from ui import render_page_header
    render_page_header("SOPs & Trainings")

    # Top-level tabs: SOP content | Requests
    sop_tab, req_tab = st.tabs(["📋 SOPs & Trainings", "📝 Requests"])

    # ----------------------------------------------------------------
    # TAB 2: Requests — form-fill submissions
    # ----------------------------------------------------------------
    with req_tab:
        st.markdown('<div class="section-header">Submit a Request</div>',
                    unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:13px;color:{SLATE};font-family:Arial;margin-bottom:16px;">'
            "Use the form below to submit a request to the Vantage Finance team. "
            "All submissions are logged and reviewed within 2 business days."
            "</div>",
            unsafe_allow_html=True
        )

        REQUEST_TYPES = [
            "New Company Onboarding",
            "KPI / Metric Change",
            "Data Restatement",
            "Attribute Addition or Edit",
            "Formula Change",
            "User Access & Permissions",
            "Report Change or New Report",
            "Ad Hoc Data Request",
            "Platform Issue / Bug",
            "Other",
        ]

        with st.container():
            r1, r2 = st.columns(2)
            with r1:
                req_type = st.selectbox("Request Type *", REQUEST_TYPES,
                                        key="req_type")
                req_company = st.text_input("Portfolio Company (if applicable)",
                                             placeholder="e.g. ATI, Mavis, Summer Fridays",
                                             key="req_company")
                req_priority = st.selectbox("Priority *",
                                             ["Normal", "High", "Urgent"],
                                             key="req_priority")
            with r2:
                req_submitter = st.text_input("Your Name *",
                                               placeholder="First Last",
                                               key="req_submitter")
                req_email = st.text_input("Your Email *",
                                           placeholder="name@tsgconsumer.com",
                                           key="req_email")
                req_due = st.date_input("Requested By Date",
                                         key="req_due")

            req_description = st.text_area(
                "Description *",
                placeholder="Please describe the request in detail. Include any relevant context, "
                            "data sources, or examples.",
                height=140,
                key="req_description"
            )
            req_attachments = st.text_input(
                "Relevant Links / File Paths (optional)",
                placeholder="e.g. SharePoint link, 73Strings path, Google Drive URL",
                key="req_attachments"
            )

            st.markdown("<br>", unsafe_allow_html=True)
            sub_col, _ = st.columns([1, 4])
            with sub_col:
                submitted = st.button("Submit Request", type="primary",
                                       use_container_width=True, key="req_submit")

            if submitted:
                missing = []
                if not req_submitter.strip(): missing.append("Your Name")
                if not req_email.strip():     missing.append("Your Email")
                if not req_description.strip(): missing.append("Description")
                if missing:
                    st.error(f"Please fill in the required fields: {', '.join(missing)}")
                else:
                    # Log to session state (in production, write to a DB/sheet)
                    if "req_submissions" not in st.session_state:
                        st.session_state["req_submissions"] = []
                    import datetime
                    st.session_state["req_submissions"].append({
                        "Submitted":    datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Type":         req_type,
                        "Company":      req_company or "—",
                        "Priority":     req_priority,
                        "Submitter":    req_submitter,
                        "Email":        req_email,
                        "Due By":       str(req_due),
                        "Description":  req_description,
                        "Links":        req_attachments or "—",
                        "Status":       "Submitted",
                    })
                    st.success(
                        f"✅ Request submitted! The Vantage Finance team will follow up "
                        f"at **{req_email}** within 2 business days."
                    )

        # Show prior submissions this session
        if st.session_state.get("req_submissions"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-header">Submissions This Session</div>',
                        unsafe_allow_html=True)
            import pandas as _rpd
            req_df = _rpd.DataFrame(st.session_state["req_submissions"])
            st.dataframe(req_df, use_container_width=True, hide_index=True)

    # ----------------------------------------------------------------
    # TAB 1: SOPs & Trainings — search + left nav + content
    # ----------------------------------------------------------------
    with sop_tab:

        # Search bar at top
        search_query = st.text_input(
            "Search SOP content",
            placeholder="e.g. KPI governance, restatement, user access...",
            key="sop_search"
        )

        # Two-panel layout: sidebar nav + content
        sidebar_col, content_col = st.columns([1, 4])

        # Determine active section
        if "sop_active" not in st.session_state:
            st.session_state["sop_active"] = "contacts"
        active = st.session_state["sop_active"]

        # Scrollable left nav CSS — sticky, independent scroll
        st.markdown("""
        <style>
        div[data-testid="column"]:first-child {
            position: sticky;
            top: 60px;
            max-height: calc(100vh - 80px);
            overflow-y: auto;
            align-self: flex-start;
        }
        </style>
        """, unsafe_allow_html=True)

        # Sidebar navigation — always type="secondary" to prevent Streamlit
        # from dropping the widget on rerun; active state shown via label prefix
        with sidebar_col:
            for group, sections in SOP_SECTIONS.items():
                st.markdown(
                    f'<div style="font-size:10px;font-weight:700;color:{SLATE};'
                    f'text-transform:uppercase;letter-spacing:0.5px;'
                    f'padding:10px 0 4px 0;margin-top:4px;text-align:left;">{group}</div>',
                    unsafe_allow_html=True
                )
                for label, key in sections.items():
                    is_active = (key == active)
                    btn_label = f"▶  {label}" if is_active else f"    {label}"
                    # Always secondary — type change caused buttons to disappear on rerun
                    if st.button(
                        btn_label,
                        key=f"sop_nav_{key}",
                        use_container_width=True,
                        type="secondary",
                    ):
                        st.session_state["sop_active"] = key
                        st.rerun()

        # Content area
        with content_col:
            # AI Q&A panel
            with st.expander("AI Q&A — Ask anything about this SOP", expanded=False):
                sop_chat_key = "sop_ai_chat"
                if sop_chat_key not in st.session_state:
                    st.session_state[sop_chat_key] = []

                suggested = [
                    "What are the SLAs for PortCo data submission?",
                    "Who approves new KPIs?",
                    "How do I request a restatement?",
                    "What naming conventions should I use for formulas?",
                    "What is the escalation process for missed deadlines?",
                    "How do I create a new company in 73Strings?",
                ]
                if not st.session_state[sop_chat_key]:
                    sug_cols = st.columns(3)
                    for i, s in enumerate(suggested):
                        if sug_cols[i % 3].button(s, key=f"sop_sug_{i}", use_container_width=True):
                            st.session_state[sop_chat_key].append({"role": "user", "content": s})
                            try:
                                from ai import ask_claude
                                resp = ask_claude(s, SOP_AI_CONTEXT, [])
                                st.session_state[sop_chat_key].append({"role": "assistant", "content": resp})
                            except Exception as exc:
                                st.session_state[sop_chat_key].append(
                                    {"role": "assistant", "content": f"AI unavailable: {exc}"})
                            st.rerun()

            for msg in st.session_state[sop_chat_key]:
                role_style = (
                    f"background:{NAVY};color:white;padding:8px 12px;border-radius:10px 10px 2px 10px;"
                    if msg["role"] == "user" else
                    f"background:{LIGHT_BG};color:{NAVY};padding:8px 12px;border-radius:10px 10px 10px 2px;"
                    f"border:1px solid {BORDER};"
                )
                st.markdown(
                    f'<div style="{role_style}font-size:12px;font-family:Arial;margin:4px 0;">'
                    f'{msg["content"]}</div>',
                    unsafe_allow_html=True
                )

            if st.session_state[sop_chat_key]:
                if st.button("Clear conversation", key="sop_clear_chat"):
                    st.session_state[sop_chat_key] = []
                    st.rerun()

            user_q = st.chat_input("Ask anything about the SOP...", key="sop_chat_input")
            if user_q:
                st.session_state[sop_chat_key].append({"role": "user", "content": user_q})
                try:
                    from ai import ask_claude
                    resp = ask_claude(user_q, SOP_AI_CONTEXT, st.session_state[sop_chat_key][:-1])
                    st.session_state[sop_chat_key].append({"role": "assistant", "content": resp})
                except Exception as exc:
                    st.session_state[sop_chat_key].append(
                        {"role": "assistant", "content": f"AI unavailable: {exc}"})
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # If searching, find matching sections
        if search_query.strip():
            st.markdown(
                f'<div style="font-size:12px;color:{SLATE};margin-bottom:12px;">'
                f'Showing results for: <b>{search_query}</b> — click a section to navigate</div>',
                unsafe_allow_html=True
            )
            query_lower = search_query.lower()
            matches = []
            for group, sections in SOP_SECTIONS.items():
                for label, key in sections.items():
                    if query_lower in label.lower() or query_lower in group.lower():
                        matches.append((group, label, key))
            if matches:
                for group, label, key in matches:
                    if st.button(f"{group} → {label}", key=f"sop_match_{key}"):
                        st.session_state["sop_active"] = key
                        st.session_state["sop_search"] = ""
                        st.rerun()
            else:
                st.info("No matching sections found. Try the AI Q&A above for specific questions.")

        # Render active section
        render_fn = RENDER_MAP.get(active)
        if render_fn:
            render_fn()
        else:
            st.info("Select a section from the sidebar.")
