export default function CtaBanner({ onPrint, onCopyJson, onScrollToTop }) {
  return (
    <section className="container">
      <div className="cta-banner-dark">
        <div>
          <h3 className="cta-banner-title">
            Take Your Personalized Plan Into the Real World
          </h3>
          <p className="cta-banner-text">
            Export your customized periodization schedule and daily nutrition targets.
            Print a clean PDF breakdown or extract the raw JSON prediction payload for integration into your personal tracking system.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", zIndex: 2 }}>
          <button
            type="button"
            className="btn-on-dark"
            onClick={onPrint}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="6 9 6 2 18 2 18 9" />
              <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
              <rect x="6" y="14" width="12" height="8" />
            </svg>
            <span>Print / Save Plan</span>
          </button>

          <button
            type="button"
            className="btn-secondary-on-dark"
            onClick={onCopyJson}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            <span>Copy JSON Payload</span>
          </button>
        </div>
      </div>
    </section>
  );
}
