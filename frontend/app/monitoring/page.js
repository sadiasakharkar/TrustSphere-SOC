"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import AppShell from "@/components/AppShell";
import MaterialIcon from "@/components/MaterialIcon";
import { monitoringControlPanel, monitoringStats, normalizedRows } from "@/lib/data";

function classificationTone(name) {
  if (name === "True Positive") return "tone-primary";
  if (name === "False Positive") return "tone-error";
  return "tone-muted";
}

export default function MonitoringPage() {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState("");

  return (
    <AppShell
      eyebrow="Step 2: Monitoring & Ingestion"
      title="Live Ingestion."
      description="Upload log packages for normalization and heuristic pre-filtering. TrustSphere handles multi-source ingestion including Sysmon, Azure AD, and cloud events."
      actions={
        <>
          <button
            className="secondary-button"
            onClick={() => fileInputRef.current?.click()}
            type="button"
          >
            Upload Logs
          </button>
          <input
            accept=".json,.csv,application/json,text/csv"
            className="hidden-file-input"
            onChange={(event) => {
              const file = event.target.files?.[0];
              setSelectedFile(file ? file.name : "");
            }}
            ref={fileInputRef}
            type="file"
          />
          <button className="secondary-button" type="button">Start Simulation</button>
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
            <span className="pill">Ready</span>
          </div>
        </section>
      ) : null}

      <section className="stats-grid">
        {monitoringStats.map((stat) => (
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

      <section className="content-grid">
        <article className="wide-card">
          <div className="card-header">
            <div>
              <h3>Ingestion Command Center</h3>
              <p>Operational context for analysts before incident generation, without repeating the top-level dashboard stats.</p>
            </div>
            <span className="pill">se4.json</span>
          </div>
          <div className="command-center-grid">
            <section className="command-card">
              <div className="command-card-head">
                <h4>Source Health</h4>
                <p>Live parser and stream readiness.</p>
              </div>
              <div className="source-health-list">
                {monitoringControlPanel.sourceHealth.map((item) => (
                  <div key={item.source} className="source-health-row">
                    <div>
                      <strong>{item.source}</strong>
                      <p>{item.events}</p>
                    </div>
                    <div className="source-health-meta">
                      <span className={`health-pill ${item.tone}`}>{item.status}</span>
                      <small>{item.lag}</small>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="command-card">
              <div className="command-card-head">
                <h4>Parser Readiness</h4>
                <p>What is ready to classify right now.</p>
              </div>
              <div className="readiness-list">
                {monitoringControlPanel.parserReadiness.map((item) => (
                  <div key={item.label} className="readiness-item">
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                    <p>{item.detail}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="command-card">
              <div className="command-card-head">
                <h4>Next Analyst Actions</h4>
                <p>Recommended checks before escalation.</p>
              </div>
              <div className="action-note-list">
                {monitoringControlPanel.nextActions.map((item) => (
                  <div key={item} className="action-note">
                    <span />
                    <p>{item}</p>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>

        <aside className="side-column">
          <article className="journey-card">
            <p className="mini-title">Simulation Journey</p>
            <div className="journey-step active">
              <span>01</span>
              <div>
                <strong>System Configuration</strong>
                <p>Connect tenant, sources, and analyst profile.</p>
              </div>
            </div>
            <div className="journey-step active current">
              <span>02</span>
              <div>
                <strong>Live Monitoring</strong>
                <p>Prefiltering 3.4k events/sec across active streams.</p>
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
            <p>[SYSTEM] Initializing intake stream...</p>
            <p>{">"} Loading se4.json [OK]</p>
            <p>{">"} Normalizing logs... 1024/1024</p>
            <p>{">"} Pattern match: Suspicious_PowerShell</p>
            <p className="primary-copy">{">"} Applied prefilter policy: Default_v2</p>
            <p className="cursor">_</p>
          </article>
        </aside>
      </section>

      <section className="wide-card table-card">
        <div className="card-header">
          <div>
            <h3>Prefilter Normalization Results</h3>
            <p>Classification-ready rows prepared for incident generation.</p>
          </div>
          <button className="primary-button" type="button">Generate Incidents</button>
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
              </tr>
            </thead>
            <tbody>
              {normalizedRows.map((row) => (
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
