// Button.jsx
import React from 'react';

const Button = ({ text, onClick, type = 'button', className = '', disabled }) => {
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={`btn ${className}`}>
      {text}
    </button>
  );
};

export default Button;
// End of Button.jsx