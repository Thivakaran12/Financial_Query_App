// src/components/CompanySelector.jsx
import React from 'react';
import PropTypes from 'prop-types';
import './CompanySelector.css';

export default function CompanySelector({ options, value, onChange }) {
  return (
    <select
      className="company-selector"
      value={value}
      onChange={e => onChange(e.target.value)}
    >
      {options.map(opt => (
        <option key={opt} value={opt}>{opt}</option>
      ))}
    </select>
  );
}

CompanySelector.propTypes = {
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  value:   PropTypes.string.isRequired,
  onChange:PropTypes.func.isRequired,
};
