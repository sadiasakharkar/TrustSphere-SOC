import Link from "next/link";
import MaterialIcon from "@/components/MaterialIcon";

const otp = ["5", "2", "9", "", "", ""];

export default function LoginPage() {
  return (
    <main className="login-page">
      <section className="hero-panel">
        <div className="orb orb-left" />
        <div className="orb orb-right" />
        <div className="hero-content">
          <div className="brand-lockup">
            <MaterialIcon name="security" filled className="hero-brand-icon" />
            <span>TrustSphere</span>
          </div>
          <p className="eyebrow inverse">Editorial Security Platform</p>
          <h1>
            The Digital <span>Vault</span>
          </h1>
          <p className="hero-copy">
            Institutional-grade security operations for the modern banking analyst.
            Monitor, investigate, and respond with precision.
          </p>
          <div className="hero-metrics">
            <div>
              <strong>99.9%</strong>
              <span>Uptime Guarantee</span>
            </div>
            <div>
              <strong>AES-256</strong>
              <span>End-to-End Encryption</span>
            </div>
          </div>
          <div className="trust-chip">
            <MaterialIcon name="verified_user" filled className="chip-icon" />
            <span>SOC-2 Type II Certified Compliance</span>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <div className="panel-stack" />
        <div className="login-card">
          <div>
            <h2>Analyst Portal</h2>
            <p>Provide your credentials to access the secure terminal.</p>
          </div>

          <div className="form-grid">
            <label>
              <span>Work Email</span>
              <div className="input-shell">
                <MaterialIcon name="mail" className="muted-icon" />
                <input defaultValue="analyst@trustsphere.com" type="email" />
              </div>
            </label>

            <label>
              <span>Vault Password</span>
              <div className="input-shell">
                <MaterialIcon name="lock" className="muted-icon" />
                <input defaultValue="secure-enterprise" type="password" />
              </div>
            </label>
          </div>

          <div className="mfa-card">
            <div className="mfa-header">
              <MaterialIcon name="security_update_good" className="primary-icon" />
              <div>
                <p>Multi-Factor Required</p>
                <span>Enter authentication code sent on email.</span>
              </div>
            </div>
            <div className="otp-row">
              {otp.map((digit, index) => (
                <input key={index} defaultValue={digit} maxLength={1} type="text" />
              ))}
            </div>
          </div>

          <Link className="primary-button login-cta" href="/monitoring">
            Access Terminal
            <MaterialIcon name="arrow_forward" />
          </Link>

          <div className="login-meta">
            <span>Forgot password?</span>
            <div className="status-inline">
              <span className="status-dot" />
              <span>System Status: Optimal</span>
            </div>
          </div>

          <div className="device-card">
            <div className="device-icon">
              <MaterialIcon name="devices" filled className="primary-icon" />
            </div>
            <div>
              <p>Device Verification</p>
              <span>Verified: MacBook Pro (London HQ Office)</span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
