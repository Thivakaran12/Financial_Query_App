// src/components/PnLChart.jsx
import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';

export default function PnLChart({ data }) {
  // sort by date ascending
  const sorted = [...data].sort((a,b) =>
    new Date(a.period_end_date) - new Date(b.period_end_date)
  );

  return (
    <div style={{ width: '100%', height: 400 }}>
      <ResponsiveContainer>
        <LineChart data={sorted}>
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
