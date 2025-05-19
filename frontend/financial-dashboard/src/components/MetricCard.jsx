import React from 'react';
import PropTypes from 'prop-types';
import './MetricCard.css';

/**
 * MetricCard
 * ----------
 * Shows a headline metric plus an optional delta (positive or negative).
 */
export default function MetricCard({ title, value, delta = null, unit = '' }) {
  const isPos = delta !== null && delta >= 0;

  return (
    <div className="metric-card">
      <div className="metric-title">{title}</div>

      <div className="metric-value">
        {value.toLocaleString()} {unit}
      </div>

      {delta !== null && (
        <div
          className={`metric-delta ${isPos ? 'pos' : 'neg'}`}
          title="Quarter-on-Quarter change"
        >
          {isPos ? '▲' : '▼'} {Math.abs(delta).toFixed(2)}%
        </div>
      )}
    </div>
  );
}

MetricCard.propTypes = {
  title:  PropTypes.string.isRequired,
  value:  PropTypes.number.isRequired,
  delta:  PropTypes.number,
  unit:   PropTypes.string,
};
