import { useState, useMemo } from "react";

export default function FoodCatalogView({ items, goalLabel }) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTag, setSelectedTag] = useState("all");

  const filteredItems = useMemo(() => {
    let list = items || [];
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      list = list.filter((it) => (it.product_name || "").toLowerCase().includes(q) || (it.rank_reason || "").toLowerCase().includes(q));
    }
    if (selectedTag !== "all") {
      list = list.filter((it) => (it.tags || []).some((t) => t.toLowerCase().includes(selectedTag.toLowerCase())));
    }
    return list;
  }, [items, searchTerm, selectedTag]);

  return (
    <div id="food-explorer">
      <div className="section-header" style={{ marginBottom: "24px" }}>
        <div className="section-eyebrow">K-NEAREST NEIGHBORS FOOD RANKING</div>
        <h3 className="section-title">
          Foods Ranked for Your Goal: {goalLabel || "Balanced Nutrition"}
        </h3>
        <p className="section-description">
          Ranked by euclidean distance in nutrient space, filtered against your dietary preferences and reported allergens. Values displayed per 100g dataset basis.
        </p>
      </div>

      {/* Large Search Pill Bar */}
      <div style={{ marginBottom: "20px" }}>
        <div className="search-pill-large">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            placeholder="Search nutrient catalog by food name or benefit (e.g. Salmon, Oats, Protein)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button
              type="button"
              className="btn-ghost"
              onClick={() => setSearchTerm("")}
              style={{ fontSize: "12px" }}
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Category Filter Tabs */}
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "28px" }}>
        {["all", "Protein", "Fiber", "Keto", "Vegan", "Fats"].map((tag) => (
          <button
            key={tag}
            type="button"
            className={`pill-tab ${selectedTag === tag ? "pill-tab-active" : ""}`}
            onClick={() => setSelectedTag(tag)}
            style={{ fontSize: "13px", padding: "6px 14px" }}
          >
            {tag === "all" ? "All Ranked Foods" : tag}
          </button>
        ))}
      </div>

      {/* Food Cards Grid */}
      {filteredItems.length === 0 ? (
        <div className="alert-callout warning">
          No food items match your search filter or allergen screening criteria. Try adjusting your search query.
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "20px" }}>
          {filteredItems.map((item) => (
            <div key={`${item.rank}-${item.product_name}`} className="card-base" style={{ display: "flex", flexDirection: "column" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
                <span className="badge-popular">Rank #{item.rank}</span>
                <span style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-brand-green-dark)" }}>
                  {item.energy_kcal ?? "–"} kcal
                </span>
              </div>

              <h4 style={{ fontSize: "18px", fontWeight: 600, color: "var(--color-ink)", marginBottom: "8px", lineHeight: 1.3 }}>
                {item.product_name || "Catalog Food"}
              </h4>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginBottom: "14px" }}>
                {(item.tags || []).map((t, idx) => (
                  <span
                    key={idx}
                    className={idx % 3 === 0 ? "badge-purple" : idx % 3 === 1 ? "badge-orange" : "badge-blue"}
                    style={{ fontSize: "10px" }}
                  >
                    {t}
                  </span>
                ))}
              </div>

              <div style={{ background: "var(--color-surface)", borderRadius: "8px", padding: "10px 12px", marginBottom: "14px", display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "6px", textAlign: "center" }}>
                <div>
                  <div style={{ fontSize: "10px", color: "var(--color-steel)", textTransform: "uppercase" }}>Protein</div>
                  <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-ink)" }}>{item.proteins_100g ?? "–"}g</div>
                </div>
                <div>
                  <div style={{ fontSize: "10px", color: "var(--color-steel)", textTransform: "uppercase" }}>Carbs</div>
                  <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-ink)" }}>{item.carbs_100g ?? "–"}g</div>
                </div>
                <div>
                  <div style={{ fontSize: "10px", color: "var(--color-steel)", textTransform: "uppercase" }}>Fat</div>
                  <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-ink)" }}>{item.fat_100g ?? "–"}g</div>
                </div>
                <div>
                  <div style={{ fontSize: "10px", color: "var(--color-steel)", textTransform: "uppercase" }}>Fiber</div>
                  <div style={{ fontSize: "13px", fontWeight: 700, color: "var(--color-ink)" }}>{item.fiber_100g ?? "–"}g</div>
                </div>
              </div>

              <p style={{ fontSize: "12px", color: "var(--color-slate)", marginTop: "auto", lineHeight: 1.5, borderTop: "1px solid var(--color-hairline)", paddingTop: "10px" }}>
                <strong>KNN Rationale:</strong> {item.rank_reason || "Aligned with high nutrient density vectors."}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
