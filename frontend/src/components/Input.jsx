//Input.jsx
import React from 'react';

const Input = ({ type, id, className, placeholder, onChange }) => {
  return (
    <input
      type={type}
      id={id}
      className={`input ${className}`}
      placeholder={placeholder}
      onChange={onChange}
    />
  );
};

export default Input;
// End of Input.jsx