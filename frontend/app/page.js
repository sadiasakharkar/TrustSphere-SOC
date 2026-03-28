"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("analyst@trustsphere.com");
  const [password, setPassword] = useState("secure-enterprise");
  const [error, setError] = useState("");

  const isEmailValid = /\S+@\S+\.\S+/.test(email);
  const isPasswordValid = password.trim().length >= 8;
  const canSubmit = isEmailValid && isPasswordValid;

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

    setError("");
    router.push("/monitoring");
  }

  return (
    <main className="simple-login-page">
      <section className="simple-login-brand">
        <h1>TrustSphere</h1>
      </section>

      <section className="simple-login-panel">
        <form className="simple-login-card" onSubmit={handleSubmit}>
          <div className="simple-login-copy">
            <h2>Login</h2>
            <p>Enter your email and password to open the dashboard.</p>
          </div>

          <div className="simple-login-fields">
            <label className="simple-login-field">
              <span>Email</span>
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
            </label>

            <label className="simple-login-field">
              <span>Password</span>
              <input
                autoComplete="current-password"
                onChange={(event) => {
                  setPassword(event.target.value);
                  setError("");
                }}
                placeholder="Enter your password"
                type="password"
                value={password}
              />
            </label>
          </div>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="simple-login-button" disabled={!canSubmit} type="submit">
            Login
          </button>
        </form>
      </section>
    </main>
  );
}
