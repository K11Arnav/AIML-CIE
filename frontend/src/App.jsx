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

const ALLERGIES = ["Gluten", "Peanuts", "Dairy", "Soy", "Eggs", "Fish"];

export default function App() {
  const [health, setHealth] = useState({ state: "loading" });
  const [opts, setOpts] = useState({ state: "loading" });
  const [f, setF] = useState({
    age: "30", height_cm: "165", weight_kg: "65", gender: "Female",
    goal: "weight loss", equipment: "dumbbells", workout_duration_minutes: "45",
    fitness_level: "beginner", activity_level: "moderate", workout_days_per_week: "4",
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
    { value: "bodyweight", label: "Bodyweight / no equipment (At Home)" },
    { value: "dumbbells", label: "Dumbbells / basic equipment (Dumbbell Only)" },
    { value: "full gym", label: "Full gym (Full Gym)" },
  ]).map((o) => ({ value: o.value, label: o.label || o.value }));

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
              <Select label="Goal" value={f.goal} onChange={setV("goal")} options={(opts.data.goals || ["weight loss", "muscle gain", "general fitness"]).map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Equipment you have">
              <Select label="Equipment" value={f.equipment} onChange={setV("equipment")} options={eqOpts} />
            </Field>
            <Field label="Workout time per session (min)"><input value={f.workout_duration_minutes} onChange={set("workout_duration_minutes")} inputMode="numeric" /></Field>
            <Field label="Fitness level">
              <Select label="Fitness level" value={f.fitness_level} onChange={setV("fitness_level")} options={["beginner", "intermediate", "advanced"].map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Activity level">
              <Select label="Activity level" value={f.activity_level} onChange={setV("activity_level")} options={["sedentary", "moderate", "active"].map((v) => ({ value: v, label: v }))} />
            </Field>
            <Field label="Workout days per week"><input value={f.workout_days_per_week} onChange={set("workout_days_per_week")} inputMode="numeric" placeholder="1–7" /></Field>
            <Field label="Injuries / limitations (or “none”)">
              <input value={f.injuries_or_limitations} onChange={set("injuries_or_limitations")} placeholder="none" />
            </Field>
            <Field label="Dietary preference">
              <Select label="Dietary preference" value={f.dietary_preference} onChange={setV("dietary_preference")} options={["any", "vegetarian", "non vegetarian"].map((v) => ({ value: v, label: v }))} />
            </Field>
            <div className="full">
              <MultiSelect legend="Allergies (hard exclusions)" options={ALLERGIES.map((v) => ({ value: v, label: v }))} selected={f.allergies} onChange={setV("allergies")} />
            </div>
            <div className="full"><button type="submit">Get diet + workout recommendations</button></div>
          </form>
          <p className="meta">Note: {opts.data.safety_note}</p>
          <Result state={res} render={(data) => <UnifiedResults data={data} />} />
        </section>
      )}
    </div>
  );
}

function UnifiedResults({ data }) {
  const diet = data.diet, workout = data.workout;
  const hasFoods = (diet.items || []).length > 0 || (diet.recipes || []).length > 0;
  const allergyNote = diet.allergen_warning || null;
  return (
    <div>
      <p className="meta">BMI {data.profile?.bmi}</p>
      <p className="meta">{data.safety_note}</p>

      <h2>Workout plan</h2>
      <p className="meta">{workout.method} · {workout.n_candidates ?? 0} compatible programs</p>
      {workout.unmet?.length > 0 && <p className="warn">Notes: {workout.unmet.join("; ")}</p>}
      {!workout.primary && <p className="warn">No compatible program — try a different equipment or duration.</p>}
      {workout.primary && <PlanCard p={workout.primary} heading={workout.primary.choice_label || "Recommended plan"} />}

      <h2>Diet recommendations</h2>
      <CalorieCard target={data.daily_calorie_target} />
      {allergyNote && <p className="warn">{allergyNote}</p>}
      <h3>Foods you can eat</h3>
      {!hasFoods && <p>No matching foods are available for the selected preferences and restrictions.</p>}
      {diet.items?.map((item) => (
        <FoodCard key={item.rank + (item.product_name || "")} item={item} goal={data.diet_goal} />
      ))}
      {(diet.recipes || []).slice(0, 10).map((rec, i) => (
        <RecipeCard key={rec.name + i} rec={rec} />
      ))}
    </div>
  );
}

/** Daily calorie target: calculated estimate, never a measured fact.
 *  Falls back to an explicit unavailable message instead of a made-up number. */
function CalorieCard({ target }) {
  if (!target || !(target.kcal_per_day > 0)) {
    return (
      <div className="card">
        <h3>Daily calorie target unavailable</h3>
        <p className="meta">The target could not be determined reliably for this profile, so none is shown rather than a fabricated number.</p>
      </div>
    );
  }
  return (
    <div className="card">
      <h3>Daily calorie target: {target.kcal_per_day} kcal/day</h3>
      <p className="meta">{target.method}.</p>
      {target.activity_assumed && <p className="meta">Activity level not provided — assumed “{target.activity_level_used}”. Set it on the form for a better estimate.</p>}
      <p className="meta">{target.disclaimer}</p>
    </div>
  );
}

/** Food card: per-100 g dataset values only. No serving sizes, ingredients, or
 *  dietary-category labels exist in the food catalog, so the card says so
 *  instead of inventing them. No preparation times are shown. */
function FoodCard({ item, goal }) {
  const basis = item.explanation?.serving_basis || "per 100 g";
  const g = (v) => (v ?? "–") + (v == null ? "" : "g");
  return (
    <div className="card">
      <h3>#{item.rank} {item.product_name || "Unnamed product"} <small>{item.food_type || ""}</small></h3>
      <p className="meta"><b>{item.energy_kcal ?? "–"} kcal</b> {basis} (dataset value — no serving-size data, nothing scaled)</p>
      <p className="meta">Protein {g(item.proteins_100g)} · Carbs {g(item.carbs_100g)} · Fat {g(item.fat_100g)} · Fibre {g(item.fiber_100g)} ({basis}; – = unavailable, never zero)</p>
      <p className="meta">Ingredients: not listed in the food dataset — the name alone doesn’t define ingredients.</p>
      {item.missing_nutrition?.length > 0 && <p className="warn">Unavailable for this food: {item.missing_nutrition.join(", ")} (shown as –)</p>}
      <p className="meta">Why for your goal ({goal}): {item.why}</p>
    </div>
  );
}

/** Recipe card: real ingredient list + dataset diet label. The recipe dataset
 *  has no nutrient or serving data, so none is shown. No prep/cook times. */
function RecipeCard({ rec }) {
  const ings = String(rec.ingredients || "").split(",").map((s) => s.trim()).filter(Boolean);
  return (
    <div className="card">
      <h3>{rec.name} <small>{[rec.diet, rec.course].filter(Boolean).join(" · ")}</small></h3>
      {rec.diet && <p className="meta">Dietary category (dataset label): {rec.diet}</p>}
      <p className="meta">Ingredients: {ings.length > 0 ? ings.join(", ") : "not listed"}</p>
      {rec.unmatched_ingredients?.length > 0 && <p className="meta">Unresolved: {rec.unmatched_ingredients.join("; ")}</p>}
      <p className="meta">Nutrition: unavailable — the recipe dataset has no nutrient values.</p>
      <p className="meta">Ingredient coverage {rec.ingredient_coverage}{rec.state ? ` · ${rec.state}${rec.region ? `, ${rec.region}` : ""}` : ""}</p>
      {rec.compatibility_status !== "compatible_with_known_preferences" && rec.explanation && (
        <p className="meta">{rec.explanation}</p>
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

function Result({ state, render }) {
  if (state.state === "idle") return null;
  if (state.state === "loading") return <p className="meta">Loading…</p>;
  if (state.state === "error") return <p className="error">Error: {state.message}</p>;
  return render(state.data);
}
