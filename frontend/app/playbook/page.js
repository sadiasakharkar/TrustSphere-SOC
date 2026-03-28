import AppShell from "@/components/AppShell";
import D3RiskDonut from "@/components/D3RiskDonut";
import { evidenceTimeline, riskBreakdown } from "@/lib/data";

export default function PlaybookPage() {
  return (
    <AppShell
      eyebrow="Step 5: Final Playbook Output"
      title="Requires Human Approval"
      description="Case ID: #SOC-882-QX. Automated mitigation is paused for mandatory override because the model detected patterns consistent with payment manipulation."
    >
      <section className="playbook-grid">
        <div className="playbook-main">
          <article className="wide-card narrative-card">
            <div className="card-header">
              <div>
                <h3>AI Intelligence Report</h3>
                <p>Editorial summary built for a security analyst rather than an engineering log reader.</p>
              </div>
              <span className="pill warm">Critical Escalation</span>
            </div>
            <p className="narrative-copy">
              The system detected atypical transaction velocities originating from a legacy VPN node.
              While the credentials are valid, the behavior pattern matches known payment manipulation
              techniques where high-value items are moved during low-traffic windows. Human approval is
              required because the affected account has high financial and reputational sensitivity.
            </p>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>Recommended Response Actions</h3>
                <p>Prioritized actions ready for analyst approval.</p>
              </div>
            </div>
            <div className="action-list">
              <div className="action-row">
                <div>
                  <strong>Lock account</strong>
                  <p>Full identity quarantine to prevent lateral escalation.</p>
                </div>
                <span className="table-chip tone-error">High</span>
              </div>
              <div className="action-row">
                <div>
                  <strong>Flush Session Tokens</strong>
                  <p>Invalidate active sessions and browser cookies.</p>
                </div>
                <span className="table-chip tone-primary">Medium</span>
              </div>
              <div className="action-row">
                <div>
                  <strong>Audit Transaction Log</strong>
                  <p>Confirm manipulation attempt with historical comparison.</p>
                </div>
                <span className="table-chip tone-muted">Low</span>
              </div>
            </div>
          </article>
        </div>

        <aside className="playbook-side">
          <article className="wide-card donut-card">
            <D3RiskDonut data={riskBreakdown} />
            <div className="legend-list">
              {riskBreakdown.map((item) => (
                <div key={item.label} className="legend-item">
                  <span className="legend-dot" style={{ background: item.color }} />
                  <span>{item.label}</span>
                  <strong>{item.value}%</strong>
                </div>
              ))}
            </div>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>Evidence Proof</h3>
                <p>Signal timeline supporting the final recommendation.</p>
              </div>
            </div>
            <div className="timeline-list">
              {evidenceTimeline.map((entry) => (
                <div key={entry.title} className="timeline-item">
                  <span className="timeline-dot" style={{ background: entry.color }} />
                  <div>
                    <strong>{entry.title}</strong>
                    <p>{entry.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <div className="stacked-actions">
            <button className="primary-button full-width" type="button">Approve & Execute Mitigation</button>
            <button className="secondary-button full-width" type="button">Dismiss as False Positive</button>
            <button className="ghost-button full-width" type="button">Send to Fraud Investigation</button>
          </div>
        </aside>
      </section>
    </AppShell>
  );
}
