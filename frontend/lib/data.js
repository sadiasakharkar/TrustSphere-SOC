export const navItems = [
  { href: "/", label: "Access Control", icon: "lock" },
  { href: "/monitoring", label: "Live Ingestion", icon: "analytics" },
  { href: "/incidents", label: "Incident Queue", icon: "security" },
  { href: "/terminal", label: "Analyst Terminal", icon: "terminal" },
  { href: "/playbook", label: "Response Playbook", icon: "auto_fix_high" }
];

export const monitoringStats = [
  {
    label: "True Positives",
    value: "05",
    accent: "var(--primary)",
    note: "+2 since last upload",
    icon: "verified_user"
  },
  {
    label: "False Positives",
    value: "02",
    accent: "var(--error)",
    note: "Heuristic override applied",
    icon: "gpp_maybe"
  },
  {
    label: "Uncertain",
    value: "03",
    accent: "var(--tertiary-container)",
    note: "Requires manual review",
    icon: "help_outline"
  },
  {
    label: "Noise Removed",
    value: "40%",
    accent: "var(--secondary)",
    note: "Normalization efficiency",
    icon: "filter_alt"
  }
];

export const eventTrend = [
  { minute: "14:00", total: 2400, suspicious: 220, filtered: 950 },
  { minute: "14:05", total: 3150, suspicious: 280, filtered: 1260 },
  { minute: "14:10", total: 2950, suspicious: 260, filtered: 1090 },
  { minute: "14:15", total: 3800, suspicious: 390, filtered: 1520 },
  { minute: "14:20", total: 3420, suspicious: 310, filtered: 1340 },
  { minute: "14:25", total: 4100, suspicious: 450, filtered: 1705 }
];

export const normalizedRows = [
  {
    id: "LOG003",
    source: "sysmon",
    status: "Suspicious",
    classification: "True Positive",
    confidence: 92
  },
  {
    id: "LOG004",
    source: "sysmon",
    status: "Normal Tool",
    classification: "False Positive",
    confidence: 15
  },
  {
    id: "LOG005",
    source: "cloud_watch",
    status: "Unknown",
    classification: "Uncertain",
    confidence: 48
  },
  {
    id: "LOG006",
    source: "azure_ad",
    status: "Elevated Auth",
    classification: "True Positive",
    confidence: 88
  }
];

export const incidents = [
  {
    severity: "High",
    title: "Possible Credential Abuse",
    entity: "User: sys_admin",
    risk: "Risk Score: 91%",
    confidence: "Confidence: 87%",
    stage: "Stage: Initial Access",
    time: "14:20 UTC",
    summary: "Multiple abnormal login and privilege behaviors detected.",
    accent: "var(--error)"
  },
  {
    severity: "Medium",
    title: "Outbound Traffic Spike",
    entity: "Node: DB-PROD-01",
    risk: "Risk Score: 64%",
    confidence: "Confidence: 94%",
    stage: "Stage: Exfiltration",
    time: "14:12 UTC",
    summary: "Unusual volume of encrypted data leaving the internal subnet.",
    accent: "var(--tertiary-container)"
  },
  {
    severity: "Low",
    title: "New Admin Account Created",
    entity: "Creator: hr_portal_svc",
    risk: "Risk Score: 22%",
    confidence: "Confidence: 100%",
    stage: "Stage: Persistence",
    time: "13:58 UTC",
    summary: "A new administrative identity was provisioned unexpectedly.",
    accent: "var(--secondary)"
  },
  {
    severity: "Warning",
    title: "Endpoint Script Execution",
    entity: "Device: WKSTN-442",
    risk: "Risk Score: 78%",
    confidence: "Confidence: 62%",
    stage: "Stage: Execution",
    time: "13:45 UTC",
    summary: "Potential script-based execution from a workstation endpoint.",
    accent: "var(--tertiary)"
  }
];

export const riskBreakdown = [
  { label: "Behavior Analysis", value: 35, color: "var(--error)" },
  { label: "System Abuse", value: 30, color: "var(--tertiary)" },
  { label: "Geopolitical Risk", value: 20, color: "var(--primary)" },
  { label: "Identity Drift", value: 15, color: "var(--secondary)" }
];

export const evidenceTimeline = [
  {
    title: "Unusual Transaction Velocity",
    detail: "12 attempts in 400ms",
    color: "var(--error)"
  },
  {
    title: "Known VPN Node Detected",
    detail: "Provider: NordVPN (Shadow Exit)",
    color: "var(--primary)"
  },
  {
    title: "Header Mismatch",
    detail: "Browser: Chrome | User-Agent: Safari",
    color: "var(--tertiary)"
  },
  {
    title: "New IP Location",
    detail: "Kyiv, Ukraine (Unexpected)",
    color: "var(--outline)"
  }
];

export const analystIncidents = [
  {
    id: "INC-001",
    title: "Privilege escalation from finance manager session",
    severity: "critical",
    risk: 94,
    confidence: 91,
    who: "finance_mgr@bank.local",
    environment: "Windows endpoint · Finance subnet",
    time: "14:20 UTC",
    summary:
      "A finance workstation authenticated successfully, launched encoded PowerShell, and attempted a privilege escalation chain that reached a domain admin token context within 40 seconds.",
    tags: ["Credential Abuse", "PowerShell", "Lateral Movement"],
    sources: [
      { file: "sysmon-fin-17.evtx", events: 812, hits: 7, primary: true, description: "Process ancestry and encoded PowerShell execution from FIN-WS-17." },
      { file: "ad-auth-bridge.json", events: 164, hits: 3, primary: false, description: "Directory authentication anomalies and token elevation trail." }
    ],
    evidence: [
      { signal: "Encoded PowerShell launched", observation: "Base64 payload spawned from Excel child process.", contribution: 31 },
      { signal: "Privilege token duplication", observation: "Token impersonation observed against an elevated service account.", contribution: 28 },
      { signal: "Abnormal admin resource access", observation: "Domain admin share access attempted from finance VLAN.", contribution: 22 }
    ],
    riskBreakdown: [
      { label: "Execution anomaly", value: 40, color: "var(--error)" },
      { label: "Identity misuse", value: 34, color: "var(--primary)" },
      { label: "Lateral movement", value: 20, color: "var(--tertiary-container)" }
    ],
    confidenceReasons: [
      "PowerShell lineage matches known post-exploitation sequences.",
      "Admin token access originated from a non-admin workstation.",
      "Corroborated by both Sysmon and AD telemetry."
    ],
    stages: [
      { name: "Execution", sub: "Encoded PowerShell", color: "var(--error)" },
      { name: "Privilege Escalation", sub: "Token duplication", color: "var(--primary)" },
      { name: "Lateral Movement", sub: "Admin share probe", color: "var(--tertiary-container)" }
    ],
    impact: [
      { label: "Likelihood", value: "Very high", tone: "danger" },
      { label: "Blast radius", value: "Finance + directory tier", tone: "danger" },
      { label: "Response SLA", value: "< 15 minutes", tone: "warning" },
      { label: "Business impact", value: "Payment operations at risk", tone: "neutral" }
    ],
    actions: [
      { name: "Disable finance_mgr account", why: "Cuts active session risk immediately.", urgency: "High" },
      { name: "Isolate FIN-WS-17", why: "Stops further lateral movement from the host.", urgency: "High" },
      { name: "Revoke privileged tokens", why: "Removes any impersonated elevated sessions.", urgency: "Medium" }
    ],
    logs: [
      "14:19:58Z  winlog/4624  finance_mgr interactive logon from FIN-WS-17",
      "14:20:03Z  sysmon/1     excel.exe -> powershell.exe -enc SQBFAFgA",
      "14:20:17Z  sysmon/10    token duplication requested for svc_ops_admin",
      "14:20:41Z  smb          \\\\dc01\\admin$ access attempt from FIN-WS-17"
    ]
  },
  {
    id: "INC-002",
    title: "Outbound encrypted transfer from database node",
    severity: "high",
    risk: 81,
    confidence: 86,
    who: "db-prod-01",
    environment: "Linux node · Payments cluster",
    time: "14:12 UTC",
    summary:
      "A production database node initiated a sustained encrypted outbound stream to an uncommon cloud endpoint immediately after a backup exclusion policy was modified.",
    tags: ["Exfiltration", "Database", "Cloud Egress"],
    sources: [
      { file: "zeek-egress.log", events: 1431, hits: 8, primary: true, description: "Outbound connection metadata and byte volumes." },
      { file: "backup-policy.yaml", events: 11, hits: 1, primary: false, description: "Recent policy diff excluding finance archive paths." }
    ],
    evidence: [
      { signal: "Unusual outbound volume", observation: "148GB sent to a low-frequency endpoint in 12 minutes.", contribution: 34 },
      { signal: "Backup exclusion modified", observation: "Sensitive archive path removed minutes before transfer.", contribution: 23 },
      { signal: "Destination reputation drift", observation: "Endpoint not seen in the last 30 days of baseline traffic.", contribution: 18 }
    ],
    riskBreakdown: [
      { label: "Egress anomaly", value: 42, color: "var(--error)" },
      { label: "Policy tampering", value: 27, color: "var(--primary)" },
      { label: "Baseline drift", value: 12, color: "var(--tertiary-container)" }
    ],
    confidenceReasons: [
      "Traffic pattern diverges from scheduled backup windows.",
      "Policy change materially increases exfiltration suspicion.",
      "Destination lacks historical allowlist coverage."
    ],
    stages: [
      { name: "Collection", sub: "Archive prep", color: "var(--primary)" },
      { name: "Exfiltration", sub: "TLS transfer", color: "var(--error)" }
    ],
    impact: [
      { label: "Likelihood", value: "High", tone: "danger" },
      { label: "Data sensitivity", value: "Payment archive", tone: "danger" },
      { label: "Containment effort", value: "Medium", tone: "warning" },
      { label: "Operational impact", value: "Node can be failed over", tone: "neutral" }
    ],
    actions: [
      { name: "Block destination IP", why: "Stops the active outbound stream immediately.", urgency: "High" },
      { name: "Snapshot db-prod-01", why: "Preserves volatile evidence before containment.", urgency: "Medium" },
      { name: "Restore backup policy", why: "Reinstate guardrails around sensitive paths.", urgency: "Medium" }
    ],
    logs: [
      "14:10:02Z  gitops       backup-policy.yaml changed by svc_automation",
      "14:11:14Z  zeek         db-prod-01 -> 52.216.146.19:443 sent=148GB",
      "14:11:28Z  auditd       tar process touched finance/archive/quarterly",
      "14:12:01Z  dns          lookup for uncommon cloud endpoint completed"
    ]
  },
  {
    id: "INC-003",
    title: "Backup workflow or ransomware staging ambiguity",
    severity: "uncertain",
    risk: 55,
    confidence: 45,
    who: "svc_jenkins",
    environment: "Jenkins host · Backup lane",
    time: "03:06 UTC",
    summary:
      "A Jenkins backup workflow deleted shadow copies and created a large encrypted archive, which is consistent with both legitimate backup behavior and early ransomware staging.",
    tags: ["Uncertain", "Backup", "VSS Delete"],
    sources: [
      { file: "jenkins-nightly.log", events: 208, hits: 6, primary: true, description: "Job orchestration and process execution details." },
      { file: "aws-egress.log", events: 96, hits: 2, primary: false, description: "Outbound transfer to an AWS endpoint that may be owned internally." }
    ],
    evidence: [
      { signal: "Shadow copy deletion", observation: "vssadmin delete shadows executed in backup context.", contribution: 22 },
      { signal: "Encrypted archive created", observation: "Finance_Data_20260327.aes256 written to staging disk.", contribution: 19 },
      { signal: "Large AWS transfer", observation: "150GB sent to 52.216.146.19 over TLS.", contribution: 14 }
    ],
    riskBreakdown: [
      { label: "Potential ransomware behavior", value: 35, color: "var(--tertiary-container)" },
      { label: "Legitimate automation context", value: 30, color: "var(--primary)" },
      { label: "Unverified destination", value: 20, color: "var(--outline)" }
    ],
    confidenceReasons: [
      "Automation context weakens the malicious hypothesis.",
      "AWS ownership remains unresolved.",
      "More evidence is needed before containment."
    ],
    stages: [
      { name: "Unknown Intent", sub: "Backup or ransomware?", color: "var(--tertiary-container)" }
    ],
    impact: [
      { label: "Likelihood", value: "Uncertain (55%)", tone: "warning" },
      { label: "If malicious", value: "Finance data encrypted", tone: "danger" },
      { label: "If benign", value: "Routine backup", tone: "success" },
      { label: "Resolution time", value: "~10 minutes", tone: "neutral" }
    ],
    actions: [
      { name: "Verify AWS bucket ownership", why: "Most direct way to resolve the ambiguity.", urgency: "Medium" },
      { name: "Check encryption key custody", why: "Corporate key confirms backup workflow.", urgency: "Medium" },
      { name: "Review Jenkins job config", why: "Confirms whether VSS deletion is documented.", urgency: "Low" }
    ],
    logs: [
      "02:00:15Z  sysmon/1     Nightly-CloudBackup.ps1 launched by jenkins.exe",
      "02:05:00Z  sysmon/1     vssadmin delete shadows /for=c: /oldest",
      "03:05:10Z  sysmon/11    Finance_Data_20260327.aes256 created",
      "03:06:00Z  zeek         150GB transferred to 52.216.146.19:443"
    ]
  }
];
