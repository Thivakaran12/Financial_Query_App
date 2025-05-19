import React from 'react';
import './ChartCard.css';

export default function ChartCard({ title, infos = [], children }) {
  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3>{title}</h3>
        <div className="chart-card-infos">
          {infos.map((info, i) => (
            <div key={i} className="chart-card-info">{info}</div>
          ))}
        </div>
      </div>
      <div className="chart-card-body">{children}</div>
    </div>
  );
}
