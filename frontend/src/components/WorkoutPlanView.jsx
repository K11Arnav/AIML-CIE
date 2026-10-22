import { useState } from "react";

export default function WorkoutPlanView({ workout, onSelectExercise }) {
  const primary = workout.primary;
  const alternatives = workout.alternatives || [];
  const [selectedPlanIndex, setSelectedPlanIndex] = useState(0); // 0 = primary, 1.. = alternative
  const [activeDayIndex, setActiveDayIndex] = useState(0);

  const activePlan = selectedPlanIndex === 0 ? primary : alternatives[selectedPlanIndex - 1];

  if (!activePlan) {
    return (
      <div className="alert-callout warning">
        No compatible workout plans found for your current equipment constraints. Try selecting a broader equipment category.
      </div>
    );
  }

  const daysList = activePlan.layout?.days || [];
  const currentDay = daysList[activeDayIndex] || daysList[0];
  const dc = activePlan.duration_check || {};
  const unmetWarnings = workout.unmet || [];

  return (
    <div>
      {/* Injury / Safety Unmet Notes */}
      {unmetWarnings.length > 0 && (
        <div className="alert-callout warning">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}>
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div>
            <strong>Medical &amp; Physical Safeguard Warning:</strong>
            <ul style={{ paddingLeft: "18px", marginTop: "4px" }}>
              {unmetWarnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* 3-Tier Plan Comparison Cards (MongoDB Pricing Tier Style) */}
      <div style={{ marginBottom: "32px" }}>
        <div className="section-eyebrow">EQUIPMENT-CONSTRAINED PERIODIZATION</div>
        <h3 style={{ fontSize: "24px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "16px" }}>
          Selected Workout Architecture
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "20px" }}>
          {/* Primary Plan Card (Featured) */}
          {primary && (
            <div className={selectedPlanIndex === 0 ? "pricing-card-featured" : "pricing-card"}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <span className="badge-popular">Primary Model Match</span>
                <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--color-brand-green-dark)" }}>
                  {(primary.model_probability * 100).toFixed(1)}% prob
                </span>
              </div>

              <h4 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "6px" }}>
                {primary.plan}
              </h4>
              <p style={{ fontSize: "13px", color: "var(--color-slate)", marginBottom: "16px" }}>
                {primary.style} · {primary.workout_days_per_week} days/week · {primary.sets} sets scheme
              </p>

              <div style={{ fontSize: "12px", color: "var(--color-steel)", background: "white", padding: "10px", borderRadius: "6px", marginBottom: "16px" }}>
                <div><strong>Equipment:</strong> {primary.equipment}</div>
                <div><strong>Experience:</strong> {primary.experience_level}</div>
              </div>

              <button
                type="button"
                className={selectedPlanIndex === 0 ? "btn-primary" : "btn-secondary"}
                onClick={() => { setSelectedPlanIndex(0); setActiveDayIndex(0); }}
                style={{ width: "100%", marginTop: "auto" }}
              >
                {selectedPlanIndex === 0 ? "✓ Currently Viewing" : "Switch to Primary Plan"}
              </button>
            </div>
          )}

          {/* Alternative Plan Cards */}
          {alternatives.map((alt, idx) => {
            const isSelected = selectedPlanIndex === idx + 1;
            return (
              <div key={alt.plan} className={isSelected ? "pricing-card-featured" : "pricing-card"}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                  <span className="badge-purple">Alternative {idx + 1}</span>
                  <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--color-slate)" }}>
                    {(alt.model_probability * 100).toFixed(1)}% prob
                  </span>
                </div>

                <h4 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "6px" }}>
                  {alt.plan}
                </h4>
                <p style={{ fontSize: "13px", color: "var(--color-slate)", marginBottom: "16px" }}>
                  {alt.style} · {alt.workout_days_per_week} days/week
                </p>

                <div style={{ fontSize: "12px", color: "var(--color-steel)", background: "var(--color-surface)", padding: "10px", borderRadius: "6px", marginBottom: "16px" }}>
                  <div><strong>Equipment:</strong> {alt.equipment}</div>
                  <div><strong>Experience:</strong> {alt.experience_level}</div>
                </div>

                <button
                  type="button"
                  className={isSelected ? "btn-primary" : "btn-secondary"}
                  onClick={() => { setSelectedPlanIndex(idx + 1); setActiveDayIndex(0); }}
                  style={{ width: "100%", marginTop: "auto" }}
                >
                  {isSelected ? "✓ Currently Viewing" : `Select Alternative ${idx + 1}`}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Heuristic Duration Check Panel */}
      <div className="card-base" style={{ marginBottom: "32px", padding: "20px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div style={{ fontSize: "12px", color: "var(--color-steel)", fontWeight: 600, textTransform: "uppercase" }}>
              Session Duration Validation
            </div>
            <div style={{ fontSize: "16px", fontWeight: 600, color: "var(--color-ink)", marginTop: "2px" }}>
              Estimated: ~{dc.estimated ?? "45"} min/session (Requested: {dc.requested ?? "–"} min)
            </div>
            <div style={{ fontSize: "13px", color: "var(--color-slate)", marginTop: "4px" }}>
              {dc.note}
            </div>
          </div>

          <span className={dc.fits !== false ? "badge-green-soft" : "badge-orange"}>
            {dc.fits !== false ? "✓ Fits Time Budget" : "⚠️ Exceeds Requested Time"}
          </span>
        </div>
      </div>

      {/* Weekly Schedule & Exercises Table */}
      <div className="card-feature">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div className="section-eyebrow">DAY-BY-DAY EXERCISE PROTOCOL</div>
            <h4 style={{ fontSize: "22px", fontWeight: 600, color: "var(--color-ink)" }}>
              Weekly Exercise Schedule
            </h4>
          </div>

          {/* Day Tabs */}
          <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
            {daysList.map((d, i) => (
              <button
                key={d.day}
                type="button"
                className={`pill-tab ${activeDayIndex === i ? "pill-tab-active" : ""}`}
                onClick={() => setActiveDayIndex(i)}
                style={{ padding: "6px 14px", fontSize: "13px" }}
              >
                {d.day}
              </button>
            ))}
          </div>
        </div>

        {currentDay && (
          <div>
            <div style={{ background: "var(--color-surface)", padding: "12px 16px", borderRadius: "8px", marginBottom: "16px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "14px", fontWeight: 600, color: "var(--color-ink)" }}>
                Focus: {currentDay.body_part}
              </span>
              <span style={{ fontSize: "12px", color: "var(--color-steel)" }}>
                {currentDay.exercises?.length || 0} exercises assigned
              </span>
            </div>

            <div className="comparison-table-wrap">
              <table className="comparison-table">
                <thead>
                  <tr>
                    <th>Exercise Name</th>
                    <th>Muscle Target</th>
                    <th>Volume / Sets</th>
                    <th>Repetitions</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(currentDay.exercises || []).map((ex, exIdx) => (
                    <tr key={`${ex.name}-${exIdx}`}>
                      <td style={{ fontWeight: 600, color: "var(--color-ink)" }}>
                        {ex.name}
                      </td>
                      <td>
                        <span className="badge-purple" style={{ fontSize: "10px" }}>
                          {ex.body_part || currentDay.body_part || "Compound"}
                        </span>
                      </td>
                      <td>{ex.sets ?? "3"} sets</td>
                      <td>{ex.reps ?? "10-12"}</td>
                      <td>
                        <button
                          type="button"
                          className="btn-ghost"
                          onClick={() => onSelectExercise({ ...ex, body_part: ex.body_part || currentDay.body_part })}
                          style={{ fontSize: "12px", color: "var(--color-brand-green-dark)", fontWeight: 600 }}
                        >
                          View Movement Guide →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
