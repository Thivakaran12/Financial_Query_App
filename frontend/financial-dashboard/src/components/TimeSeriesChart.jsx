import React from 'react';
import {
  ResponsiveContainer,
  AreaChart, Area,
  XAxis, YAxis, Tooltip, CartesianGrid,
  Legend
} from 'recharts';
import './ChartCard.css';

export default function TimeSeriesChart({
  data, companies, metric, fromDate, toDate
}) {
  // build chartData identical to before
  let merged = companies.flatMap(slug =>
    (data[slug] || [])
      .filter(r =>
        (!fromDate || new Date(r.period_end_date) >= fromDate) &&
        (!toDate   || new Date(r.period_end_date) <= toDate)
      )
      .map(r => ({ ...r, slug }))
  );

  // unique, sorted dates
  const dates = Array.from(
    new Set(merged.map(r => r.period_end_date))
  ).sort();

  // one row per date
  const chartData = dates.map(date => {
    const obj = { period_end_date: date };
    companies.forEach(slug => {
      const rec = merged.find(r => r.period_end_date === date && r.slug === slug);
      obj[slug] = rec ? rec[metric] : null;
    });
    return obj;
  });

  return (
    <div className="chart-card">
      <h3>Time Series</h3>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={chartData}
          margin={{ top: 20, right: 20, left: 40, bottom: 60 }}
        >
          {/* Define gradient fills */}
          <defs>
            <linearGradient id="gradBlue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#5c4dff" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#5c4dff" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="gradOrange" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#ff7f0e" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#ff7f0e" stopOpacity={0}/>
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="period_end_date"
            tick={{ fontSize: 11, angle: -45, textAnchor: 'end' }}
          />
          <YAxis />
          <Tooltip />

          {/* Render an <Area> per company */}
          {companies.map((slug, idx) => (
            <Area
              key={slug}
              type="monotone"
              dataKey={slug}
              stroke={idx === 0 ? "#5c4dff" : "#ff7f0e"}
              fill={idx === 0 ? "url(#gradBlue)" : "url(#gradOrange)"}
              dot={{ r: 4 }}
            />
          ))}
          <Legend verticalAlign="top" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
