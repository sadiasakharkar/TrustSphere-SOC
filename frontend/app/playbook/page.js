import AppShell from "@/components/AppShell";
import D3RiskDonut from "@/components/D3RiskDonut";
import { bankingPlaybook } from "@/lib/data";

export default function PlaybookPage() {
  return (
    <AppShell
      eyebrow="Analyst Response Playbook"
      title="Banking Incident Playbook"
      description={`Case ID: ${bankingPlaybook.caseId}. ${bankingPlaybook.status}.`}
    >
      <section className="playbook-grid">
        <div className="playbook-main">
          <article className="wide-card narrative-card">
            <div className="card-header">
              <div>
                <h3>1. Incident Summary</h3>
                <p>Short human-readable explanation of what happened.</p>
              </div>
              <span className="pill warm">{bankingPlaybook.riskLabel} Risk</span>
            </div>
            <p className="narrative-copy">{bankingPlaybook.incidentSummary}</p>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>2. Evidence Panel</h3>
                <p>Transparent proof supporting the incident decision.</p>
              </div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Signal</th>
                    <th>Observation</th>
                    <th>Risk Contribution</th>
                  </tr>
                </thead>
                <tbody>
                  {bankingPlaybook.evidencePanel.map((item) => (
                    <tr key={item.signal}>
                      <td><strong>{item.signal}</strong></td>
                      <td>{item.observation}</td>
                      <td><span className="table-chip tone-error">+{item.contribution}%</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>6. Recommended Actions</h3>
                <p>AI suggests actions, but execution requires human approval.</p>
              </div>
              <span className="pill">Human Approval Only</span>
            </div>
            <div className="action-list">
              {bankingPlaybook.actions.map((action) => (
                <div key={action.title} className="action-row">
                  <div>
                    <strong>{action.title}</strong>
                    <p>{action.impact}</p>
                  </div>
                  <span className={`table-chip ${action.urgency === "High" ? "tone-error" : "tone-primary"}`}>
                    {action.urgency}
                  </span>
                </div>
              ))}
            </div>
            <p className="page-copy" style={{ marginTop: "1rem" }}>
              Requires analyst approval within 60 seconds.
            </p>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>7. Business Impact Estimate</h3>
                <p>Cyber risk translated into business language.</p>
              </div>
            </div>
            <div className="timeline-list">
              {bankingPlaybook.businessImpact.map((item) => (
                <div key={item} className="timeline-item">
                  <span className="timeline-dot" style={{ background: "var(--error)" }} />
                  <div>
                    <strong>Potential Impact</strong>
                    <p>{item}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>8. Explainability</h3>
                <p>Plain-language reasoning based only on observed evidence.</p>
              </div>
            </div>
            <p className="narrative-copy">{bankingPlaybook.explainability}</p>
          </article>
        </div>

        <aside className="playbook-side">
          <article className="wide-card donut-card">
            <D3RiskDonut
              data={bankingPlaybook.riskBreakdown}
              totalValue={`${bankingPlaybook.riskScore}%`}
              totalLabel="Final Risk Score"
            />
            <div className="legend-list">
              {bankingPlaybook.riskBreakdown.map((item) => (
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
                <h3>3. Risk Score Calculation</h3>
                <p>Explainable score breakdown instead of a black-box number.</p>
              </div>
            </div>
            <div className="timeline-list">
              {bankingPlaybook.riskBreakdown.map((item) => (
                <div key={item.label} className="timeline-item">
                  <span className="timeline-dot" style={{ background: item.color }} />
                  <div>
                    <strong>{item.label}</strong>
                    <p>{item.value}% contribution</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>4. Confidence Level</h3>
                <p>Banks separate confidence from raw risk.</p>
              </div>
            </div>
            <div className="legend-list">
              <div className="legend-item">
                <span className="legend-dot" style={{ background: "var(--primary)" }} />
                <span>{bankingPlaybook.confidence.level}</span>
                <strong>{bankingPlaybook.confidence.score}%</strong>
              </div>
            </div>
            <div className="timeline-list" style={{ marginTop: "1rem" }}>
              {bankingPlaybook.confidence.reasons.map((reason) => (
                <div key={reason} className="timeline-item">
                  <span className="timeline-dot" style={{ background: "var(--primary)" }} />
                  <div>
                    <strong>Reason</strong>
                    <p>{reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="wide-card">
            <div className="card-header">
              <div>
                <h3>5. Attack Stage</h3>
                <p>Mapped to the incident lifecycle for analyst context.</p>
              </div>
            </div>
            <p className="narrative-copy">{bankingPlaybook.attackStage}</p>
          </article>

          <div className="stacked-actions">
            <button className="primary-button full-width" type="button">Approve Analyst Actions</button>
            <button className="secondary-button full-width" type="button">Escalate for Manual Review</button>
            <button className="ghost-button full-width" type="button">Mark as False Positive</button>
          </div>
        </aside>
      </section>
    </AppShell>
  );
}
