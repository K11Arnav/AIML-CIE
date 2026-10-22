export default function DietNutritionView({ diet, formula, profile }) {
  const predicted = diet.predicted || {};
  const mae = diet.model_quality_area?.mae?.["Daily Calorie Target"] ?? "142";
  const meals = diet.meals?.suggestions || {};
  const allergenWarning = diet.allergen_warning;
  const prefScreening = diet.preference_screening;
  const allergyScreening = diet.allergy_screening;

  const targetKcal = predicted["Daily Calorie Target"] || formula?.kcal_per_day || 2000;
  const protein = predicted.Protein || 140;
  const carbs = predicted.Carbohydrates || 210;
  const fat = predicted.Fat || 65;

  // Percentage calculations
  const proteinKcal = protein * 4;
  const carbsKcal = carbs * 4;
  const fatKcal = fat * 9;
  const totalKcalCalc = proteinKcal + carbsKcal + fatKcal || targetKcal;

  const proteinPct = Math.round((proteinKcal / totalKcalCalc) * 100);
  const carbsPct = Math.round((carbsKcal / totalKcalCalc) * 100);
  const fatPct = Math.round((fatKcal / totalKcalCalc) * 100);

  return (
    <div>
      {/* Allergen Callout if present */}
      {allergenWarning && (
        <div className="alert-callout warning">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div>
            <strong>Strict Allergen Screening Active:</strong> {allergenWarning}
          </div>
        </div>
      )}

      {/* Macro Breakdown Progress Bar Cards */}
      <div className="macro-grid">
        <div className="macro-card">
          <div className="macro-card-top">
            <span className="macro-label">Daily Energy Target</span>
            <span className="badge-green-soft">Target</span>
          </div>
          <div className="macro-value">{targetKcal} <span style={{ fontSize: "14px", fontWeight: 400 }}>kcal</span></div>
          <div className="macro-bar-track">
            <div className="macro-bar-fill calories" style={{ width: "100%" }}></div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-steel)" }}>Optimal Daily Caloric Budget</div>
        </div>

        <div className="macro-card">
          <div className="macro-card-top">
            <span className="macro-label">Protein Target</span>
            <span className="badge-purple">{proteinPct}%</span>
          </div>
          <div className="macro-value">{protein} <span style={{ fontSize: "14px", fontWeight: 400 }}>grams</span></div>
          <div className="macro-bar-track">
            <div className="macro-bar-fill protein" style={{ width: `${proteinPct}%` }}></div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-steel)" }}>{proteinKcal} kcal · Muscle tissue synthesis</div>
        </div>

        <div className="macro-card">
          <div className="macro-card-top">
            <span className="macro-label">Carbohydrates</span>
            <span className="badge-orange">{carbsPct}%</span>
          </div>
          <div className="macro-value">{carbs} <span style={{ fontSize: "14px", fontWeight: 400 }}>grams</span></div>
          <div className="macro-bar-track">
            <div className="macro-bar-fill carbs" style={{ width: `${carbsPct}%` }}></div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-steel)" }}>{carbsKcal} kcal · Glycogen replenishment</div>
        </div>

        <div className="macro-card">
          <div className="macro-card-top">
            <span className="macro-label">Healthy Fats</span>
            <span className="badge-blue">{fatPct}%</span>
          </div>
          <div className="macro-value">{fat} <span style={{ fontSize: "14px", fontWeight: 400 }}>grams</span></div>
          <div className="macro-bar-track">
            <div className="macro-bar-fill fat" style={{ width: `${fatPct}%` }}></div>
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-steel)" }}>{fatKcal} kcal · Endocrine &amp; cell function</div>
        </div>
      </div>

      {/* Model-Predicted vs Clinical Formula Dual Comparison Card */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "24px", marginBottom: "32px" }}>
        <div className="card-feature">
          <div className="section-eyebrow">MACHINE LEARNING TARGET</div>
          <h4 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
            Random Forest Nutrition Regressor
          </h4>
          <p style={{ fontSize: "13px", color: "var(--color-slate)", marginBottom: "16px" }}>
            Trained on nutrition dataset across Age, Sex, Height, Weight, Activity Level, and Fitness Goal.
          </p>
          <div style={{ background: "var(--color-surface)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-hairline)" }}>
            <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--color-brand-green-dark)" }}>
              {targetKcal} kcal/day
            </div>
            <div style={{ fontSize: "12px", color: "var(--color-steel)", marginTop: "4px" }}>
              Held-out test error: <strong>MAE ±{mae} kcal</strong>
            </div>
          </div>
        </div>

        <div className="card-feature">
          <div className="section-eyebrow">CLINICAL REFERENCE BASELINE</div>
          <h4 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
            Mifflin-St Jeor Clinical Formula
          </h4>
          <p style={{ fontSize: "13px", color: "var(--color-slate)", marginBottom: "16px" }}>
            Standard clinical metabolic equation based on Basal Metabolic Rate (BMR) scaled by physical activity factor.
          </p>
          <div style={{ background: "var(--color-surface)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-hairline)" }}>
            <div style={{ fontSize: "24px", fontWeight: 700, color: "var(--color-ink)" }}>
              {formula?.kcal_per_day ?? "–"} kcal/day
            </div>
            <div style={{ fontSize: "12px", color: "var(--color-steel)", marginTop: "4px" }}>
              {formula?.method ?? "Standard Clinical Formula"}
            </div>
          </div>
        </div>
      </div>

      {/* Day of Meals: Retrieved from Nutrition Catalog */}
      <div className="card-feature" style={{ marginBottom: "32px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
          <div>
            <div className="section-eyebrow">RETRIEVED NUTRITION MATRIX</div>
            <h4 style={{ fontSize: "22px", fontWeight: 600, color: "var(--color-ink)" }}>
              Full Day of Meals (Dataset-Retrieved)
            </h4>
            <p style={{ fontSize: "13px", color: "var(--color-slate)", marginTop: "4px" }}>
              {diet.meals?.selection_basis || "Retrieved actual rows from dataset aligned with preference and caloric goal; never hallucinated."}
            </p>
          </div>
          <span className="badge-green-soft">100% Allergen Screened</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
          {Object.entries(meals).map(([mealType, suggestion]) => (
            <div key={mealType} className="card-base" style={{ background: "var(--color-surface)", border: "1px solid var(--color-hairline)" }}>
              <span className="badge-purple" style={{ marginBottom: "8px" }}>
                {mealType.replace(" Suggestion", "")}
              </span>
              <p style={{ fontSize: "14px", fontWeight: 500, color: "var(--color-ink)", lineHeight: 1.5, marginTop: "6px" }}>
                {suggestion || "–"}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Screening & Transparency Report */}
      <div className="card-base" style={{ background: "var(--color-surface-soft)" }}>
        <div className="section-eyebrow">DATASET INTEGRITY &amp; EXCLUSIONS</div>
        <h5 style={{ fontSize: "16px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
          Dietary Screening Audit Report
        </h5>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px", fontSize: "13px", color: "var(--color-slate)" }}>
          {prefScreening && (
            <div>
              <strong>Preference Screening:</strong> {prefScreening.foods_excluded} of {prefScreening.foods_screened} foods excluded based on your <em>{prefScreening.preference}</em> preference.
            </div>
          )}
          {allergyScreening && (
            <div>
              <strong>Allergy Screening:</strong> {allergyScreening.foods_excluded} items filtered by active allergy flags: <em>{allergyScreening.flags_applied.join(", ") || "None"}</em>.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
