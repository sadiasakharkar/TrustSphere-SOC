"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import AppShell from "@/components/AppShell";
import { incidents } from "@/lib/data";

export default function IncidentsPage() {
  const router = useRouter();
  const [queue, setQueue] = useState("active");

  const queueIncidents = useMemo(() => {
    if (queue === "resolved") {
      return incidents.filter((incident) => incident.severity === "Low");
    }
    if (queue === "archived") {
      return [];
    }
    return incidents.filter((incident) => incident.severity !== "Low");
  }, [queue]);

  return (
    <AppShell
      title="Incident Queue"
      description="Monitoring real-time threats across the infrastructure, filtered by active level 3 analyst protocols."
      actions={
        <div className="segment-control">
          <button className={`segment ${queue === "active" ? "active" : ""}`} onClick={() => setQueue("active")} type="button">Active</button>
          <button className={`segment ${queue === "resolved" ? "active" : ""}`} onClick={() => setQueue("resolved")} type="button">Resolved</button>
          <button className={`segment ${queue === "archived" ? "active" : ""}`} onClick={() => setQueue("archived")} type="button">Archived</button>
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
        {queueIncidents.map((incident) => (
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
        {!queueIncidents.length ? (
          <article className="incident-card" style={{ "--accent": "var(--outline)" }}>
            <div className="incident-main">
              <div className="severity-tag">Info</div>
              <h3>No incidents in this queue</h3>
              <p>The selected queue is currently empty.</p>
            </div>
          </article>
        ) : null}
      </section>
    </AppShell>
  );
}
