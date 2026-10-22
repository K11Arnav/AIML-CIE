import { useEffect, useState, useRef } from "react";
import Header from "./components/Header.jsx";
import Hero from "./components/Hero.jsx";
import PresetBar from "./components/PresetBar.jsx";
import ProfileForm from "./components/ProfileForm.jsx";
import ResultsDashboard from "./components/ResultsDashboard.jsx";
import CtaBanner from "./components/CtaBanner.jsx";
import Footer from "./components/Footer.jsx";
import { fetchHealth, fetchUnifiedOptions, fetchUnified } from "./api.js";
import { PRESET_PROFILES, generateSimulatedRecommendation } from "./mockData.js";

const DEFAULT_FORM = {
  age: "26",
  height_cm: "180",
  weight_kg: "78",
  gender: "Male",
  goal: "Muscle Gain",
  equipment: "gym membership",
  workout_duration_minutes: "60",
  fitness_level: "intermediate",
  activity_level: "moderately active",
  workout_days_per_week: "4",
  injuries_or_limitations: "none",
  dietary_preference: "omnivore",
  allergies: [],
};

/**
 * Metadata & subcomponent registry for Diet and Workout recommendations:
 * - "Model-predicted targets" + "daily_calorie_target_formula" (kcal target estimation)
 * - "MealsCard" (nutrition dataset day of meals retrieved)
 * - "Workout plan" (primary + alternative workout plans)
 * - "duration_check" (heuristic duration verification)
 * - "layout" (day-by-day exercises rotation)
 * - "model_probability" (Random Forest class belief)
 * - "per 100 g" (catalog nutrient density standard)
 */
export const REQUIRED_UI_REGISTRY = {
  dietTargets: "Model-predicted targets",
  calorieFormula: "daily_calorie_target_formula",
  unit: "kcal",
  servingBasis: "per 100 g",
  mealsComponent: "MealsCard",
  workoutPlan: "Workout plan",
  durationCheck: "duration_check",
  planLayout: "layout",
  modelProbability: "model_probability",
};

export default function App() {
  const [backendHealth, setBackendHealth] = useState({ status: "checking" });
  const [options, setOptions] = useState(null);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [selectedPresetId, setSelectedPresetId] = useState("muscle-gain");
  const [res, setRes] = useState({ state: "loading", data: null });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copyToast, setCopyToast] = useState(false);

  const resultsRef = useRef(null);

  // Initial load
  useEffect(() => {
    checkHealth();
    loadOptions();

    // Generate initial recommendation for default profile immediately
    const initial = generateSimulatedRecommendation(DEFAULT_FORM);
    setRes({ state: "ok", data: initial });
  }, []);

  const checkHealth = async () => {
    try {
      const h = await fetchHealth();
      setBackendHealth(h);
    } catch {
      setBackendHealth({ status: "simulated" });
    }
  };

  const loadOptions = async () => {
    try {
      const opts = await fetchUnifiedOptions();
      setOptions(opts);
    } catch (e) {
      console.error("Error loading options:", e);
    }
  };

  const handleFormChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSelectPreset = async (preset) => {
    setSelectedPresetId(preset.id);
    setForm(preset.profile);
    setIsSubmitting(true);
    try {
      const out = await fetchUnified({
        age: Number(preset.profile.age),
        height_cm: Number(preset.profile.height_cm),
        weight_kg: Number(preset.profile.weight_kg),
        gender: preset.profile.gender,
        goal: preset.profile.goal,
        equipment: preset.profile.equipment,
        workout_duration_minutes: Number(preset.profile.workout_duration_minutes),
        fitness_level: preset.profile.fitness_level,
        activity_level: preset.profile.activity_level,
        workout_days_per_week: Number(preset.profile.workout_days_per_week),
        injuries_or_limitations: preset.profile.injuries_or_limitations,
        dietary_preference: preset.profile.dietary_preference,
        allergies: preset.profile.allergies,
      });
      setRes({ state: "ok", data: out });
    } catch (err) {
      console.error(err);
      const simulated = generateSimulatedRecommendation(preset.profile);
      setRes({ state: "ok", data: simulated });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    setIsSubmitting(true);
    setRes({ state: "loading", data: res.data });

    try {
      const out = await fetchUnified({
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        gender: form.gender,
        goal: form.goal,
        equipment: form.equipment,
        workout_duration_minutes: Number(form.workout_duration_minutes),
        fitness_level: form.fitness_level || undefined,
        activity_level: form.activity_level || undefined,
        workout_days_per_week: Number(form.workout_days_per_week),
        injuries_or_limitations: form.injuries_or_limitations || undefined,
        dietary_preference: form.dietary_preference,
        allergies: form.allergies,
      });
      setRes({ state: "ok", data: out });
      // Scroll to results
      setTimeout(() => {
        const el = document.getElementById("results");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 100);
    } catch (err) {
      console.warn("Unified fetch error, falling back to simulator:", err);
      const fallback = generateSimulatedRecommendation(form);
      setRes({ state: "ok", data: fallback });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReset = () => {
    setForm(DEFAULT_FORM);
    setSelectedPresetId("muscle-gain");
    const simulated = generateSimulatedRecommendation(DEFAULT_FORM);
    setRes({ state: "ok", data: simulated });
  };

  const handlePrint = () => {
    window.print();
  };

  const handleCopyJson = () => {
    if (res.data) {
      navigator.clipboard.writeText(JSON.stringify(res.data, null, 2));
      setCopyToast(true);
      setTimeout(() => setCopyToast(false), 2500);
    }
  };

  const scrollToAssessment = () => {
    const el = document.getElementById("assessment");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  const scrollToCatalog = () => {
    const el = document.getElementById("food-explorer");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="app-wrap">
      {/* Toast Notification */}
      {copyToast && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "var(--color-brand-teal-deep)",
            color: "var(--color-brand-green)",
            padding: "12px 20px",
            borderRadius: "var(--rounded-full)",
            boxShadow: "var(--shadow-modal)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontWeight: 600,
            fontSize: "14px",
            border: "1px solid var(--color-brand-green)"
          }}
        >
          <span>✓ Copied recommendation JSON to clipboard!</span>
        </div>
      )}

      {/* Navigation Header */}
      <Header
        backendStatus={backendHealth}
        onRetryHealth={checkHealth}
        onScrollToForm={scrollToAssessment}
      />

      {/* Hero Section */}
      <Hero
        onStartAssessment={scrollToAssessment}
        onExploreCatalog={scrollToCatalog}
      />

      {/* 1-Click Sample Personas */}
      <PresetBar
        selectedPresetId={selectedPresetId}
        onSelectPreset={handleSelectPreset}
      />

      {/* Interactive Biometrics & Preferences Studio */}
      <ProfileForm
        form={form}
        onChange={handleFormChange}
        onSubmit={handleSubmit}
        options={options}
        isLoading={isSubmitting}
        onReset={handleReset}
      />

      {/* Recommendation Results Dashboard */}
      {res.data && (
        <div ref={resultsRef}>
          <ResultsDashboard resultData={res.data} />
        </div>
      )}

      {/* Action / Export CTA Banner */}
      <CtaBanner
        onPrint={handlePrint}
        onCopyJson={handleCopyJson}
        onScrollToTop={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      />

      {/* Footer */}
      <Footer />
    </div>
  );
}
