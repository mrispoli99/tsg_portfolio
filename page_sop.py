"""
page_sop.py  —  SOP Reference + 10 Request Forms
Native Streamlit — no iframe, no sandboxing issues.
Forms email to mphan@tsgconsumer.com on submit via mailto link.
"""

import streamlit as st

RECIPIENT = "mphan@tsgconsumer.com"
NAVY  = "#071733"; SLATE = "#3F6680"; SKY  = "#A8CFDE"; GOLD  = "#F3B51F"
GREEN = "#06865C"; RED   = "#C0392B"; BORDER = "#E0E4EA"; LIGHT = "#F4F6F9"

CSS = f"""<style>
.sop-grp{{font-size:9px;font-weight:700;color:#8A9BB0;text-transform:uppercase;
  letter-spacing:.5px;padding:8px 4px 3px;margin-top:2px}}
.info-box{{background:#EFF5FA;border-left:3px solid {SKY};border-radius:0 6px 6px 0;
  padding:9px 12px;font-size:11.5px;color:{SLATE};line-height:1.6;margin:10px 0}}
.warn-box{{background:#FFF8E8;border-left:3px solid {GOLD};border-radius:0 6px 6px 0;
  padding:9px 12px;font-size:11.5px;color:#7a5500;line-height:1.6;margin:10px 0}}
.step-list{{list-style:none;padding:0;margin:8px 0}}
.step-list li{{display:flex;gap:8px;padding:6px 0;border-bottom:.5px solid {BORDER};
  font-size:12px;line-height:1.55}}
.sn{{min-width:20px;height:20px;border-radius:50%;background:{NAVY};color:white;
  font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;margin-top:1px}}
.gov-table{{width:100%;border-collapse:collapse;font-size:11.5px;margin:10px 0}}
.gov-table th{{background:{NAVY};color:white;padding:7px 10px;text-align:left;
  font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.3px}}
.gov-table td{{padding:7px 10px;border-bottom:.5px solid {BORDER};vertical-align:top;line-height:1.5}}
.gov-table tr:nth-child(even) td{{background:{LIGHT}}}
.gov-table .rl{{font-weight:700;color:{SLATE};background:#EFF5FA;min-width:130px}}
.phase-table{{width:100%;border-collapse:collapse;font-size:11px;margin:10px 0}}
.phase-table th{{background:{SLATE};color:white;padding:6px 8px;text-align:left;
  font-size:10px;font-weight:700;text-transform:uppercase}}
.phase-table td{{padding:6px 8px;border-bottom:.5px solid {BORDER};vertical-align:top;line-height:1.4}}
.phase-table tr:nth-child(even) td{{background:{LIGHT}}}
.ph-name{{font-weight:700;color:{NAVY}}}
.t-badge{{background:#FDEFD5;color:{NAVY};border-radius:3px;padding:1px 6px;
  font-size:10px;white-space:nowrap;display:inline-block}}
.sla-table{{width:100%;border-collapse:collapse;font-size:11px;margin:10px 0}}
.sla-table th{{background:{NAVY};color:white;padding:6px 10px;text-align:left;font-size:10px;font-weight:700}}
.sla-table td{{padding:6px 10px;border-bottom:.5px solid {BORDER};vertical-align:top;line-height:1.4}}
.sla-table tr:nth-child(even) td{{background:{LIGHT}}}
.sev-h{{color:{RED};font-weight:700}} .sev-m{{color:#8a6000;font-weight:700}} .sev-l{{color:{GREEN};font-weight:700}}
.contact-table{{width:100%;border-collapse:collapse;font-size:11px;margin:10px 0}}
.contact-table th{{background:{SLATE};color:white;padding:6px 10px;font-size:10px;font-weight:700;text-align:left}}
.contact-table td{{padding:6px 10px;border-bottom:.5px solid {BORDER};vertical-align:top;line-height:1.4}}
.contact-table tr:nth-child(even) td{{background:{LIGHT}}}
.def-table{{width:100%;border-collapse:collapse;font-size:11.5px;margin:10px 0}}
.def-table th{{background:{SLATE};color:white;padding:6px 10px;text-align:left;font-size:10px;font-weight:700}}
.def-table td{{padding:7px 10px;border-bottom:.5px solid {BORDER};vertical-align:top;line-height:1.5}}
.def-table tr:nth-child(even) td{{background:{LIGHT}}}
.def-term{{font-weight:700;color:{NAVY}}}
.form-badge{{display:inline-block;background:{GOLD};color:{NAVY};font-size:9px;font-weight:700;
  padding:2px 8px;border-radius:3px;margin-bottom:6px;letter-spacing:.3px}}
.form-title{{font-size:16px;font-weight:700;color:{NAVY};margin-bottom:3px}}
.form-desc{{font-size:11.5px;color:{SLATE};line-height:1.6;margin-bottom:10px}}
.route-row{{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:14px;align-items:center}}
.route-lbl{{font-size:9px;font-weight:700;color:#8A9BB0;text-transform:uppercase;letter-spacing:.3px}}
.rr-approver{{background:#FFF8E8;border:.5px solid {GOLD};border-radius:3px;
  padding:2px 8px;font-size:10px;color:#7a5500;font-weight:700}}
.rr-notify{{background:#F0F9F5;border:.5px solid #A0D4BC;border-radius:3px;
  padding:2px 8px;font-size:10px;color:{GREEN};font-weight:700}}
.fsec-hdr{{font-size:9px;font-weight:700;color:{SLATE};text-transform:uppercase;
  letter-spacing:.5px;border-bottom:1px solid {BORDER};padding-bottom:4px;margin:14px 0 8px 0}}
.submit-toast{{background:{GREEN};color:white;border-radius:8px;padding:10px 16px;
  font-size:13px;font-weight:700;text-align:center;margin-bottom:10px}}
.mailto-btn{{display:inline-block;background:{NAVY};color:white !important;border-radius:6px;
  padding:8px 20px;font-size:12px;font-weight:700;text-decoration:none;font-family:Arial,sans-serif}}
.mailto-btn:hover{{background:{SLATE};color:white !important}}
</style>"""

SOP_SECTIONS = {
    "Governance": ["Points of Contact","Roles & Responsibilities","Definitions",
                   "Timeline & SLAs","Escalation & Issues","Access & Permissions"],
    "Metric Governance": ["Portfolio KPI Governance","Company KPI Governance","Reporting Governance"],
    "Onboarding": ["Portfolio Companies","Deal Team","Senior Management"],
    "Platform Use": ["Creating New Companies","Requesting Data","Attribute Management","Formula Management"],
    "Technology": ["PowerBI & SharePoint","IT & Platform Support"],
}
FORM_SECTIONS = {
    "Company & Data": ["01 — New Company Intake","03 — Ad Hoc Data Request","04 — Restatement Request"],
    "Metrics & Attributes": ["05 — KPI / Formula Change","06 — Attribute Change"],
    "Access & Users": ["02 — User Access Request"],
    "Platform & Tech": ["07 — IT Support Ticket","08 — Compliance Review",
                        "09 — Tech Initiative","10 — PowerBI Change"],
}

def _sh(text):
    st.markdown(f'<div class="fsec-hdr">{text}</div>', unsafe_allow_html=True)

def _fh(num, title, desc, routes):
    route_html = "".join(
        f'<span class="rr-approver">{r}</span>' if any(r.startswith(x) for x in ("Approver","Assigned","Triaged"))
        else f'<span class="rr-notify">{r}</span>'
        for r in routes)
    st.markdown(f"""<div class="form-badge">FORM {num}</div>
    <div class="form-title">{title}</div>
    <div class="form-desc">{desc}</div>
    <div class="route-row"><span class="route-lbl">Routes to:</span>{route_html}</div>""",
    unsafe_allow_html=True)

def _mailto(subject, fields):
    import urllib.parse
    lines = [f"FORM: {subject}","Submitted via TSG Consumer Portfolio Dashboard","",
             "─"*48,""]
    for sec, items in fields.items():
        lines.append(f"[ {sec.upper()} ]")
        for lbl, val in items:
            if val: lines.append(f"{lbl}: {val}")
        lines.append("")
    lines += ["─"*48,"Sent from TSG Consumer Portfolio Dashboard"]
    return (f"mailto:{RECIPIENT}?subject={urllib.parse.quote('[TSG Request] '+subject)}"
            f"&body={urllib.parse.quote(chr(10).join(lines))}")

def _done(url):
    st.markdown('<div class="submit-toast">✓ Opening your email client to complete submission.</div>', unsafe_allow_html=True)
    st.markdown(f'<a class="mailto-btn" href="{url}" target="_blank">📧 Open Email to Submit</a>', unsafe_allow_html=True)

# ─── SOP CONTENT ────────────────────────────────────────────────────────────
def _sop(page):
    st.markdown(CSS, unsafe_allow_html=True)
    if page == "Points of Contact":
        st.markdown("**Points of Contact** — Primary contacts for platform, data, and reporting.")
        st.markdown("""<table class="contact-table"><thead><tr><th>Name</th><th>Role</th><th>Team</th><th>Responsible For</th></tr></thead><tbody>
          <tr><td><strong>Michelle Phan</strong></td><td>Finance &amp; AI Lead</td><td>TSG Vantage</td><td>Platform oversight, KPI governance, reporting</td></tr>
          <tr><td><strong>Matt Rispoli</strong></td><td>Technology Lead</td><td>Vantage Finance</td><td>73Strings config, IT support, PowerBI</td></tr>
          <tr><td><strong>Jess Collazo-Young</strong></td><td>Data Operations</td><td>Offshore Team</td><td>Entity creation, data ingestion, attribute setup</td></tr>
          <tr><td><strong>Drew Weilbacher</strong></td><td>Compliance</td><td>TSG Compliance</td><td>Investor-facing material review, admin access</td></tr>
        </tbody></table><div class="info-box">For all form submissions email <strong>mphan@tsgconsumer.com</strong>. For 73Strings technical issues use Form 07.</div>""", unsafe_allow_html=True)
    elif page == "Roles & Responsibilities":
        st.markdown("**Roles & Responsibilities** — RACI matrix across all platform activities.")
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">Vantage Finance</td><td>Owns KPI governance, approves all formula/attribute changes, validates data quality, manages 73Strings config</td></tr>
          <tr><td class="rl">Deal Team</td><td>Approves new company onboarding, provides written sign-off on entity creation, owns valuation workbook</td></tr>
          <tr><td class="rl">Offshore Team</td><td>Executes entity creation, data ingestion, attribute setup, and restatements under Vantage Finance direction</td></tr>
          <tr><td class="rl">TSG Finance</td><td>Reviews portfolio KPI definitions, approves investor-facing metric changes</td></tr>
          <tr><td class="rl">TSG Compliance</td><td>Reviews and approves investor-facing materials, signs off on admin access requests</td></tr>
          <tr><td class="rl">Senior Management</td><td>Approves technology initiatives, receives reporting outputs, provides strategic direction</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Definitions":
        st.markdown("**Definitions** — Key terms used across all SOPs and forms.")
        st.markdown("""<table class="def-table"><thead><tr><th>Term</th><th>Definition</th></tr></thead><tbody>
          <tr><td class="def-term">73Strings</td><td>The primary portfolio data management platform.</td></tr>
          <tr><td class="def-term">LTM</td><td>Last Twelve Months. Rolling twelve-month period ending at the most recent reporting date.</td></tr>
          <tr><td class="def-term">Attribute</td><td>A named data field in 73Strings (e.g. "Net Revenue"). Maps to a row in the PortCo financial statements.</td></tr>
          <tr><td class="def-term">Formula / KPI</td><td>A calculated metric derived from attributes (e.g. EBITDA Margin = EBITDA / Net Revenue).</td></tr>
          <tr><td class="def-term">SOCF</td><td>Statement of Cash Flows. Cash flow attributes must be appended with "(SOCF)" in 73Strings.</td></tr>
          <tr><td class="def-term">Restatement</td><td>Correction to a previously submitted and closed reporting period.</td></tr>
          <tr><td class="def-term">PortCo</td><td>Portfolio Company — any company held in the TSG fund portfolio.</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Timeline & SLAs":
        st.markdown("**Timeline & SLAs** — Service level agreements for standard request types.")
        st.markdown("""<table class="sla-table"><thead><tr><th>Request Type</th><th>SLA</th><th>Severity</th><th>Notes</th></tr></thead><tbody>
          <tr><td>Critical platform outage</td><td>1 business day</td><td class="sev-h">Critical</td><td>Technology Lead may act immediately; retroactive sign-off</td></tr>
          <tr><td>User access (new/offboard)</td><td>1 business day</td><td class="sev-h">High</td><td>Offboard: must be actioned same day as departure</td></tr>
          <tr><td>Data error / restatement</td><td>3 business days</td><td class="sev-h">High</td><td>Requires Vantage Finance approval before action</td></tr>
          <tr><td>Ad hoc data request</td><td>3–5 business days</td><td class="sev-m">Medium</td><td>Subject to data availability and PortCo cooperation</td></tr>
          <tr><td>Attribute / KPI change</td><td>5 business days</td><td class="sev-m">Medium</td><td>Dual approval required before implementation</td></tr>
          <tr><td>New company onboarding</td><td>10–14 business days</td><td class="sev-l">Standard</td><td>Depends on completeness of intake form</td></tr>
          <tr><td>Technology initiative</td><td>Review within 10 days</td><td class="sev-l">Low</td><td>Roadmap inclusion at Executive Sponsor discretion</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Escalation & Issues":
        st.markdown("**Escalation & Issues** — How to escalate issues not resolved within SLA.")
        st.markdown("""<ul class="step-list">
          <li><div class="sn">1</div><div><strong>Log the issue</strong> — Submit Form 07 or email mphan@tsgconsumer.com with title, description, and severity.</div></li>
          <li><div class="sn">2</div><div><strong>Initial triage (24h)</strong> — Technology Lead (Matt Rispoli) reviews and assigns priority. Critical issues actioned immediately.</div></li>
          <li><div class="sn">3</div><div><strong>Vendor escalation</strong> — If 73Strings vendor involvement needed, Technology Lead coordinates with 73S Helpdesk.</div></li>
          <li><div class="sn">4</div><div><strong>Executive escalation</strong> — Unresolved after 3 days or business-blocking: escalate to Michelle Phan.</div></li>
          <li><div class="sn">5</div><div><strong>Resolution documentation</strong> — All resolved issues documented with root cause in Platform Support Tracker.</div></li>
        </ul><div class="warn-box">Data integrity issues affecting investor-facing materials must be escalated to TSG Compliance regardless of severity.</div>""", unsafe_allow_html=True)
    elif page == "Access & Permissions":
        st.markdown("**Access & Permissions** — Access control framework.")
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">User Types</td><td>Admin (full config) · Active User (read + write) · PortCo User (data entry) · Read Only</td></tr>
          <tr><td class="rl">Provisioning</td><td>All access requests via Form 02. Admin access requires TSG Compliance approval.</td></tr>
          <tr><td class="rl">Offboarding SLA</td><td>Accounts inactivated within 1 business day of departure notification.</td></tr>
          <tr><td class="rl">Quarterly Review</td><td>Technology Lead audits active user list quarterly. Inactive accounts >90 days deactivated.</td></tr>
          <tr><td class="rl">PowerBI / SharePoint</td><td>Submit Form 10 for dashboard access changes.</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Portfolio KPI Governance":
        st.markdown("**Portfolio KPI Governance** — Standards for portfolio-level KPIs.")
        st.markdown('<div class="info-box">All portfolio KPIs must be defined in the KPI Change Log before implementation. Changes require TSG Finance review and Vantage Finance approval.</div>', unsafe_allow_html=True)
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">Scope</td><td>All metrics in portfolio-level dashboards, fund reports, and LP materials</td></tr>
          <tr><td class="rl">Approval</td><td>New KPI: Vantage Finance + TSG Finance · Modification: Vantage Finance · Retirement: Vantage Finance sign-off</td></tr>
          <tr><td class="rl">Documentation</td><td>KPI name, definition, formula, data source, display format, investor-facing flag — all required before implementation</td></tr>
          <tr><td class="rl">Validation</td><td>New KPIs validated against 3 historical periods before live deployment</td></tr>
          <tr><td class="rl">Change Request</td><td>Use Form 05 (KPI / Formula Change Request)</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Company KPI Governance":
        st.markdown("**Company KPI Governance** — Standards for company-specific KPIs.")
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">Scope</td><td>All company-level KPIs per portfolio company (e.g. same-store sales, subscriber count, GMV)</td></tr>
          <tr><td class="rl">Approval</td><td>Deal Team Lead must approve. Investor-facing KPIs also require TSG Compliance sign-off.</td></tr>
          <tr><td class="rl">Uniqueness</td><td>Each KPI name must be unique within the company context.</td></tr>
          <tr><td class="rl">Change Request</td><td>Use Form 05 (KPI / Formula Change Request)</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Reporting Governance":
        st.markdown("**Reporting Governance** — Standards for all reporting outputs.")
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">Recurring Reports</td><td>Quarterly portfolio dashboard · Monthly KPI snapshots · Annual fund performance summary</td></tr>
          <tr><td class="rl">Investor-Facing</td><td>All materials for LPs, lenders, or board members must complete Compliance Review (Form 08) before distribution</td></tr>
          <tr><td class="rl">Version Control</td><td>All reports versioned with date and period. Prior versions retained for 3 years.</td></tr>
          <tr><td class="rl">Restatements</td><td>Use Form 04. Investor-facing restatements require TSG Compliance notification.</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Portfolio Companies":
        st.markdown("**Onboarding: Portfolio Companies** — Target: 2 clean data submissions within 60 days.")
        st.markdown("""<table class="phase-table"><thead><tr><th>Phase</th><th>Timing</th><th>Key Activities</th><th>Success Criteria</th></tr></thead><tbody>
          <tr><td class="ph-name">Intake &amp; Setup</td><td><span class="t-badge">Day 0–3</span></td><td>Complete New Company Intake Form; get Deal Team written approval</td><td>Form approved; entity created in 73S</td></tr>
          <tr><td class="ph-name">Kickoff</td><td><span class="t-badge">Day 3–7</span></td><td>Schedule kickoff with PortCo Finance contact; introduce platform</td><td>Kickoff completed; PortCo understands process</td></tr>
          <tr><td class="ph-name">Template Build</td><td><span class="t-badge">Day 7–14</span></td><td>Create attributes and financial template in 73S; map to chart of accounts</td><td>Template validated and ready</td></tr>
          <tr><td class="ph-name">System Activation</td><td><span class="t-badge">Day 14–21</span></td><td>Send first automated data request; confirm PortCo receipt</td><td>First request delivered successfully</td></tr>
          <tr><td class="ph-name">First Submission</td><td><span class="t-badge">Day 21–30</span></td><td>Receive data; validate; resolve discrepancies</td><td>Clean dataset; no critical errors</td></tr>
          <tr><td class="ph-name">Stabilization</td><td><span class="t-badge">Day 30–60</span></td><td>Repeat cycle; monitor timeliness; reduce errors</td><td>2nd successful submission</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Deal Team":
        st.markdown("**Onboarding: Deal Team** — Target: complete within 14 days.")
        st.markdown("""<table class="phase-table"><thead><tr><th>Phase</th><th>Timing</th><th>Key Activities</th><th>Success Criteria</th></tr></thead><tbody>
          <tr><td class="ph-name">Access &amp; Setup</td><td><span class="t-badge">Day 0–2</span></td><td>Grant access to reporting tool, Excel plug-in, PowerBI, shared drives</td><td>User can log into all systems</td></tr>
          <tr><td class="ph-name">Tool Orientation</td><td><span class="t-badge">Day 1–5</span></td><td>Walkthrough of platform navigation; where data lives</td><td>User understands where to find key data</td></tr>
          <tr><td class="ph-name">Excel Plug-in Training</td><td><span class="t-badge">Day 3–7</span></td><td>Install and train on Excel plug-in (data pulls, refreshes, templates)</td><td>User can independently pull and refresh data</td></tr>
          <tr><td class="ph-name">Valuation Workflow</td><td><span class="t-badge">Day 7–14</span></td><td>Train on updating valuation workbook using Excel plug-in</td><td>User can update valuation file with live data</td></tr>
          <tr><td class="ph-name">Certification</td><td><span class="t-badge">Day 10–14</span></td><td>Complete test case: update valuation + generate report + validate outputs</td><td>User demonstrates full workflow competency</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Senior Management":
        st.markdown("**Onboarding: Senior Management** — Focused onboarding for MDs and Operating Partners. Target: 10 days.")
        st.markdown("""<table class="phase-table"><thead><tr><th>Phase</th><th>Timing</th><th>Key Activities</th><th>Success Criteria</th></tr></thead><tbody>
          <tr><td class="ph-name">Access &amp; Setup</td><td><span class="t-badge">Day 0–2</span></td><td>Provide access to PowerBI dashboards and key reporting materials</td><td>User can access all dashboards</td></tr>
          <tr><td class="ph-name">Reporting Overview</td><td><span class="t-badge">Day 1–5</span></td><td>Walkthrough of portfolio dashboards, KPIs, standard views</td><td>User knows what standard reporting exists</td></tr>
          <tr><td class="ph-name">KPI Framing</td><td><span class="t-badge">Day 1–5</span></td><td>High-level overview of key KPIs: definitions, what matters, trends</td><td>User understands core metrics</td></tr>
          <tr><td class="ph-name">Dashboard Navigation</td><td><span class="t-badge">Day 3–7</span></td><td>Focused walkthrough: filters, slicing, drilling into PortCos, exporting</td><td>User can navigate and extract insights</td></tr>
          <tr><td class="ph-name">Decision Use Cases</td><td><span class="t-badge">Day 7–10</span></td><td>Apply reporting to real scenarios: IC prep, board materials, performance reviews</td><td>User can leverage reporting in decisions</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "Creating New Companies":
        st.markdown("**Creating New Companies** — Admin access only: 73S Monitor > Briefcase Button.")
        st.markdown("""<ul class="step-list">
          <li><div class="sn">1</div><div><strong>Receive New Company Form</strong> — Get Deal Team written approval. Save form. Log into 73Strings.</div></li>
          <li><div class="sn">2</div><div><strong>Click "Create Entity"</strong> — Panel appears on the right.</div></li>
          <li><div class="sn">3</div><div><strong>Define Entity Details</strong> — Entity Type: External · Layer: Portfolio Company · Name, Sector, Currency (USD), Fiscal Year End, Investment Date, Website.</div></li>
          <li><div class="sn">4</div><div><strong>Define Company Profile</strong> — Overview &gt; Profile.</div></li>
          <li><div class="sn">5</div><div><strong>Add Company Contacts</strong> — My Portfolio &gt; PortCo &gt; Overview &gt; Contacts.</div></li>
          <li><div class="sn">6</div><div><strong>Add Company Attributes</strong> — Settings &gt; Bulk Upload &gt; Attributes Template. Append "(SOCF)" to cash flow labels.</div></li>
          <li><div class="sn">7</div><div><strong>Create Template</strong> — My Portfolio &gt; PortCo &gt; Overview &gt; Template.</div></li>
          <li><div class="sn">8</div><div><strong>Import Financials</strong> — My Portfolio &gt; PortCo &gt; Data Import. Highlight data, click extract, map attributes 1:1, click submit.</div></li>
        </ul><div class="warn-box">Do not begin entity creation if the intake form has missing required fields.</div>""", unsafe_allow_html=True)
    elif page == "Requesting Data":
        st.markdown("**Requesting Data** — Standard process for ad hoc data requests.")
        st.markdown("""<ul class="step-list">
          <li><div class="sn">1</div><div><strong>Submit Form 03</strong> with Deal Team approval and business justification.</div></li>
          <li><div class="sn">2</div><div><strong>Offshore Team prepares request</strong> — Standard template with period, data version, and format requirements.</div></li>
          <li><div class="sn">3</div><div><strong>PortCo submits data</strong> — Via 73Strings data portal or secure email.</div></li>
          <li><div class="sn">4</div><div><strong>Validation</strong> — Offshore Team validates against prior periods and flags anomalies.</div></li>
          <li><div class="sn">5</div><div><strong>Ingestion</strong> — Validated data imported into 73Strings and KPIs updated.</div></li>
        </ul><div class="info-box">SLA: 3–5 business days from request submission.</div>""", unsafe_allow_html=True)
    elif page == "Attribute Management":
        st.markdown("**Attribute Management** — Adding, renaming, or retiring attributes. Dual approval required.")
        st.markdown("""<ul class="step-list">
          <li><div class="sn">1</div><div><strong>Submit Form 06</strong> with change type, attribute details, and reason.</div></li>
          <li><div class="sn">2</div><div><strong>Dual Approval</strong> — Deal Team Lead and Vantage Finance must both approve before any change.</div></li>
          <li><div class="sn">3</div><div><strong>Implement Change</strong> — Offshore Team executes in 73Strings: Settings &gt; Attributes.</div></li>
          <li><div class="sn">4</div><div><strong>Historical Data</strong> — If renaming, confirm historical data maps correctly.</div></li>
          <li><div class="sn">5</div><div><strong>Log Change</strong> — Document in Attribute Change Log with date, approver, and description.</div></li>
        </ul>""", unsafe_allow_html=True)
    elif page == "Formula Management":
        st.markdown("**Formula Management** — Creating and updating calculated formulas (KPIs).")
        st.markdown("""<ul class="step-list">
          <li><div class="sn">1</div><div><strong>Submit Form 05</strong> with full formula definition and data sources.</div></li>
          <li><div class="sn">2</div><div><strong>Approval</strong> — Vantage Finance approves; TSG Finance reviews investor-facing formulas.</div></li>
          <li><div class="sn">3</div><div><strong>Build in 73Strings</strong> — Settings &gt; Formulas. Use exact attribute names. Add description and display format.</div></li>
          <li><div class="sn">4</div><div><strong>Validate Against History</strong> — Run formula for 3 prior periods. Compare to known correct values.</div></li>
          <li><div class="sn">5</div><div><strong>Deploy</strong> — Once validated, mark as active. Log in KPI Change Log.</div></li>
        </ul><div class="warn-box">Never modify a live formula during reporting periods.</div>""", unsafe_allow_html=True)
    elif page == "PowerBI & SharePoint":
        st.markdown("**PowerBI & SharePoint** — Governance for dashboard changes and SharePoint access.")
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">Change Requests</td><td>All dashboard changes submitted via Form 10. Approved by Michelle Phan; assigned to Matt Rispoli.</td></tr>
          <tr><td class="rl">SharePoint Access</td><td>New or modified SharePoint access submitted via Form 10. IT (Halcyon) notified for provisioning.</td></tr>
          <tr><td class="rl">Investor-Facing Reports</td><td>Any PowerBI report for LP or lender distribution requires Compliance Review (Form 08).</td></tr>
          <tr><td class="rl">Scheduled Refresh</td><td>Dashboards refresh automatically after 73Strings data ingestion cycle.</td></tr>
        </tbody></table>""", unsafe_allow_html=True)
    elif page == "IT & Platform Support":
        st.markdown("**IT & Platform Support** — Reporting 73Strings technical issues.")
        st.markdown("""<table class="gov-table"><thead><tr><th></th><th>Details</th></tr></thead><tbody>
          <tr><td class="rl">How to Submit</td><td>Use Form 07. Include issue type, severity, description, and screenshots.</td></tr>
          <tr><td class="rl">Triage</td><td>Technology Lead (Matt Rispoli) reviews within 1 business day. Critical issues actioned immediately.</td></tr>
          <tr><td class="rl">Vendor Escalation</td><td>Issues requiring 73Strings vendor involvement coordinated by Technology Lead per SLA terms.</td></tr>
          <tr><td class="rl">Resolution Tracking</td><td>All issues logged with root cause and resolution summary.</td></tr>
        </tbody></table>""", unsafe_allow_html=True)

# ─── FORM RENDERERS ──────────────────────────────────────────────────────────
def _form(key):
    st.markdown(CSS, unsafe_allow_html=True)

    if key == "01 — New Company Intake":
        _fh("01","New Company Intake Form",
            "Complete when onboarding a new portfolio company. Deal Team lead must provide written approval first.",
            ["Approver: Deal Team Lead","Approver: Vantage Finance",
             "Notified: Jess Collazo-Young","Assigned: Offshore Team"])
        with st.form("f01"):
            _sh("Company Identity")
            c1,c2=st.columns(2); legal=c1.text_input("Legal Entity Name *"); dba=c2.text_input("DBA / Trading Name")
            c3,c4,c5=st.columns(3)
            fund=c3.selectbox("Fund *",["","TSG7","TSG8","TSG9"])
            sector=c4.selectbox("Sector *",["","Beauty & Personal Care","Household","Health & Wellness","Education","Restaurant","Consumer Tech"])
            geo=c5.selectbox("Geography *",["","United States","Canada","United Kingdom","Other"])
            _sh("Investment Details")
            c6,c7,c8=st.columns(3)
            inv_date=c6.date_input("Investment Date *",value=None)
            fy=c7.selectbox("Fiscal Year End *",["","January","February","March","April","May","June","July","August","September","October","November","December"])
            freq=c8.selectbox("Reporting Frequency *",["","Monthly","Quarterly"])
            c9,c10=st.columns(2); own=c9.text_input("TSG Ownership % *"); sec=c10.selectbox("Security Type *",["","Preferred Equity","Common Equity","Structured","Minority","Control"])
            _sh("Contacts")
            c11,c12=st.columns(2); pcn=c11.text_input("PortCo Finance Contact Name *"); pce=c12.text_input("PortCo Finance Contact Email *")
            c13,c14=st.columns(2); dta=c13.text_input("Deal Team Associate *"); dtv=c14.text_input("Deal Team VP *")
            _sh("Financial Statements")
            st.write("**Statements to Collect***")
            sc1,sc2,sc3,sc4,sc5,sc6=st.columns(6)
            is_=sc1.checkbox("Income Stmt",value=True); bs=sc2.checkbox("Balance Sheet",value=True); cf=sc3.checkbox("Cash Flow (SOCF)",value=True)
            ks=sc4.checkbox("KPI Supplement"); bud=sc5.checkbox("Budget/Forecast"); eb=sc6.checkbox("EBITDA Bridge")
            st.write("**Data Complexities**")
            dc1,dc2,dc3,dc4=st.columns(4)
            ms=dc1.checkbox("Multi-subsidiary"); mc=dc2.checkbox("Multi-currency"); ns=dc3.checkbox("Non-standard fiscal"); nc=dc4.checkbox("None")
            _sh("Deal Team Approval")
            c15,c16=st.columns(2); dtl=c15.text_input("Approving Deal Team Lead Name *"); dle=c16.text_input("Approving Deal Team Lead Email *")
            conf=st.checkbox("I confirm this form is complete and accurate")
            if st.form_submit_button("Submit & Notify Team",type="primary"):
                stmts=", ".join(filter(None,["Income Statement" if is_ else "","Balance Sheet" if bs else "","Cash Flow (SOCF)" if cf else "","KPI Supplement" if ks else "","Budget/Forecast" if bud else "","EBITDA Bridge" if eb else ""]))
                compl=", ".join(filter(None,["Multi-subsidiary" if ms else "","Multi-currency" if mc else "","Non-standard fiscal" if ns else "","None" if nc else ""]))
                _done(_mailto("New Company Intake Form",{"Company Identity":[("Legal Name",legal),("DBA",dba),("Fund",fund),("Sector",sector),("Geography",geo)],"Investment Details":[("Investment Date",str(inv_date) if inv_date else ""),("FY End",fy),("Frequency",freq),("Ownership %",own),("Security Type",sec)],"Contacts":[("PortCo Contact",pcn),("PortCo Email",pce),("DT Associate",dta),("DT VP",dtv)],"Financials":[("Statements",stmts),("Complexities",compl)],"Approval":[("Lead Name",dtl),("Lead Email",dle),("Confirmed","Yes" if conf else "No")]}))

    elif key == "02 — User Access Request":
        _fh("02","User Access Request",
            "New user setup, role changes, or offboarding. Admin access routed to TSG Compliance.",
            ["Approver: Vantage Finance","Assigned: Offshore Team"])
        with st.form("f02"):
            _sh("Request Type & User Details")
            rtype=st.selectbox("Request Type *",["","New User","Role Change","Offboard / Inactivate","Add PortCo User"])
            c1,c2=st.columns(2); un=c1.text_input("User Full Name *"); ue=c2.text_input("User Email *")
            c3,c4=st.columns(2); ut=c3.text_input("User's Team / Company"); utit=c4.text_input("User's Title / Role")
            utype=""; ulevel=""; ucos=""
            cur_a=""; new_a=""; rch=""
            lday=None; dea=False
            if rtype in ("New User","Add PortCo User"):
                _sh("Access Configuration")
                c5,c6=st.columns(2)
                utype=c5.selectbox("User Type *",["","Admin","Active User","PortCo User"])
                ulevel=c6.selectbox("Access Level *",["","Read only","Read + Write","Admin"])
                if utype=="Admin": st.warning("Admin access requires TSG Compliance (Drew Weilbacher) review before setup proceeds.")
                ucos=st.text_input("Companies to Grant Access",placeholder="List company names, or 'All portfolio'")
            elif rtype=="Role Change":
                _sh("Role Change Details")
                cur_a=st.text_input("Current Access"); new_a=st.text_input("Requested New Access *"); rch=st.text_area("Reason for Change *")
            elif rtype=="Offboard / Inactivate":
                _sh("Offboarding Details")
                st.warning("SLA: User must be inactivated within 1 business day of departure notification.")
                lday=st.date_input("Last Day of Access *",value=None); dea=st.checkbox("I confirm this user should be deactivated")
            _sh("Requested By")
            c7,c8=st.columns(2); rn=c7.text_input("Requestor Name *"); re=c8.text_input("Requestor Email *")
            if st.form_submit_button("Submit & Notify Team",type="primary"):
                _done(_mailto("User Access Request",{"Request":[("Type",rtype),("User",un),("Email",ue),("Team",ut),("Title",utit),("User Type",utype),("Access Level",ulevel),("Companies",ucos),("Current Access",cur_a),("New Access",new_a),("Reason",rch),("Last Day",str(lday) if lday else ""),("Deactivation Confirmed","Yes" if dea else "")],"Requested By":[("Name",rn),("Email",re)]}))

    elif key == "03 — Ad Hoc Data Request":
        _fh("03","Ad Hoc Data Request",
            "For non-recurring data requests outside the normal quarterly cycle.",
            ["Approver: Deal Team Lead","Notified: Vantage Finance","Assigned: Offshore Team"])
        with st.form("f03"):
            _sh("Request Details")
            c1,c2=st.columns(2); co=c1.text_input("Portfolio Company *"); fund=c2.selectbox("Fund *",["","TSG7","TSG8","TSG9"])
            c3,c4=st.columns(2); ver=c3.selectbox("Data Version *",["","Actual","Budget","Forecast"]); per=c4.text_input("Reporting Period *",placeholder="e.g. Q3 2024")
            st.write("**Statements Requested***")
            s1,s2,s3,s4,s5=st.columns(5)
            si=s1.checkbox("Income Stmt"); sb=s2.checkbox("Balance Sheet"); sc=s3.checkbox("Cash Flow"); sk=s4.checkbox("KPI Supplement"); sm=s5.checkbox("EBITDA Bridge")
            just=st.text_area("Business Justification *",placeholder="e.g. IC prep, lender request...")
            c5,c6=st.columns(2); due=c5.date_input("Data Needed By *",value=None); dt=c6.text_input("Deal Team Associate *")
            _sh("Requested By")
            c7,c8=st.columns(2); rn=c7.text_input("Requestor Name *"); re=c8.text_input("Requestor Email *")
            if st.form_submit_button("Submit & Notify Team",type="primary"):
                stmts=", ".join(filter(None,["Income Statement" if si else "","Balance Sheet" if sb else "","Cash Flow" if sc else "","KPI Supplement" if sk else "","EBITDA Bridge" if sm else ""]))
                _done(_mailto("Ad Hoc Data Request",{"Request":[("Company",co),("Fund",fund),("Version",ver),("Period",per),("Statements",stmts),("Justification",just),("Needed By",str(due) if due else ""),("DT Associate",dt)],"Requested By":[("Name",rn),("Email",re)]}))

    elif key == "04 — Restatement Request":
        _fh("04","Restatement Request",
            "When an error is identified in a previously submitted and closed period.",
            ["Approver: Vantage Finance","Notified: Deal Team","Assigned: Offshore Team"])
        with st.form("f04"):
            _sh("Restatement Details")
            c1,c2=st.columns(2); co=c1.text_input("Portfolio Company *"); pers=c2.text_input("Period(s) Affected *",placeholder="e.g. Q2 2024, Q3 2024")
            st.write("**Statements Affected***")
            s1,s2,s3,s4=st.columns(4)
            si=s1.checkbox("Income Stmt"); sb=s2.checkbox("Balance Sheet"); sc=s3.checkbox("Cash Flow"); sk=s4.checkbox("KPI Supplement")
            err=st.text_area("Description of Error *",placeholder="Describe what was incorrect and how it was identified...")
            c3,c4=st.columns(2)
            cause=c3.selectbox("Root Cause *",["","PortCo submitted incorrect data","Mapping error in 73Strings","Formula / calculation error","Reclassification by PortCo","Audit adjustment","Other"])
            inv=c4.selectbox("Investor-Facing? *",["","Yes — Compliance notified","No"])
            if inv=="Yes — Compliance notified": st.warning("TSG Compliance (Drew Weilbacher) will be automatically notified and must approve before corrected materials are redistributed.")
            kpis=st.text_area("KPIs / Reports Impacted *",placeholder="List all KPIs, dashboards, and reports needing re-validation...")
            _sh("Requested By")
            c5,c6=st.columns(2); rn=c5.text_input("Requestor Name *"); re=c6.text_input("Requestor Email *")
            if st.form_submit_button("Submit & Notify Team",type="primary"):
                stmts=", ".join(filter(None,["Income Statement" if si else "","Balance Sheet" if sb else "","Cash Flow" if sc else "","KPI Supplement" if sk else ""]))
                _done(_mailto("Restatement Request",{"Details":[("Company",co),("Periods Affected",pers),("Statements",stmts),("Error Description",err),("Root Cause",cause),("Investor-Facing",inv),("KPIs / Reports Impacted",kpis)],"Requested By":[("Name",rn),("Email",re)]}))

    elif key == "05 — KPI / Formula Change":
        _fh("05","KPI / Formula Change Request",
            "Add a new KPI or formula, or modify an existing one. All changes validated before going live.",
            ["Approver: Vantage Finance","Review: TSG Finance","Assigned: Offshore Team"])
        with st.form("f05"):
            _sh("Change Type")
            c1,c2=st.columns(2)
            rtype=c1.selectbox("Request Type *",["","Add new Portfolio KPI","Add new Company KPI","Add new Formula","Update existing KPI","Update existing Formula","Retire KPI / Formula"])
            kname=c2.text_input("KPI / Formula Name *",placeholder="e.g. EBITDA Margin")
            c3,c4=st.columns(2)
            applies=c3.selectbox("Applies To *",["","All portfolio companies","Specific company only","Specific fund only"])
            freq=c4.selectbox("Reporting Frequency *",["","Monthly","Quarterly","Annual","LTM rolling"])
            _sh("Definition & Logic")
            bdef=st.text_area("Business Definition *",placeholder="Plain language description of what this KPI measures...")
            calc=st.text_area("Calculation Logic / Formula *",placeholder="Exact formula and data sources, e.g. EBITDA Margin = EBITDA / Net Revenue")
            c5,c6=st.columns(2)
            inv=c5.selectbox("Investor-Facing? *",["","Yes — TSG Compliance approval required","No","Potentially — flag for review"])
            dtl=c6.text_input("Deal Team Lead Approving",placeholder="For company KPIs")
            _sh("Requested By")
            c7,c8=st.columns(2); rn=c7.text_input("Requestor Name *"); re=c8.text_input("Requestor Email *")
            if st.form_submit_button("Submit & Notify Team",type="primary"):
                _done(_mailto("KPI / Formula Change Request",{"Change Type":[("Request Type",rtype),("KPI Name",kname),("Applies To",applies),("Frequency",freq)],"Definition":[("Business Definition",bdef),("Calculation",calc),("Investor-Facing",inv),("DT Lead",dtl)],"Requested By":[("Name",rn),("Email",re)]}))

    elif key == "06 — Attribute Change":
        _fh("06","Attribute Change Request",
            "Add, edit, rename, or retire a company attribute in 73Strings. Dual approval required.",
            ["Approver: Deal Team Lead","Approver: Vantage Finance","Assigned: Offshore Team"])
        with st.form("f06"):
            _sh("Change Type & Attribute Details")
            c1,c2=st.columns(2)
            ctype=c1.selectbox("Change Type *",["","Add new attribute","Rename existing attribute","Update attribute properties","Retire attribute","Add synonym"])
            co=c2.text_input("Portfolio Company *",placeholder="Company name or 'All companies'")
            c3,c4=st.columns(2)
            cur=c3.text_input("Current Attribute Name",placeholder="For updates only")
            new=c4.text_input("New / Proposed Attribute Name *",placeholder="Must be unique")
            c5,c6,c7=st.columns(3)
            tag=c5.selectbox("Attribute Tag *",["","Income Statement","Balance Sheet","Cash Flow (SOCF)","KPI","Covenant","General Details","ESG"])
            ftype=c6.selectbox("Field Type *",["","Numerical","Text"])
            disp=c7.selectbox("Display Property",["","Currency","Percentage","Multiple","Absolute Number"])
            reason=st.text_area("Reason for Change *",placeholder="e.g. PortCo renamed this line item in Q3 2024 financials...")
            _sh("Requested By")
            c8,c9=st.columns(2); rn=c8.text_input("Requestor Name *"); re=c9.text_input("Requestor Email *")
            if st.form_submit_button("Submit & Notify Team",type="primary"):
                _done(_mailto("Attribute Change Request",{"Attribute Details":[("Change Type",ctype),("Company",co),("Current Name",cur),("New Name",new),("Tag",tag),("Field Type",ftype),("Display",disp),("Reason",reason)],"Requested By":[("Name",rn),("Email",re)]}))

    elif key == "07 — IT Support Ticket":
        _fh("07","IT & Platform Support Ticket",
            "For 73Strings technical issues, platform errors, or configuration requests.",
            ["Triaged by: Technology Lead (Vantage Finance)","Assigned: 73Strings Helpdesk"])
        with st.form("f07"):
            _sh("Issue Classification")
            c1,c2=st.columns(2)
            itype=c1.selectbox("Issue Type *",["","Platform error / bug","Data not loading / refresh failure","Access / login issue","Configuration change request","Performance issue","Other"])
            sev=c2.selectbox("Severity *",["","Critical — platform down / data loss","High — blocking work","Medium — workaround exists","Low — minor"])
            if sev=="Critical — platform down / data loss": st.warning("Critical: Technology Lead may action immediately with retroactive sign-off. SLA: 1 business day.")
            title=st.text_input("Issue Title *",placeholder="Brief descriptive title")
            desc=st.text_area("Detailed Description *",placeholder="What you were trying to do, what happened, what you expected...")
            c3,c4=st.columns(2)
            aff=c3.text_input("Affected Company",placeholder="Company name or 'All'")
            odate=c4.date_input("Date Issue First Observed",value=None)
            _sh("Submitted By")
            c5,c6=st.columns(2); yn=c5.text_input("Your Name *"); ye=c6.text_input("Your Email *")
            team=st.selectbox("Team",["","Vantage Finance","Deal Team","Offshore Team","Portfolio Company","Senior Management"])
            if st.form_submit_button("Submit Ticket",type="primary"):
                _done(_mailto("IT & Platform Support Ticket",{"Issue":[("Type",itype),("Severity",sev),("Title",title),("Description",desc),("Affected Company",aff),("Date Observed",str(odate) if odate else "")],"Submitted By":[("Name",yn),("Email",ye),("Team",team)]}))

    elif key == "08 — Compliance Review":
        _fh("08","Compliance Review Request",
            "Required before distributing any investor-facing materials or making material changes to externally shared reports.",
            ["Assigned: Drew Weilbacher (TSG Compliance)","Notified: Vantage Finance"])
        with st.form("f08"):
            _sh("Material Details")
            mname=st.text_input("Material / Report Name *",placeholder="e.g. TSG9 Portfolio Datasheet Q3 2024")
            c1,c2=st.columns(2)
            rtype=c1.selectbox("Review Type *",["","New material — first distribution","Material change to existing report","Correction / restatement","New KPI added to investor report"])
            ddate=c2.date_input("Target Distribution Date *",value=None)
            st.write("**Intended Audience***")
            a1,a2,a3,a4,a5=st.columns(5)
            lp=a1.checkbox("LP investors"); lend=a2.checkbox("Lenders"); board=a3.checkbox("Board members"); prosp=a4.checkbox("Prospective investors"); reg=a5.checkbox("Regulators")
            chg=st.text_area("Description of Changes *",placeholder="Describe what changed from the prior version...")
            vfa=st.selectbox("Has Vantage Finance approved this version? *",["","Yes","Pending"])
            _sh("Requested By")
            c3,c4=st.columns(2); rn=c3.text_input("Requestor Name *"); re=c4.text_input("Requestor Email *")
            if st.form_submit_button("Submit for Compliance Review",type="primary"):
                aud=", ".join(filter(None,["LP investors" if lp else "","Lenders" if lend else "","Board members" if board else "","Prospective investors" if prosp else "","Regulators" if reg else ""]))
                _done(_mailto("Compliance Review Request",{"Material":[("Name",mname),("Review Type",rtype),("Distribution Date",str(ddate) if ddate else ""),("Audience",aud),("Changes",chg),("VF Approved",vfa)],"Requested By":[("Name",rn),("Email",re)]}))

    elif key == "09 — Tech Initiative":
        _fh("09","Technology Initiative Intake",
            "Propose new technology or automation initiatives, system enhancements, or infrastructure upgrades.",
            ["Approver: Executive Sponsor","Notified: Technology Lead / PMO"])
        with st.form("f09"):
            _sh("Initiative Overview")
            iname=st.text_input("Initiative Name *")
            obj=st.text_area("Business Objective *",placeholder="What business problem does this solve?")
            ben=st.text_area("Expected Benefits *",placeholder="Quantify where possible: time saved, error reduction...")
            c1,c2,c3=st.columns(3)
            pri=c1.selectbox("Priority *",["","High","Medium","Low"])
            cost=c2.text_input("Estimated Cost",placeholder="e.g. $50K, TBD")
            tl=c3.text_input("Estimated Timeline",placeholder="e.g. 6–8 weeks")
            risk=st.text_area("Risk & Control Impact",placeholder="Identify data security, compliance, or operational risks...")
            _sh("Business Owner")
            c4,c5=st.columns(2); on=c4.text_input("Owner Name *"); oe=c5.text_input("Owner Email *")
            c6,c7=st.columns(2); ex=c6.text_input("Executive Sponsor"); sd=c7.date_input("Target Start Date",value=None)
            if st.form_submit_button("Submit Initiative",type="primary"):
                _done(_mailto("Technology Initiative Intake",{"Overview":[("Name",iname),("Objective",obj),("Benefits",ben),("Priority",pri),("Cost",cost),("Timeline",tl),("Risk",risk)],"Business Owner":[("Owner",on),("Email",oe),("Executive Sponsor",ex),("Start Date",str(sd) if sd else "")]}))

    elif key == "10 — PowerBI Change":
        _fh("10","PowerBI Dashboard Change Request",
            "New dashboard pages, layout changes, KPI additions, threshold changes, or SharePoint access updates.",
            ["Approver: Michelle Phan","Assigned: Matt Rispoli","Notified: IT (Halcyon) if SharePoint"])
        with st.form("f10"):
            _sh("Change Details")
            st.write("**Change Type***")
            t1,t2,t3,t4=st.columns(4)
            np_=t1.checkbox("New dashboard page"); lay=t2.checkbox("Layout / visual change"); nk=t3.checkbox("New KPI added"); thr=t4.checkbox("Threshold change")
            t5,t6,t7=st.columns(3)
            dc=t5.checkbox("Data source / refresh change"); sp=t6.checkbox("SharePoint access change"); bf=t7.checkbox("Bug fix")
            dash=st.selectbox("Affected Dashboard / Page *",["","Homepage / Portfolio Overview","Fund Snapshot","Company Detail","Credit & Debt","Consumer KPIs","Flags & Alerts","Documents","New page"])
            cdesc=st.text_area("Change Description *",placeholder="Describe exactly what needs to change — metric names, visual types, filter behavior...")
            just=st.text_area("Business Justification *",placeholder="Why is this change needed? What decision or workflow does it support?")
            _sh("Flag / Alert Threshold Changes (if applicable)")
            k1,k2,k3=st.columns(3)
            kn=k1.text_input("KPI / Metric Name",placeholder="e.g. Net Leverage")
            ct=k2.text_input("Current Threshold",placeholder="e.g. Red > 6.0x")
            nt=k3.text_input("Proposed Threshold",placeholder="e.g. Red > 5.5x")
            _sh("Priority & Requestor")
            p1,p2=st.columns(2)
            pri=p1.selectbox("Priority *",["","High — needed before next reporting cycle","Medium — next available sprint","Low — backlog"])
            nbd=p2.date_input("Needed By Date",value=None)
            r1,r2=st.columns(2); rn=r1.text_input("Requestor Name *"); re=r2.text_input("Requestor Email *")
            if st.form_submit_button("Submit Change Request",type="primary"):
                ctypes=", ".join(filter(None,["New page" if np_ else "","Layout change" if lay else "","New KPI" if nk else "","Threshold change" if thr else "","Data source change" if dc else "","SharePoint access" if sp else "","Bug fix" if bf else ""]))
                _done(_mailto("PowerBI Dashboard Change Request",{"Change Details":[("Change Types",ctypes),("Dashboard",dash),("Description",cdesc),("Justification",just)],"Threshold":[("KPI",kn),("Current",ct),("Proposed",nt)],"Priority & Requestor":[("Priority",pri),("Needed By",str(nbd) if nbd else ""),("Requestor",rn),("Email",re)]}))


# ─── MAIN ────────────────────────────────────────────────────────────────────
def page_sop():
    st.markdown(CSS, unsafe_allow_html=True)
    for k,v in [("sop_panel","SOP Reference"),("sop_page","Points of Contact"),("sop_form","01 — New Company Intake")]:
        if k not in st.session_state: st.session_state[k]=v

    # Top panel switcher
    st.markdown(f'<div style="background:{NAVY};padding:0 16px;height:44px;display:flex;align-items:center;gap:16px;margin-bottom:12px;border-radius:6px;"><span style="font-size:14px;font-weight:700;color:white;padding-right:16px;border-right:.5px solid rgba(255,255,255,.2);margin-right:8px;">TSG <span style="font-weight:400;color:{SKY}">CONSUMER</span></span></div>', unsafe_allow_html=True)

    c1,c2,_ = st.columns([2,2,8])
    if c1.button("📋 SOP Reference", type="primary" if st.session_state["sop_panel"]=="SOP Reference" else "secondary", use_container_width=True):
        st.session_state["sop_panel"]="SOP Reference"; st.rerun()
    if c2.button("📝 Request Forms  (10)", type="primary" if st.session_state["sop_panel"]=="Request Forms" else "secondary", use_container_width=True):
        st.session_state["sop_panel"]="Request Forms"; st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    nav_col, content_col = st.columns([1, 4])

    if st.session_state["sop_panel"] == "SOP Reference":
        with nav_col:
            for grp, pages in SOP_SECTIONS.items():
                st.markdown(f'<div class="sop-grp">{grp}</div>', unsafe_allow_html=True)
                for pg in pages:
                    active = st.session_state["sop_page"] == pg
                    if st.button(pg, key=f"sn_{pg}", use_container_width=True,
                                 type="primary" if active else "secondary"):
                        st.session_state["sop_page"] = pg; st.rerun()
        with content_col:
            with st.container(border=True):
                _sop(st.session_state["sop_page"])
    else:
        with nav_col:
            for grp, forms in FORM_SECTIONS.items():
                st.markdown(f'<div class="sop-grp">{grp}</div>', unsafe_allow_html=True)
                for fm in forms:
                    active = st.session_state["sop_form"] == fm
                    if st.button(fm, key=f"fn_{fm}", use_container_width=True,
                                 type="primary" if active else "secondary"):
                        st.session_state["sop_form"] = fm; st.rerun()
        with content_col:
            with st.container(border=True):
                _form(st.session_state["sop_form"])
