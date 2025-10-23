import React from 'react';
import './ActionButton.css';

const ActionButton = ({ onNoAction, isVisible = false, disabled = false }) => {
  if (!isVisible) {
    return null;
  }

  const handleClick = () => {
    if (!disabled && onNoAction) {
      onNoAction();
    }
  };

  return (
    <div className="action-button-container">
      <button 
        onClick={handleClick}
        className={`action-button ${disabled ? 'action-button-disabled' : ''}`}
        disabled={disabled}
      >
        No ejecutar acción
      </button>
    </div>
  );
};

export default ActionButton;