import { useMemo } from "react";

export default function ProfileForm({
  form,
  onChange,
  onSubmit,
  options,
  isLoading,
  onReset
}) {
  // Live calculated BMI
  const bmiInfo = useMemo(() => {
    const h = Number(form.height_cm);
    const w = Number(form.weight_kg);
    if (!h || !w || h <= 0 || w <= 0) return null;
    const heightM = h / 100;
    const bmi = Number((w / (heightM * heightM)).toFixed(1));
    let cat = "Normal weight";
    let status = "normal";
    if (bmi < 18.5) {
      cat = "Underweight";
      status = "warning";
    } else if (bmi >= 25 && bmi < 30) {
      cat = "Overweight";
      status = "warning";
    } else if (bmi >= 30) {
      cat = "Obese";
      status = "warning";
    }
    return { bmi, cat, status };
  }, [form.height_cm, form.weight_kg]);

  const toggleAllergy = (allergy) => {
    const current = form.allergies || [];
    if (current.includes(allergy)) {
      onChange("allergies", current.filter((a) => a !== allergy));
    } else {
      onChange("allergies", [...current, allergy]);
    }
  };

  const removeAllergy = (allergy) => {
    const current = form.allergies || [];
    onChange("allergies", current.filter((a) => a !== allergy));
  };

  const goalOptions = options?.goals || [
    "Muscle Gain", "Weight Loss", "General Health", "Strength",
    "Endurance", "Tone Up", "Powerlifting", "Flexibility",
    "CrossFit", "Athletic Performance", "Marathon Training"
  ];

  const equipmentOptions = options?.equipment || [
    { value: "bodyweight only", label: "Bodyweight / no equipment" },
    { value: "yoga mat", label: "Yoga mat (mobility, floor work)" },
    { value: "home dumbbells", label: "Home dumbbells / kettlebell" },
    { value: "full home gym", label: "Full home gym (barbell + rack)" },
    { value: "gym membership", label: "Gym membership (machines, cables, barbell)" }
  ];

  const allergyList = options?.allergies || [
    "Gluten", "Peanuts", "Dairy", "Tree nuts", "Soy", "Eggs", "Fish / seafood"
  ];

  return (
    <section id="assessment" className="container" style={{ padding: "64px 24px" }}>
      <div className="section-header">
        <div className="section-eyebrow">UNIFIED AI RECOMMENDATION STUDIO</div>
        <h2 className="section-title">Configure Your Biometrics &amp; Preferences</h2>
        <p className="section-description">
          One single submission passes all features into the Random Forest workout classifier and
          the nutrition regression model. No redundant input; everything is enforced by strict ML constraints.
        </p>
      </div>

      <form onSubmit={onSubmit} className="form-card">
        <div className="form-header">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span className="badge-green-soft">Dual-Stage Engine</span>
            <span style={{ fontSize: "14px", color: "var(--color-slate)" }}>
              All fields are consumed as model features
            </span>
          </div>

          <button
            type="button"
            className="btn-ghost"
            onClick={onReset}
            style={{ fontSize: "13px" }}
          >
            Reset to Default
          </button>
        </div>

        <div className="form-body">
          {/* SECTION 1: BIOMETRICS & BMI GAUGE */}
          <div className="form-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            <span>1. Core Biometrics</span>
          </div>

          <div className="form-grid-3">
            <div className="form-field">
              <label className="form-label" htmlFor="age-input">
                <span>Age (Years)</span>
                <span className="form-hint">5 – 100</span>
              </label>
              <input
                id="age-input"
                className="text-input"
                type="number"
                min="5"
                max="100"
                value={form.age}
                onChange={(e) => onChange("age", e.target.value)}
                required
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="height-input">
                <span>Height (cm)</span>
                <span className="form-hint">50 – 250 cm</span>
              </label>
              <input
                id="height-input"
                className="text-input"
                type="number"
                min="50"
                max="250"
                value={form.height_cm}
                onChange={(e) => onChange("height_cm", e.target.value)}
                required
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="weight-input">
                <span>Weight (kg)</span>
                <span className="form-hint">20 – 300 kg</span>
              </label>
              <input
                id="weight-input"
                className="text-input"
                type="number"
                step="0.1"
                min="20"
                max="300"
                value={form.weight_kg}
                onChange={(e) => onChange("weight_kg", e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-grid-2" style={{ marginBottom: "32px", alignItems: "center" }}>
            <div className="form-field">
              <label className="form-label" htmlFor="gender-select">
                <span>Biological Sex (BMR &amp; Model Feature)</span>
              </label>
              <select
                id="gender-select"
                className="text-input"
                value={form.gender}
                onChange={(e) => onChange("gender", e.target.value)}
              >
                <option value="Female">Female</option>
                <option value="Male">Male</option>
              </select>
            </div>

            {/* Live BMI Indicator */}
            {bmiInfo && (
              <div className="bmi-preview-card">
                <div>
                  <div style={{ fontSize: "12px", color: "var(--color-steel)", fontWeight: 600, textTransform: "uppercase" }}>
                    Live BMI Estimate
                  </div>
                  <div className="bmi-val-block">
                    <span className="bmi-number">{bmiInfo.bmi}</span>
                    <span className={`bmi-category-tag ${bmiInfo.status}`}>
                      {bmiInfo.cat}
                    </span>
                  </div>
                </div>
                <div style={{ textAlign: "right", fontSize: "12px", color: "var(--color-stone)" }}>
                  <div>Healthy standard: 18.5 – 24.9</div>
                  <div>Used for calorie expenditure weighting</div>
                </div>
              </div>
            )}
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--color-hairline)", margin: "32px 0" }} />

          {/* SECTION 2: WORKOUT ENVIRONMENT & CONSTRAINTS */}
          <div className="form-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M6 5v14M18 5v14M2 9h4M2 15h4M18 9h4M18 15h4M6 12h12" />
            </svg>
            <span>2. Workout Goals &amp; Equipment Constraints</span>
          </div>

          <div className="form-grid-3">
            <div className="form-field">
              <label className="form-label" htmlFor="goal-select">
                <span>Primary Goal</span>
              </label>
              <select
                id="goal-select"
                className="text-input"
                value={form.goal}
                onChange={(e) => onChange("goal", e.target.value)}
              >
                {goalOptions.map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="equipment-select">
                <span>Available Equipment</span>
              </label>
              <select
                id="equipment-select"
                className="text-input"
                value={form.equipment}
                onChange={(e) => onChange("equipment", e.target.value)}
              >
                {equipmentOptions.map((eq) => (
                  <option key={eq.value} value={eq.value}>{eq.label}</option>
                ))}
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="duration-input">
                <span>Session Duration (Minutes)</span>
                <span className="form-hint">Heuristic Check</span>
              </label>
              <input
                id="duration-input"
                className="text-input"
                type="number"
                min="15"
                max="180"
                value={form.workout_duration_minutes}
                onChange={(e) => onChange("workout_duration_minutes", e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-grid-3" style={{ marginBottom: "32px" }}>
            <div className="form-field">
              <label className="form-label" htmlFor="fitness-level-select">
                <span>Fitness Experience Level</span>
              </label>
              <select
                id="fitness-level-select"
                className="text-input"
                value={form.fitness_level}
                onChange={(e) => onChange("fitness_level", e.target.value)}
              >
                <option value="beginner">Beginner (0-1 yr)</option>
                <option value="intermediate">Intermediate (1-3 yrs)</option>
                <option value="advanced">Advanced (3+ yrs)</option>
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="workout-days-input">
                <span>Frequency (Days / Week)</span>
                <span className="form-hint">1 to 7</span>
              </label>
              <input
                id="workout-days-input"
                className="text-input"
                type="number"
                min="1"
                max="7"
                value={form.workout_days_per_week}
                onChange={(e) => onChange("workout_days_per_week", e.target.value)}
                required
              />
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="injury-select">
                <span>Injury / Limitation Focus</span>
              </label>
              <select
                id="injury-select"
                className="text-input"
                value={form.injuries_or_limitations}
                onChange={(e) => onChange("injuries_or_limitations", e.target.value)}
              >
                <option value="none">None (Full Clearance)</option>
                <option value="knee">Knee limitation</option>
                <option value="shoulder">Shoulder limitation</option>
                <option value="back">Lower Back limitation</option>
                <option value="ankle">Ankle limitation</option>
              </select>
            </div>
          </div>

          <hr style={{ border: "none", borderTop: "1px solid var(--color-hairline)", margin: "32px 0" }} />

          {/* SECTION 3: DIET & NUTRITION ARCHITECTURE */}
          <div className="form-section-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
              <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
              <line x1="6" y1="1" x2="6" y2="4" />
              <line x1="10" y1="1" x2="10" y2="4" />
              <line x1="14" y1="1" x2="14" y2="4" />
            </svg>
            <span>3. Dietary Architecture &amp; Allergies</span>
          </div>

          <div className="form-grid-2" style={{ marginBottom: "24px" }}>
            <div className="form-field">
              <label className="form-label" htmlFor="activity-level-select">
                <span>Activity Level (TDEE Factor)</span>
              </label>
              <select
                id="activity-level-select"
                className="text-input"
                value={form.activity_level}
                onChange={(e) => onChange("activity_level", e.target.value)}
              >
                <option value="sedentary">Sedentary (Desk job, little exercise)</option>
                <option value="lightly active">Lightly Active (1-3 days/wk)</option>
                <option value="moderately active">Moderately Active (3-5 days/wk)</option>
                <option value="very active">Very Active (6-7 days/wk heavy)</option>
              </select>
            </div>

            <div className="form-field">
              <label className="form-label" htmlFor="diet-pref-select">
                <span>Dietary Preference</span>
              </label>
              <select
                id="diet-pref-select"
                className="text-input"
                value={form.dietary_preference}
                onChange={(e) => onChange("dietary_preference", e.target.value)}
              >
                <option value="any">Any (No specific preference)</option>
                <option value="omnivore">Omnivore (Meat, Fish, Plants)</option>
                <option value="vegetarian">Vegetarian (No meat/fish)</option>
                <option value="vegan">Vegan (100% Plant-based)</option>
              </select>
            </div>
          </div>

          {/* Allergy Multiselect Chips */}
          <div className="form-field" style={{ marginBottom: "32px" }}>
            <div className="multiselect-fieldset">
              <div className="multiselect-legend">Allergies &amp; Strict Exclusions (Hard Excluded in Catalog)</div>

              <div className="selected-chips-row">
                {(!form.allergies || form.allergies.length === 0) ? (
                  <span style={{ fontSize: "13px", color: "var(--color-stone)", fontStyle: "italic" }}>
                    No allergens selected (all food categories eligible)
                  </span>
                ) : (
                  form.allergies.map((allergy) => (
                    <span key={allergy} className="selected-chip">
                      <span>{allergy}</span>
                      <button
                        type="button"
                        className="chip-remove-btn"
                        onClick={() => removeAllergy(allergy)}
                        title={`Remove ${allergy}`}
                      >
                        ×
                      </button>
                    </span>
                  ))
                )}
              </div>

              <div className="checkbox-options-grid">
                {allergyList.map((allergy) => {
                  const isChecked = form.allergies?.includes(allergy);
                  return (
                    <label key={allergy} className="custom-checkbox-label">
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => toggleAllergy(allergy)}
                      />
                      <span>{allergy}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Submit Button (Pill button-primary with bright MongoDB green) */}
          <div>
            <button
              type="submit"
              className="btn-primary"
              disabled={isLoading}
              style={{
                width: "100%",
                padding: "14px 28px",
                fontSize: "16px",
                borderRadius: "var(--rounded-full)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px"
              }}
            >
              {isLoading ? (
                <>
                  <span className="status-dot" style={{ backgroundColor: "#001e2b" }}></span>
                  <span>Executing Dual-Stage Machine Learning Pipeline...</span>
                </>
              ) : (
                <>
                  <span>Generate Personalized Workout &amp; Diet Plan</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
