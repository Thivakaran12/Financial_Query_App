import React from 'react';
import PropTypes from 'prop-types';
import './NavBar.css';

export default function NavBar({ tabs, active, onChange }) {
  return (
    <nav className="navbar">
      <div className="navbar-title">Financial Performance Dashboard</div>
      <div className="navbar-tabs">
        {tabs.map(t => (
          <button
            key={t.value}
            className={`navbar-tab${t.value===active?' active':''}`}
            onClick={()=>onChange(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>
    </nav>
  );
}

NavBar.propTypes = {
  tabs:   PropTypes.array.isRequired,
  active: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};
