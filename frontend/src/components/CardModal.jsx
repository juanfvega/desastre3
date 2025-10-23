// src/components/CardModal.jsx
import React, { useEffect, useMemo, useState, useCallback } from "react";
import Card from "./Card";
import CardDetailModal from "./CardDetailModal";
import "./CardModal.css";
import { createHttpService } from "../services/HttpService";

const http = createHttpService();

// Helpers
const isDetectiveCard = (c) => {
  const t = (c?.type ?? "").toString().toLowerCase();
  return t === "detective" || (c?.name ?? "").toString().startsWith("detective_");
};

const CardModal = ({
  // ===== DEV (existentes) =====
  isOpen,
  onClose,
  Cards,
  onDiscardAction,
  onClickLookIntoAshes,
  selectedDiscardPileCard,
  setCards,
  gameData,
  player,

  // ===== NUESTROS (opcionales) =====
  gameId: gameIdProp,
  playerId: playerIdProp,
  onHandRefresh, // opcional: refrescar la mano luego de jugar
}) => {
  // ====== Estado base (dev) ======
  const [selectedCard, setSelectedCard] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // ====== Backend sets / canPlay / acciones nuevas ======
  const [canState, setCanState] = useState(null); // { can_play, by_hand, by_table }
  const [canLoading, setCanLoading] = useState(false);
  const [canError, setCanError] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [sets, setSets] = useState([]);
  const [setsLoading, setSetsLoading] = useState(false);
  const [drafting, setDrafting] = useState(false);

  // Derivar ids si no vienen por props nuevas
  const gameId = gameIdProp ?? gameData?.gameId ?? gameData?.id ?? gameData?.game?.id;
  const playerId = playerIdProp ?? player?.id ?? player?.playerId ?? gameData?.playerId;

  // ====== Triples UI (visual) ======
  const triplesInfo = useMemo(() => {
    if (!Array.isArray(Cards)) return { groups: [], highlightSet: new Set(), namesInTriple: new Set() };
    const byName = new Map();
    Cards.forEach((c, i) => {
      if (!isDetectiveCard(c)) return;
      const key = c?.name;
      if (!key) return;
      if (!byName.has(key)) byName.set(key, []);
      byName.get(key).push(i);
    });
    const groups = [];
    const highlightSet = new Set();
    const namesInTriple = new Set();
    for (const [name, idxs] of byName.entries()) {
      if (idxs.length >= 3) {
        groups.push({ name, count: idxs.length, indices: idxs.slice(0, 3) });
        idxs.slice(0, 3).forEach((i) => highlightSet.add(i));
        namesInTriple.add(name);
      }
    }
    groups.sort((a, b) => b.count - a.count);
    return { groups, highlightSet, namesInTriple };
  }, [Cards]);

  const hasTriples = triplesInfo.groups.length > 0;
  const selectedIsTriple = selectedCard && triplesInfo.namesInTriple.has(selectedCard.name);

  // ====== Escape & scroll lock (dev) ======
  useEffect(() => {
    const handleEscape = (event) => event.key === "Escape" && onClose();
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  // ====== Click en carta (abre detalle + canPlay) ======
  const handleCardClick = (card) => {
    setSelectedCard(card);
    setIsDetailModalOpen(true);

    // consultar can_play_card apenas abre (si tenemos ids)
    if (gameId && playerId && card?.name) {
      (async () => {
        setCanLoading(true);
        setCanError(null);
        setCanState(null);
        try {
          const can = await http.canPlayCard(gameId, playerId, card.name);
          setCanState(typeof can === "boolean" ? { can_play: can } : can);
        } catch (e) {
          setCanError(e?.payload?.detail || e?.payload?.message || "No se pudo verificar si la carta es jugable.");
        } finally {
          setCanLoading(false);
        }
      })();
    }
  };

  const handleDetailModalClose = () => {
    setIsDetailModalOpen(false);
    setSelectedCard(null);
    setCanState(null);
    setCanError(null);
    setCanLoading(false);
  };

  const handleOverlayClick = () => {
    isDetailModalOpen ? handleDetailModalClose() : onClose();
  };

  // Wrapper dev (no cerrar aquí, delega al handler externo)
  const wrapperDiscardAction = (card) => onDiscardAction?.(card, handleDetailModalClose);

  // ====== Sets (carga y polling suave) ======
  const loadSets = useCallback(async () => {
    if (!gameId) return;
    setSetsLoading(true);
    try {
      const data = await http.getSets?.(gameId) ?? await http.watchSets?.(gameId);
      const normalized = Array.isArray(data) ? data : data?.sets || [];
      setSets(normalized);
    } finally {
      setSetsLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    if (!gameId) return;
    loadSets();
    const id = setInterval(() => { loadSets().catch(() => {}); }, 5000);
    return () => clearInterval(id);
  }, [gameId, loadSets]);

  // ====== Draft desde set (equipo) ======
  const handleDraftFromSet = async (setName) => {
    if (!gameId || !playerId || !setName) return;
    setDrafting(true);
    try {
      await http.draftCard(gameId, playerId, setName);
      await loadSets();
    } catch (_) {
      // mostrar silencioso para no romper flujo
    } finally {
      setDrafting(false);
    }
  };

  // ====== Jugar carta (tu backend) ======
  const handlePlaySelected = async () => {
    if (!gameId || !playerId || !selectedCard?.name) return;
    if (!isDetectiveCard(selectedCard)) return; // solo sets de detectives por ahora
    // backend gobierna: requiere by_hand verdadero
    if (canState && canState.by_hand === false) return;

    setPlaying(true);
    try {
      await (http.playCard
        ? http.playCard(gameId, playerId, selectedCard.name, { player_hand: true })
        : http.request(`/games/${gameId}/${playerId}/${selectedCard.name}/play_card`, {
            method: "POST",
            body: JSON.stringify({ player_hand: true }),
          })
      );

      // refrescos
      await onHandRefresh?.(); // si el contenedor lo provee
      await loadSets();

      handleDetailModalClose();
    } catch (e) {
      // no alertamos para no romper UX del equipo; debug opcional:
      // console.error("playCard error", e);
    } finally {
      setPlaying(false);
    }
  };

  // ====== Botón/estado para backend play ======
  const allowPlayByHand = !!(canState?.by_hand ?? canState?.can_play);

  // ====== DEV: acciones dummy existentes ======
  const UsedAction = (card) => {
    // Mantengo stub dev (por compat); si tu CardDetailModal lo usa, seguirá funcionando
    // console.log("Usar:", card?.name);
  };

  if (!isOpen) return null;

  return (
    <div className="cards-modal-overlay" onClick={handleOverlayClick}>
      <div className="cards-modal" onClick={(e) => e.stopPropagation()}>
        {/* Cabecera compacta con triples (solo visual) */}
        <div
          className="cards-modal-header"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px" }}
        >
          <h3 style={{ margin: 0 }}>Mis cartas</h3>
          {hasTriples ? (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
              <span style={{ color: "#22c55e", fontWeight: 700 }}>🎯 ¡Tenés 3 iguales!</span>
              {triplesInfo.groups.map((g) => (
                <span
                  key={g.name}
                  style={{
                    padding: "4px 8px",
                    borderRadius: 12,
                    background: "#0f172a",
                    border: "1px solid #22c55e",
                    color: "#a7f3d0",
                    fontSize: 12,
                  }}
                  title={`Aparecen ${g.count} veces`}
                >
                  {g.name} (x{g.count})
                </span>
              ))}
            </div>
          ) : (
            <span style={{ color: "#94a3b8" }}>No tenés ternas todavía</span>
          )}
        </div>

        {/* Grilla de cartas (dev) */}
        <div className="cards-modal-content">
          {Cards && Cards.length > 0 ? (
            <div className="cards-grid">
              {Cards.map((card, index) => {
                const highlighted = isDetectiveCard(card) && triplesInfo.highlightSet.has(index);
                return (
                  <div
                    key={card.id || index}
                    className="card-highlight-wrapper"
                    style={{
                      border: highlighted ? "2px solid #22c55e" : "2px solid transparent",
                      borderRadius: 12,
                      padding: 6,
                      transition: "border-color .2s ease",
                    }}
                  >
                    <Card
                      card={card}
                      onCardClick={handleCardClick}
                      data-testid={`card-${card.id}`}
                    />
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="no-cards-message">
              <p>No tienes cartas asignadas.</p>
            </div>
          )}
        </div>
      </div>

      {/* Modal de detalle (dev + features nuevas como children) */}
      <CardDetailModal
        isOpen={isDetailModalOpen}
        onClose={handleDetailModalClose}
        card={selectedCard}
        onUsedAction={UsedAction}
        onDiscardAction={wrapperDiscardAction}
        onClickLookIntoAshes={onClickLookIntoAshes}
        selectedDiscardPileCard={selectedDiscardPileCard}
        setCards={setCards}
        gameData={gameData}
        player={player}
        // props informativas opcionales por si CardDetailModal las usa
        canState={canState}
        canLoading={canLoading}
      >
        {/* Botón de jugar con backend (solo si detectiva) */}
        {isDetectiveCard(selectedCard) && (canLoading || canState) && (
          <>
            <button
              onClick={handlePlaySelected}
              disabled={playing || canLoading || !allowPlayByHand}
              className="btn-play-set"
              style={{
                marginTop: "10px",
                padding: "8px 14px",
                borderRadius: "8px",
                background: "#22c55e",
                border: "none",
                color: "white",
                cursor: "pointer",
                fontWeight: 600,
              }}
            >
              {canLoading ? "Verificando..." : playing ? "Jugando..." : allowPlayByHand ? `Jugar set de ${selectedCard?.name}` : "No se puede jugar desde la mano"}
            </button>
            {canError && (
              <div style={{ marginTop: 6, fontSize: 12, color: "#ef4444", textAlign: "center" }}>
                {canError}
              </div>
            )}
          </>
        )}

        {/* Acción de draft sobre sets (equipo) */}
        {Array.isArray(sets) && sets.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong>Sets</strong>
              <button
                onClick={loadSets}
                disabled={setsLoading}
                className="btn-refresh-sets"
                style={{
                  padding: "4px 8px",
                  borderRadius: 6,
                  border: "1px solid #e5e7eb",
                  background: "#f9fafb",
                  fontSize: 12,
                }}
              >
                {setsLoading ? "Actualizando..." : "Actualizar"}
              </button>
            </div>

            <ul className="grid grid-cols-2 gap-2" style={{ marginTop: 8 }}>
              {sets.map((s, i) => (
                <li key={s?.name || i} className="border rounded p-2 flex items-center justify-between">
                  <span>{s?.name ?? "Set"}</span>
                  <button
                    disabled={drafting}
                    onClick={() => handleDraftFromSet(s?.name)}
                    className="px-2 py-1 text-xs rounded"
                    style={{ background: "#4f46e5", color: "white" }}
                  >
                    {drafting ? "Tomando..." : "Tomar del draft"}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Fallback: si no hay canState aún pero la selección es triple, permitir botón clásico */}
        {selectedIsTriple && !canLoading && !canState && (
          <button
            onClick={handlePlaySelected}
            disabled={playing}
            className="btn-play-set"
            style={{
              marginTop: "10px",
              padding: "8px 14px",
              borderRadius: "8px",
              background: "#22c55e",
              border: "none",
              color: "white",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            {playing ? "Jugando..." : `Jugar set de ${selectedCard?.name}`}
          </button>
        )}
      </CardDetailModal>
    </div>
  );
};

export default CardModal;
