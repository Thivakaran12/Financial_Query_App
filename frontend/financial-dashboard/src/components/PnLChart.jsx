/**
 * PnlChart.jsx
 *
 * Renders a line chart of Revenue, Gross Profit, and Net Income
 * over time using Recharts.
 */

import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import './PnlChart.css';

/**
 * @typedef {Object} PnlRecord
 * @property {string} period_end_date ISO date string (YYYY-MM-DD)
 * @property {number} revenue
 * @property {number} gross_profit
 * @property {number} net_income
 */

/**
 * PnlChart component displays a time series of key P&L metrics.
 *
 * @param {{ data: PnlRecord[] }} props
 */
export default function PnlChart({ data }) {
  const sortedData = useMemo(() => {
    return [...data].sort(
      (a, b) =>
        new Date(a.period_end_date).getTime() -
        new Date(b.period_end_date).getTime()
    );
  }, [data]);

  return (
    <div className="pnl-chart-container">
      <ResponsiveContainer>
        <LineChart data={sortedData}>
          <XAxis dataKey="period_end_date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line
            type="monotone"
            dataKey="revenue"
            name="Revenue"
            stroke="#8884d8"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="gross_profit"
            name="Gross Profit"
            stroke="#82ca9d"
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="net_income"
            name="Net Income"
            stroke="#ffc658"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

PnlChart.propTypes = {
  /** Array of P&L records to plot */
  data: PropTypes.arrayOf(
    PropTypes.shape({
      period_end_date: PropTypes.string.isRequired,
      revenue: PropTypes.number.isRequired,
      gross_profit: PropTypes.number.isRequired,
      net_income: PropTypes.number.isRequired,
    })
  ).isRequired,
};
