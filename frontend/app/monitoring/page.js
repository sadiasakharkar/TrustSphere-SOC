"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import MaterialIcon from "@/components/MaterialIcon";
import { saveLiveAnalysis } from "@/lib/liveAnalysis";

function classificationTone(name) {
  if (name === "True Positive") return "tone-primary";
  if (name === "False Positive") return "tone-error";
  return "tone-muted";
}

const defaultTerminal = [
  "[SYSTEM] Initializing intake stream...",
  "> Awaiting uploaded log package...",
  "> Live ingestion pipeline ready",
  "> Prefilter model and anomaly scorer loaded",
];

export default function MonitoringPage() {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [stats, setStats] = useState([]);
  const [rows, setRows] = useState([]);
  const [terminalLines, setTerminalLines] = useState(defaultTerminal);

  async function handleSimulation() {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/ingestion", { method: "GET" });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Unable to run simulation.");
      }
      saveLiveAnalysis(data);
      setSelectedFile(data.fileName || "Simulation");
      setStats(data.stats || []);
      setRows(data.rows || []);
      setTerminalLines(data.terminal || defaultTerminal);
    } catch (simulationError) {
      setError(simulationError.message || "Unable to run simulation.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file) {
    if (!file) return;
    setSelectedFile(file.name);
    setLoading(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("/api/ingestion", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Unable to process uploaded logs.");
      }
      saveLiveAnalysis(data);
      setStats(data.stats || []);
      setRows(data.rows || []);
      setTerminalLines(data.terminal || defaultTerminal);
    } catch (uploadError) {
      setError(uploadError.message || "Unable to process uploaded logs.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell
      eyebrow="Step 2: Monitoring & Ingestion"
      title="Live Ingestion."
      description="Upload log packages for normalization and heuristic pre-filtering. TrustSphere handles multi-source ingestion including Sysmon, Azure AD, and cloud events."
      actions={
        <>
          <button
            className="secondary-button"
            disabled={loading}
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            {loading ? "Processing..." : "Upload Logs"}
          </button>
          <input
            accept=".json,.csv,.xlsx,.syslog,.log,application/json,text/csv"
            className="hidden-file-input"
            onChange={(event) => handleUpload(event.target.files?.[0])}
            ref={fileInputRef}
            type="file"
          />
          <button className="secondary-button" disabled={loading} onClick={handleSimulation} type="button">
            Start Simulation
          </button>
          <Link className="secondary-button" href="/terminal">Terminal View</Link>
        </>
      }
    >
      {selectedFile ? (
        <section className="wide-card selected-file-banner">
          <div className="card-header compact">
            <div>
              <h3>Selected Upload</h3>
              <p>{selectedFile}</p>
            </div>
            <span className="pill">{loading ? "Running" : "Processed"}</span>
          </div>
        </section>
      ) : null}

      {error ? (
        <section className="wide-card selected-file-banner">
          <div className="card-header compact">
            <div>
              <h3>Pipeline Error</h3>
              <p>{error}</p>
            </div>
            <span className="pill warm">Check Input</span>
          </div>
        </section>
      ) : null}

      {stats.length ? (
        <section className="stats-grid">
          {stats.map((stat) => (
            <article key={stat.label} className="stat-card" style={{ "--accent": stat.accent }}>
              <div className="stat-top">
                <span>{stat.label}</span>
                <MaterialIcon name={stat.icon} filled className="accent-icon" />
              </div>
              <strong>{stat.value}</strong>
              <p>{stat.note}</p>
            </article>
          ))}
        </section>
      ) : (
        <section className="wide-card selected-file-banner">
          <div className="card-header compact">
            <div>
              <h3>No Live Analysis Yet</h3>
              <p>Upload a log package or start a simulation to render ML-calculated prefilter metrics.</p>
            </div>
            <span className="pill">Awaiting File</span>
          </div>
        </section>
      )}

      <section className="content-grid side-only">
        <aside className="side-column">
          <article className="journey-card">
            <p className="mini-title">Simulation Journey</p>
            <div className="journey-step active">
              <span>01</span>
              <div>
                <strong>System Configuration</strong>
                <p>Connected to live normalization and prefilter models.</p>
              </div>
            </div>
            <div className="journey-step active current">
              <span>02</span>
              <div>
                <strong>Live Monitoring</strong>
                <p>Uploaded package is being scored by TrustSphere models.</p>
              </div>
            </div>
            <div className="journey-step">
              <span>03</span>
              <div>
                <strong>Incident Queue</strong>
                <p>Escalate suspicious clusters for analyst review.</p>
              </div>
            </div>
          </article>

          <article className="terminal-card">
            <div className="terminal-lights">
              <span />
              <span />
              <span />
            </div>
            {terminalLines.map((line) => (
              <p key={line}>{line}</p>
            ))}
            <p className="cursor">_</p>
          </article>
        </aside>
      </section>

      <section className="wide-card table-card">
        <div className="card-header">
          <div>
            <h3>Prefilter Normalization Results</h3>
            <p>Classification-ready rows prepared by the live TrustSphere pipeline.</p>
          </div>
          <button className="primary-button" onClick={handleSimulation} type="button">
            Refresh Live Results
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Source</th>
                <th>Status</th>
                <th>Classification</th>
                <th>Confidence</th>
                <th>Anomaly</th>
                <th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {rows.length ? (
                rows.map((row) => (
                  <tr key={row.id}>
                    <td className="mono">{row.id}</td>
                    <td>{row.source}</td>
                    <td>{row.status}</td>
                    <td>
                      <span className={`table-chip ${classificationTone(row.classification)}`}>
                        {row.classification}
                      </span>
                    </td>
                    <td>
                      <div className="meter">
                        <div className="meter-fill" style={{ width: `${row.confidence}%` }} />
                      </div>
                    </td>
                    <td>
                      <div className="meter">
                        <div className="meter-fill" style={{ width: `${row.anomalyScore ?? 0}%` }} />
                      </div>
                    </td>
                    <td>{row.severity}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td className="mono" colSpan="7">
                    No real prefilter output yet. Upload a file to display normalized rows, classifications,
                    confidence, and anomaly scores from the ML pipeline.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
