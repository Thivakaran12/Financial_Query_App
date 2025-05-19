import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import './ChartCard.css';

export default function ComparisonChart({ companies, data, metric }) {
  const chartData = companies.map(slug => {
    const latest = (data[slug] || [])
      .sort((a,b)=>new Date(b.period_end_date)-new Date(a.period_end_date))[0];
    return {
      slug,
      value: latest ? latest[metric] : 0
    };
  });

  return (
    <div className="chart-card">
      <h3>Comparison</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={chartData}
          margin={{ top:20, right:20, left:40, bottom:60 }}
        >
          <XAxis
            dataKey="slug"
            tick={{ fontSize:12, angle:-45, textAnchor:'end' }}
          />
          <YAxis />
          <Tooltip formatter={v=>v.toLocaleString()} />
          <Legend verticalAlign="top" height={28}/>
          <Bar dataKey="value" name={metric.replace('_',' ')} fill="#2ca02c" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
