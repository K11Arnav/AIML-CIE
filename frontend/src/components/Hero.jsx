import { useState } from "react";

export default function Hero({ onStartAssessment, onExploreCatalog }) {
  const [activeTab, setActiveTab] = useState("pipeline");

  return (
    <section className="hero-band-dark">
      <div className="container">
        <div className="hero-grid">
          {/* Left Column: Headline & Action Buttons */}
          <div>
            <div className="hero-eyebrow">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              <span>PRECISION BIOMETRIC &amp; NUTRITION INTELLIGENCE</span>
            </div>

            <h1 className="hero-title">
              One Unified Profile.<br />
              <span className="highlight-green">Zero Guesswork.</span>
            </h1>

            <p className="hero-subtitle">
              Dual Random Forest classifiers and k-NN nutrient mapping tuned on validated training data.
              Get equipment-constrained workout periodization and clinically estimated, allergen-filtered macronutrient targets in one single click.
            </p>

            <div className="hero-button-row">
              <button
                type="button"
                className="btn-on-dark"
                onClick={onStartAssessment}
              >
                <span>Launch Recommender</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>

              <button
                type="button"
                className="btn-secondary-on-dark"
                onClick={onExploreCatalog}
              >
                Explore Food Catalog
              </button>
            </div>

            <div className="hero-stats-row">
              <div className="hero-stat-item">
                <span className="hero-stat-value">89.4%</span>
                <span className="hero-stat-label">Model Test Accuracy</span>
              </div>
              <div className="hero-stat-item">
                <span className="hero-stat-value">100%</span>
                <span className="hero-stat-label">Equipment Enforced</span>
              </div>
              <div className="hero-stat-item">
                <span className="hero-stat-value">0-Leak</span>
                <span className="hero-stat-label">Allergen Screening</span>
              </div>
            </div>
          </div>

          {/* Right Column: Code / Model Mockup Card */}
          <div>
            <div className="code-mockup-card">
              <div className="mockup-header">
                <div className="mockup-dots">
                  <span className="mockup-dot red"></span>
                  <span className="mockup-dot yellow"></span>
                  <span className="mockup-dot green"></span>
                </div>
                <div className="mockup-tabs">
                  <button
                    type="button"
                    className={`mockup-tab ${activeTab === "pipeline" ? "active" : ""}`}
                    onClick={() => setActiveTab("pipeline")}
                  >
                    unified_pipeline.py
                  </button>
                  <button
                    type="button"
                    className={`mockup-tab ${activeTab === "vector" ? "active" : ""}`}
                    onClick={() => setActiveTab("vector")}
                  >
                    feature_vector.json
                  </button>
                  <button
                    type="button"
                    className={`mockup-tab ${activeTab === "metrics" ? "active" : ""}`}
                    onClick={() => setActiveTab("metrics")}
                  >
                    model_metrics.log
                  </button>
                </div>
              </div>

              <div className="mockup-body">
                {activeTab === "pipeline" && (
                  <div>
                    <div className="mockup-line">
                      <span className="mockup-num">1</span>
                      <span className="mockup-text"><span className="code-keyword">from</span> ml.recommender <span className="code-keyword">import</span> FitnessRecommender</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">2</span>
                      <span className="mockup-text"><span className="code-keyword">from</span> ml.calories <span className="code-keyword">import</span> estimate_daily_calories</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">3</span>
                      <span className="mockup-text"><span className="code-comment"># Single profile submit feeds dual Random Forest engines</span></span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">4</span>
                      <span className="mockup-text">rec = FitnessRecommender.load(<span className="code-str">"artifacts/"</span>)</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">5</span>
                      <span className="mockup-text">workout = rec.recommend_workout(profile)</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">6</span>
                      <span className="mockup-text">diet = rec.recommend_diet(profile)</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">7</span>
                      <span className="mockup-text"><span className="code-keyword">assert</span> workout[<span className="code-str">"primary"</span>][<span className="code-str">"equipment"</span>] == profile[<span className="code-str">"equipment"</span>]</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">8</span>
                      <span className="mockup-text"><span className="code-func">print</span>(<span className="code-str">f"Plan: &#123;workout['primary']['plan']&#125; (p=&#123;workout['primary']['model_probability']&#125;)"</span>)</span>
                    </div>
                    <div className="mockup-line">
                      <span className="mockup-num">9</span>
                      <span className="mockup-text"><span className="code-func">print</span>(<span className="code-str">f"Target Calories: &#123;diet['predicted']['Daily Calorie Target']&#125; kcal"</span>)</span>
                    </div>
                  </div>
                )}

                {activeTab === "vector" && (
                  <div>
                    <div className="mockup-line"><span className="mockup-num">1</span><span className="mockup-text">&#123;</span></div>
                    <div className="mockup-line"><span className="mockup-num">2</span><span className="mockup-text">  <span className="code-str">"biometrics"</span>: &#123; <span className="code-accent">"age"</span>: <span className="code-val">26</span>, <span className="code-accent">"bmi"</span>: <span className="code-val">24.1</span>, <span className="code-accent">"gender"</span>: <span className="code-str">"Male"</span> &#125;,</span></div>
                    <div className="mockup-line"><span className="mockup-num">3</span><span className="mockup-text">  <span className="code-str">"workout_rf"</span>: &#123;</span></div>
                    <div className="mockup-line"><span className="mockup-num">4</span><span className="mockup-text">    <span className="code-accent">"goal"</span>: <span className="code-str">"Muscle Gain"</span>,</span></div>
                    <div className="mockup-line"><span className="mockup-num">5</span><span className="mockup-text">    <span className="code-accent">"equipment_constraint"</span>: <span className="code-str">"gym membership"</span>,</span></div>
                    <div className="mockup-line"><span className="mockup-num">6</span><span className="mockup-text">    <span className="code-accent">"session_cap_min"</span>: <span className="code-val">60</span></span></div>
                    <div className="mockup-line"><span className="mockup-num">7</span><span className="mockup-text">  &#125;,</span></div>
                    <div className="mockup-line"><span className="mockup-num">8</span><span className="mockup-text">  <span className="code-str">"diet_screening"</span>: &#123; <span className="code-accent">"allergens"</span>: [], <span className="code-accent">"pref"</span>: <span className="code-str">"Omnivore"</span> &#125;</span></div>
                    <div className="mockup-line"><span className="mockup-num">9</span><span className="mockup-text">&#125;</span></div>
                  </div>
                )}

                {activeTab === "metrics" && (
                  <div>
                    <div className="mockup-line"><span className="mockup-num">1</span><span className="mockup-text"><span className="code-comment">[INFO] Loaded workout_model.joblib (RandomForestClassifier)</span></span></div>
                    <div className="mockup-line"><span className="mockup-num">2</span><span className="mockup-text"><span className="code-accent">Accuracy (Held-out Test):</span> <span className="code-func">0.8941</span> (Baseline: 0.341)</span></div>
                    <div className="mockup-line"><span className="mockup-num">3</span><span className="mockup-text"><span className="code-comment">[INFO] Loaded diet_model.joblib (RandomForestRegressor)</span></span></div>
                    <div className="mockup-line"><span className="mockup-num">4</span><span className="mockup-text"><span className="code-accent">MAE (Calorie Target):</span> <span className="code-func">±142.5 kcal</span></span></div>
                    <div className="mockup-line"><span className="mockup-num">5</span><span className="mockup-text"><span className="code-comment">[INFO] KNN Food Vector Space: 500+ ingredients indexed</span></span></div>
                    <div className="mockup-line"><span className="mockup-num">6</span><span className="mockup-text"><span className="code-str">STATUS: ALL ENGINES INITIALIZED AND READY</span></span></div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
