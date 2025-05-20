import React, { useState, useEffect, useMemo } from 'react';
import DatePicker                          from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

import MetricCard            from './MetricCard';
import TimeSeriesChart       from './TimeSeriesChart';
import ComparisonChart       from './ComparisonChart';
import QoPGrowthChart        from './QoPGrowthChart';
import GrossMarginChart      from './GrossMarginChart';
import NetMarginChart        from './NetMarginChart';
import TTMNetIncomeChart     from './TTMNetIncomeChart';
import EntitySelector        from './EntitySelector';
import { fetchCompanyData }  from '../services/financialApi';

import './Dashboard.css';

const METRIC_TABS = [
  { label: 'Revenue',      value: 'revenue'      },
  { label: 'Gross Profit', value: 'gross_profit' },
  { label: 'Net Profit',   value: 'net_income'   },
];

const ALL_COMPANIES = ['dipped-products', 'richard-pieris'];

export default function Dashboard() {
  const [metric,    setMetric]    = useState('revenue');
  const [data,      setData]      = useState({});
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);
  const [fromDate,  setFromDate]  = useState(null);
  const [toDate,    setToDate]    = useState(null);
  const [companies, setCompanies] = useState([...ALL_COMPANIES]);

  useEffect(() => {
    (async () => {
      try {
        const out = {};
        for (const slug of ALL_COMPANIES) {
          out[slug] = await fetchCompanyData(slug);
        }
        setData(out);
      } catch {
        setError('Failed to load data');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const summary = useMemo(() => {
    return companies
      .map(slug => {
        const recs = (data[slug] || [])
          .filter(r =>
            (!fromDate || new Date(r.period_end_date) >= fromDate) &&
            (!toDate   || new Date(r.period_end_date) <= toDate)
          )
          .sort((a,b) => new Date(b.period_end_date) - new Date(a.period_end_date));
        if (!recs.length) return null;

        const [latest, prev] = recs;
        const last4 = recs.slice(0,4);
        const ttmNet = last4.reduce((sum, r) => sum + r.net_income, 0);
        const delta = prev
          ? (latest[metric] - prev[metric]) / Math.abs(prev[metric]) * 100
          : null;

        return {
          slug,
          revenue: latest.revenue,
          gm:      (latest.gross_profit / latest.revenue) * 100,
          nm:      (latest.net_income    / latest.revenue) * 100,
          ttmNet,
          delta,
        };
      })
      .filter(Boolean);
  }, [data, companies, fromDate, toDate, metric]);

  if (loading) return <p className="loading">Loading…</p>;
  if (error)   return <p className="error">{error}</p>;

  return (
    <div className="dashboard">
      {/* — Page Title — */}
      <h1 className="page-title">Financial Dashboard</h1>

      {/* — Filters Row — */}
      <div className="filters-row">
        <EntitySelector
          options={ALL_COMPANIES}
          value={companies}
          onChange={setCompanies}
        />
        <DatePicker
          selected={fromDate}
          onChange={setFromDate}
          placeholderText="From"
          isClearable
        />
        <DatePicker
          selected={toDate}
          onChange={setToDate}
          placeholderText="To"
          isClearable
        />
      </div>

      {/* — KPI Cards — */}
      <div className="metrics-row">
        {summary.map(s => (
          <React.Fragment key={s.slug}>
            <MetricCard
              title={`${s.slug.replace('-', ' ')} Revenue`}
              value={(s.revenue / 1000).toFixed(2)}
              unit="k LKR"
              delta={s.delta}
            />
            <MetricCard
              title="Gross Profit %"
              value={s.gm.toFixed(2)}
            />
            <MetricCard
              title="Net Profit %"
              value={s.nm.toFixed(2)}
            />
            <MetricCard
              title="TTM Net Income"
              value={(s.ttmNet / 1000).toFixed(2)}
              unit="k LKR"
            />
          </React.Fragment>
        ))}
      </div>

      {/* — Metric Toggle Tabs — */}
      <div className="tab-row">
        {METRIC_TABS.map(tab => (
          <button
            key={tab.value}
            className={tab.value === metric ? 'tab active' : 'tab'}
            onClick={() => setMetric(tab.value)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* — Charts Grid — */}
      <div className="charts-grid">
        <TimeSeriesChart
          data={data}
          companies={companies}
          metric={metric}
          fromDate={fromDate}
          toDate={toDate}
        />
        <ComparisonChart
          data={data}
          companies={companies}
          metric={metric}
        />
        <QoPGrowthChart
          data={data}
          companies={companies}
          metric={metric}
          fromDate={fromDate}
          toDate={toDate}
        />
        <GrossMarginChart
          data={data}
          companies={companies}
          fromDate={fromDate}
          toDate={toDate}
        />
        <NetMarginChart
          data={data}
          companies={companies}
          fromDate={fromDate}
          toDate={toDate}
        />
        <TTMNetIncomeChart
          data={data}
          companies={companies}
        />
      </div>
    </div>
  );
}
