import React from 'react';
import { NavLink } from 'react-router-dom';
import './Layout.css';          // ← just imports the styles in the next file

export default function Layout({ children }) {
  return (
    <div className="app-grid">
      {/* ───────── Sidebar ───────── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          COLOMBO STOCK<br />EXCHANGE (CSE)
        </div>

        <nav className="sidebar-nav">
          <NavLink end to="/"       className="nav-item">
            Dashboard
          </NavLink>
          <NavLink      to="/chat" className="nav-item">
            Chat with Virtual Agent
          </NavLink>
        </nav>
      </aside>

      {/* ───────── Main panel ───────── */}
      <main className="main">
        {/* no top bar any more – the date was removed per your last request */}
        <section className="content">{children}</section>
      </main>
    </div>
  );
}
