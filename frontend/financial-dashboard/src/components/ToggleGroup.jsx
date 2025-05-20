// src/components/ToggleGroup.jsx
import React from 'react';
import './ToggleGroup.css';

export default function ToggleGroup({ options, selected, onChange }) {
  return (
    <div className="toggle-group">
      {options.map(opt => (
        <button
          key={opt.value}
          className={
            opt.value === selected
              ? 'toggle-btn toggle-btn--active'
              : 'toggle-btn'
          }
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
