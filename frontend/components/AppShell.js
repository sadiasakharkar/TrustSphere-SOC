"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import MaterialIcon from "@/components/MaterialIcon";
import { navItems } from "@/lib/data";

export default function AppShell({ eyebrow, title, description, actions, children }) {
  const pathname = usePathname();

  return (
    <div className="app-shell">
      <header className="topbar glass-panel">
        <div className="brand">TrustSphere SOC</div>
        <div className="topbar-tools">
          <div className="search-chip">
            <MaterialIcon name="search" className="muted-icon" />
            <span>Global investigation</span>
          </div>
          <button className="icon-button" type="button">
            <MaterialIcon name="terminal" className="muted-icon" />
          </button>
          <button className="icon-button" type="button">
            <MaterialIcon name="notifications" className="muted-icon" />
          </button>
          <button className="avatar" type="button">
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
          <button className="primary-button full-width" type="button">
            Open Analyst Terminal
          </button>
          <div className="footer-links">
            <span>System Health</span>
            <span>Documentation</span>
          </div>
        </div>
      </aside>

      <main className="canvas">
        <section className="page-header">
          <div>
            {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
            <h1>{title}</h1>
            <p className="page-copy">{description}</p>
          </div>
          {actions ? <div className="page-actions">{actions}</div> : null}
        </section>
        {children}
      </main>
    </div>
  );
}
