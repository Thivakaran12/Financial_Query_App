import React from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer, BarChart, Bar,
  XAxis, YAxis, Tooltip, Legend,
} from 'recharts';
import ChartCard from './ChartCard';

/** Add QoQ % for a field in descending time order */
function addQoQ(arr, field) {
  return arr.map((r,i) => {
    const prev = arr[i+1];
    const pct  = prev
      ? ((r[field] - prev[field]) / Math.abs(prev[field])) * 100
      : null;
    return { ...r, [`${field}_qoq`]: pct };
  });
}

export default function QoPGrowthChart({ data, companies, metric, fromDate, toDate }) {
  // flatten, filter by date, sort desc per company
  const merged = companies.flatMap(slug => {
    const recs = (data[slug]||[])
      .filter(r => (!fromDate || new Date(r.period_end_date)>=fromDate)
                && (!toDate   || new Date(r.period_end_date)<=toDate))
      .sort((a,b)=>new Date(b.period_end_date)-new Date(a.period_end_date))
      .slice(0,8);
    return addQoQ(recs, metric).map(r => ({ ...r, slug }));
  });

  return (
    <ChartCard title={`QoQ % Growth: ${metric.replace('_',' ')}`}>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart
          data={merged}
          margin={{ top:20, right:20, left:50, bottom:60 }}
        >
          <XAxis
            dataKey="period_end_date"
            tick={{ fontSize:11, angle:-45, textAnchor:'end' }}
          />
          <YAxis />
          <Tooltip formatter={v => v?.toFixed(2)+'%'} />
          <Legend />
          {companies.map((slug,i) => (
            <Bar
              key={slug}
              dataKey={d=>d.slug===slug?d[`${metric}_qoq`]:null}
              name={slug}
              fill={i===0?'#1f77b4':'#ff7f0e'}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

QoPGrowthChart.propTypes = {
  data:      PropTypes.object.isRequired,
  companies: PropTypes.array.isRequired,
  metric:    PropTypes.string.isRequired,
  fromDate:  PropTypes.instanceOf(Date),
  toDate:    PropTypes.instanceOf(Date),
};
