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
  const [pointerStyle, setPointerStyle] = useState({
    "--pointer-x": "50%",
    "--pointer-y": "50%",
    "--tilt-x": "0deg",
    "--tilt-y": "0deg",
  });
  const canSubmit =
    email.trim().length > 0 && password.trim().length > 0 && !loading;

  function handlePointerMove(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;
    const tiltX = ((y - 50) / 18).toFixed(2);
    const tiltY = ((50 - x) / 18).toFixed(2);
    setPointerStyle({
      "--pointer-x": `${x}%`,
      "--pointer-y": `${y}%`,
      "--tilt-x": `${tiltX}deg`,
      "--tilt-y": `${tiltY}deg`,
    });
  }

  function handlePointerLeave() {
    setPointerStyle({
      "--pointer-x": "50%",
      "--pointer-y": "50%",
      "--tilt-x": "0deg",
      "--tilt-y": "0deg",
    });
  }

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
    <main
      className="simple-login-page"
      onMouseLeave={handlePointerLeave}
      onMouseMove={handlePointerMove}
      style={pointerStyle}
    >
      <section className="simple-login-brand">
        <div className="simple-login-ambient simple-login-ambient-one" />
        <div className="simple-login-ambient simple-login-ambient-two" />
        <div className="simple-login-pointer-glow" />
        <div className="simple-login-grid" />

        <div className="simple-login-brand-copy">
          <h1>TrustSphere</h1>
        </div>

        <div className="simple-login-orbit" aria-hidden="true">
          <div className="simple-login-orbit-ring simple-login-orbit-ring-one" />
          <div className="simple-login-orbit-ring simple-login-orbit-ring-two" />
          <div className="simple-login-orbit-core">
            <span />
          </div>
          <div className="simple-login-orbit-node simple-login-node-one" />
          <div className="simple-login-orbit-node simple-login-node-two" />
          <div className="simple-login-orbit-node simple-login-node-three" />
          <div className="simple-login-orbit-node simple-login-node-four" />
        </div>
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
        </form>
      </section>
    </main>
  );
}
