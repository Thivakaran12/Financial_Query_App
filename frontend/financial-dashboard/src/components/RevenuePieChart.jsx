import React from 'react';
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend
} from 'recharts';
import './ChartCard.css';

const PIE_COLOURS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'];

export default function RevenuePieChart({ data, companies }) {
  const chartData = companies.map((slug,i) => {
    const latest = (data[slug]||[])
      .sort((a,b)=>new Date(b.period_end_date)-new Date(a.period_end_date))[0];
    return { name: slug, value: latest ? latest.revenue : 0, fill: PIE_COLOURS[i%4] };
  });

  return (
    <div className="chart-card">
      <h3>Latest-Quarter Revenue Split</h3>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            dataKey="value"
            nameKey="name"
            outerRadius={100}
            label={({name, percent})=>`${name} ${(percent*100).toFixed(0)}%`}
          >
            {chartData.map((entry,i)=><Cell key={i} fill={entry.fill} />)}
          </Pie>
          <Tooltip formatter={v=>v.toLocaleString()} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
