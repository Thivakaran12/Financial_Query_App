import React from 'react';
import './DateRangePicker.css';

export default function DateRangePicker({
  startDate, endDate, onStartChange, onEndChange,
}) {
  return (
    <div className="drp">
      <label>
        From{' '}
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartChange(e.target.value)}
        />
      </label>
      <label>
        To{' '}
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndChange(e.target.value)}
        />
      </label>
    </div>
  );
}
