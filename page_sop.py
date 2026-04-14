"""
page_sop.py
===========
SOP & Trainings page with 10 request forms.
Forms match the TSG mockup design and email to mphan@tsgconsumer.com on submit.
"""

import streamlit as st
import streamlit.components.v1 as components


RECIPIENT = "mphan@tsgconsumer.com"

SOP_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,sans-serif;background:#F4F6F9;color:#071733;font-size:13px}
:root{
  --navy:#071733;--slate:#3F6680;--sky:#A8CFDE;--gold:#F3B51F;
  --green:#06865C;--red:#C0392B;--papaya:#FDEFD5;
  --bg:#F4F6F9;--bg2:#FFFFFF;--bg3:#F0F4F8;
  --border:#E0E4EA;--border2:#CBD3DE;
  --text:#071733;--text2:#3F6680;--text3:#8A9BB0;
}

/* Shell */
.shell{display:flex;flex-direction:column;min-height:100vh;background:var(--bg)}

/* Top tabs */
.topbar{background:var(--navy);display:flex;align-items:center;padding:0 16px;gap:0;height:44px}
.topbar-logo{font-size:14px;font-weight:700;color:#fff;padding-right:20px;border-right:0.5px solid rgba(255,255,255,0.15);margin-right:4px;white-space:nowrap}
.topbar-logo span{font-weight:400;color:var(--sky)}
.topbar-tabs{display:flex;height:44px}
.topbar-tab{padding:0 18px;font-size:11px;font-weight:700;color:rgba(255,255,255,0.55);cursor:pointer;border-bottom:3px solid transparent;display:flex;align-items:center;white-space:nowrap;text-transform:uppercase;letter-spacing:0.5px;transition:color 0.12s}
.topbar-tab:hover{color:#fff}
.topbar-tab.active{color:var(--gold);border-bottom-color:var(--gold)}
.topbar-badge{background:var(--gold);color:var(--navy);font-size:9px;font-weight:700;padding:1px 5px;border-radius:3px;margin-left:5px}

/* Panels */
.panel{display:none;min-height:calc(100vh - 44px)}
.panel.active{display:flex}

/* Sidebar shared */
.sidebar{width:210px;flex-shrink:0;background:#FFFFFF;border-right:0.5px solid var(--border);padding:12px 0;overflow-y:auto}
.grp-label{font-size:9px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:0.5px;padding:10px 14px 4px;margin-top:4px}
.s-tab{padding:7px 14px;font-size:11.5px;color:var(--text2);cursor:pointer;border-left:3px solid transparent;display:flex;align-items:center;justify-content:space-between;gap:6px;transition:all 0.1s;line-height:1.3}
.s-tab:hover{background:var(--bg);color:var(--text)}
.s-tab.active{background:var(--bg);color:var(--navy);border-left-color:var(--gold);font-weight:700}
.s-dot{width:6px;height:6px;border-radius:50%;background:var(--sky);flex-shrink:0}
.s-tab.active .s-dot{background:var(--gold)}
.s-num{font-size:9px;font-weight:700;background:var(--bg3);color:var(--text3);padding:1px 5px;border-radius:3px;border:0.5px solid var(--border)}
.s-tab.active .s-num{background:var(--gold);color:var(--navy);border-color:var(--gold)}

/* Content pane */
.pane{flex:1;padding:24px 28px;background:var(--bg);overflow-y:auto}
.sub-pane{display:none}.sub-pane.active{display:block}

/* SOP content */
.sop-breadcrumb{font-size:10px;color:var(--text3);margin-bottom:10px;letter-spacing:0.3px}
.sop-title{font-size:17px;font-weight:700;color:var(--navy);margin-bottom:4px}
.sop-desc{font-size:12px;color:var(--text2);line-height:1.6;margin-bottom:14px;max-width:680px}
.raci-row{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap}
.raci-pill{padding:4px 10px;border-radius:20px;font-size:10px;font-weight:700}
.rp-r{background:var(--navy);color:#fff}
.rp-a{background:var(--gold);color:var(--navy)}
.rp-c{background:var(--sky);color:var(--navy)}
.rp-i{background:var(--bg3);color:var(--slate);border:0.5px solid var(--sky)}
.info-box{background:#EFF5FA;border-left:3px solid var(--sky);border-radius:0 6px 6px 0;padding:9px 12px;font-size:11.5px;color:var(--slate);line-height:1.6;margin:10px 0}
.warn-box{background:#FFF8E8;border-left:3px solid var(--gold);border-radius:0 6px 6px 0;padding:9px 12px;font-size:11.5px;color:#7a5500;line-height:1.6;margin:10px 0}
.step-list{list-style:none;padding:0;margin:8px 0}
.step-list li{display:flex;gap:8px;padding:6px 0;border-bottom:0.5px solid var(--border);font-size:12px;line-height:1.55}
.sn{min-width:20px;height:20px;border-radius:50%;background:var(--navy);color:#fff;font-size:9px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-top:1px}
.phase-table{width:100%;border-collapse:collapse;font-size:11px;margin:12px 0}
.phase-table th{background:var(--slate);color:#fff;padding:6px 8px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.3px}
.phase-table td{padding:6px 8px;border-bottom:0.5px solid var(--border);vertical-align:top;line-height:1.4}
.phase-table tr:nth-child(even) td{background:var(--bg3)}
.ph-name{font-weight:700;color:var(--navy)}
.t-badge{background:var(--papaya);color:var(--navy);border-radius:3px;padding:1px 6px;font-size:10px;white-space:nowrap;display:inline-block}
.gov-table{width:100%;border-collapse:collapse;font-size:11.5px;margin:12px 0}
.gov-table th{background:var(--navy);color:#fff;padding:7px 10px;text-align:left;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.3px}
.gov-table td{padding:7px 10px;border-bottom:0.5px solid var(--border);vertical-align:top;line-height:1.5}
.gov-table tr:nth-child(even) td{background:var(--bg3)}
.gov-table .rl{font-weight:700;color:var(--slate);background:#EFF5FA;min-width:110px}
.def-table{width:100%;border-collapse:collapse;font-size:11.5px;margin:10px 0}
.def-table th{background:var(--slate);color:#fff;padding:6px 10px;text-align:left;font-size:10px;font-weight:700}
.def-table td{padding:7px 10px;border-bottom:0.5px solid var(--border);vertical-align:top;line-height:1.5}
.def-table tr:nth-child(even) td{background:var(--bg3)}
.def-term{font-weight:700;color:var(--navy)}
.sla-table{width:100%;border-collapse:collapse;font-size:11px;margin:10px 0}
.sla-table th{background:var(--navy);color:#fff;padding:6px 10px;text-align:left;font-size:10px;font-weight:700}
.sla-table td{padding:6px 10px;border-bottom:0.5px solid var(--border);vertical-align:top;line-height:1.4}
.sla-table tr:nth-child(even) td{background:var(--bg3)}
.contact-table{width:100%;border-collapse:collapse;font-size:11px;margin:10px 0}
.contact-table th{background:var(--slate);color:#fff;padding:6px 10px;font-size:10px;font-weight:700;text-align:left}
.contact-table td{padding:6px 10px;border-bottom:0.5px solid var(--border);vertical-align:top;line-height:1.4}
.contact-table tr:nth-child(even) td{background:var(--bg3)}
.sev-h{color:var(--red);font-weight:700}
.sev-m{color:#8a6000;font-weight:700}
.sev-l{color:var(--green);font-weight:700}
.rc-r{color:var(--green);font-weight:700}
.rc-a{color:#8a6000;font-weight:700}
.rc-c{color:var(--slate);font-weight:700}

/* Form elements */
.form-header-block{margin-bottom:18px}
.form-badge{display:inline-block;background:var(--gold);color:var(--navy);font-size:9px;font-weight:700;padding:2px 8px;border-radius:3px;margin-bottom:6px;letter-spacing:0.3px}
.form-title{font-size:16px;font-weight:700;color:var(--navy);margin-bottom:3px}
.form-desc{font-size:11.5px;color:var(--text2);line-height:1.6;margin-bottom:10px}
.route-row{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:14px;align-items:center}
.route-lbl{font-size:9px;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:0.3px}
.rr-approver{background:#FFF8E8;border:0.5px solid var(--gold);border-radius:3px;padding:2px 8px;font-size:10px;color:#7a5500;font-weight:700}
.rr-notify{background:#F0F9F5;border:0.5px solid #A0D4BC;border-radius:3px;padding:2px 8px;font-size:10px;color:var(--green);font-weight:700}
.fsec{margin-bottom:16px;background:#FFFFFF;border:0.5px solid var(--border);border-radius:8px;padding:14px 16px}
.fsec-label{font-size:9px;font-weight:700;color:var(--slate);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:10px;padding-bottom:6px;border-bottom:0.5px solid var(--border)}
.frow{display:grid;gap:10px;margin-bottom:10px}
.frow-2{grid-template-columns:1fr 1fr}
.frow-3{grid-template-columns:1fr 1fr 1fr}
.field{display:flex;flex-direction:column;gap:4px;margin-bottom:6px}
.field label{font-size:10px;font-weight:700;color:var(--text);letter-spacing:0.1px}
.field label .req{color:var(--red);margin-left:1px}
.field label .hint{font-weight:400;color:var(--text3);font-size:9px;margin-left:4px}
.field input,.field select,.field textarea{
  padding:7px 10px;border:0.5px solid var(--border2);border-radius:6px;
  font-size:12px;font-family:Arial,sans-serif;color:var(--text);
  background:#FFFFFF;outline:none;transition:border-color 0.15s,box-shadow 0.15s}
.field input:focus,.field select:focus,.field textarea:focus{
  border-color:var(--slate);box-shadow:0 0 0 2px rgba(63,102,128,0.12)}
.field textarea{resize:vertical;min-height:64px;line-height:1.5}
.chk-group{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}
.chk-item{display:flex;align-items:center;gap:5px;font-size:11.5px;cursor:pointer;color:var(--text2)}
.chk-item input{accent-color:var(--navy);width:13px;height:13px}
.file-drop{border:1.5px dashed var(--border2);border-radius:6px;padding:12px;text-align:center;font-size:11px;color:var(--text2);background:var(--bg3);cursor:pointer;margin-top:6px}
.cond-field{display:none;background:var(--bg3);border-radius:6px;padding:10px 12px;border:0.5px solid var(--border);margin-top:8px}
.cond-field.show{display:block}
.form-footer{display:flex;align-items:center;justify-content:space-between;padding-top:14px;border-top:0.5px solid var(--border);margin-top:6px}
.req-note{font-size:10px;color:var(--text3)}
.btn-submit{background:var(--navy);color:#fff;border:none;border-radius:6px;padding:8px 20px;font-size:12px;font-weight:700;cursor:pointer;font-family:Arial,sans-serif;transition:background 0.15s}
.btn-submit:hover{background:var(--slate)}
.btn-reset{background:none;border:0.5px solid var(--border2);border-radius:6px;padding:8px 14px;font-size:11.5px;color:var(--text2);cursor:pointer;font-family:Arial,sans-serif}
.toast{background:var(--green);color:#fff;border-radius:8px;padding:10px 16px;font-size:12px;font-weight:700;text-align:center;margin-bottom:14px;display:none;align-items:center;gap:8px}
.toast.show{display:flex;justify-content:center}
</style>
</head>
<body>
<div class="shell">

<!-- TOP TABS -->
<div class="topbar">
  <div class="topbar-logo">TSG <span>CONSUMER</span></div>
  <div class="topbar-tabs">
    <div class="topbar-tab active" onclick="switchPanel('sop',this)">SOP Reference</div>
    <div class="topbar-tab" onclick="switchPanel('forms',this)">Request Forms <span class="topbar-badge">10</span></div>
  </div>
</div>

<!-- ═══════════════════ PANEL A: SOP REFERENCE ═══════════════════ -->
<div class="panel active" id="panel-sop">
  <div class="sidebar">
    <div class="grp-label">Governance</div>
    <div class="s-tab active" onclick="showSub('sop','contacts',this)"><div class="s-dot"></div>Points of Contact</div>
    <div class="s-tab" onclick="showSub('sop','roles',this)"><div class="s-dot"></div>Roles &amp; Responsibilities</div>
    <div class="s-tab" onclick="showSub('sop','definitions',this)"><div class="s-dot"></div>Definitions</div>
    <div class="s-tab" onclick="showSub('sop','sla',this)"><div class="s-dot"></div>Timeline &amp; SLAs</div>
    <div class="s-tab" onclick="showSub('sop','escalation',this)"><div class="s-dot"></div>Escalation &amp; Issues</div>
    <div class="s-tab" onclick="showSub('sop','access',this)"><div class="s-dot"></div>Access &amp; Permissions</div>
    <div class="grp-label">Metric Governance</div>
    <div class="s-tab" onclick="showSub('sop','portfolio-kpi',this)"><div class="s-dot"></div>Portfolio KPI Governance</div>
    <div class="s-tab" onclick="showSub('sop','company-kpi',this)"><div class="s-dot"></div>Company KPI Governance</div>
    <div class="s-tab" onclick="showSub('sop','reporting',this)"><div class="s-dot"></div>Reporting Governance</div>
    <div class="grp-label">Onboarding</div>
    <div class="s-tab" onclick="showSub('sop','onboard-portco',this)"><div class="s-dot"></div>Portfolio Companies</div>
    <div class="s-tab" onclick="showSub('sop','onboard-deal',this)"><div class="s-dot"></div>Deal Team</div>
    <div class="s-tab" onclick="showSub('sop','onboard-mgmt',this)"><div class="s-dot"></div>Senior Management</div>
    <div class="grp-label">Platform Use</div>
    <div class="s-tab" onclick="showSub('sop','new-company',this)"><div class="s-dot"></div>Creating New Companies</div>
    <div class="s-tab" onclick="showSub('sop','request-data',this)"><div class="s-dot"></div>Requesting Data</div>
    <div class="s-tab" onclick="showSub('sop','attributes',this)"><div class="s-dot"></div>Attribute Management</div>
    <div class="s-tab" onclick="showSub('sop','formulas',this)"><div class="s-dot"></div>Formula Management</div>
    <div class="grp-label">Technology</div>
    <div class="s-tab" onclick="showSub('sop','powerbi',this)"><div class="s-dot"></div>PowerBI &amp; SharePoint</div>
    <div class="s-tab" onclick="showSub('sop','it-support',this)"><div class="s-dot"></div>IT &amp; Platform Support</div>
  </div>
  <div class="pane">
    <div id="sop-contacts" class="sub-pane active">
      <div class="sop-breadcrumb">Governance</div>
      <div class="sop-title">Points of Contact</div>
      <div class="sop-desc">Primary contacts for platform, data, and reporting queries. For urgent issues outside business hours, escalate to the Technology Lead.</div>
      <table class="contact-table">
        <thead><tr><th>Name</th><th>Role</th><th>Team</th><th>Responsible For</th></tr></thead>
        <tbody>
          <tr><td><strong>Michelle Phan</strong></td><td>Finance &amp; AI Lead</td><td>TSG Vantage</td><td>Platform oversight, KPI governance, reporting</td></tr>
          <tr><td><strong>Matt Rispoli</strong></td><td>Technology Lead</td><td>Vantage Finance</td><td>73Strings config, IT support, PowerBI</td></tr>
          <tr><td><strong>Jess Collazo-Young</strong></td><td>Data Operations</td><td>Offshore Team</td><td>Entity creation, data ingestion, attribute setup</td></tr>
          <tr><td><strong>Drew Weilbacher</strong></td><td>Compliance</td><td>TSG Compliance</td><td>Investor-facing material review, admin access</td></tr>
        </tbody>
      </table>
      <div class="info-box">For all form submissions and change requests, email <strong>mphan@tsgconsumer.com</strong>. For 73Strings technical issues, use the IT Support form (Form 07).</div>
    </div>
    <div id="sop-roles" class="sub-pane">
      <div class="sop-breadcrumb">Governance</div>
      <div class="sop-title">Roles &amp; Responsibilities</div>
      <div class="sop-desc">RACI matrix defining accountability across all platform activities.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">Vantage Finance</td><td>Owns KPI governance, approves all formula/attribute changes, validates data quality, manages 73Strings configuration</td></tr>
          <tr><td class="rl">Deal Team</td><td>Approves new company onboarding, provides written sign-off on entity creation, owns valuation workbook</td></tr>
          <tr><td class="rl">Offshore Team</td><td>Executes entity creation, data ingestion, attribute setup, and restatements under Vantage Finance direction</td></tr>
          <tr><td class="rl">TSG Finance</td><td>Reviews portfolio KPI definitions, approves investor-facing metric changes</td></tr>
          <tr><td class="rl">TSG Compliance</td><td>Reviews and approves investor-facing materials, signs off on admin access requests</td></tr>
          <tr><td class="rl">Senior Management</td><td>Approves technology initiatives, receives reporting outputs, provides strategic direction</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-definitions" class="sub-pane">
      <div class="sop-breadcrumb">Governance</div>
      <div class="sop-title">Definitions</div>
      <div class="sop-desc">Key terms used across all SOPs and forms.</div>
      <table class="def-table">
        <thead><tr><th>Term</th><th>Definition</th></tr></thead>
        <tbody>
          <tr><td class="def-term">73Strings</td><td>The primary portfolio data management platform. All financial data, KPIs, and attributes are stored and managed here.</td></tr>
          <tr><td class="def-term">LTM</td><td>Last Twelve Months. Rolling twelve-month period ending at the most recent reporting date.</td></tr>
          <tr><td class="def-term">Attribute</td><td>A named data field in 73Strings (e.g. "Net Revenue", "Gross Profit"). Maps to a row in the PortCo financial statements.</td></tr>
          <tr><td class="def-term">Formula / KPI</td><td>A calculated metric derived from one or more attributes (e.g. EBITDA Margin = EBITDA / Net Revenue).</td></tr>
          <tr><td class="def-term">SOCF</td><td>Statement of Cash Flows. Cash flow attributes must be appended with "(SOCF)" in 73Strings.</td></tr>
          <tr><td class="def-term">Restatement</td><td>Correction to a previously submitted and closed reporting period. Requires Vantage Finance approval.</td></tr>
          <tr><td class="def-term">PortCo</td><td>Portfolio Company — any company held in the TSG fund portfolio.</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-sla" class="sub-pane">
      <div class="sop-breadcrumb">Governance</div>
      <div class="sop-title">Timeline &amp; SLAs</div>
      <div class="sop-desc">Service level agreements for standard request types.</div>
      <table class="sla-table">
        <thead><tr><th>Request Type</th><th>SLA</th><th>Severity</th><th>Notes</th></tr></thead>
        <tbody>
          <tr><td>Critical platform outage</td><td>1 business day</td><td class="sev-h">Critical</td><td>Technology Lead may act immediately; retroactive sign-off</td></tr>
          <tr><td>User access (new/offboard)</td><td>1 business day</td><td class="sev-h">High</td><td>Offboard: must be actioned same day as departure</td></tr>
          <tr><td>Data error / restatement</td><td>3 business days</td><td class="sev-h">High</td><td>Requires Vantage Finance approval before action</td></tr>
          <tr><td>Ad hoc data request</td><td>3–5 business days</td><td class="sev-m">Medium</td><td>Subject to data availability and PortCo cooperation</td></tr>
          <tr><td>Attribute / KPI change</td><td>5 business days</td><td class="sev-m">Medium</td><td>Dual approval required before implementation</td></tr>
          <tr><td>New company onboarding</td><td>10–14 business days</td><td class="sev-l">Standard</td><td>Depends on completeness of intake form</td></tr>
          <tr><td>Technology initiative</td><td>Review within 10 days</td><td class="sev-l">Low</td><td>Roadmap inclusion at Executive Sponsor discretion</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-escalation" class="sub-pane">
      <div class="sop-breadcrumb">Governance</div>
      <div class="sop-title">Escalation &amp; Issues</div>
      <div class="sop-desc">How to escalate issues that are not resolved within SLA or require executive attention.</div>
      <ul class="step-list">
        <li><div class="sn">1</div><div><strong>Log the issue</strong> — Submit an IT Support Ticket (Form 07) or email mphan@tsgconsumer.com with the issue title, description, and severity.</div></li>
        <li><div class="sn">2</div><div><strong>Initial triage (24h)</strong> — Technology Lead (Matt Rispoli) reviews and assigns priority. Critical issues actioned immediately.</div></li>
        <li><div class="sn">3</div><div><strong>Vendor escalation</strong> — If issue requires 73Strings vendor involvement, Technology Lead coordinates with the 73S Helpdesk per SLA terms.</div></li>
        <li><div class="sn">4</div><div><strong>Executive escalation</strong> — If unresolved after 3 business days or if the issue is business-blocking, escalate to Michelle Phan who will involve Executive Sponsor as needed.</div></li>
        <li><div class="sn">5</div><div><strong>Resolution documentation</strong> — All resolved issues documented with root cause and resolution summary in the Platform Support Tracker.</div></li>
      </ul>
      <div class="warn-box">Data integrity issues affecting investor-facing materials must be escalated to TSG Compliance (Drew Weilbacher) regardless of severity level.</div>
    </div>
    <div id="sop-access" class="sub-pane">
      <div class="sop-breadcrumb">Governance</div>
      <div class="sop-title">Access &amp; Permissions</div>
      <div class="sop-desc">Access control framework for the 73Strings platform and associated reporting tools.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">User Types</td><td>Admin (full config access) · Active User (read + write) · PortCo User (data entry only) · Read Only</td></tr>
          <tr><td class="rl">Provisioning</td><td>All access requests submitted via Form 02. Admin access requires TSG Compliance approval.</td></tr>
          <tr><td class="rl">Offboarding SLA</td><td>Accounts must be inactivated within 1 business day of departure notification.</td></tr>
          <tr><td class="rl">Quarterly Review</td><td>Technology Lead audits active user list quarterly. Inactive accounts &gt;90 days are deactivated.</td></tr>
          <tr><td class="rl">PowerBI / SharePoint</td><td>Managed separately via IT. Submit Form 10 for dashboard access changes.</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-portfolio-kpi" class="sub-pane">
      <div class="sop-breadcrumb">Metric Governance</div>
      <div class="sop-title">Portfolio KPI Governance</div>
      <div class="sop-desc">Standards for portfolio-level KPIs used in fund reporting and investor materials.</div>
      <div class="info-box">All portfolio KPIs must be defined in the KPI Change Log before implementation. Changes require TSG Finance review and Vantage Finance approval.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">Scope</td><td>All metrics displayed in portfolio-level dashboards, fund reports, and LP materials</td></tr>
          <tr><td class="rl">Approval</td><td>New KPI: Vantage Finance + TSG Finance approval · Modification: Vantage Finance approval · Retirement: Vantage Finance sign-off</td></tr>
          <tr><td class="rl">Documentation</td><td>KPI name, business definition, formula, data source, display format, and investor-facing flag — all required before implementation</td></tr>
          <tr><td class="rl">Validation</td><td>New KPIs validated against 3 historical periods before live deployment. Results reviewed by Vantage Finance.</td></tr>
          <tr><td class="rl">Change Request</td><td>Use Form 05 (KPI / Formula Change Request)</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-company-kpi" class="sub-pane">
      <div class="sop-breadcrumb">Metric Governance</div>
      <div class="sop-title">Company KPI Governance</div>
      <div class="sop-desc">Standards for company-specific KPIs that supplement standard financials.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">Scope</td><td>All company-level KPIs defined per portfolio company (e.g. same-store sales, subscriber count, GMV)</td></tr>
          <tr><td class="rl">Approval</td><td>Deal Team Lead must approve company KPIs before implementation. Investor-facing KPIs also require TSG Compliance sign-off.</td></tr>
          <tr><td class="rl">Uniqueness</td><td>Each KPI name must be unique within the company context. Cross-company KPIs use standardized naming.</td></tr>
          <tr><td class="rl">Change Request</td><td>Use Form 05 (KPI / Formula Change Request)</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-reporting" class="sub-pane">
      <div class="sop-breadcrumb">Metric Governance</div>
      <div class="sop-title">Reporting Governance</div>
      <div class="sop-desc">Standards for all recurring and ad hoc reporting outputs.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">Recurring Reports</td><td>Quarterly portfolio dashboard · Monthly KPI snapshots · Annual fund performance summary</td></tr>
          <tr><td class="rl">Investor-Facing</td><td>All materials distributed to LPs, lenders, or board members must complete Compliance Review (Form 08) before distribution</td></tr>
          <tr><td class="rl">Version Control</td><td>All reports versioned with date and period. Prior versions retained for 3 years.</td></tr>
          <tr><td class="rl">Restatements</td><td>Use Form 04. Investor-facing restatements require TSG Compliance notification.</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-onboard-portco" class="sub-pane">
      <div class="sop-breadcrumb">Onboarding</div>
      <div class="sop-title">Onboarding: Portfolio Companies</div>
      <div class="sop-desc">End-to-end onboarding process for new portfolio companies. Target: 2 clean data submissions within 60 days.</div>
      <div class="raci-row">
        <span class="raci-pill rp-r">R: Offshore Team; Vantage Finance</span>
        <span class="raci-pill rp-a">A: Vantage Finance</span>
        <span class="raci-pill rp-c">C: Deal Team; TSG Finance</span>
        <span class="raci-pill rp-i">I: Senior Management</span>
      </div>
      <table class="phase-table">
        <thead><tr><th>Phase</th><th>Timing</th><th>Key Activities</th><th>RACI</th><th>Success Criteria</th></tr></thead>
        <tbody>
          <tr><td class="ph-name">Phase 1: Intake &amp; Setup</td><td><span class="t-badge">Day 0–3</span></td><td>Complete New Company Intake Form; get Deal Team written approval</td><td class="rc-r">R: VF</td><td>Form approved; entity created in 73S</td></tr>
          <tr><td class="ph-name">Phase 2: Kickoff</td><td><span class="t-badge">Day 3–7</span></td><td>Schedule kickoff with PortCo Finance contact; introduce platform and submission template</td><td class="rc-r">R: VF</td><td>Kickoff completed; PortCo understands process</td></tr>
          <tr><td class="ph-name">Phase 3: Template Build</td><td><span class="t-badge">Day 7–14</span></td><td>Create attributes and financial template in 73S; map to PortCo chart of accounts</td><td class="rc-r">R: Offshore</td><td>Template validated and ready</td></tr>
          <tr><td class="ph-name">Phase 4: System Activation</td><td><span class="t-badge">Day 14–21</span></td><td>Send first automated data request; confirm PortCo receipt</td><td class="rc-a">A: VF</td><td>First request delivered successfully</td></tr>
          <tr><td class="ph-name">Phase 5: First Submission</td><td><span class="t-badge">Day 21–30</span></td><td>Receive data; validate; resolve discrepancies</td><td class="rc-r">R: Offshore</td><td>Clean dataset; no critical errors</td></tr>
          <tr><td class="ph-name">Phase 6: Stabilization</td><td><span class="t-badge">Day 30–60</span></td><td>Repeat cycle; monitor timeliness; reduce errors</td><td class="rc-r">R: Offshore</td><td>2nd successful submission</td></tr>
          <tr><td class="ph-name">Phase 7: Complete</td><td><span class="t-badge">~Day 60</span></td><td>Confirm independence; documentation complete; BAU</td><td class="rc-a">A: VF</td><td>2 clean cycles; full handoff</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-onboard-deal" class="sub-pane">
      <div class="sop-breadcrumb">Onboarding</div>
      <div class="sop-title">Onboarding: Deal Team</div>
      <div class="sop-desc">Full deal team onboarding including system access, Excel plug-in training, valuation workflow, and certification. Target: complete within 14 days.</div>
      <div class="raci-row">
        <span class="raci-pill rp-r">R: Vantage Finance; Deal Team</span>
        <span class="raci-pill rp-a">A: Vantage Finance</span>
        <span class="raci-pill rp-c">C: TSG Finance</span>
        <span class="raci-pill rp-i">I: Senior Management</span>
      </div>
      <table class="phase-table">
        <thead><tr><th>Phase</th><th>Timing</th><th>Key Activities</th><th>Success Criteria</th></tr></thead>
        <tbody>
          <tr><td class="ph-name">Phase 0: Access &amp; Setup</td><td><span class="t-badge">Day 0–2</span></td><td>Grant access to reporting tool, Excel plug-in, PowerBI, shared drives</td><td>User can log into all systems</td></tr>
          <tr><td class="ph-name">Phase 1: Tool Orientation</td><td><span class="t-badge">Day 1–5</span></td><td>Walkthrough of platform navigation; where data lives; source docs</td><td>User understands where to find key data</td></tr>
          <tr><td class="ph-name">Phase 2: Excel Plug-in Training</td><td><span class="t-badge">Day 3–7</span></td><td>Install and train on Excel plug-in (data pulls, refreshes, templates)</td><td>User can independently pull and refresh data</td></tr>
          <tr><td class="ph-name">Phase 3: Valuation Workflow</td><td><span class="t-badge">Day 7–14</span></td><td>Train on updating valuation workbook using Excel plug-in</td><td>User can update valuation file with live data</td></tr>
          <tr><td class="ph-name">Phase 4: PowerBI Reporting</td><td><span class="t-badge">Day 7–14</span></td><td>Train on accessing dashboards, filtering, exporting, interpreting metrics</td><td>User can navigate and extract insights from PowerBI</td></tr>
          <tr><td class="ph-name">Phase 5: Certification</td><td><span class="t-badge">Day 10–14</span></td><td>Complete test case: update valuation + generate report + validate outputs</td><td>User demonstrates full workflow competency</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-onboard-mgmt" class="sub-pane">
      <div class="sop-breadcrumb">Onboarding</div>
      <div class="sop-title">Onboarding: Senior Management</div>
      <div class="sop-desc">Focused onboarding for MDs and Operating Partners. Emphasis on dashboard navigation, KPI interpretation, and decision use cases. Target: 10 days.</div>
      <div class="raci-row">
        <span class="raci-pill rp-r">R: Senior Management</span>
        <span class="raci-pill rp-a">A: Vantage Finance</span>
        <span class="raci-pill rp-c">C: TSG Finance; Vantage Non-Finance</span>
      </div>
      <table class="phase-table">
        <thead><tr><th>Phase</th><th>Timing</th><th>Key Activities</th><th>Success Criteria</th></tr></thead>
        <tbody>
          <tr><td class="ph-name">Phase 0: Access &amp; Setup</td><td><span class="t-badge">Day 0–2</span></td><td>Provide access to PowerBI dashboards and key reporting materials</td><td>User can access all dashboards without friction</td></tr>
          <tr><td class="ph-name">Phase 1: Reporting Overview</td><td><span class="t-badge">Day 1–5</span></td><td>Walkthrough of portfolio dashboards, KPIs, standard views, and reporting cadence</td><td>User knows what standard reporting exists</td></tr>
          <tr><td class="ph-name">Phase 2: KPI Framing</td><td><span class="t-badge">Day 1–5</span></td><td>High-level overview of key KPIs: definitions, what matters, how to interpret trends</td><td>User understands core metrics and decision relevance</td></tr>
          <tr><td class="ph-name">Phase 3: Dashboard Navigation</td><td><span class="t-badge">Day 3–7</span></td><td>Focused walkthrough: filters, slicing, drilling into PortCos, exporting views</td><td>User can quickly navigate and extract insights</td></tr>
          <tr><td class="ph-name">Phase 4: Decision Use Cases</td><td><span class="t-badge">Day 7–10</span></td><td>Apply reporting to real scenarios: IC prep, board materials, performance reviews</td><td>User can leverage reporting in decision-making</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-new-company" class="sub-pane">
      <div class="sop-breadcrumb">Platform Use</div>
      <div class="sop-title">Creating New Companies</div>
      <div class="sop-desc">End-to-end process for creating a new portfolio company in 73Strings. Admin access only: 73S Monitor &gt; Briefcase Button (left toolbar).</div>
      <div class="raci-row">
        <span class="raci-pill rp-r">R: Offshore Team; Vantage Finance</span>
        <span class="raci-pill rp-a">A: Vantage Finance</span>
        <span class="raci-pill rp-c">C: Deal Team; TSG Finance</span>
      </div>
      <ul class="step-list">
        <li><div class="sn">1</div><div><strong>Receive New Company Form</strong> — Send to Deal Team for written approval. Save the form in the designated folder. Log into 73Strings.</div></li>
        <li><div class="sn">2</div><div><strong>Click "Create Entity"</strong> — Panel appears on the right.</div></li>
        <li><div class="sn">3</div><div><strong>Define Entity Details</strong> — Entity Type: External · Layer: Portfolio Company · Name, Description, Sector, Currency (USD), Fiscal Year End, Investment Date, Website. All information must come from the intake form.</div></li>
        <li><div class="sn">4</div><div><strong>Define Company Profile</strong> — Overview &gt; Profile.</div></li>
        <li><div class="sn">5</div><div><strong>Add Company Contacts</strong> — My Portfolio &gt; PortCo &gt; Overview &gt; Contacts. Include PortCo contact and deal team member.</div></li>
        <li><div class="sn">6</div><div><strong>Add Company Attributes</strong> — Settings &gt; Bulk Upload &gt; Get All Templates &gt; Attributes Template. Copy/paste financial labels. Append "(SOCF)" to any cash flow labels. Import back into 73S.</div></li>
        <li><div class="sn">7</div><div><strong>Create Template</strong> — My Portfolio &gt; PortCo &gt; Overview &gt; Template. Create new financial template using company name.</div></li>
        <li><div class="sn">8</div><div><strong>Import Financials</strong> — My Portfolio &gt; PortCo &gt; Data Import. Highlight data in Excel (without headers, include date row). Click extract. Select correct template. Map attributes 1:1. Click submit.</div></li>
      </ul>
      <div class="warn-box">Do not begin entity creation if the intake form has missing required fields. Notify the Deal Team with a specific list of missing items.</div>
    </div>
    <div id="sop-request-data" class="sub-pane">
      <div class="sop-breadcrumb">Platform Use</div>
      <div class="sop-title">Requesting Data</div>
      <div class="sop-desc">Standard process for submitting ad hoc or supplemental data requests to portfolio companies.</div>
      <ul class="step-list">
        <li><div class="sn">1</div><div><strong>Submit Form 03</strong> (Ad Hoc Data Request) with Deal Team approval and business justification.</div></li>
        <li><div class="sn">2</div><div><strong>Offshore Team prepares request</strong> — Uses the standard request template. Includes specific period, data version, and format requirements.</div></li>
        <li><div class="sn">3</div><div><strong>PortCo submits data</strong> — Via 73Strings data portal or secure email.</div></li>
        <li><div class="sn">4</div><div><strong>Validation</strong> — Offshore Team validates against prior periods and flags anomalies.</div></li>
        <li><div class="sn">5</div><div><strong>Ingestion</strong> — Validated data imported into 73Strings and KPIs updated.</div></li>
      </ul>
      <div class="info-box">SLA: 3–5 business days from request submission, depending on PortCo responsiveness and data complexity.</div>
    </div>
    <div id="sop-attributes" class="sub-pane">
      <div class="sop-breadcrumb">Platform Use</div>
      <div class="sop-title">Attribute Management</div>
      <div class="sop-desc">Adding, renaming, or retiring attributes in 73Strings. All changes require dual approval before implementation.</div>
      <ul class="step-list">
        <li><div class="sn">1</div><div><strong>Submit Form 06</strong> (Attribute Change Request) with change type, attribute details, and reason.</div></li>
        <li><div class="sn">2</div><div><strong>Dual Approval</strong> — Deal Team Lead and Vantage Finance must both approve before any change is made.</div></li>
        <li><div class="sn">3</div><div><strong>Implement Change</strong> — Offshore Team executes in 73Strings: Settings &gt; Attributes.</div></li>
        <li><div class="sn">4</div><div><strong>Historical Data</strong> — If renaming, confirm historical data maps correctly. Re-import if necessary.</div></li>
        <li><div class="sn">5</div><div><strong>Log Change</strong> — Document in the Attribute Change Log with date, approver, and change description.</div></li>
      </ul>
    </div>
    <div id="sop-formulas" class="sub-pane">
      <div class="sop-breadcrumb">Platform Use</div>
      <div class="sop-title">Formula Management</div>
      <div class="sop-desc">Creating and updating calculated formulas (KPIs) in 73Strings. Formulas are calculated from attributes and must be validated before going live.</div>
      <ul class="step-list">
        <li><div class="sn">1</div><div><strong>Submit Form 05</strong> (KPI / Formula Change Request) with the full formula definition and data sources.</div></li>
        <li><div class="sn">2</div><div><strong>Approval</strong> — Vantage Finance approves; TSG Finance reviews investor-facing formulas.</div></li>
        <li><div class="sn">3</div><div><strong>Build in 73Strings</strong> — Settings &gt; Formulas. Use exact attribute names. Add description and display format.</div></li>
        <li><div class="sn">4</div><div><strong>Validate Against History</strong> — Run formula for 3 prior periods. Compare to known correct values.</div></li>
        <li><div class="sn">5</div><div><strong>Deploy</strong> — Once validated, mark as active. Log in KPI Change Log.</div></li>
      </ul>
      <div class="warn-box">Never modify a live formula during reporting periods. Schedule changes for post-close periods only.</div>
    </div>
    <div id="sop-powerbi" class="sub-pane">
      <div class="sop-breadcrumb">Technology</div>
      <div class="sop-title">PowerBI &amp; SharePoint</div>
      <div class="sop-desc">Governance for PowerBI dashboard changes, SharePoint access, and report distribution.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">Change Requests</td><td>All dashboard changes submitted via Form 10 (PowerBI Change Request). Approved by Michelle Phan; assigned to Matt Rispoli.</td></tr>
          <tr><td class="rl">SharePoint Access</td><td>New or modified SharePoint access submitted via Form 10. IT (Halcyon) notified for provisioning.</td></tr>
          <tr><td class="rl">Investor-Facing Reports</td><td>Any PowerBI report or export intended for LP or lender distribution requires Compliance Review (Form 08).</td></tr>
          <tr><td class="rl">Scheduled Refresh</td><td>Dashboards refresh automatically after 73Strings data ingestion cycle. Manual refresh available via PowerBI Service.</td></tr>
        </tbody>
      </table>
    </div>
    <div id="sop-it-support" class="sub-pane">
      <div class="sop-breadcrumb">Technology</div>
      <div class="sop-title">IT &amp; Platform Support</div>
      <div class="sop-desc">Process for reporting 73Strings technical issues, platform errors, or system configuration requests.</div>
      <table class="gov-table">
        <thead><tr><th></th><th>Details</th></tr></thead>
        <tbody>
          <tr><td class="rl">Scope</td><td>All use of the 73Strings platform · All personnel who access, input data, review, or approve outputs</td></tr>
          <tr><td class="rl">How to Submit</td><td>Use Form 07 (IT &amp; Platform Support Ticket). Include issue type, severity, description, and screenshots.</td></tr>
          <tr><td class="rl">Triage</td><td>Technology Lead (Matt Rispoli) reviews within 1 business day. Critical issues actioned immediately.</td></tr>
          <tr><td class="rl">Vendor Escalation</td><td>Issues requiring 73Strings vendor involvement coordinated by Technology Lead per SLA terms.</td></tr>
          <tr><td class="rl">Resolution Tracking</td><td>All issues logged with root cause and resolution summary. Monthly review of open tickets.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<!-- ═══════════════════ PANEL B: REQUEST FORMS ═══════════════════ -->
<div class="panel" id="panel-forms">
  <div class="sidebar">
    <div class="grp-label">Company &amp; Data</div>
    <div class="s-tab active" onclick="showSub('forms','f-new-co',this)"><span>New Company Intake</span><span class="s-num">01</span></div>
    <div class="s-tab" onclick="showSub('forms','f-adhoc',this)"><span>Ad Hoc Data Request</span><span class="s-num">03</span></div>
    <div class="s-tab" onclick="showSub('forms','f-restate',this)"><span>Restatement Request</span><span class="s-num">04</span></div>
    <div class="grp-label">Metrics &amp; Attributes</div>
    <div class="s-tab" onclick="showSub('forms','f-kpi',this)"><span>KPI / Formula Change</span><span class="s-num">05</span></div>
    <div class="s-tab" onclick="showSub('forms','f-attr',this)"><span>Attribute Change</span><span class="s-num">06</span></div>
    <div class="grp-label">Access &amp; Users</div>
    <div class="s-tab" onclick="showSub('forms','f-user',this)"><span>User Access Request</span><span class="s-num">02</span></div>
    <div class="grp-label">Platform &amp; Tech</div>
    <div class="s-tab" onclick="showSub('forms','f-it',this)"><span>IT Support Ticket</span><span class="s-num">07</span></div>
    <div class="s-tab" onclick="showSub('forms','f-compliance',this)"><span>Compliance Review</span><span class="s-num">08</span></div>
    <div class="s-tab" onclick="showSub('forms','f-tech',this)"><span>Tech Initiative</span><span class="s-num">09</span></div>
    <div class="s-tab" onclick="showSub('forms','f-pbi',this)"><span>PowerBI Change</span><span class="s-num">10</span></div>
  </div>
  <div class="pane">
    <div id="toast" class="toast">✓ &nbsp;Form submitted — Michelle Phan has been notified.</div>

    <!-- ── FORM 01: NEW COMPANY ── -->
    <div class="sub-pane active" id="f-new-co">
      <div class="form-header-block">
        <div class="form-badge">FORM 01</div>
        <div class="form-title">New Company Intake Form</div>
        <div class="form-desc">Complete when onboarding a new portfolio company into 73Strings. Deal Team lead must provide written approval before entity creation begins.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Deal Team Lead</span><span class="rr-approver">Approver: Vantage Finance</span><span class="rr-notify">Notified: Jess Collazo-Young</span><span class="rr-notify">Assigned: Offshore Team</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Company Identity</div>
        <div class="frow frow-2">
          <div class="field"><label>Legal Entity Name <span class="req">*</span></label><input type="text" id="f1-legal" placeholder="Full legal name"></div>
          <div class="field"><label>DBA / Trading Name <span class="hint">if different</span></label><input type="text" id="f1-dba" placeholder="Doing business as..."></div>
        </div>
        <div class="frow frow-3">
          <div class="field"><label>Fund <span class="req">*</span></label><select id="f1-fund"><option value="">Select...</option><option>TSG7</option><option>TSG8</option><option>TSG9</option></select></div>
          <div class="field"><label>Sector <span class="req">*</span></label><select id="f1-sector"><option value="">Select...</option><option>Beauty & Personal Care</option><option>Household</option><option>Health & Wellness</option><option>Education</option><option>Restaurant</option><option>Consumer Tech</option></select></div>
          <div class="field"><label>Geography <span class="req">*</span></label><select id="f1-geo"><option value="">Select...</option><option>United States</option><option>Canada</option><option>United Kingdom</option><option>Other</option></select></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Investment Details</div>
        <div class="frow frow-3">
          <div class="field"><label>Investment Date <span class="req">*</span></label><input type="date" id="f1-inv-date"></div>
          <div class="field"><label>Fiscal Year End <span class="req">*</span></label><select id="f1-fy"><option value="">Select month...</option><option>January</option><option>February</option><option>March</option><option>April</option><option>May</option><option>June</option><option>July</option><option>August</option><option>September</option><option>October</option><option>November</option><option>December</option></select></div>
          <div class="field"><label>Reporting Frequency <span class="req">*</span></label><select id="f1-freq"><option value="">Select...</option><option>Monthly</option><option>Quarterly</option></select></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>TSG Ownership % <span class="req">*</span></label><input type="text" id="f1-own" placeholder="e.g. 55%"></div>
          <div class="field"><label>Security Type <span class="req">*</span></label><select id="f1-sec"><option value="">Select...</option><option>Preferred Equity</option><option>Common Equity</option><option>Structured</option><option>Minority</option><option>Control</option></select></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Contacts</div>
        <div class="frow frow-2">
          <div class="field"><label>PortCo Finance Contact Name <span class="req">*</span></label><input type="text" id="f1-pc-name"></div>
          <div class="field"><label>PortCo Finance Contact Email <span class="req">*</span></label><input type="email" id="f1-pc-email" placeholder="name@company.com"></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>Deal Team Associate <span class="req">*</span></label><input type="text" id="f1-dt-assoc"></div>
          <div class="field"><label>Deal Team VP <span class="req">*</span></label><input type="text" id="f1-dt-vp"></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Financial Statements &amp; Data</div>
        <div class="field"><label>Statements to be Collected <span class="req">*</span></label>
          <div class="chk-group">
            <label class="chk-item"><input type="checkbox" id="f1-is" checked> Income Statement</label>
            <label class="chk-item"><input type="checkbox" id="f1-bs" checked> Balance Sheet</label>
            <label class="chk-item"><input type="checkbox" id="f1-cf" checked> Cash Flow (SOCF)</label>
            <label class="chk-item"><input type="checkbox" id="f1-kpi"> KPI Supplement</label>
            <label class="chk-item"><input type="checkbox" id="f1-bud"> Budget / Forecast</label>
            <label class="chk-item"><input type="checkbox" id="f1-mgmt"> Mgmt Adj. EBITDA Bridge</label>
          </div>
        </div>
        <div class="field" style="margin-top:8px"><label>Known Data Complexities</label>
          <div class="chk-group">
            <label class="chk-item"><input type="checkbox" id="f1-sub"> Multiple subsidiaries</label>
            <label class="chk-item"><input type="checkbox" id="f1-cur"> Multi-currency</label>
            <label class="chk-item"><input type="checkbox" id="f1-nfp"> Non-standard fiscal periods</label>
            <label class="chk-item"><input type="checkbox" id="f1-none"> None</label>
          </div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Deal Team Approval</div>
        <div class="frow frow-2">
          <div class="field"><label>Approving Deal Team Lead Name <span class="req">*</span></label><input type="text" id="f1-dt-lead"></div>
          <div class="field"><label>Approving Deal Team Lead Email <span class="req">*</span></label><input type="email" id="f1-dt-lead-email"></div>
        </div>
        <div class="field"><label class="chk-item" style="font-size:11.5px"><input type="checkbox" id="f1-confirm"> I confirm the information in this form is complete and accurate</label></div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-new-co')">Clear</button><button class="btn-submit" onclick="sendForm('f-new-co','New Company Intake')">Submit &amp; Notify Team</button></div></div>
    </div>

    <!-- ── FORM 02: USER ACCESS ── -->
    <div class="sub-pane" id="f-user">
      <div class="form-header-block">
        <div class="form-badge">FORM 02</div>
        <div class="form-title">User Access Request</div>
        <div class="form-desc">New user setup, role changes, or offboarding. Admin-level access requests are automatically routed to TSG Compliance for additional review.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Vantage Finance</span><span class="rr-notify">Assigned: Offshore Team</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Request Type &amp; User Details</div>
        <div class="field"><label>Request Type <span class="req">*</span></label>
          <select id="f2-type" onchange="handleAT(this)"><option value="">Select...</option><option value="new">New User</option><option value="change">Role Change</option><option value="offboard">Offboard / Inactivate</option><option value="portco">Add PortCo User</option></select>
        </div>
        <div class="frow frow-2" style="margin-top:8px">
          <div class="field"><label>User Full Name <span class="req">*</span></label><input type="text" id="f2-name"></div>
          <div class="field"><label>User Email <span class="req">*</span></label><input type="email" id="f2-email"></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>User's Team / Company</label><input type="text" id="f2-team"></div>
          <div class="field"><label>User's Title / Role</label><input type="text" id="f2-title"></div>
        </div>
      </div>
      <div class="cond-field" id="new-user-fields">
        <div class="fsec-label">Access Configuration</div>
        <div class="frow frow-2">
          <div class="field"><label>User Type <span class="req">*</span></label><select id="f2-utype" onchange="handleUT(this)"><option value="">Select...</option><option value="admin">Admin</option><option value="active">Active User</option><option value="portco">PortCo User</option></select></div>
          <div class="field"><label>Access Level <span class="req">*</span></label><select id="f2-level"><option value="">Select...</option><option>Read only</option><option>Read + Write</option><option>Admin</option></select></div>
        </div>
        <div class="cond-field" id="admin-warn"><div class="warn-box" style="margin:0">Admin access requires TSG Compliance (Drew Weilbacher) review. This request will be automatically routed before setup proceeds.</div></div>
        <div class="field" style="margin-top:8px"><label>Companies to Grant Access</label><input type="text" id="f2-companies" placeholder="List company names, or 'All portfolio'"></div>
      </div>
      <div class="cond-field" id="change-fields">
        <div class="fsec-label">Role Change Details</div>
        <div class="field"><label>Current Access</label><input type="text" id="f2-cur-access"></div>
        <div class="field"><label>Requested New Access <span class="req">*</span></label><input type="text" id="f2-new-access"></div>
        <div class="field"><label>Reason for Change <span class="req">*</span></label><textarea id="f2-reason"></textarea></div>
      </div>
      <div class="cond-field" id="offboard-fields">
        <div class="fsec-label">Offboarding Details</div>
        <div class="warn-box">SLA: User must be inactivated within 1 business day of departure notification.</div>
        <div class="field" style="margin-top:8px"><label>Last Day of Access <span class="req">*</span></label><input type="date" id="f2-last-day"></div>
        <div class="field"><label class="chk-item"><input type="checkbox" id="f2-deact"> I confirm this user should be deactivated</label></div>
      </div>
      <div class="fsec" style="margin-top:12px">
        <div class="fsec-label">Requested By</div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f2-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f2-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-user')">Clear</button><button class="btn-submit" onclick="sendForm('f-user','User Access Request')">Submit &amp; Notify Team</button></div></div>
    </div>

    <!-- ── FORM 03: AD HOC DATA ── -->
    <div class="sub-pane" id="f-adhoc">
      <div class="form-header-block">
        <div class="form-badge">FORM 03</div>
        <div class="form-title">Ad Hoc Data Request</div>
        <div class="form-desc">For non-recurring data requests outside the normal quarterly cycle. Deal Team approval and Vantage Finance notification required.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Deal Team Lead</span><span class="rr-notify">Notified: Vantage Finance</span><span class="rr-notify">Assigned: Offshore Team</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Request Details</div>
        <div class="frow frow-2">
          <div class="field"><label>Portfolio Company <span class="req">*</span></label><input type="text" id="f3-co"></div>
          <div class="field"><label>Fund <span class="req">*</span></label><select id="f3-fund"><option value="">Select...</option><option>TSG7</option><option>TSG8</option><option>TSG9</option></select></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>Data Version <span class="req">*</span></label><select id="f3-ver"><option value="">Select...</option><option>Actual</option><option>Budget</option><option>Forecast</option></select></div>
          <div class="field"><label>Reporting Period <span class="req">*</span></label><input type="text" id="f3-period" placeholder="e.g. Q3 2024"></div>
        </div>
        <div class="field"><label>Statements Requested <span class="req">*</span></label>
          <div class="chk-group">
            <label class="chk-item"><input type="checkbox" id="f3-is"> Income Statement</label>
            <label class="chk-item"><input type="checkbox" id="f3-bs"> Balance Sheet</label>
            <label class="chk-item"><input type="checkbox" id="f3-cf"> Cash Flow</label>
            <label class="chk-item"><input type="checkbox" id="f3-kpi"> KPI Supplement</label>
            <label class="chk-item"><input type="checkbox" id="f3-mgmt"> Mgmt EBITDA Bridge</label>
          </div>
        </div>
        <div class="field" style="margin-top:8px"><label>Business Justification <span class="req">*</span></label><textarea id="f3-just" placeholder="e.g. IC prep, lender request, board materials..."></textarea></div>
        <div class="frow frow-2">
          <div class="field"><label>Data Needed By <span class="req">*</span></label><input type="date" id="f3-due"></div>
          <div class="field"><label>Deal Team Associate <span class="req">*</span></label><input type="text" id="f3-dt"></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Requested By</div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f3-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f3-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-adhoc')">Clear</button><button class="btn-submit" onclick="sendForm('f-adhoc','Ad Hoc Data Request')">Submit &amp; Notify Team</button></div></div>
    </div>

    <!-- ── FORM 04: RESTATEMENT ── -->
    <div class="sub-pane" id="f-restate">
      <div class="form-header-block">
        <div class="form-badge">FORM 04</div>
        <div class="form-title">Restatement Request</div>
        <div class="form-desc">When an error is identified in a previously submitted and closed period. Vantage Finance must approve scope before Offshore Team proceeds.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Vantage Finance</span><span class="rr-notify">Notified: Deal Team</span><span class="rr-notify">Assigned: Offshore Team</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Restatement Details</div>
        <div class="frow frow-2">
          <div class="field"><label>Portfolio Company <span class="req">*</span></label><input type="text" id="f4-co"></div>
          <div class="field"><label>Period(s) Affected <span class="req">*</span></label><input type="text" id="f4-periods" placeholder="e.g. Q2 2024, Q3 2024"></div>
        </div>
        <div class="field"><label>Statements Affected <span class="req">*</span></label>
          <div class="chk-group">
            <label class="chk-item"><input type="checkbox" id="f4-is"> Income Statement</label>
            <label class="chk-item"><input type="checkbox" id="f4-bs"> Balance Sheet</label>
            <label class="chk-item"><input type="checkbox" id="f4-cf"> Cash Flow</label>
            <label class="chk-item"><input type="checkbox" id="f4-kpi"> KPI Supplement</label>
          </div>
        </div>
        <div class="field" style="margin-top:8px"><label>Description of Error <span class="req">*</span></label><textarea id="f4-error" placeholder="Describe what was incorrect and how it was identified..."></textarea></div>
        <div class="frow frow-2">
          <div class="field"><label>Root Cause <span class="req">*</span></label><select id="f4-cause"><option value="">Select...</option><option>PortCo submitted incorrect data</option><option>Mapping error in 73Strings</option><option>Formula / calculation error</option><option>Reclassification by PortCo</option><option>Audit adjustment</option><option>Other</option></select></div>
          <div class="field"><label>Investor-Facing? <span class="req">*</span></label><select id="f4-inv" onchange="document.getElementById('inv-warn').className=this.value==='yes'?'cond-field show':'cond-field'"><option value="">Select...</option><option value="yes">Yes — Compliance notified</option><option value="no">No</option></select></div>
        </div>
        <div class="cond-field" id="inv-warn"><div class="warn-box" style="margin:0">TSG Compliance (Drew Weilbacher) will be automatically notified and must approve before corrected materials are redistributed.</div></div>
        <div class="field" style="margin-top:10px"><label>KPIs / Reports Impacted <span class="req">*</span></label><textarea id="f4-kpis" placeholder="List all KPIs, dashboards, and reports needing re-validation..."></textarea></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Requested By</div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f4-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f4-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-restate')">Clear</button><button class="btn-submit" onclick="sendForm('f-restate','Restatement Request')">Submit &amp; Notify Team</button></div></div>
    </div>

    <!-- ── FORM 05: KPI / FORMULA ── -->
    <div class="sub-pane" id="f-kpi">
      <div class="form-header-block">
        <div class="form-badge">FORM 05</div>
        <div class="form-title">KPI / Formula Change Request</div>
        <div class="form-desc">Add a new KPI or formula, or modify an existing one. All changes must be logged in the KPI Change Log and validated before going live.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Vantage Finance</span><span class="rr-approver">Review: TSG Finance</span><span class="rr-notify">Assigned: Offshore Team</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Change Type</div>
        <div class="frow frow-2">
          <div class="field"><label>Request Type <span class="req">*</span></label><select id="f5-type"><option value="">Select...</option><option>Add new Portfolio KPI</option><option>Add new Company KPI</option><option>Add new Formula</option><option>Update existing KPI</option><option>Update existing Formula</option><option>Retire KPI / Formula</option></select></div>
          <div class="field"><label>KPI / Formula Name <span class="req">*</span></label><input type="text" id="f5-name" placeholder="e.g. EBITDA Margin"></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>Applies To <span class="req">*</span></label><select id="f5-applies"><option value="">Select...</option><option>All portfolio companies</option><option>Specific company only</option><option>Specific fund only</option></select></div>
          <div class="field"><label>Reporting Frequency <span class="req">*</span></label><select id="f5-freq"><option value="">Select...</option><option>Monthly</option><option>Quarterly</option><option>Annual</option><option>LTM rolling</option></select></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Definition &amp; Logic</div>
        <div class="field"><label>Business Definition <span class="req">*</span></label><textarea id="f5-def" placeholder="Plain language description of what this KPI measures..."></textarea></div>
        <div class="field"><label>Calculation Logic / Formula <span class="req">*</span></label><textarea id="f5-calc" placeholder="Exact formula and data sources, e.g. EBITDA Margin = EBITDA / Net Revenue"></textarea></div>
        <div class="frow frow-2">
          <div class="field"><label>Investor-Facing? <span class="req">*</span></label><select id="f5-inv"><option value="">Select...</option><option>Yes — TSG Compliance approval required</option><option>No</option><option>Potentially — flag for review</option></select></div>
          <div class="field"><label>Deal Team Lead Approving</label><input type="text" id="f5-dt" placeholder="For company KPIs — name of approver"></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Requested By</div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f5-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f5-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-kpi')">Clear</button><button class="btn-submit" onclick="sendForm('f-kpi','KPI / Formula Change Request')">Submit &amp; Notify Team</button></div></div>
    </div>

    <!-- ── FORM 06: ATTRIBUTE ── -->
    <div class="sub-pane" id="f-attr">
      <div class="form-header-block">
        <div class="form-badge">FORM 06</div>
        <div class="form-title">Attribute Change Request</div>
        <div class="form-desc">Add, edit, rename, or retire a company attribute in 73Strings. Requires Deal Team lead and Vantage Finance approval before implementation.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Deal Team Lead</span><span class="rr-approver">Approver: Vantage Finance</span><span class="rr-notify">Assigned: Offshore Team</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Change Type &amp; Attribute Details</div>
        <div class="frow frow-2">
          <div class="field"><label>Change Type <span class="req">*</span></label><select id="f6-type"><option value="">Select...</option><option>Add new attribute</option><option>Rename existing attribute</option><option>Update attribute properties</option><option>Retire attribute</option><option>Add synonym</option></select></div>
          <div class="field"><label>Portfolio Company <span class="req">*</span></label><input type="text" id="f6-co" placeholder="Company name or 'All companies'"></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>Current Attribute Name <span class="hint">for updates</span></label><input type="text" id="f6-cur-name"></div>
          <div class="field"><label>New / Proposed Attribute Name <span class="req">*</span></label><input type="text" id="f6-new-name" placeholder="Must be unique in the system"></div>
        </div>
        <div class="frow frow-3">
          <div class="field"><label>Attribute Tag <span class="req">*</span></label><select id="f6-tag"><option value="">Select...</option><option>Income Statement</option><option>Balance Sheet</option><option>Cash Flow (SOCF)</option><option>KPI</option><option>Covenant</option><option>General Details</option><option>ESG</option></select></div>
          <div class="field"><label>Field Type <span class="req">*</span></label><select id="f6-field-type"><option value="">Select...</option><option>Numerical</option><option>Text</option></select></div>
          <div class="field"><label>Display Property</label><select id="f6-display"><option value="">Select...</option><option>Currency</option><option>Percentage</option><option>Multiple</option><option>Absolute Number</option></select></div>
        </div>
        <div class="field"><label>Reason for Change <span class="req">*</span></label><textarea id="f6-reason" placeholder="e.g. PortCo renamed this line item in Q3 2024 financials..."></textarea></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Requested By</div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f6-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f6-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-attr')">Clear</button><button class="btn-submit" onclick="sendForm('f-attr','Attribute Change Request')">Submit &amp; Notify Team</button></div></div>
    </div>

    <!-- ── FORM 07: IT SUPPORT ── -->
    <div class="sub-pane" id="f-it">
      <div class="form-header-block">
        <div class="form-badge">FORM 07</div>
        <div class="form-title">IT &amp; Platform Support Ticket</div>
        <div class="form-desc">For 73Strings technical issues, platform errors, or system configuration requests. Emergency fixes may be actioned immediately with retroactive sign-off.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Triaged by: Technology Lead (Vantage Finance)</span><span class="rr-notify">Escalated to: 73Strings Helpdesk</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Issue Classification</div>
        <div class="frow frow-2">
          <div class="field"><label>Issue Type <span class="req">*</span></label><select id="f7-type"><option value="">Select...</option><option>Platform error / bug</option><option>Data not loading / refresh failure</option><option>Access / login issue</option><option>Configuration change request</option><option>Performance issue</option><option>Other</option></select></div>
          <div class="field"><label>Severity <span class="req">*</span></label><select id="f7-sev" onchange="document.getElementById('crit-warn').className=this.value==='critical'?'cond-field show':'cond-field'"><option value="">Select...</option><option value="critical">Critical — platform down / data loss</option><option value="high">High — blocking work</option><option value="medium">Medium — workaround exists</option><option value="low">Low — minor</option></select></div>
        </div>
        <div class="cond-field" id="crit-warn"><div class="warn-box" style="margin:4px 0 0">Critical: Technology Lead may action immediately. SLA: 1 business day.</div></div>
        <div class="field" style="margin-top:8px"><label>Issue Title <span class="req">*</span></label><input type="text" id="f7-title" placeholder="Brief descriptive title"></div>
        <div class="field"><label>Detailed Description <span class="req">*</span></label><textarea id="f7-desc" placeholder="Describe the issue: what you were trying to do, what happened, what you expected..."></textarea></div>
        <div class="frow frow-2">
          <div class="field"><label>Affected Company <span class="hint">if applicable</span></label><input type="text" id="f7-co" placeholder="Company name or 'All'"></div>
          <div class="field"><label>Date Issue First Observed</label><input type="date" id="f7-date"></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Submitted By</div>
        <div class="frow frow-2">
          <div class="field"><label>Your Name <span class="req">*</span></label><input type="text" id="f7-name"></div>
          <div class="field"><label>Your Email <span class="req">*</span></label><input type="email" id="f7-email"></div>
        </div>
        <div class="field"><label>Team</label><select id="f7-team"><option value="">Select...</option><option>Vantage Finance</option><option>Deal Team</option><option>Offshore Team</option><option>Portfolio Company</option><option>Senior Management</option></select></div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-it')">Clear</button><button class="btn-submit" onclick="sendForm('f-it','IT & Platform Support Ticket')">Submit Ticket</button></div></div>
    </div>

    <!-- ── FORM 08: COMPLIANCE ── -->
    <div class="sub-pane" id="f-compliance">
      <div class="form-header-block">
        <div class="form-badge">FORM 08</div>
        <div class="form-title">Compliance Review Request</div>
        <div class="form-desc">Required before distributing any investor-facing materials or making material changes to externally shared reports. Routes directly to Drew Weilbacher.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Assigned: Drew Weilbacher (TSG Compliance)</span><span class="rr-notify">Notified: Vantage Finance</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Material Details</div>
        <div class="field"><label>Material / Report Name <span class="req">*</span></label><input type="text" id="f8-name" placeholder="e.g. TSG9 Portfolio Datasheet Q3 2024"></div>
        <div class="frow frow-2">
          <div class="field"><label>Review Type <span class="req">*</span></label><select id="f8-type"><option value="">Select...</option><option>New material — first distribution</option><option>Material change to existing report</option><option>Correction / restatement</option><option>New KPI added to investor report</option></select></div>
          <div class="field"><label>Target Distribution Date <span class="req">*</span></label><input type="date" id="f8-date"></div>
        </div>
        <div class="field"><label>Intended Audience <span class="req">*</span></label>
          <div class="chk-group">
            <label class="chk-item"><input type="checkbox" id="f8-lp"> LP investors</label>
            <label class="chk-item"><input type="checkbox" id="f8-lend"> Lenders</label>
            <label class="chk-item"><input type="checkbox" id="f8-board"> Board members</label>
            <label class="chk-item"><input type="checkbox" id="f8-prosp"> Prospective investors</label>
            <label class="chk-item"><input type="checkbox" id="f8-reg"> Regulators</label>
          </div>
        </div>
        <div class="field"><label>Description of Changes <span class="req">*</span></label><textarea id="f8-changes" placeholder="Describe what changed from the prior version..."></textarea></div>
        <div class="field"><label>Has Vantage Finance approved this version? <span class="req">*</span></label><select id="f8-vf"><option value="">Select...</option><option>Yes</option><option>Pending</option></select></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Requested By</div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f8-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f8-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-compliance')">Clear</button><button class="btn-submit" onclick="sendForm('f-compliance','Compliance Review Request')">Submit for Compliance Review</button></div></div>
    </div>

    <!-- ── FORM 09: TECH INITIATIVE ── -->
    <div class="sub-pane" id="f-tech">
      <div class="form-header-block">
        <div class="form-badge">FORM 09</div>
        <div class="form-title">Technology Initiative Intake</div>
        <div class="form-desc">Propose new technology or automation initiatives, system enhancements, or infrastructure upgrades. Requires Executive Sponsor approval before roadmap inclusion.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Executive Sponsor</span><span class="rr-notify">Notified: Technology Lead / PMO</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Initiative Overview</div>
        <div class="field"><label>Initiative Name <span class="req">*</span></label><input type="text" id="f9-name"></div>
        <div class="field"><label>Business Objective <span class="req">*</span></label><textarea id="f9-obj" placeholder="What business problem does this solve?"></textarea></div>
        <div class="field"><label>Expected Benefits <span class="req">*</span></label><textarea id="f9-benefits" placeholder="Quantify where possible: time saved, error reduction, reporting improvement..."></textarea></div>
        <div class="frow frow-3">
          <div class="field"><label>Priority <span class="req">*</span></label><select id="f9-pri"><option value="">Select...</option><option>High</option><option>Medium</option><option>Low</option></select></div>
          <div class="field"><label>Estimated Cost</label><input type="text" id="f9-cost" placeholder="e.g. $50K, TBD"></div>
          <div class="field"><label>Estimated Timeline</label><input type="text" id="f9-timeline" placeholder="e.g. 6–8 weeks"></div>
        </div>
        <div class="field"><label>Risk &amp; Control Impact</label><textarea id="f9-risk" placeholder="Identify data security, compliance, or operational risks..."></textarea></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Business Owner</div>
        <div class="frow frow-2">
          <div class="field"><label>Owner Name <span class="req">*</span></label><input type="text" id="f9-owner-name"></div>
          <div class="field"><label>Owner Email <span class="req">*</span></label><input type="email" id="f9-owner-email"></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>Executive Sponsor</label><input type="text" id="f9-exec"></div>
          <div class="field"><label>Target Start Date</label><input type="date" id="f9-start"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-tech')">Clear</button><button class="btn-submit" onclick="sendForm('f-tech','Technology Initiative Intake')">Submit Initiative</button></div></div>
    </div>

    <!-- ── FORM 10: POWERBI ── -->
    <div class="sub-pane" id="f-pbi">
      <div class="form-header-block">
        <div class="form-badge">FORM 10</div>
        <div class="form-title">PowerBI Dashboard Change Request</div>
        <div class="form-desc">For new dashboard pages, layout changes, KPI additions, flag/alert threshold changes, or SharePoint access updates.</div>
        <div class="route-row"><span class="route-lbl">Routes to:</span><span class="rr-approver">Approver: Michelle Phan</span><span class="rr-notify">Assigned: Matt Rispoli</span><span class="rr-notify">Notified: IT (Halcyon) if SharePoint</span></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Change Details</div>
        <div class="field"><label>Change Type <span class="req">*</span></label>
          <div class="chk-group">
            <label class="chk-item"><input type="checkbox" id="f10-new-page"> New dashboard page</label>
            <label class="chk-item"><input type="checkbox" id="f10-layout"> Layout / visual change</label>
            <label class="chk-item"><input type="checkbox" id="f10-kpi"> New KPI added</label>
            <label class="chk-item"><input type="checkbox" id="f10-thresh"> Flag / alert threshold change</label>
            <label class="chk-item"><input type="checkbox" id="f10-data"> Data source / refresh change</label>
            <label class="chk-item"><input type="checkbox" id="f10-sp"> SharePoint access change</label>
            <label class="chk-item"><input type="checkbox" id="f10-bug"> Bug fix</label>
          </div>
        </div>
        <div class="field" style="margin-top:8px"><label>Affected Dashboard / Page <span class="req">*</span></label><select id="f10-dash"><option value="">Select...</option><option>Homepage / Portfolio Overview</option><option>Fund Snapshot</option><option>Company Detail</option><option>Credit & Debt</option><option>Consumer KPIs</option><option>Flags & Alerts</option><option>Documents</option><option>New page</option></select></div>
        <div class="field"><label>Change Description <span class="req">*</span></label><textarea id="f10-desc" placeholder="Describe exactly what needs to change — include metric names, visual types, filter behavior..."></textarea></div>
        <div class="field"><label>Business Justification <span class="req">*</span></label><textarea id="f10-just" placeholder="Why is this change needed? What decision or workflow does it support?"></textarea></div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Flag / Alert Threshold Changes <span style="font-weight:400;font-size:9px">(if applicable)</span></div>
        <div class="frow frow-3">
          <div class="field"><label>KPI / Metric Name</label><input type="text" id="f10-kpi-name" placeholder="e.g. Net Leverage"></div>
          <div class="field"><label>Current Threshold</label><input type="text" id="f10-cur-thresh" placeholder="e.g. Red > 6.0x"></div>
          <div class="field"><label>Proposed Threshold</label><input type="text" id="f10-new-thresh" placeholder="e.g. Red > 5.5x"></div>
        </div>
      </div>
      <div class="fsec">
        <div class="fsec-label">Priority &amp; Requestor</div>
        <div class="frow frow-2">
          <div class="field"><label>Priority <span class="req">*</span></label><select id="f10-pri"><option value="">Select...</option><option>High — needed before next reporting cycle</option><option>Medium — next available sprint</option><option>Low — backlog</option></select></div>
          <div class="field"><label>Needed By Date</label><input type="date" id="f10-date"></div>
        </div>
        <div class="frow frow-2">
          <div class="field"><label>Requestor Name <span class="req">*</span></label><input type="text" id="f10-req-name"></div>
          <div class="field"><label>Requestor Email <span class="req">*</span></label><input type="email" id="f10-req-email"></div>
        </div>
      </div>
      <div class="form-footer"><span class="req-note">* Required fields</span><div style="display:flex;gap:8px"><button class="btn-reset" onclick="resetForm('f-pbi')">Clear</button><button class="btn-submit" onclick="sendForm('f-pbi','PowerBI Dashboard Change Request')">Submit Change Request</button></div></div>
    </div>

  </div><!-- .pane -->
</div><!-- #panel-forms -->

</div><!-- .shell -->

<script>
const RECIPIENT = 'mphan@tsgconsumer.com';

function switchPanel(p, tab) {
  document.querySelectorAll('.panel').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.topbar-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + p).classList.add('active');
  tab.classList.add('active');
}

function showSub(panel, id, tab) {
  const parentEl = document.getElementById('panel-' + panel);
  parentEl.querySelectorAll('.sub-pane').forEach(p => p.classList.remove('active'));
  parentEl.querySelectorAll('.s-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if (tab) tab.classList.add('active');
  const toast = document.getElementById('toast');
  if (toast) toast.classList.remove('show');
}

function handleAT(sel) {
  document.getElementById('new-user-fields').className = (sel.value === 'new' || sel.value === 'portco') ? 'cond-field show' : 'cond-field';
  document.getElementById('change-fields').className = sel.value === 'change' ? 'cond-field show' : 'cond-field';
  document.getElementById('offboard-fields').className = sel.value === 'offboard' ? 'cond-field show' : 'cond-field';
}

function handleUT(sel) {
  document.getElementById('admin-warn').className = sel.value === 'admin' ? 'cond-field show' : 'cond-field';
}

function resetForm(id) {
  const f = document.getElementById(id);
  f.querySelectorAll('input:not([type=checkbox]):not([type=radio])').forEach(i => i.value = '');
  f.querySelectorAll('select').forEach(s => s.selectedIndex = 0);
  f.querySelectorAll('textarea').forEach(t => t.value = '');
  f.querySelectorAll('input[type=checkbox],input[type=radio]').forEach(c => c.checked = false);
  f.querySelectorAll('.cond-field').forEach(c => c.classList.remove('show'));
}

function getVal(id) {
  const el = document.getElementById(id);
  if (!el) return '';
  if (el.type === 'checkbox') return el.checked ? 'Yes' : 'No';
  return el.value || '';
}

function getCheckedLabels(containerEl) {
  if (!containerEl) return '';
  const checked = [...containerEl.querySelectorAll('input[type=checkbox]:checked')]
    .map(cb => cb.parentElement.textContent.trim());
  return checked.length ? checked.join(', ') : 'None selected';
}

// Build email body from all filled fields in a form section
function buildBody(formId, formName) {
  const form = document.getElementById(formId);
  const lines = [`FORM: ${formName}`, `Submitted via TSG Consumer Portfolio Dashboard`, ``, `${'─'.repeat(50)}`, ``];

  // Collect all labels and their corresponding values
  form.querySelectorAll('.fsec').forEach(sec => {
    const secLabel = sec.querySelector('.fsec-label');
    if (secLabel) lines.push(`[ ${secLabel.textContent.trim().toUpperCase()} ]`);

    sec.querySelectorAll('.field').forEach(field => {
      const label = field.querySelector('label');
      if (!label) return;
      const labelText = label.textContent.replace('*','').replace(/\s+/g,' ').trim();

      // Check for checkbox group
      const chkGroup = field.querySelector('.chk-group');
      if (chkGroup) {
        lines.push(`${labelText}: ${getCheckedLabels(chkGroup)}`);
        return;
      }

      // Regular input/select/textarea
      const input = field.querySelector('input:not([type=checkbox]), select, textarea');
      if (input) {
        const val = input.value.trim();
        if (val) lines.push(`${labelText}: ${val}`);
      }
    });

    lines.push('');
  });

  lines.push(`${'─'.repeat(50)}`);
  lines.push(`Sent from TSG Consumer Portfolio Dashboard`);
  return lines.join('\n');
}

function sendForm(formId, formName) {
  const body = buildBody(formId, formName);
  const subject = encodeURIComponent(`[TSG Request] ${formName}`);
  const bodyEncoded = encodeURIComponent(body);
  const mailtoLink = `mailto:${RECIPIENT}?subject=${subject}&body=${bodyEncoded}`;
  window.open(mailtoLink, '_blank');

  // Show success toast
  const toast = document.getElementById('toast');
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 4000);
}
</script>
</body>
</html>
"""


def page_sop():
    # Inject CSS to remove Streamlit padding around the component
    st.markdown("""
    <style>
    .block-container { padding-top: 0 !important; padding-left: 0 !important;
                       padding-right: 0 !important; max-width: 100% !important; }
    iframe { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

    components.html(SOP_HTML, height=820, scrolling=True)
