
import React from 'react';
import PropTypes from 'prop-types';

const Avatar = ({ src,size = 50, className = '' }) => {
  return (
    <img
      src={src}
      className={`avatar ${className}`}
      style={{ width: size, height: size, borderRadius: '50%' }}
    />
  );
};

Avatar.propTypes = {
  src: PropTypes.string.isRequired,
  size: PropTypes.number,
  className: PropTypes.string,
};

export default Avatar;
