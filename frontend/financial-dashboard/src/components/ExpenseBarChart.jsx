import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import './ChartCard.css';

export default function ExpenseBarChart({ data, companies }) {
  const chartData = companies.map(slug => {
    const latest = (data[slug] || [])
      .sort((a,b)=>new Date(b.period_end_date)-new Date(a.period_end_date))[0];
    return { slug, opex: latest ? latest.operating_expenses : 0 };
  });

  return (
    <div className="chart-card">
      <h3>Operating Expenses</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top:20, right:20, left:40, bottom:60 }}
        >
          <XAxis dataKey="slug" tick={{ fontSize:12 }} />
          <YAxis />
          <Tooltip formatter={v=>v.toLocaleString()} />
          <Legend />
          <Bar dataKey="opex" name="OpEx" fill="#ff7f0e" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
