"use client";

import { useMemo, useState } from "react";
import AppShell from "@/components/AppShell";
import { analystIncidents } from "@/lib/data";

const TABS = ["Triage", "Investigation", "Closed"];

function severityTone(severity) {
  if (severity === "critical") return "danger";
  if (severity === "high") return "warning";
  return "uncertain";
}

export default function TerminalPage() {
  const [tab, setTab] = useState("Triage");
  const [filter, setFilter] = useState("all");
  const [selectedId, setSelectedId] = useState(analystIncidents[0]?.id ?? null);
  const [modalOpen, setModalOpen] = useState(false);
  const [approvedActions, setApprovedActions] = useState({});

  const filteredIncidents = useMemo(() => {
    if (filter === "all") return analystIncidents;
    return analystIncidents.filter((incident) => incident.severity === filter);
  }, [filter]);

  const selectedIncident =
    filteredIncidents.find((incident) => incident.id === selectedId) ??
    filteredIncidents[0] ??
    null;

  function approveAction(incidentId, actionName) {
    setApprovedActions((current) => ({
      ...current,
      [`${incidentId}:${actionName}`]: true
    }));
  }

  const summaryCounts = {
    all: analystIncidents.length,
    critical: analystIncidents.filter((incident) => incident.severity === "critical").length,
    high: analystIncidents.filter((incident) => incident.severity === "high").length,
    uncertain: analystIncidents.filter((incident) => incident.severity === "uncertain").length
  };

  return (
    <AppShell
      eyebrow="Analyst Workflow"
      title="Analyst Terminal"
      description="Investigation and triage workspace for active TrustSphere incidents, adapted from the analyst HTML view into the current frontend."
    >
      <section className="analyst-terminal">
        <div className="terminal-topbar">
          <div className="terminal-tabs">
            {TABS.map((tabName) => (
              <button
                key={tabName}
                className={`terminal-tab ${tab === tabName ? "active" : ""}`}
                onClick={() => setTab(tabName)}
                type="button"
              >
                {tabName}
              </button>
            ))}
          </div>
          <div className="terminal-status">
            <span>SOC-Tier2 · Shift 09:00-17:00</span>
            <span className="terminal-live">LIVE</span>
          </div>
        </div>

        <div className="terminal-layout">
          <aside className="terminal-list-panel">
            <div className="terminal-list-head">
              <div>
                <h3>Active Incidents</h3>
                <p>{filteredIncidents.length} incidents</p>
              </div>
              <div className="terminal-summary-row">
                <button
                  className={`terminal-summary ${filter === "all" ? "active" : ""}`}
                  onClick={() => setFilter("all")}
                  type="button"
                >
                  <strong>{summaryCounts.all}</strong>
                  <span>All</span>
                </button>
                <button
                  className={`terminal-summary ${filter === "critical" ? "active" : ""}`}
                  onClick={() => setFilter("critical")}
                  type="button"
                >
                  <strong>{summaryCounts.critical}</strong>
                  <span>Critical</span>
                </button>
                <button
                  className={`terminal-summary ${filter === "high" ? "active" : ""}`}
                  onClick={() => setFilter("high")}
                  type="button"
                >
                  <strong>{summaryCounts.high}</strong>
                  <span>High</span>
                </button>
                <button
                  className={`terminal-summary ${filter === "uncertain" ? "active" : ""}`}
                  onClick={() => setFilter("uncertain")}
                  type="button"
                >
                  <strong>{summaryCounts.uncertain}</strong>
                  <span>Uncertain</span>
                </button>
              </div>
            </div>

            <div className="terminal-incident-list">
              {filteredIncidents.map((incident) => (
                <button
                  key={incident.id}
                  className={`terminal-incident-card ${selectedIncident?.id === incident.id ? "selected" : ""} ${severityTone(incident.severity)}`}
                  onClick={() => setSelectedId(incident.id)}
                  type="button"
                >
                  <div className="terminal-incident-header">
                    <h4>{incident.title}</h4>
                    <strong>{incident.risk}%</strong>
                  </div>
                  <p>{incident.who}</p>
                  <div className="terminal-incident-footer">
                    <div className="terminal-tag-list">
                      {incident.tags.map((tag) => (
                        <span key={tag} className="terminal-tag">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <time>{incident.time}</time>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <section className="terminal-detail-panel">
            {selectedIncident ? (
              <>
                <div className="terminal-detail-head">
                  <div>
                    <span className="terminal-incident-id">
                      {selectedIncident.id} · {selectedIncident.who}
                    </span>
                    <h2>{selectedIncident.title}</h2>
                    <div className="terminal-detail-meta">
                      <span>{selectedIncident.environment}</span>
                      <span>{selectedIncident.risk}% risk</span>
                      <span>{selectedIncident.confidence}% confidence</span>
                    </div>
                  </div>
                  <div className="terminal-detail-actions">
                    <button className="secondary-button" onClick={() => setModalOpen(true)} type="button">
                      View Source Files
                    </button>
                    <button className="primary-button" type="button">
                      Escalate
                    </button>
                  </div>
                </div>

                <div className="terminal-source-trail">
                  <span>Driven By</span>
                  {selectedIncident.sources.map((source) => (
                    <button
                      key={source.file}
                      className={`terminal-source-chip ${source.primary ? "primary" : ""}`}
                      onClick={() => setModalOpen(true)}
                      type="button"
                    >
                      {source.file}
                      <small>
                        {source.hits}/{source.events} events
                      </small>
                    </button>
                  ))}
                </div>

                <div className="terminal-detail-scroll">
                  <article className="terminal-section">
                    <div className="terminal-section-head">
                      <span>What Happened</span>
                    </div>
                    <div className="terminal-section-body">
                      <p>{selectedIncident.summary}</p>
                    </div>
                  </article>

                  <article className="terminal-section">
                    <div className="terminal-section-head">
                      <span>Evidence</span>
                      <small>Signal contribution to risk</small>
                    </div>
                    <div className="terminal-section-body">
                      <div className="terminal-evidence-list">
                        {selectedIncident.evidence.map((item) => (
                          <div key={item.signal} className="terminal-evidence-row">
                            <div>
                              <strong>{item.signal}</strong>
                              <p>{item.observation}</p>
                            </div>
                            <div className="terminal-evidence-bar">
                              <div
                                className={`terminal-evidence-fill ${severityTone(selectedIncident.severity)}`}
                                style={{ width: `${item.contribution}%` }}
                              />
                            </div>
                            <span>+{item.contribution}%</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </article>

                  <div className="terminal-two-up">
                    <article className="terminal-section">
                      <div className="terminal-section-head">
                        <span>Risk Score</span>
                      </div>
                      <div className="terminal-section-body">
                        <div className="terminal-big-score">{selectedIncident.risk}%</div>
                        <div className="terminal-breakdown">
                          {selectedIncident.riskBreakdown.map((item) => (
                            <div key={item.label} className="terminal-breakdown-row">
                              <span>{item.label}</span>
                              <div className="terminal-breakdown-track">
                                <div
                                  className="terminal-breakdown-fill"
                                  style={{ width: `${item.value}%`, background: item.color }}
                                />
                              </div>
                              <strong>{item.value}%</strong>
                            </div>
                          ))}
                        </div>
                      </div>
                    </article>

                    <article className="terminal-section">
                      <div className="terminal-section-head">
                        <span>Confidence</span>
                      </div>
                      <div className="terminal-section-body">
                        <div className="terminal-confidence">{selectedIncident.confidence}%</div>
                        <div className="terminal-reason-list">
                          {selectedIncident.confidenceReasons.map((reason) => (
                            <p key={reason}>{reason}</p>
                          ))}
                        </div>
                      </div>
                    </article>
                  </div>

                  <article className="terminal-section">
                    <div className="terminal-section-head">
                      <span>Attack Stages</span>
                    </div>
                    <div className="terminal-section-body">
                      <div className="terminal-stage-list">
                        {selectedIncident.stages.map((stage) => (
                          <div key={stage.name} className="terminal-stage-node">
                            <span className="terminal-stage-dot" style={{ background: stage.color }} />
                            <div>
                              <strong>{stage.name}</strong>
                              <p>{stage.sub}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </article>

                  <article className="terminal-section">
                    <div className="terminal-section-head">
                      <span>Business Impact</span>
                    </div>
                    <div className="terminal-section-body">
                      <div className="terminal-impact-grid">
                        {selectedIncident.impact.map((item) => (
                          <div key={item.label} className="terminal-impact-card">
                            <span>{item.label}</span>
                            <strong className={`tone-${item.tone}`}>{item.value}</strong>
                          </div>
                        ))}
                      </div>
                    </div>
                  </article>

                  <article className="terminal-section">
                    <div className="terminal-section-head">
                      <span>Recommended Actions</span>
                    </div>
                    <div className="terminal-section-body">
                      <div className="terminal-action-list">
                        {selectedIncident.actions.map((action) => {
                          const approved = approvedActions[`${selectedIncident.id}:${action.name}`];

                          return (
                            <div key={action.name} className="terminal-action-row">
                              <div>
                                <strong>{action.name}</strong>
                                <p>{action.why}</p>
                              </div>
                              <div className="terminal-action-controls">
                                <span className={`terminal-urgency ${action.urgency.toLowerCase()}`}>
                                  {action.urgency}
                                </span>
                                <button
                                  className={`terminal-approve ${approved ? "done" : ""}`}
                                  disabled={approved}
                                  onClick={() => approveAction(selectedIncident.id, action.name)}
                                  type="button"
                                >
                                  {approved ? "Approved" : "Approve"}
                                </button>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </article>
                </div>
              </>
            ) : (
              <div className="terminal-empty">
                <h3>No incidents in this filter</h3>
                <p>Choose another severity filter or return to the monitoring dashboard.</p>
              </div>
            )}
          </section>
        </div>

        {modalOpen && selectedIncident ? (
          <div className="terminal-modal-overlay" onClick={() => setModalOpen(false)}>
            <div className="terminal-modal" onClick={(event) => event.stopPropagation()}>
              <div className="terminal-modal-head">
                <div>
                  <h3>Source Files for {selectedIncident.id}</h3>
                  <p>
                    {selectedIncident.sources.length} files ·{" "}
                    {selectedIncident.sources.reduce((total, source) => total + source.events, 0)} events
                  </p>
                </div>
                <button className="ghost-button" onClick={() => setModalOpen(false)} type="button">
                  Close
                </button>
              </div>
              <div className="terminal-modal-body">
                {selectedIncident.sources.map((source) => (
                  <article key={source.file} className="terminal-modal-source">
                    <div className="terminal-modal-source-head">
                      <div>
                        <strong>{source.file}</strong>
                        <p>{source.description}</p>
                      </div>
                      <span>{source.hits}/{source.events} flagged</span>
                    </div>
                    <div className="terminal-log-list">
                      {selectedIncident.logs.map((line) => (
                        <code key={`${source.file}-${line}`}>{line}</code>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        ) : null}
      </section>
    </AppShell>
  );
}
