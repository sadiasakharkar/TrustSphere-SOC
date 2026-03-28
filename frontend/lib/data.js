export const navItems = [
  { href: "/", label: "Access Control", icon: "lock" },
  { href: "/monitoring", label: "Live Ingestion", icon: "analytics" },
  { href: "/incidents", label: "Incident Queue", icon: "security" },
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
