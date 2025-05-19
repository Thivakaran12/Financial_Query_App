import React from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer,
  PieChart, Pie, Cell, Tooltip, Legend
} from 'recharts';
import ChartCard from './ChartCard';

const COLORS = ['#1f77b4','#ff7f0e'];

export default function SharePieChart({ summary, metric }) {
  const data = summary.map((s, i) => ({
    name: s.slug.replace('-', ' '),
    value: Math.abs(s[metric]),
  }));

  return (
    <ChartCard title={`${metric.replace('_',' ')} Share`}>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            outerRadius={80}
            label={({ name, percent }) =>
              `${name}: ${(percent*100).toFixed(0)}%`
            }
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={v => v.toLocaleString()} />
          <Legend verticalAlign="bottom" height={36}/>
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

SharePieChart.propTypes = {
  summary: PropTypes.arrayOf(
    PropTypes.shape({
      slug: PropTypes.string.isRequired,
      revenue: PropTypes.number,
      gross_profit: PropTypes.number,
      net_income: PropTypes.number,
    })
  ).isRequired,
  metric: PropTypes.oneOf(['revenue','gross_profit','net_income']).isRequired,
};
