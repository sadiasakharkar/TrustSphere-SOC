"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { incidents } from "@/lib/data";

export default function IncidentsPage() {
  const router = useRouter();
  const [statusFilter, setStatusFilter] = useState("active");

  const filteredIncidents = useMemo(() => {
    if (statusFilter === "active") {
      return incidents.filter((incident) => incident.severity !== "Low");
    }
    if (statusFilter === "resolved") {
      return incidents.filter((incident) => incident.severity === "Low");
    }
    return [];
  }, [statusFilter]);

  return (
    <AppShell
      title="Incident Queue"
      description="Monitoring real-time threats across the infrastructure, filtered by active level 3 analyst protocols."
      actions={
        <div className="segment-control">
          <button className={`segment ${statusFilter === "active" ? "active" : ""}`} onClick={() => setStatusFilter("active")} type="button">Active</button>
          <button className={`segment ${statusFilter === "resolved" ? "active" : ""}`} onClick={() => setStatusFilter("resolved")} type="button">Resolved</button>
          <button className={`segment ${statusFilter === "archived" ? "active" : ""}`} onClick={() => setStatusFilter("archived")} type="button">Archived</button>
        </div>
      }
    >
      <section className="incident-top-grid">
        <article className="mini-stat">
          <span>Critical Alerts</span>
          <strong className="error-copy">04</strong>
          <p>+2 since last hour</p>
        </article>
        <article className="mini-stat">
          <span>Mean Time to Resolve</span>
          <strong className="primary-copy">14m</strong>
          <p>Below threshold</p>
        </article>
        <article className="network-banner">
          <span>Network Health</span>
          <strong>Stable Performance</strong>
        </article>
      </section>

      <section className="incident-list">
        {filteredIncidents.map((incident) => (
          <article
            key={`${incident.title}-${incident.time}`}
            className="incident-card"
            style={{ "--accent": incident.accent }}
          >
            <div className="incident-main">
              <div className="severity-tag">{incident.severity}</div>
              <h3>{incident.title}</h3>
              <div className="incident-meta">
                <span>{incident.entity}</span>
                <span>{incident.risk}</span>
                <span>{incident.confidence}</span>
                <span>{incident.stage}</span>
              </div>
              <p>{incident.summary}</p>
            </div>
            <div className="incident-side">
              <time>{incident.time}</time>
              <button className="secondary-button" onClick={() => router.push("/terminal")} type="button">Investigate</button>
            </div>
          </article>
        ))}
        {!filteredIncidents.length ? (
          <article className="incident-card" style={{ "--accent": "var(--outline)" }}>
            <div className="incident-main">
              <div className="severity-tag">Info</div>
              <h3>No incidents in this queue</h3>
              <p>The selected queue is empty right now.</p>
            </div>
          </article>
        ) : null}
      </section>
    </AppShell>
  );
}
