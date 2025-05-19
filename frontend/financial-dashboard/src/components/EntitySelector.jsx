/** Pill-style multi-select for companies */
import React from 'react';
import PropTypes from 'prop-types';
import Select from 'react-select';

export default function EntitySelector({ options, value, onChange }) {
  const selectOpts = options.map(o => ({ label: o.replace('-', ' '), value: o }));
  const selected   = value.map(v => ({ label: v.replace('-', ' '), value: v }));

  return (
    <Select
      isMulti
      options={selectOpts}
      value={selected}
      onChange={vals => onChange(vals.map(v => v.value))}
      className="entity-selector"
      classNamePrefix="entity"
      placeholder="Select entities…"
    />
  );
}

EntitySelector.propTypes = {
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  value:   PropTypes.arrayOf(PropTypes.string).isRequired,
  onChange:PropTypes.func.isRequired,
};
