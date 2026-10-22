export default function Header({ backendStatus, onRetryHealth, onScrollToForm }) {
  const isOnline = backendStatus.status === "online";

  return (
    <header>
      {/* Sticky Top Promo Strip */}
      <div className="promo-banner">
        <span className="promo-badge">ML Engine v2.0</span>
        <span>Dual-Stage Intelligence: Random Forest Classifiers + KNN Nutrition Matcher Active</span>
      </div>

      {/* Main Top Navigation */}
      <nav className="top-nav">
        <div className="top-nav-inner">
          <a href="#" className="brand-logo">
            <div className="brand-icon">
              {/* MongoDB leaf + fitness pulse glyph */}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2z" opacity="0.3"/>
                <path d="M12 6v6l4 2" />
                <path d="M4 14l3.5-3.5L11 14l5-6 4 4" stroke="#00ed64" strokeWidth="2.5"/>
              </svg>
            </div>
            <span>FitSphere<span style={{ color: "#00ed64" }}>.ai</span></span>
          </a>

          <ul className="nav-links">
            <li><a href="#assessment" className="nav-link">Recommender</a></li>
            <li><a href="#workout-plans" className="nav-link">Workout Architecture</a></li>
            <li><a href="#diet-nutrition" className="nav-link">Nutrition &amp; Macros</a></li>
            <li><a href="#food-explorer" className="nav-link">Food Catalog</a></li>
            <li><a href="#ml-telemetry" className="nav-link">Model Telemetry</a></li>
          </ul>

          <div className="nav-actions">
            <div
              className={`backend-status-pill ${isOnline ? "online" : "simulated"}`}
              onClick={onRetryHealth}
              title={isOnline ? "Backend is live on port 5000" : "Running on local validated ML simulation. Click to check backend."}
            >
              <span className="status-dot"></span>
              <span>{isOnline ? "API Live (Port 5000)" : "ML Simulator (Ready)"}</span>
            </div>

            <button
              type="button"
              className="btn-primary"
              onClick={onScrollToForm}
              style={{ padding: "8px 18px", fontSize: "13px" }}
            >
              Start Assessment →
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
}
