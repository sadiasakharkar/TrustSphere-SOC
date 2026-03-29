"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import MaterialIcon from "@/components/MaterialIcon";
import { navItems } from "@/lib/data";

export default function AppShell({ eyebrow, title, description, actions, children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [statusMessage, setStatusMessage] = useState("");
  const showHeader = title || description || eyebrow || actions;

  return (
    <div className="app-shell">
      <header className="topbar glass-panel">
        <div className="brand">TrustSphere SOC</div>
        <div className="topbar-tools">
          <div className="search-chip">
            <MaterialIcon name="search" className="muted-icon" />
            <span>Global investigation</span>
          </div>
          <button className="icon-button" onClick={() => router.push("/terminal")} type="button">
            <MaterialIcon name="terminal" className="muted-icon" />
          </button>
          <button
            className="icon-button"
            onClick={() => setStatusMessage("No new analyst notifications right now.")}
            type="button"
          >
            <MaterialIcon name="notifications" className="muted-icon" />
          </button>
          <button className="avatar" onClick={() => router.push("/")} type="button">
            TS
          </button>
        </div>
      </header>

      <aside className="sidebar">
        <div className="sidebar-card">
          <div className="sidebar-badge">
            <MaterialIcon name="shield" filled className="sidebar-badge-icon" />
          </div>
          <div>
            <p className="sidebar-title">SOC Console</p>
            <p className="sidebar-copy">Level 3 Analyst</p>
          </div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                className={`nav-link ${active ? "active" : ""}`}
                href={item.href}
              >
                <MaterialIcon name={item.icon} filled={active} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <button className="primary-button full-width" onClick={() => router.push("/terminal")} type="button">
            Open Analyst Terminal
          </button>
          <div className="footer-links">
            <span>System Health</span>
            <span>Documentation</span>
          </div>
        </div>
      </aside>

      <main className="canvas">
        {statusMessage ? (
          <section className="wide-card selected-file-banner">
            <div className="card-header compact">
              <div>
                <h3>System Update</h3>
                <p>{statusMessage}</p>
              </div>
              <button className="ghost-button" onClick={() => setStatusMessage("")} type="button">
                Close
              </button>
            </div>
          </section>
        ) : null}
        {showHeader ? (
          <section className="page-header">
            <div>
              {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
              {title ? <h1>{title}</h1> : null}
              {description ? <p className="page-copy">{description}</p> : null}
            </div>
            {actions ? <div className="page-actions">{actions}</div> : null}
          </section>
        ) : null}
        {children}
      </main>
    </div>
  );
}
