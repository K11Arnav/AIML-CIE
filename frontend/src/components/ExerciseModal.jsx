export default function ExerciseModal({ exercise, onClose }) {
  if (!exercise) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="badge-purple" style={{ marginBottom: "6px" }}>
              {exercise.body_part || "Target Muscle"}
            </span>
            <h3 style={{ fontSize: "22px", fontWeight: 600, color: "var(--color-ink)", marginTop: "4px" }}>
              {exercise.name}
            </h3>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        <div className="modal-body">
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "20px" }}>
            <div style={{ background: "var(--color-surface)", padding: "12px", borderRadius: "8px", border: "1px solid var(--color-hairline)" }}>
              <div style={{ fontSize: "11px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>Sets</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--color-ink)" }}>{exercise.sets || "3"}</div>
            </div>
            <div style={{ background: "var(--color-surface)", padding: "12px", borderRadius: "8px", border: "1px solid var(--color-hairline)" }}>
              <div style={{ fontSize: "11px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>Reps / Time</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "var(--color-ink)" }}>{exercise.reps || "10-12"}</div>
            </div>
            <div style={{ background: "var(--color-surface)", padding: "12px", borderRadius: "8px", border: "1px solid var(--color-hairline)" }}>
              <div style={{ fontSize: "11px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>Equipment</div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-brand-green-dark)", textTransform: "capitalize" }}>
                {exercise.equipment || "Standard"}
              </div>
            </div>
          </div>

          <h4 style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
            Execution Guide &amp; Mechanics
          </h4>
          <p style={{ fontSize: "14px", color: "var(--color-slate)", lineHeight: "1.6", marginBottom: "16px" }}>
            {exercise.description ||
              "Maintain full core engagement throughout the entire range of motion. Control the eccentric phase for 2 to 3 seconds before initiating explosive concentric drive."}
          </p>

          <div className="alert-callout warning" style={{ marginBottom: "0" }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <div>
              <strong>Form Safety Cue:</strong> Stop immediately if sharp joint pain occurs. Exercise selection should never aggravate reported limitations.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
