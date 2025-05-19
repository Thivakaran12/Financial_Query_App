import React from 'react';
import PropTypes from 'prop-types';
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import ChartCard from './ChartCard';

const color = ['#1f77b4','#ff7f0e','#2ca02c','#d62728'];

export default function MarginTrendChart({
  data, companies, marginKey, fromDate, toDate
}) {
  const merged = companies.flatMap(slug =>
    (data[slug]||[])
      .filter(r => (!fromDate || new Date(r.period_end_date)>=fromDate)
                && (!toDate   || new Date(r.period_end_date)<=toDate))
      .map(r => ({
        period_end_date: r.period_end_date,
        [slug]: (r[marginKey] / r.revenue) * 100
      }))
  );

  const dates = Array.from(new Set(merged.map(r=>r.period_end_date))).sort();
  const chartData = dates.map(d => {
    const row = { period_end_date:d };
    companies.forEach(s=>{
      const rec = merged.find(r=>r.period_end_date===d && r[s]!==undefined);
      if(rec) row[s]=rec[s];
    });
    return row;
  });

  return (
    <ChartCard title={`Trend – ${marginKey.replace('_',' ')} %`}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top:20, right:20, left:40, bottom:60 }}
        >
          <XAxis
            dataKey="period_end_date"
            tick={{ fontSize:11, angle:-45, textAnchor:'end' }}
          />
          <YAxis />
          <Tooltip formatter={v=>v?.toFixed(2)+'%'} />
          <Legend />
          {companies.map((slug,i)=>(
            <Line
              key={slug}
              dataKey={slug}
              dot={false}
              stroke={color[i]}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

MarginTrendChart.propTypes = {
  data: PropTypes.object.isRequired,
  companies: PropTypes.array.isRequired,
  marginKey: PropTypes.oneOf(['gross_profit','operating_income','net_income']).isRequired,
  fromDate: PropTypes.instanceOf(Date),
  toDate:   PropTypes.instanceOf(Date),
};
