import AppShell from "@/components/AppShell";
import D3LineChart from "@/components/D3LineChart";
import MaterialIcon from "@/components/MaterialIcon";
import { eventTrend, monitoringStats, normalizedRows } from "@/lib/data";

function classificationTone(name) {
  if (name === "True Positive") return "tone-primary";
  if (name === "False Positive") return "tone-error";
  return "tone-muted";
}

export default function MonitoringPage() {
  return (
    <AppShell
      eyebrow="Step 2: Monitoring & Ingestion"
      title="Live Ingestion."
      description="Upload log packages for normalization and heuristic pre-filtering. TrustSphere handles multi-source ingestion including Sysmon, Azure AD, and cloud events."
      actions={
        <>
          <button className="secondary-button" type="button">Upload Logs</button>
          <button className="secondary-button" type="button">Start Simulation</button>
          <button className="secondary-button" type="button">Terminal View</button>
        </>
      }
    >
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
              <h3>Event Volume Pulse</h3>
              <p>Real-time D3 chart for intake rate, suspicious detections, and filtered noise.</p>
            </div>
            <span className="pill">se4.json</span>
          </div>
          <D3LineChart data={eventTrend} />
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
