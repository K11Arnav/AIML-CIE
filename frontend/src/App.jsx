import { useEffect, useState } from "react";
import { fetchUnified, fetchUnifiedOptions, fetchHealth } from "./api.js";

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

const ALLERGIES = ["Gluten", "Peanuts", "Dairy", "Tree nuts", "Soy", "Eggs", "Fish / seafood"];

export default function App() {
  const [health, setHealth] = useState({ state: "loading" });
  const [opts, setOpts] = useState({ state: "loading" });
  const [f, setF] = useState({
    age: "30", height_cm: "165", weight_kg: "65", gender: "Female",
    goal: "Muscle Gain", equipment: "home dumbbells", workout_duration_minutes: "45",
    fitness_level: "beginner", activity_level: "moderately active", workout_days_per_week: "4",
    injuries_or_limitations: "none", dietary_preference: "any", allergies: [],
  });
  const [res, setRes] = useState({ state: "idle" });

  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth({ state: "ok", detail: h }))
      .catch(() => setHealth({ state: "down" }));
    fetchUnifiedOptions()
      .then((o) => setOpts({ state: "ok", data: o }))
      .catch((e) => setOpts({ state: "error", message: e.message }));
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setRes({ state: "loading" });
    try {
      const out = await fetchUnified({
        age: num(f.age),
        height_cm: num(f.height_cm),
        weight_kg: num(f.weight_kg),
        gender: f.gender,
        goal: f.goal,
        equipment: f.equipment,
        workout_duration_minutes: num(f.workout_duration_minutes),
        fitness_level: f.fitness_level || undefined,
        activity_level: f.activity_level || undefined,
        workout_days_per_week: num(f.workout_days_per_week),
        injuries_or_limitations: f.injuries_or_limitations || undefined,
        dietary_preference: f.dietary_preference,
        allergies: f.allergies,
      });
      setRes({ state: "ok", data: out });
    } catch (err) {
      setRes({ state: "error", message: err.message });
    }
  };

  const set = (key) => (e) => setF((s) => ({ ...s, [key]: e.target.value }));
  const setV = (key) => (v) => setF((s) => ({ ...s, [key]: v }));
  const eqOpts = (opts.data?.equipment || [
    { value: "bodyweight only", label: "Bodyweight / no equipment" },
    { value: "home dumbbells", label: "Home dumbbells / kettlebell" },
    { value: "full home gym", label: "Full home gym (barbell + rack)" },
    { value: "gym membership", label: "Gym membership (machines, cables, barbell)" },
    { value: "yoga mat", label: "Yoga mat (mobility, floor work)" },
  ]).map((o) => ({ value: o.value, label: o.label || o.value }));
  const goalOpts = (opts.data?.goals || ["Weight Loss", "Muscle Gain", "General Health"])
    .map((v) => ({ value: v, label: v }));
  const actOpts = (opts.data?.activity_levels || ["sedentary", "lightly active", "moderately active", "very active"])
    .map((v) => ({ value: v, label: v.replace(/\b\w/g, (c) => c.toUpperCase()) }));
  const injOpts = (opts.data?.injuries || ["none", "knee", "ankle", "shoulder", "back"])
    .map((v) => ({ value: v, label: v === "none" ? "None" : v.replace(/\b\w/g, (c) => c.toUpperCase()) }));
  const prefOpts = (opts.data?.dietary_preferences || ["any", "omnivore", "vegetarian", "vegan"])
    .map((v) => ({ value: v, label: v === "any" ? "Any" : v.replace(/\b\w/g, (c) => c.toUpperCase()) }));

  return (
    <div className="wrap">
      <h1>Fitness Recommendations <small>(local demo)</small></h1>
      <p className="note">Informational only — not medical advice. One profile, one submit — diet + workout together.</p>
      <div className={`health ${health.state}`}>
        Backend: {health.state === "loading" ? "checking…" : health.state === "ok" ? `connected (ML: ${health.detail?.ml_service?.status ?? "?"})` : "unavailable — start backend + ML service"}
      </div>

      {opts.state === "loading" && <p className="meta">Loading options…</p>}
      {opts.state === "error" && <p className="error">Could not load options: {opts.message} (is the backend + ML service running?)</p>}

      {opts.state === "ok" && (
        <section>
          <form onSubmit={submit} className="form">
            <Field label="Age (years)"><input value={f.age} onChange={set("age")} inputMode="numeric" /></Field>
            <Field label="Height (cm)"><input value={f.height_cm} onChange={set("height_cm")} inputMode="numeric" /></Field>
            <Field label="Weight (kg)"><input value={f.weight_kg} onChange={set("weight_kg")} inputMode="decimal" /></Field>
            <Field label="Gender">
              <Select label="Gender" value={f.gender} onChange={setV("gender")} options={["Female", "Male"].map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Goal">
              <Select label="Goal" value={f.goal} onChange={setV("goal")} options={goalOpts} />
            </Field>
            <Field label="Equipment you have">
              <Select label="Equipment" value={f.equipment} onChange={setV("equipment")} options={eqOpts} />
            </Field>
            <Field label="Workout time per session (min)"><input value={f.workout_duration_minutes} onChange={set("workout_duration_minutes")} inputMode="numeric" /></Field>
            <Field label="Fitness level">
              <Select label="Fitness level" value={f.fitness_level} onChange={setV("fitness_level")} options={["beginner", "intermediate", "advanced"].map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Activity level">
              <Select label="Activity level" value={f.activity_level} onChange={setV("activity_level")} options={actOpts} />
            </Field>
            <Field label="Workout days per week"><input value={f.workout_days_per_week} onChange={set("workout_days_per_week")} inputMode="numeric" placeholder="1–7" /></Field>
            <Field label="Injury / limitation focus">
              <Select label="Injuries or limitations" value={f.injuries_or_limitations} onChange={setV("injuries_or_limitations")} options={injOpts} />
            </Field>
            <Field label="Dietary preference">
              <Select label="Dietary preference" value={f.dietary_preference} onChange={setV("dietary_preference")} options={prefOpts} />
            </Field>
            <div className="full">
              <MultiSelect legend="Allergies (hard exclusions)" options={ALLERGIES.map((v) => ({ value: v, label: v }))} selected={f.allergies} onChange={setV("allergies")} />
            </div>
            <div className="full"><button type="submit">Get diet + workout recommendations</button></div>
          </form>
          {opts.data?.safety_note && <p className="meta">Note: {opts.data.safety_note}</p>}
          <Result state={res} render={(data) => <UnifiedResults data={data} />} />
        </section>
      )}
    </div>
  );
}

function UnifiedResults({ data }) {
  const diet = data.diet, workout = data.workout;
  const allergyNote = diet.allergen_warning || null;
  const rq = workout.model_quality || {};
  return (
    <div>
      <p className="meta">BMI {data.profile?.bmi}</p>
      <p className="meta">{data.safety_note}</p>

      <h2>Workout plan</h2>
      <p className="meta">Model: RandomForest classifier on smartfit_workout_dataset.csv (test accuracy {rq.test_accuracy ?? "–"}, dummy baseline {rq.dummy_accuracy ?? "–"}). Every profile field you submit is a model feature.</p>
      {workout.unmet?.length > 0 && <p className="warn">Notes: {workout.unmet.join("; ")}</p>}
      {!workout.primary && <p className="warn">No compatible plan — try different equipment.</p>}
      {workout.primary && <PlanCard p={workout.primary} heading={workout.primary.choice_label || "Recommended plan"} />}
      {(workout.alternatives || []).map((p, i) => <PlanCard key={p.plan} p={p} heading={p.choice_label || `Alternative ${i + 1}`} />)}

      <h2>Diet recommendations</h2>
      <CalorieCard target={data.daily_calorie_target_formula} predicted={diet.predicted} modelQuality={diet.model_quality_area} />
      {allergyNote && <p className="warn">{allergyNote}</p>}
      {diet.meals && <MealsCard meals={diet.meals} />}
      <h3>Foods ranked for your goal ({data.diet_goal})</h3>
      {diet.preference_screening && <p className="meta">{diet.preference_screening.foods_excluded} of {diet.preference_screening.foods_screened} foods excluded by {diet.preference_screening.preference} screening.</p>}
      {diet.allergy_screening && <p className="meta">{diet.allergy_screening.foods_excluded} further foods excluded by allergy flags: {diet.allergy_screening.flags_applied.join(", ")}.</p>}
      {(diet.items || []).length === 0 && <p>No matching foods (check allergy screening above).</p>}
      {(diet.items || []).map((item) => <FoodCard key={item.rank + (item.product_name || "")} item={item} />)}
    </div>
  );
}

/** Model-predicted macros + formula-based daily target, clearly separated. */
function CalorieCard({ target, predicted, modelQuality }) {
  const mae = predicted ? (modelQuality?.mae?.["Daily Calorie Target"] ?? "–") : null;
  return (
    <div className="card">
      <h3>Model-predicted targets (RF on nutrition_dataset)</h3>
      {predicted
        ? <p className="meta"><b>{predicted["Daily Calorie Target"]} kcal/day</b> · Protein {predicted.Protein} g · Carbs {predicted.Carbohydrates} g · Fat {predicted.Fat} g (MAE±{mae} kcal on held-out data)</p>
        : <p className="meta">No macro prediction available.</p>}
      <h3>Formula estimate (Mifflin-St Jeor)</h3>
      {target && target.kcal_per_day > 0
        ? <p className="meta">{target.kcal_per_day} kcal/day — {target.method}.{target.activity_assumed ? ` Activity level not provided — assumed “${target.activity_level_used}”, set it for a better estimate.` : ""}</p>
        : <p className="meta">Formula estimate unavailable for this profile.</p>}
      <p className="meta">{target?.disclaimer}</p>
    </div>
  );
}

/** Meal suggestions: retrieved rows from nutrition_dataset.csv, never generated. */
function MealsCard({ meals }) {
  const s = meals.suggestions || {};
  return (
    <div className="card">
      <h3>Day of meals (retrieved, not generated)</h3>
      <p className="meta">{meals.selection_basis} Matching preference rows: {meals.matches}.</p>
      <ul>
        {Object.entries(s).map(([k, v]) => (
          <li key={k}><b>{k.replace(" Suggestion", "")}:</b> {v ?? "–"}</li>
        ))}
      </ul>
      <p className="meta">Row context: {MealsCard.ctx(meals)}</p>
      <p className="meta">Suggestions allergen-screened against keyword-derived flags (ml/allergens.py) — verify ingredient labels yourself.</p>
    </div>
  );
}
MealsCard.ctx = (meals) => {
  const r = meals.row_context || {};
  return `${r["Dietary Preference"] ?? "–"} · ${r["Fitness Goal"] ?? "–"} · ${r["Daily Calorie Target"] ?? "–"} kcal row target`;
};

/** Food card: per-100 g dataset values only. No serving sizes, ingredients, or
 *  allergen flags exist in the food catalog, so the card says so instead of
 *  inventing them. */
function FoodCard({ item }) {
  const basis = item.serving_basis || "per 100 g";
  const g = (v) => (v ?? "–") + (v == null ? "" : "g");
  return (
    <div className="card">
      <h3>#{item.rank} {item.product_name || "Unnamed food"}</h3>
      <p className="meta"><b>{item.energy_kcal ?? "–"} kcal</b> {basis} (dataset value — nothing scaled)</p>
      <p className="meta">Protein {g(item.proteins_100g)} · Carbs {g(item.carbs_100g)} · Fat {g(item.fat_100g)} · Fibre {g(item.fiber_100g)} ({basis}; – = unavailable, never zero)</p>
      {item.missing_nutrition?.length > 0 && <p className="warn">Unavailable for this food: {item.missing_nutrition.join(", ")} (shown as –)</p>}
      <p className="meta">{item.rank_reason}</p>
    </div>
  );
}

function PlanCard({ p, heading }) {
  const dc = p.duration_check || {};
  return (
    <div className="card">
      <p className="choice">{heading}</p>
      <h3>{p.plan}</h3>
      <p className="meta">{p.style} · {p.goal} · {p.experience_level} · {p.equipment} · {p.workout_days_per_week} days/week · {p.sets}×{p.reps ?? "timed"} scheme</p>
      <p className="meta">Model probability: {p.model_probability} (equipment-constrained; model belief, not accuracy)</p>
      <p className="meta">Duration: {dc.estimated != null ? `~${dc.estimated} min/session (heuristic)` : "cannot be estimated"} — {dc.note}</p>
      <p className="meta">Session layout from datasets/exercises.json (deterministic mapping in ml/plan_layout.py; first {EX_PER_DAY} compatible exercises per day).</p>
      <table>
        <thead><tr><th>Day</th><th>Focus</th><th>Exercise</th><th>Sets</th><th>Reps</th></tr></thead>
        <tbody>
          {(p.layout?.days || []).map((d) => d.exercises.map((x, i) => (
            <tr key={`${d.day}-${i}`}>
              <td>{d.day}</td>
              <td>{d.body_part}</td>
              <td>{x.name}</td>
              <td>{x.sets ?? "–"}</td>
              <td>{x.reps ?? "timed"}</td>
            </tr>
          )))}
        </tbody>
      </table>
    </div>
  );
}
const EX_PER_DAY = 5;

function Result({ state, render }) {
  if (state.state === "idle") return null;
  if (state.state === "loading") return <p className="meta">Loading…</p>;
  if (state.state === "error") return <p className="error">Error: {state.message}</p>;
  return render(state.data);
}
