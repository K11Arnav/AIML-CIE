import { useState } from "react";
import UnifiedOverview from "./UnifiedOverview.jsx";
import WorkoutPlanView from "./WorkoutPlanView.jsx";
import DietNutritionView from "./DietNutritionView.jsx";
import FoodCatalogView from "./FoodCatalogView.jsx";
import MLTelemetryView from "./MLTelemetryView.jsx";
import ExerciseModal from "./ExerciseModal.jsx";

export default function ResultsDashboard({ resultData }) {
  const [activeTab, setActiveTab] = useState("unified");
  const [modalExercise, setModalExercise] = useState(null);

  if (!resultData) return null;

  const data = resultData.data || resultData;
  const workout = data.workout || {};
  const diet = data.diet || {};
  const profile = data.profile || {};
  const formula = data.daily_calorie_target_formula || {};

  return (
    <section id="results" className="container" style={{ padding: "0 24px 64px" }}>
      {/* Navigation Tabs (MongoDB Pill Tabs style) */}
      <div className="pill-tabs-nav">
        <button
          type="button"
          className={`pill-tab ${activeTab === "unified" ? "pill-tab-active" : ""}`}
          onClick={() => setActiveTab("unified")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <rect x="3" y="3" width="7" height="7" />
            <rect x="14" y="3" width="7" height="7" />
            <rect x="14" y="14" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" />
          </svg>
          <span>Unified Dashboard</span>
        </button>

        <button
          type="button"
          id="workout-plans"
          className={`pill-tab ${activeTab === "workout" ? "pill-tab-active" : ""}`}
          onClick={() => setActiveTab("workout")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M6 5v14M18 5v14M2 9h4M2 15h4M18 9h4M18 15h4M6 12h12" />
          </svg>
          <span>Workout Architecture</span>
        </button>

        <button
          type="button"
          id="diet-nutrition"
          className={`pill-tab ${activeTab === "diet" ? "pill-tab-active" : ""}`}
          onClick={() => setActiveTab("diet")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
            <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
          </svg>
          <span>Diet &amp; Macronutrients</span>
        </button>

        <button
          type="button"
          className={`pill-tab ${activeTab === "catalog" ? "pill-tab-active" : ""}`}
          onClick={() => setActiveTab("catalog")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
          </svg>
          <span>Ranked Food Catalog</span>
        </button>

        <button
          type="button"
          className={`pill-tab ${activeTab === "telemetry" ? "pill-tab-active" : ""}`}
          onClick={() => setActiveTab("telemetry")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          <span>Model Telemetry</span>
        </button>
      </div>

      {/* Active Tab View */}
      {activeTab === "unified" && (
        <UnifiedOverview data={data} onSelectTab={setActiveTab} />
      )}

      {activeTab === "workout" && (
        <WorkoutPlanView
          workout={workout}
          onSelectExercise={(ex) => setModalExercise(ex)}
        />
      )}

      {activeTab === "diet" && (
        <DietNutritionView
          diet={diet}
          formula={formula}
          profile={profile}
        />
      )}

      {activeTab === "catalog" && (
        <FoodCatalogView
          items={diet.items || []}
          goalLabel={data.diet_goal}
        />
      )}

      {activeTab === "telemetry" && (
        <MLTelemetryView
          modelQuality={workout.model_quality}
        />
      )}

      {/* Modal for Exercise Details */}
      {modalExercise && (
        <ExerciseModal
          exercise={modalExercise}
          onClose={() => setModalExercise(null)}
        />
      )}
    </section>
  );
}
