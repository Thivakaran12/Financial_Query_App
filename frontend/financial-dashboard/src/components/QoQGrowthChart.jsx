import React from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, Tooltip, Legend,
} from 'recharts';
import ChartCard from './ChartCard';

/* Compute QoQ % change for each record in-place */
function addQoQ(arr, field) {
  return arr.map((rec, i) => {
    const prev = arr[i + 1];          // sorted desc later
    const pct  = prev ? ((rec[field] - prev[field]) / Math.abs(prev[field])) * 100 : null;
    return { ...rec, [`${field}_qoq`]: pct };
  });
}

export default function QoQGrowthChart({ data, companies }) {
  // flatten -> sort desc per company -> compute QoQ %
  let merged = companies.flatMap(slug =>
    [...(data[slug] || [])]
      .sort((a, b) => new Date(b.period_end_date) - new Date(a.period_end_date))
      .slice(0, 8) // last 8 quarters
  );

  merged = companies.flatMap(slug =>
    addQoQ(
      merged.filter(r => r.slug === slug),
      'revenue'
    ).map(r => ({
      ...r,
      slug,
      net_income_qoq: null,   // you can extend similarly if desired
    }))
  );

  return (
    <ChartCard title="QoQ Revenue Growth %">
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={merged}>
          <XAxis
            dataKey="period_end_date"
            tick={{ fontSize: 11, angle: -45, textAnchor: 'end' }}
          />
          <YAxis />
          <Tooltip formatter={v => v?.toFixed(2) + '%'} />
          <Legend />
          {companies.map((slug, i) => (
            <Bar
              key={slug}
              dataKey={d => (d.slug === slug ? d.revenue_qoq : null)}
              name={slug}
              stackId="a"
              fill={i === 0 ? '#1f77b4' : '#ff7f0e'}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

QoQGrowthChart.propTypes = {
  data:      PropTypes.object.isRequired,
  companies: PropTypes.array.isRequired,
};
