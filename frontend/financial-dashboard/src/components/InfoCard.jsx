import React from 'react';
import './InfoCard.css';

export default function InfoCard({ label, value, suffix = '' }) {
  return (
    <div className="info-card">
      <div className="info-label">{label}</div>
      <div className="info-value">
        {value} {suffix}
      </div>
    </div>
  );
}
