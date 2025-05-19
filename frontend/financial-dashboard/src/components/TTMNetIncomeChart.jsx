import React from 'react';
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, Tooltip, Legend
} from 'recharts';
import './ChartCard.css';

export default function TTMNetIncomeChart({ data, companies }) {
  const dates = Array.from(
    new Set(companies.flatMap(s=>data[s]||[]).map(r=>r.period_end_date))
  ).sort();

  const chartData = dates.map(date=>{
    const row={ period_end_date:date };
    companies.forEach(slug=>{
      const recs=(data[slug]||[])
        .filter(r=>new Date(r.period_end_date)<=new Date(date))
        .sort((a,b)=>new Date(b.period_end_date)-new Date(a.period_end_date))
        .slice(0,4);
      row[slug]=recs.reduce((s,r)=>s+r.net_income,0);
    });
    return row;
  });

  return (
    <div className="chart-card">
      <h3>TTM Net Income</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          data={chartData}
          margin={{ top:20, right:20, left:40, bottom:50 }}
        >
          <XAxis dataKey="period_end_date" tick={{fontSize:11}}/>
          <YAxis />
          <Tooltip formatter={v=>v.toLocaleString()} />
          <Legend />
          {companies.map((s,i)=>(
            <Line key={s} dataKey={s} dot={false} stroke={i? '#ff7f0e':'#1f77b4'} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
