import React from 'react';
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import './ChartCard.css';

export default function GrossMarginChart({ data, companies, fromDate, toDate }) {
  const dates = Array.from(
    new Set(companies.flatMap(s=>data[s]||[]).map(r=>r.period_end_date))
  ).sort();

  const chartData = dates
    .filter(d => (!fromDate||new Date(d)>=fromDate) && (!toDate||new Date(d)<=toDate))
    .map(date => {
      const row = { period_end_date: date };
      companies.forEach(slug=>{
        const rec=(data[slug]||[]).find(r=>r.period_end_date===date);
        if(rec) row[slug]=(rec.gross_profit/rec.revenue)*100;
      });
      return row;
    });

  return (
    <div className="chart-card">
      <h3>Gross-Margin %</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top:20, right:20, left:40, bottom:50 }}
        >
          <XAxis dataKey="period_end_date" tick={{fontSize:11}}/>
          <YAxis />
          <Tooltip formatter={v=>v?.toFixed(2)+' %'} />
          <Legend />
          {companies.map((s,i)=>(
            <Line key={s} dataKey={s} dot={false} stroke={i? '#ff7f0e':'#1f77b4'} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
