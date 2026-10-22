import { PRESET_PROFILES } from "../mockData.js";

export default function PresetBar({ selectedPresetId, onSelectPreset }) {
  return (
    <section className="presets-section">
      <div className="container">
        <div className="presets-container">
          <div className="presets-label">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
            <span>1-Click Sample Profiles:</span>
          </div>

          <div className="presets-pills">
            {PRESET_PROFILES.map((p) => {
              const isActive = selectedPresetId === p.id;
              return (
                <button
                  key={p.id}
                  type="button"
                  className={`preset-chip ${isActive ? "active" : ""}`}
                  onClick={() => onSelectPreset(p)}
                >
                  <span>{p.label}</span>
                  <span
                    style={{
                      fontSize: "11px",
                      opacity: 0.8,
                      background: isActive ? "rgba(0, 237, 100, 0.2)" : "rgba(0, 30, 43, 0.08)",
                      padding: "1px 6px",
                      borderRadius: "9999px"
                    }}
                  >
                    {p.badge}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
