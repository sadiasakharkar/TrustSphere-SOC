"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const canSubmit = email.trim().length > 0 && password.trim().length > 0;

  function handleSubmit(event) {
    event.preventDefault();
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
                }}
                placeholder="Enter your password"
                type="password"
                value={password}
              />
            </label>
          </div>

          <button className="simple-login-button" disabled={!canSubmit} type="submit">
            Login
          </button>
        </form>
      </section>
    </main>
  );
}
