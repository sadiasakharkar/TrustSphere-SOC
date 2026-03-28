const STORAGE_KEY = "trustsphere-live-analysis";

function toneForClassification(classification) {
  if (classification === "True Positive") return "critical";
  if (classification === "False Positive") return "uncertain";
  return "high";
}

function severityFromRow(row) {
  const severity = String(row.severity || "low").toLowerCase();
  if (severity === "critical") return "critical";
  if (severity === "high") return "high";
  return toneForClassification(row.classification);
}

function riskBreakdown(row) {
  const confidence = Number(row.confidence || 0);
  const anomaly = Number(row.anomalyScore || 0);
  const rule = Math.min(100, Math.round(confidence * 0.45));
  const behavior = Math.min(100 - rule, Math.round(anomaly * 0.35));
  const context = Math.max(0, Math.min(100 - rule - behavior, Math.round((confidence + anomaly) * 0.1)));
  return [
    { label: "Prefilter score", value: rule, color: "var(--primary)" },
    { label: "Behavior anomaly", value: behavior, color: "var(--error)" },
    { label: "Context weighting", value: context, color: "var(--tertiary-container)" },
  ];
}

function confidenceReasons(row, payload) {
  return [
    `${row.source} generated a ${row.status} event inside ${payload.fileName}.`,
    `The ML prefilter assigned ${row.confidence}% confidence with ${row.anomalyScore}% anomaly pressure.`,
    `Normalized severity is ${row.severity}, so the event remains tied to this uploaded file for analyst review.`,
  ];
}

function attackStages(row) {
  const source = String(row.source || "telemetry").toLowerCase();
  const status = String(row.status || "observed");
  if (source.includes("azure") || source.includes("office") || source.includes("auth")) {
    return [
      { name: "Initial Access", sub: status, color: "var(--primary)" },
      { name: "Credential Abuse", sub: "Identity activity", color: "var(--error)" },
    ];
  }
  if (source.includes("sysmon") || source.includes("endpoint") || source.includes("file")) {
    return [
      { name: "Execution", sub: status, color: "var(--primary)" },
      { name: "Host Analysis", sub: "Endpoint telemetry", color: "var(--tertiary-container)" },
    ];
  }
  return [
    { name: "Detection", sub: status, color: "var(--primary)" },
    { name: "Network Review", sub: "Traffic inspection", color: "var(--tertiary-container)" },
  ];
}

function buildIncident(row, payload, index) {
  const severity = severityFromRow(row);
  const risk = Math.max(Number(row.confidence || 0), Number(row.anomalyScore || 0));
  const confidence = Math.round((Number(row.confidence || 0) * 0.6) + (Number(row.anomalyScore || 0) * 0.4));
  const tagList = [row.source, row.classification, row.status].filter(Boolean);

  return {
    id: `INC-${String(index + 1).padStart(3, "0")}`,
    title: `${row.status} detected in ${payload.fileName}`,
    severity,
    risk,
    confidence,
    who: payload.fileName,
    environment: `${payload.domain} telemetry · ${payload.datasetId}`,
    time: "Current batch",
    summary: `${row.source} generated a ${row.status} event that was classified as ${row.classification}. This record comes directly from ${payload.fileName} and remains linked to the uploaded package for analyst review.`,
    tags: tagList,
    sources: [
      {
        file: payload.fileName,
        events: payload.rows.length,
        hits: 1,
        primary: true,
        description: `Uploaded package analyzed through the live TrustSphere ML ingestion path.`,
      },
    ],
    evidence: [
      { signal: "Classification", observation: row.classification, contribution: Math.min(100, Math.max(10, Number(row.confidence || 0))) },
      { signal: "Behavior anomaly", observation: `${row.anomalyScore}% anomaly score`, contribution: Math.min(100, Math.max(10, Number(row.anomalyScore || 0))) },
      { signal: "Severity", observation: row.severity, contribution: severity === "critical" ? 85 : severity === "high" ? 65 : 35 },
    ],
    riskBreakdown: riskBreakdown(row),
    confidenceReasons: confidenceReasons(row, payload),
    stages: attackStages(row),
    impact: [
      { label: "Source file", value: payload.fileName, tone: "neutral" },
      { label: "Classification", value: row.classification, tone: severity === "critical" ? "danger" : "warning" },
      { label: "Anomaly score", value: `${row.anomalyScore}%`, tone: "warning" },
      { label: "Severity", value: row.severity, tone: severity === "critical" ? "danger" : "neutral" },
    ],
    actions: [
      { name: "Review raw uploaded record", why: "Confirms the exact source event tied to this package.", urgency: "High" },
      { name: "Correlate with surrounding rows", why: "Checks whether adjacent entries in the same file form a larger incident.", urgency: "Medium" },
      { name: "Escalate if pattern repeats", why: "Reduces noise while preserving the strongest signals from this upload.", urgency: "Low" },
    ],
    logs: [
      `file=${payload.fileName}`,
      `source=${row.source}`,
      `status=${row.status}`,
      `classification=${row.classification}`,
      `confidence=${row.confidence}% anomaly=${row.anomalyScore}% severity=${row.severity}`,
    ],
  };
}

export function saveLiveAnalysis(payload) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

export function loadLiveAnalysis() {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function payloadToTerminalIncidents(payload) {
  if (!payload?.rows?.length) return [];
  return payload.rows.map((row, index) => buildIncident(row, payload, index));
}

export function payloadSummary(payload) {
  if (!payload) return null;
  return {
    fileName: payload.fileName,
    datasetId: payload.datasetId,
    domain: payload.domain,
    terminal: payload.terminal || [],
    incidents: payloadToTerminalIncidents(payload),
  };
}
