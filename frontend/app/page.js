"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const canSubmit =
    email.trim().length > 0 && password.trim().length > 0 && !loading;

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Unable to sign in with those credentials.");
        return;
      }

      router.push("/monitoring");
      router.refresh();
    } catch (fetchError) {
      setError("Unable to connect to the login service.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="simple-login-page">
      <section className="simple-login-brand">
        <div className="simple-login-ambient simple-login-ambient-one" />
        <div className="simple-login-ambient simple-login-ambient-two" />
        <div className="simple-login-grid" />

        <div className="simple-login-brand-copy">
          <p className="simple-login-kicker">Banking SOC Co-Pilot</p>
          <h1>TrustSphere</h1>
          <p className="simple-login-description">
            Normalize raw telemetry, prioritize incidents, and generate analyst-first
            response playbooks through a secure offline pipeline.
          </p>

          <div className="simple-login-signal-row">
            <article className="simple-login-signal-card">
              <strong>Offline AI</strong>
              <span>Ollama-backed incident reasoning</span>
            </article>
            <article className="simple-login-signal-card">
              <strong>Multi-Source</strong>
              <span>Sysmon, Azure AD, Zeek, cloud events</span>
            </article>
          </div>
        </div>

        <div className="simple-login-orbit" aria-hidden="true">
          <div className="simple-login-orbit-ring simple-login-orbit-ring-one" />
          <div className="simple-login-orbit-ring simple-login-orbit-ring-two" />
          <div className="simple-login-orbit-core">
            <span>Threat Mesh</span>
            <strong>Live</strong>
          </div>
          <div className="simple-login-orbit-node simple-login-node-one">SIEM</div>
          <div className="simple-login-orbit-node simple-login-node-two">EDR</div>
          <div className="simple-login-orbit-node simple-login-node-three">IAM</div>
          <div className="simple-login-orbit-node simple-login-node-four">Cloud</div>
        </div>
      </section>

      <section className="simple-login-panel">
        <form className="simple-login-card" onSubmit={handleSubmit}>
          <div className="simple-login-copy">
            <p className="simple-login-kicker">Secure Analyst Access</p>
            <h2>Enter the command layer</h2>
            <p>Sign in to review live ingestion, incident correlation, and response playbooks.</p>
          </div>

          <div className="simple-login-badges">
            <span className="pill">Human approval only</span>
            <span className="pill">Evidence-backed AI</span>
          </div>

          <div className="simple-login-fields">
            <label className="simple-login-field">
              <span>Email</span>
              <input
                autoComplete="email"
                disabled={loading}
                onChange={(event) => {
                  setEmail(event.target.value);
                }}
                placeholder="Enter email"
                type="email"
                value={email}
              />
            </label>

            <label className="simple-login-field">
              <span>Password</span>
              <div className="simple-login-password-wrap">
                <input
                  autoComplete="current-password"
                  disabled={loading}
                  onChange={(event) => {
                    setPassword(event.target.value);
                  }}
                  placeholder="Enter password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                />
                <button
                  className="simple-login-toggle"
                  disabled={loading}
                  onClick={() => setShowPassword((current) => !current)}
                  type="button"
                >
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </label>
          </div>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="simple-login-button" disabled={!canSubmit} type="submit">
            {loading ? "Signing in..." : "Login"}
          </button>

          <div className="simple-login-footer">
            <span>Encrypted analyst session</span>
            <span>Least-privilege access path</span>
          </div>
        </form>
      </section>
    </main>
  );
}
