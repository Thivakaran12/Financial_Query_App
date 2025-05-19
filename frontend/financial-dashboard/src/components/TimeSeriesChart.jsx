import React from 'react';
import {
  ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import './ChartCard.css';

export default function TimeSeriesChart({
  data, companies, metric, fromDate, toDate
}) {
  // Merge, filter and tag each record with its slug
  let merged = companies.flatMap(slug =>
    (data[slug] || []).map(rec => ({ ...rec, slug }))
  );
  if (fromDate) merged = merged.filter(r => new Date(r.period_end_date) >= fromDate);
  if (toDate)   merged = merged.filter(r => new Date(r.period_end_date) <= toDate);

  // Unique, sorted dates
  const sortedDates = Array.from(new Set(merged.map(r => r.period_end_date))).sort();

  // Build a row per date, with each company’s value
  const chartData = sortedDates.map(date => {
    const point = { period_end_date: date };
    companies.forEach(slug => {
      const rec = (data[slug] || []).find(r => r.period_end_date === date);
      point[slug] = rec ? rec[metric] : null;
    });
    return point;
  });

  return (
    <div className="chart-card">
      <h3>Time Series</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top: 20, right: 20, left: 50, bottom: 60 }}
        >
          <XAxis
            dataKey="period_end_date"
            tick={{ fontSize: 11, angle: -45, textAnchor: 'end' }}
          />
          <YAxis />
          <Tooltip formatter={val => val?.toLocaleString()} />
          <Legend verticalAlign="top" height={36} />
          {companies.map((slug, i) => (
            <Line
              key={slug}
              dataKey={slug}
              name={slug}
              dot={false}
              stroke={i === 0 ? '#1f77b4' : '#ff7f0e'}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
