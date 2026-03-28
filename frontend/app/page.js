"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import MaterialIcon from "@/components/MaterialIcon";

const initialOtp = ["5", "2", "9", "", "", ""];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("analyst@trustsphere.com");
  const [password, setPassword] = useState("secure-enterprise");
  const [otp, setOtp] = useState(initialOtp);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const isEmailValid = /\S+@\S+\.\S+/.test(email);
  const isPasswordValid = password.trim().length >= 8;
  const isOtpValid = otp.every((digit) => digit.trim().length === 1);
  const canSubmit = isEmailValid && isPasswordValid && isOtpValid;

  function handleOtpChange(index, value) {
    const nextValue = value.replace(/\D/g, "").slice(-1);
    const nextOtp = [...otp];
    nextOtp[index] = nextValue;
    setOtp(nextOtp);
    setError("");
  }

  function handleSubmit(event) {
    event.preventDefault();

    if (!isEmailValid) {
      setError("Enter a valid work email to continue.");
      return;
    }

    if (!isPasswordValid) {
      setError("Vault password must be at least 8 characters.");
      return;
    }

    if (!isOtpValid) {
      setError("Complete the 6-digit verification code.");
      return;
    }

    setError("");
    router.push("/monitoring");
  }

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
        <form className="login-card" onSubmit={handleSubmit}>
          <div>
            <h2>Analyst Portal</h2>
            <p>Provide your credentials to access the secure terminal.</p>
          </div>

          <div className="credentials-card">
            <div className="credentials-header">
              <p>Credentials</p>
              <span>Email and password are required before MFA verification.</span>
            </div>

            <div className="form-grid">
              <label>
                <span>Work Email</span>
                <div className="input-shell">
                  <MaterialIcon name="mail" className="muted-icon" />
                  <input
                    autoComplete="email"
                    onChange={(event) => {
                      setEmail(event.target.value);
                      setError("");
                    }}
                    placeholder="analyst@trustsphere.com"
                    type="email"
                    value={email}
                  />
                </div>
              </label>

              <label>
                <span>Vault Password</span>
                <div className="input-shell">
                  <MaterialIcon name="lock" className="muted-icon" />
                  <input
                    autoComplete="current-password"
                    onChange={(event) => {
                      setPassword(event.target.value);
                      setError("");
                    }}
                    placeholder="Enter your vault password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                  />
                  <button
                    aria-label={showPassword ? "Hide password" : "Show password"}
                    className="visibility-toggle"
                    onClick={() => setShowPassword((current) => !current)}
                    type="button"
                  >
                    <MaterialIcon
                      name={showPassword ? "visibility_off" : "visibility"}
                      className="muted-icon"
                    />
                  </button>
                </div>
              </label>
            </div>
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
                <input
                  key={index}
                  aria-label={`OTP digit ${index + 1}`}
                  inputMode="numeric"
                  maxLength={1}
                  onChange={(event) => handleOtpChange(index, event.target.value)}
                  type="text"
                  value={digit}
                />
              ))}
            </div>
          </div>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="primary-button login-cta" disabled={!canSubmit} type="submit">
            Access Terminal
            <MaterialIcon name="arrow_forward" />
          </button>

          <div className="login-meta">
            <button className="text-button" type="button">
              Forgot password?
            </button>
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
        </form>
      </section>
    </main>
  );
}
