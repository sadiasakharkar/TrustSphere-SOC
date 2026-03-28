const STORAGE_KEY = "trustsphere-live-analysis";

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

export function payloadSummary(payload) {
  if (!payload) return null;
  return {
    fileName: payload.fileName,
    datasetId: payload.datasetId,
    domain: payload.domain,
    terminal: payload.terminal || [],
    incidents: payload.incidents || [],
  };
}
