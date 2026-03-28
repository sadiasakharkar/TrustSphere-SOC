"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
              <input
                autoComplete="current-password"
                disabled={loading}
                onChange={(event) => {
                  setPassword(event.target.value);
                }}
                placeholder="Enter password"
                type="password"
                value={password}
              />
            </label>
          </div>

          {error ? <p className="form-error">{error}</p> : null}

          <button className="simple-login-button" disabled={!canSubmit} type="submit">
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>
      </section>
    </main>
  );
}
