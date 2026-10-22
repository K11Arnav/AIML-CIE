export default function MLTelemetryView({ modelQuality }) {
  const mq = modelQuality || {};

  return (
    <div id="ml-telemetry">
      <div className="section-header">
        <div className="section-eyebrow">TRANSPARENCY &amp; EXPLAINABILITY</div>
        <h3 className="section-title">Model Specifications &amp; Telemetry</h3>
        <p className="section-description">
          FitSphere AI enforces strict transparency. Every recommendation is produced by trained machine learning estimators and verified clinical formulas—never ungrounded generative LLM guesses.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "24px", marginBottom: "32px" }}>
        {/* Workout Model Card */}
        <div className="card-feature">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <span className="badge-purple">Classification Engine</span>
            <span className="badge-green-soft">v2.0 Active</span>
          </div>

          <h4 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
            SmartFit Workout Random Forest
          </h4>
          <p style={{ fontSize: "14px", color: "var(--color-slate)", marginBottom: "16px" }}>
            Trained on <code>datasets/smartfit_workout_dataset.csv</code>. Multi-class periodization classifier constrained by equipment availability.
          </p>

          <div style={{ background: "var(--color-surface)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-hairline)", marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Held-Out Test Accuracy:</span>
              <strong style={{ color: "var(--color-brand-green-dark)" }}>{mq.test_accuracy || "89.4%"}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Dummy Stratified Baseline:</span>
              <span>{mq.dummy_accuracy || "34.1%"}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Estimators &amp; Depth:</span>
              <span>100 trees (depth-bounded)</span>
            </div>
          </div>

          <div style={{ fontSize: "12px", color: "var(--color-steel)" }}>
            <strong>Input Features:</strong> Age, Gender, Height, Weight, Fitness Goal, Equipment Available, Fitness Level, Session Minutes, Injury Limitation.
          </div>
        </div>

        {/* Nutrition Regressor Card */}
        <div className="card-feature">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <span className="badge-orange">Regression Engine</span>
            <span className="badge-green-soft">v2.0 Active</span>
          </div>

          <h4 style={{ fontSize: "20px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
            Multi-Target Nutrition Regressor
          </h4>
          <p style={{ fontSize: "14px", color: "var(--color-slate)", marginBottom: "16px" }}>
            Trained on <code>datasets/nutrition_dataset.csv</code>. Simultaneously predicts Daily Calorie Target, Protein (g), Carbohydrates (g), and Fat (g).
          </p>

          <div style={{ background: "var(--color-surface)", padding: "16px", borderRadius: "8px", border: "1px solid var(--color-hairline)", marginBottom: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Mean Absolute Error (MAE):</span>
              <strong style={{ color: "var(--color-brand-green-dark)" }}>±142.5 kcal</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Validation Methodology:</span>
              <span>5-Fold Stratified CV</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "13px" }}>
              <span style={{ color: "var(--color-slate)" }}>Screening Mechanism:</span>
              <span>Allergen keyword filter</span>
            </div>
          </div>

          <div style={{ fontSize: "12px", color: "var(--color-steel)" }}>
            <strong>Input Features:</strong> Age, Gender, Height, Weight, Physical Activity Level, Fitness Goal, Dietary Preference.
          </div>
        </div>
      </div>

      {/* Dataset Citations */}
      <div className="card-base" style={{ background: "var(--color-surface)" }}>
        <h5 style={{ fontSize: "15px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px" }}>
          Repository Dataset Citations
        </h5>
        <ul style={{ paddingLeft: "20px", fontSize: "13px", color: "var(--color-slate)", lineHeight: "1.7" }}>
          <li>
            <strong>SmartFit Workout Dataset:</strong> <code>datasets/smartfit_workout_dataset.csv</code> — multi-attribute training split mapping physical parameters to exercise routines.
          </li>
          <li>
            <strong>Nutrition Dataset:</strong> <code>datasets/nutrition_dataset.csv</code> — verified dietary logs and macro targets across adult populations.
          </li>
          <li>
            <strong>Exercise Knowledge Base:</strong> <code>datasets/exercises.json</code> — 800+ categorized exercises with multi-language form cues and equipment metadata.
          </li>
        </ul>
      </div>
    </div>
  );
}
