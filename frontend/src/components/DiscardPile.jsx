import React from "react";
import PropTypes from "prop-types";

// Componente para mostrar la pila de descarte
const DiscardPile = ({ cards }) => {
  // Generar path de imagen tipo <type>_<name>.png en minúsculas
  const getImagePath = (name) => {
    const path = `/Cards/${name}.png`;
    return path;
  };

  return (
  <div
    className="discard-pile"
    style={{
      position: "relative",
      width: "120px",
      height: "120px",
    }}
  >
{/*separador de cartas, se agrega efecto de mazo con index iterando en top y right*/}
    {cards.map((card, index) => (
        // cada carta en la pila
      <img
        key={index}
        src={getImagePath(card.name)}
        alt={`${card.type} - ${card.name}`}
        // cada carta levemente desplazada para efecto de pila
        style={{
          position: "absolute",
          top: `${index * 0.3}px`, // separa levemente cada carta
          right: `${index * 0.3}px`,
          width: "85px",
          height: "115px",
          objectFit: "cover",
          borderRadius: "4px",
          border: "1px solid #ccc",
          zIndex: index + 1, // cada carta adelante de la anterior
          transition: "transform 0.2s ease",
        }}
      />
    ))}
  </div>
);

};
// 
DiscardPile.propTypes = {
  cards: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string.isRequired,
      name: PropTypes.string.isRequired
    })
  ).isRequired
};

export default DiscardPile;
