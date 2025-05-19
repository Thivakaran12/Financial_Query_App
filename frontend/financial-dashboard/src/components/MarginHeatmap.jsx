import React, { useMemo } from 'react';
import PropTypes from 'prop-types';
import ChartCard from './ChartCard';
import './MarginHeatmap.css';

function shade(val) {
  // val is e.g. 0.25 = 25 %
  const p = Math.min(Math.max(val, -0.1), 0.4); // clamp
  const light = 255 - Math.round(p * 400);      // darker for higher %
  return `rgb(${light},${light},255)`;          // bluish scale
}

export default function MarginHeatmap({ data, companies }) {
  const rows = useMemo(() => {
    const out = [];
    companies.forEach(slug => {
      (data[slug] || []).forEach(rec => {
        out.push({
          slug,
          date: rec.period_end_date,
          gm:   rec.gross_profit     / rec.revenue,
          om:   rec.operating_income / rec.revenue,
          nm:   rec.net_income       / rec.revenue,
        });
      });
    });
    return out.sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [data, companies]);

  return (
    <ChartCard title="Margin % Heatmap">
      <div className="heat-grid">
        <div className="heat-head"></div>
        <div className="heat-head">Gross</div>
        <div className="heat-head">Oper.</div>
        <div className="heat-head">Net</div>

        {rows.map(r => (
          <React.Fragment key={r.slug + r.date}>
            <div className="heat-label">
              {r.slug.slice(0,5)} {r.date.slice(2)}
            </div>
            {['gm','om','nm'].map(k => (
              <div
                key={k}
                className="heat-cell"
                style={{ background: shade(r[k]) }}
                title={`${(r[k]*100).toFixed(1)} %`}
              />
            ))}
          </React.Fragment>
        ))}
      </div>
    </ChartCard>
  );
}

MarginHeatmap.propTypes = {
  data:      PropTypes.object.isRequired,
  companies: PropTypes.array.isRequired,
};
