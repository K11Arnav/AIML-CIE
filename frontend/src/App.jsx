import { useEffect, useState } from "react";
import { fetchWorkout, fetchDiet, fetchHealth, fetchOptions } from "./api.js";

const num = (v) => (v === "" || v === undefined ? undefined : Number(v));

function Field({ label, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function Select({ value, onChange, options, label }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} aria-label={label}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

/** Accessible checkbox multi-select with removable selected chips. */
function MultiSelect({ legend, options, selected, onChange }) {
  const toggle = (v) => onChange(selected.includes(v) ? selected.filter((x) => x !== v) : [...selected, v]);
  return (
    <fieldset className="multi">
      <legend>{legend}</legend>
      <div className="chips">
        {selected.length === 0 && <span className="meta">none selected</span>}
        {selected.map((v) => (
          <span key={v} className="chip">
            {v}
            <button type="button" aria-label={`Remove ${v}`} onClick={() => toggle(v)}>×</button>
          </span>
        ))}
      </div>
      <div className="checks">
        {options.map((o) => (
          <label key={o.value} className="check">
            <input
              type="checkbox"
              checked={selected.includes(o.value)}
              onChange={() => toggle(o.value)}
            />
            {o.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function App() {
  const [health, setHealth] = useState({ state: "loading" });
  const [tab, setTab] = useState("workout");
  const [opts, setOpts] = useState({ state: "loading" });

  const [w, setW] = useState(null);
  const [wRes, setWRes] = useState({ state: "idle" });
  const [d, setD] = useState(null);
  const [dRes, setDRes] = useState({ state: "idle" });

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth({ state: "ok", detail: h }))
      .catch(() => setHealth({ state: "down" }));
    fetchOptions()
      .then((o) => {
        setOpts({ state: "ok" });
        const wd = o.workout.defaults, dd = o.diet.defaults;
        setW({ goal: wd.goal, experience_level: wd.experience_level, equipment: wd.equipment, available_minutes: String(wd.available_minutes), alternatives: "0" });
        setD({
          Age: "30", Gender: "Female", Weight_kg: "65", Height_cm: "165", Severity: "Moderate",
          Physical_Activity_Level: "Active", Daily_Caloric_Intake: "2200", "Cholesterol_mg/dL": "180",
          "Blood_Pressure_mmHg": "120", "Glucose_mg/dL": "95", Weekly_Exercise_Hours: "5",
          Adherence_to_Diet_Plan: "85", Dietary_Nutrient_Imbalance_Score: "1.5",
          Preferred_Cuisine: dd.cuisine, goal: "weight loss",
          allergies: ["Peanuts"], dietary_restrictions: [], top_k: String(dd.top_k),
          course: "main course", diet_preference: "any", max_time_min: "",
        });
        setOpts({ state: "ok", data: o });
      })
      .catch((e) => setOpts({ state: "error", message: e.message }));
  }, []);

  const submitWorkout = async (e) => {
    e.preventDefault();
    setWRes({ state: "loading" });
    try {
      const out = await fetchWorkout({
        goal: w.goal || undefined,
        experience_level: w.experience_level || undefined,
        equipment: w.equipment,
        available_minutes: num(w.available_minutes),
        top_n: (num(w.alternatives) || 0) + 1,  // 1 primary + up to 3 alternatives
      });
      setWRes({ state: "ok", data: out });
    } catch (err) {
      setWRes({ state: "error", message: err.message });
    }
  };

  const submitDiet = async (e) => {
    e.preventDefault();
    setDRes({ state: "loading" });
    try {
      const out = await fetchDiet({
        Age: num(d.Age), Gender: d.Gender, Weight_kg: num(d.Weight_kg), Height_cm: num(d.Height_cm),
        Severity: d.Severity, Physical_Activity_Level: d.Physical_Activity_Level,
        Daily_Caloric_Intake: num(d.Daily_Caloric_Intake), "Cholesterol_mg/dL": num(d["Cholesterol_mg/dL"]),
        "Blood_Pressure_mmHg": num(d["Blood_Pressure_mmHg"]), "Glucose_mg/dL": num(d["Glucose_mg/dL"]),
        Weekly_Exercise_Hours: num(d.Weekly_Exercise_Hours), Adherence_to_Diet_Plan: num(d.Adherence_to_Diet_Plan),
        Dietary_Nutrient_Imbalance_Score: num(d.Dietary_Nutrient_Imbalance_Score),
        Preferred_Cuisine: d.Preferred_Cuisine, goal: d.goal,
        allergies: d.allergies, dietary_restrictions: d.dietary_restrictions,
        top_k: num(d.top_k) || 5,
        course: d.course, diet_preference: d.diet_preference,
        max_time_min: num(d.max_time_min),
      });
      setDRes({ state: "ok", data: out });
    } catch (err) {
      setDRes({ state: "error", message: err.message });
    }
  };

  const set = (setter, key) => (e) => setter((s) => ({ ...s, [key]: e.target.value }));
  const setV = (setter, key) => (v) => setter((s) => ({ ...s, [key]: v }));
  const ov = (arr) => (arr || []).map((v) => ({ value: v, label: v }));

  return (
    <div className="wrap">
      <h1>Fitness Recommendations <small>(local demo)</small></h1>
      <p className="note">Informational only — not medical advice. No chatbot, login, or database in this demo.</p>
      <div className={`health ${health.state}`}>
        Backend: {health.state === "loading" ? "checking…" : health.state === "ok" ? `connected (ML: ${health.detail?.ml_service?.status ?? "?"})` : "unavailable — start backend + ML service"}
      </div>

      <div className="tabs">
        <button className={tab === "workout" ? "active" : ""} onClick={() => setTab("workout")}>Workout</button>
        <button className={tab === "diet" ? "active" : ""} onClick={() => setTab("diet")}>Diet</button>
      </div>

      {opts.state === "loading" && <p className="meta">Loading options…</p>}
      {opts.state === "error" && <p className="error">Could not load options: {opts.message} (is the backend + ML service running?)</p>}

      {opts.state === "ok" && tab === "workout" && w && (
        <section>
          <form onSubmit={submitWorkout} className="form">
            <Field label="Goal">
              <Select label="Goal" value={w.goal} onChange={setV(setW, "goal")} options={ov(opts.data.workout.goals)} />
            </Field>
            <Field label="Experience level">
              <Select label="Experience level" value={w.experience_level} onChange={setV(setW, "experience_level")} options={ov(opts.data.workout.experience_levels)} />
            </Field>
            <Field label="Available minutes">
              <Select label="Available minutes" value={w.available_minutes} onChange={setV(setW, "available_minutes")} options={opts.data.workout.available_minutes.map((m) => ({ value: String(m), label: `${m} min` }))} />
            </Field>
            <Field label="Extra alternatives (pick one instead, not as well)">
              <Select label="Alternatives" value={w.alternatives} onChange={setV(setW, "alternatives")} options={["0", "1", "2", "3"].map((n) => ({ value: n, label: n === "0" ? "None — primary only" : n }))} />
            </Field>
            <div className="full">
              <MultiSelect legend="Equipment (select all you have)" options={ov(opts.data.workout.equipment)} selected={w.equipment} onChange={setV(setW, "equipment")} />
            </div>
            <button type="submit">Get workout plan</button>
          </form>
          {opts.data.workout.notes?.map((n, i) => <p key={i} className="meta">Note: {n}</p>)}
          <Result state={wRes} render={(data) => (
            <div>
              <p className="meta">{data.method} · {data.n_candidates ?? 0} compatible programs · top_n = total plans (1 primary + alternatives)</p>
              <p className="meta">{data.usage}</p>
              {data.unmet?.length > 0 && <p className="warn">Notes: {data.unmet.join("; ")}</p>}
              {!data.primary && <p className="warn">No compatible program — try relaxing a constraint.</p>}
              {data.primary && <PlanCard p={data.primary} heading="Recommended plan" />}
              {data.alternatives?.length > 0 && (
                <div>
                  <h2>Alternatives — choose one instead of the plan above, not as well</h2>
                  {data.alternatives.map((p) => (
                    <PlanCard key={p.program} p={p} heading={p.choice_label || "Alternative"} />
                  ))}
                </div>
              )}
            </div>
          )} />
        </section>
      )}

      {opts.state === "ok" && tab === "diet" && d && (
        <section>
          <form onSubmit={submitDiet} className="form">
            <Field label="Goal">
              <Select label="Diet goal" value={d.goal} onChange={setV(setD, "goal")} options={ov(opts.data.diet.goals)} />
            </Field>
            <Field label="Cuisine">
              <Select label="Cuisine" value={d.Preferred_Cuisine} onChange={setV(setD, "Preferred_Cuisine")} options={ov(opts.data.diet.cuisines)} />
            </Field>
            <Field label="Age"><input value={d.Age} onChange={set(setD, "Age")} inputMode="numeric" /></Field>
            <Field label="Gender">
              <Select label="Gender" value={d.Gender} onChange={setV(setD, "Gender")} options={ov(["Female", "Male"])} />
            </Field>
            <Field label="Weight (kg)"><input value={d.Weight_kg} onChange={set(setD, "Weight_kg")} inputMode="decimal" /></Field>
            <Field label="Height (cm)"><input value={d.Height_cm} onChange={set(setD, "Height_cm")} inputMode="numeric" /></Field>
            <Field label="Results (top_k)">
              <Select label="Results" value={d.top_k} onChange={setV(setD, "top_k")} options={(opts.data.diet.top_k_choices || [3, 5, 10]).map((n) => ({ value: String(n), label: String(n) }))} />
            </Field>
            <Field label="Recipe course">
              <Select label="Course" value={d.course} onChange={setV(setD, "course")} options={["main course", ...(opts.data.diet.recipe_courses || [])].filter((v, i, a) => a.indexOf(v) === i).map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Recipe diet preference">
              <Select label="Diet preference" value={d.diet_preference} onChange={setV(setD, "diet_preference")} options={["any", "vegetarian", "non vegetarian"].map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Max recipe time (min, optional)"><input value={d.max_time_min} onChange={set(setD, "max_time_min")} inputMode="numeric" placeholder="e.g. 45" /></Field>
            <div className="full">
              <MultiSelect legend="Allergies" options={ov(opts.data.diet.allergies)} selected={d.allergies} onChange={setV(setD, "allergies")} />
            </div>
            <div className="full">
              <MultiSelect legend="Dietary restrictions (only Low_Sodium/Low_Sugar enforced)" options={ov(opts.data.diet.dietary_restrictions)} selected={d.dietary_restrictions} onChange={setV(setD, "dietary_restrictions")} />
            </div>
            <button type="submit">Get diet recommendations</button>
          </form>
          {opts.data.diet.notes?.map((n, i) => <p key={i} className="meta">Note: {n}</p>)}
          <Result state={dRes} render={(data) => (
            <div>
              <p className="meta">Predicted category: <b>{data.diet_category?.diet_category}</b> · goal profile: {data.goal_profile} · {data.n_eligible ?? 0} eligible foods</p>
              <p className="meta">Catalog: Indian foods only ({data.catalog_used?.source_dataset}) — {data.catalog_used?.why}</p>
              <p className="meta">{data.scope}</p>
              {data.allergen_warning && <p className="warn">Allergen data unavailable: {data.allergen_warning}</p>}
              {data.filter_notes?.length > 0 && <p className="warn">Filter notes: {data.filter_notes.map((n) => `${n.type}: ${n.value}`).join("; ")}</p>}
              {data.unmet && <p className="warn">{data.unmet}</p>}
              {(data.warnings || []).map((msg, i) => <p key={i} className="warn">{msg}</p>)}
              <ExplainDiet data={data} />
              <h2>Foods you can eat</h2>
              {Object.keys(data.eligible_foods || {}).length === 0 && <p className="warn">No eligible foods under the current filters.</p>}
              {Object.entries(data.eligible_foods || {}).map(([grp, foods]) => (
                <details key={grp} className="explain" open={grp !== "spices"}>
                  <summary>{grp} ({foods.length})</summary>
                  <ul>
                    {foods.map((f) => (
                      <li key={f.name}>{f.name} <span className="meta">· {f.energy_kcal ?? "–"} kcal/100g · {f.evidence}</span></li>
                    ))}
                  </ul>
                </details>
              ))}
              {(data.excluded_foods || []).length > 0 && (
                <details className="explain">
                  <summary>Excluded foods ({data.excluded_foods.length})</summary>
                  <ul>{data.excluded_foods.slice(0, 20).map((f) => <li key={f.name}>{f.name} — {f.evidence}</li>)}</ul>
                </details>
              )}
              <h2>Indian recipes you can consider</h2>
              {data.filtering_summary && <p className="meta">Recipes: {data.filtering_summary.recipes_before_filtering} → diet/course {data.filtering_summary.recipes_after_diet_filter} → ingredient checks {data.filtering_summary.recipes_after_ingredient_checks} → time {data.filtering_summary.recipes_after_time_filter} compatible.</p>}
              {(data.recipes || []).length === 0 && <p className="warn">No recipes passed all filters — constraints were not relaxed. Adjust course, time, or restrictions.</p>}
              {(data.recipes || []).map((rec, i) => (
                <div key={rec.name + i} className="card">
                  <h3>{rec.name} <small>{rec.course || ""} · {rec.diet || ""}</small></h3>
                  <p className="meta">
                    {rec.prep_time != null ? `${rec.prep_time} min prep` : "prep time unknown"} · {rec.cook_time != null ? `${rec.cook_time} min cook` : "cook time unknown"}
                    {rec.state ? ` · ${rec.state}` : ""}{rec.region ? `, ${rec.region}` : ""} · coverage {rec.ingredient_coverage}
                  </p>
                  <p className="meta">Ingredients: {rec.ingredients}</p>
                  {rec.unmatched_ingredients?.length > 0 && <p className="meta">Unresolved: {rec.unmatched_ingredients.join("; ")}</p>}
                  <p className="meta">{rec.explanation}</p>
                </div>
              ))}
              {(data.recipes_needs_review || []).length > 0 && (
                <details className="explain">
                  <summary>Needs ingredient review — NOT verified recommendations ({data.recipes_needs_review.length})</summary>
                  <ul>{data.recipes_needs_review.slice(0, 20).map((rec, i) => <li key={rec.name + i}>{rec.name} — {rec.explanation}</li>)}</ul>
                </details>
              )}
              <h2>Top KNN foods (by nutrient closeness)</h2>
              {data.items?.map((f) => (
                <div key={f.rank + (f.product_name || "")} className="card">
                  <h3>#{f.rank} {f.product_name || "Unnamed product"} <small>{f.food_type || ""}</small></h3>
                  <p className="meta">
                    {f.energy_kcal ?? "–"} kcal/100g · protein {f.proteins_100g ?? "–"}g · fat {f.fat_100g ?? "–"}g · carbs {f.carbs_100g ?? "–"}g ·
                    sugar {f.sugars_100g ?? "–"}g · fiber {f.fiber_100g ?? "–"}g · sodium {f.sodium_100g ?? "–"}g
                    {f.health_score != null ? ` · health score ${f.health_score}` : ""}
                  </p>
                  <p className="meta">Source: {f.explanation?.source_dataset} (per 100 g) · {f.explanation?.cuisine_evidence?.class === "indian_dish" ? "Indian dish" : "staple ingredient"} (matched “{f.explanation?.cuisine_evidence?.matched_term}”){f.explanation?.cuisine_evidence?.branded ? " · branded product" : ""} · allergy: {f.explanation?.allergy_status} — {f.explanation?.allergy_evidence}</p>
                  {f.missing_nutrition?.length > 0 && <p className="warn">Unavailable for this food: {f.missing_nutrition.join(", ")} (shown as –)</p>}
                  <p className="meta">{f.why}</p>
                </div>
              ))}
            </div>
          )} />
        </section>
      )}
    </div>
  );
}

function PlanCard({ p, heading }) {
  return (
    <div className="card">
      <p className="choice">{heading}</p>
      <h3>{p.program}</h3>
      <p className="meta">{p.goal} · {p.level} · {p.equipment} · {p.time_per_workout ?? "–"} min · {p.n_exercises_listed} sessions listed</p>
      <p className="meta">Duration: {p.duration_check?.estimated != null ? `~${p.duration_check.estimated} min` : "cannot be estimated from the data"} — {p.duration_check?.note}</p>
      <table>
        <thead><tr><th>Exercise</th><th>Sets</th><th>Reps</th><th>Intensity</th><th>Wk</th><th>Day</th></tr></thead>
        <tbody>
          {p.exercises.map((x, i) => (
            <tr key={i}><td>{x.exercise}</td><td>{x.sets ?? "–"}</td><td>{x.reps ?? "–"}</td><td>{x.intensity ?? "–"}</td><td>{x.week ?? "–"}</td><td>{x.day ?? "–"}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ExplainDiet({ data }) {
  const expl = data.diet_category?.explanation;
  return (
    <details className="explain">
      <summary>How these recommendations were generated</summary>
      <ul>
        <li><b>Predicted category: {data.diet_category?.diet_category}.</b> It describes your health profile for filtering context only — it is a model output, not a diagnosis, and it is predicted from your health inputs, <i>not</i> from your goal (a weight-loss goal can still yield “Balanced”).</li>
        {expl?.probabilities && <li>Category probabilities: {Object.entries(expl.probabilities).map(([k, v]) => `${k} ${v}`).join(" · ")}.</li>}
        {expl?.top_features?.length > 0 && <li>Most influential inputs: {expl.top_features.slice(0, 5).map((f) => `${f.feature} (${f.importance.toFixed(3)})`).join(", ")}.</li>}
        <li>Data &amp; algorithms: RandomForest category prediction + KNN ranking over scaled per-100g nutrients. Catalog: {data.catalog_used?.source_dataset} ({data.catalog_used?.why}).</li>
        <li>Candidates: {data.candidate_counts?.before_filtering} before filtering → {data.candidate_counts?.after_filtering} after.</li>
        <li>Restrictions enforced: {data.restrictions_enforced?.length > 0 ? data.restrictions_enforced.map((e) => e.restriction ? `${e.restriction} (${e.rule}, excluded ${e.excluded_rows})` : `${e.allergy} (${e.flag}, excluded ${e.excluded_rows})`).join("; ") : "none"}.
          Unsupported: {(data.filter_notes || []).filter((n) => n.type === "restriction_unsupported" || n.type === "allergy_unmapped").map((n) => n.value).join(", ") || "none"}.</li>
        <li>Each food shows why it ranked highly (KNN distance — closeness, not proof of suitability), its source dataset, allergy-check status, and any missing nutrient fields.</li>
        {data.filtering_summary && <li>Recipes: {data.filtering_summary.recipes_before_filtering} → diet/course {data.filtering_summary.recipes_after_diet_filter} → ingredient checks {data.filtering_summary.recipes_after_ingredient_checks} ({data.filtering_summary.recipes_needs_review} need review) → time {data.filtering_summary.recipes_after_time_filter} compatible. Ranked by ingredient coverage, then valid time, then name — no ML score.</li>}
        {data.allergen_warning && <li>Limitation: {data.allergen_warning}</li>}
        <li>Limitation: single-food suggestions, not a daily meal plan. {expl?.disclaimer}</li>
      </ul>
    </details>
  );
}

function Result({ state, render }) {
  if (state.state === "idle") return null;
  if (state.state === "loading") return <p className="meta">Loading…</p>;
  if (state.state === "error") return <p className="error">Error: {state.message}</p>;
  return render(state.data);
}
