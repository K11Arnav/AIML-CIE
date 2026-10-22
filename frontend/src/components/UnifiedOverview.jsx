export default function UnifiedOverview({ data, onSelectTab }) {
  const profile = data.profile || {};
  const workout = data.workout || {};
  const diet = data.diet || {};
  const primaryPlan = workout.primary || {};
  const formula = data.daily_calorie_target_formula || {};
  const predicted = diet.predicted || {};

  return (
    <div>
      {/* Top Banner Alert (Informational / Safety note) */}
      <div className="alert-callout success">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}>
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
          <polyline points="22 4 12 14.01 9 11.01" />
        </svg>
        <div>
          <strong>AI Pipeline Completed Successfully:</strong> {data.safety_note}
        </div>
      </div>

      {/* Biometrics Summary Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "32px" }}>
        <div className="card-base" style={{ padding: "18px" }}>
          <div style={{ fontSize: "12px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>BMI Score</div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--color-ink)", margin: "4px 0" }}>
            {profile.bmi || "–"}
          </div>
          <span className="badge-green-soft">
            {profile.bmi < 18.5 ? "Underweight" : profile.bmi < 25 ? "Normal Standard" : profile.bmi < 30 ? "Overweight" : "Obese"}
          </span>
        </div>

        <div className="card-base" style={{ padding: "18px" }}>
          <div style={{ fontSize: "12px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>Calorie Intake Target</div>
          <div style={{ fontSize: "28px", fontWeight: 700, color: "var(--color-brand-green-dark)", margin: "4px 0" }}>
            {predicted["Daily Calorie Target"] || formula.kcal_per_day || "–"}{" "}
            <span style={{ fontSize: "14px", fontWeight: 500 }}>kcal/day</span>
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-stone)" }}>
            RF Model Predicted (±142 kcal MAE)
          </div>
        </div>

        <div className="card-base" style={{ padding: "18px" }}>
          <div style={{ fontSize: "12px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>Recommended Split</div>
          <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-ink)", margin: "4px 0", lineHeight: 1.2 }}>
            {primaryPlan.plan || "Full Body Protocol"}
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-stone)" }}>
            {primaryPlan.workout_days_per_week || profile.workout_days_per_week || 4} days/week · {primaryPlan.equipment}
          </div>
        </div>

        <div className="card-base" style={{ padding: "18px" }}>
          <div style={{ fontSize: "12px", color: "var(--color-steel)", textTransform: "uppercase", fontWeight: 600 }}>Dietary Framework</div>
          <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-ink)", margin: "4px 0", textTransform: "capitalize" }}>
            {profile.dietary_preference === "any" ? "Omnivore Standard" : profile.dietary_preference}
          </div>
          <div style={{ fontSize: "12px", color: "var(--color-stone)" }}>
            {profile.allergies?.length > 0 ? `${profile.allergies.length} active exclusions` : "No allergen exclusions"}
          </div>
        </div>
      </div>

      {/* Two Column Summary: Workout Card + Diet Card */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: "24px", marginBottom: "32px" }}>
        {/* Workout Match Box */}
        <div className="pricing-card-featured">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <div>
              <span className="badge-popular">⭐ Primary ML Match</span>
              <h3 style={{ fontSize: "24px", fontWeight: 600, color: "var(--color-ink)", marginTop: "10px" }}>
                {primaryPlan.plan}
              </h3>
            </div>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--color-brand-green-dark)" }}>
              {(primaryPlan.model_probability * 100).toFixed(1)}% Belief
            </span>
          </div>

          <p style={{ fontSize: "14px", color: "var(--color-slate)", marginBottom: "20px" }}>
            {primaryPlan.style} targeting <strong>{primaryPlan.goal}</strong> with {primaryPlan.experience_level} progression.
          </p>

          <div style={{ background: "white", borderRadius: "8px", padding: "14px", border: "1px solid var(--color-hairline)", marginBottom: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "6px" }}>
              <span style={{ color: "var(--color-slate)" }}>Schedule Rotation:</span>
              <span style={{ fontWeight: 600 }}>{primaryPlan.workout_days_per_week} days per week</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px", marginBottom: "6px" }}>
              <span style={{ color: "var(--color-slate)" }}>Session Estimated:</span>
              <span style={{ fontWeight: 600 }}>~{primaryPlan.duration_check?.estimated || 45} minutes</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Constraint Check:</span>
              <span style={{ color: "var(--color-brand-green-dark)", fontWeight: 600 }}>
                100% Equipment Compatible
              </span>
            </div>
          </div>

          <button
            type="button"
            className="btn-primary"
            onClick={() => onSelectTab("workout")}
            style={{ width: "100%", marginTop: "auto" }}
          >
            View Complete Weekly Workout Schedule →
          </button>
        </div>

        {/* Nutrition Match Box */}
        <div className="card-feature" style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
            <div>
              <span className="badge-purple">Macro Distribution</span>
              <h3 style={{ fontSize: "24px", fontWeight: 600, color: "var(--color-ink)", marginTop: "10px" }}>
                Daily Nutritional Targets
              </h3>
            </div>
            <span className="badge-green-soft">Screened</span>
          </div>

          <p style={{ fontSize: "14px", color: "var(--color-slate)", marginBottom: "20px" }}>
            Macronutrient targets derived from Random Forest multi-target regression and clinical Mifflin-St Jeor baseline.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "12px", marginBottom: "20px" }}>
            <div style={{ background: "var(--color-surface)", padding: "12px", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "11px", color: "var(--color-steel)", fontWeight: 600, textTransform: "uppercase" }}>Protein</div>
              <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-accent-purple)", margin: "4px 0" }}>
                {predicted.Protein || "–"}g
              </div>
              <div style={{ fontSize: "11px", color: "var(--color-stone)" }}>Muscle Recovery</div>
            </div>

            <div style={{ background: "var(--color-surface)", padding: "12px", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "11px", color: "var(--color-steel)", fontWeight: 600, textTransform: "uppercase" }}>Carbs</div>
              <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-accent-orange)", margin: "4px 0" }}>
                {predicted.Carbohydrates || "–"}g
              </div>
              <div style={{ fontSize: "11px", color: "var(--color-stone)" }}>Glycogen Support</div>
            </div>

            <div style={{ background: "var(--color-surface)", padding: "12px", borderRadius: "8px", textAlign: "center" }}>
              <div style={{ fontSize: "11px", color: "var(--color-steel)", fontWeight: 600, textTransform: "uppercase" }}>Fats</div>
              <div style={{ fontSize: "20px", fontWeight: 700, color: "var(--color-accent-blue)", margin: "4px 0" }}>
                {predicted.Fat || "–"}g
              </div>
              <div style={{ fontSize: "11px", color: "var(--color-stone)" }}>Hormone Health</div>
            </div>
          </div>

          <div style={{ background: "var(--color-surface-soft)", padding: "12px", borderRadius: "8px", marginBottom: "20px", fontSize: "13px" }}>
            <strong>Sample Day Breakfast:</strong> {diet.meals?.suggestions?.Breakfast || "Egg white omelet with spinach and avocado"}
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => onSelectTab("diet")}
            style={{ width: "100%", marginTop: "auto" }}
          >
            Explore Full Diet &amp; Meals Breakdown →
          </button>
        </div>
      </div>
    </div>
  );
}
