// Express API: input validation + forwarding to the Python ML service.
// No ML logic here. Never exposes stack traces or local paths to the browser.
const express = require("express");
const cors = require("cors");

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || "http://localhost:8000";
// comma-separated allowlist, e.g. "http://localhost:5173,http://localhost:5174"
const FRONTEND_ORIGINS = (process.env.FRONTEND_ORIGIN || "http://localhost:5173,http://localhost:5174,http://localhost:4173")
  .split(",").map((s) => s.trim()).filter(Boolean);
const ML_TIMEOUT_MS = Number(process.env.ML_TIMEOUT_MS || 30000);
const PORT = Number(process.env.PORT || 5000);

function createApp(fetchImpl = fetch) {
  const app = express();
  app.use(cors({ origin: FRONTEND_ORIGINS }));
  app.use(express.json({ limit: "100kb" }));

  app.get("/api/health", async (req, res) => {
    try {
      const r = await fetchWithTimeout(fetchImpl, `${ML_SERVICE_URL}/health`, {}, ML_TIMEOUT_MS);
      const body = await safeJson(r);
      res.status(r.ok ? 200 : 503).json({
        status: r.ok ? "ok" : "degraded",
        ml_service: body,
      });
    } catch (e) {
      res.status(503).json({ status: "degraded", ml_service: null, error: "ML service unavailable" });
    }
  });

  app.post("/api/recommendations/workout", async (req, res) => {
    const err = validateWorkout(req.body);
    if (err) return res.status(400).json({ success: false, error: err });
    forward(res, fetchImpl, "/recommendations/workout", req.body);
  });

  app.post("/api/recommendations/diet", async (req, res) => {
    const err = validateDiet(req.body);
    if (err) return res.status(400).json({ success: false, error: err });
    forward(res, fetchImpl, "/recommendations/diet", req.body);
  });

  // Unified profile: one submit feeds both recommenders (validated here AND in Python).
  app.post("/api/recommendations/unified", async (req, res) => {
    const err = validateUnified(req.body);
    if (err) return res.status(400).json({ success: false, error: err });
    forward(res, fetchImpl, "/recommendations/unified", req.body);
  });

  for (const kind of ["workout", "diet", "unified"]) {
    app.get(`/api/options/${kind}`, async (req, res) => {
      try {
        const r = await fetchWithTimeout(fetchImpl, `${ML_SERVICE_URL}/options/${kind}`, {}, ML_TIMEOUT_MS);
        const data = await safeJson(r);
        if (!r.ok || !data) return res.status(502).json({ success: false, error: "ML service error" });
        return res.status(200).json(data);
      } catch (e) {
        return res.status(503).json({ success: false, error: "ML service unavailable" });
      }
    });
  }

  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    if (err && err.type === "entity.parse.failed") {
      return res.status(400).json({ success: false, error: "Request body must be JSON" });
    }
    return res.status(500).json({ success: false, error: "Unexpected server error" });
  });

  return app;
}

function validateUnified(p) {
  // Mirrors ml/unified.py ranges. Python re-validates; this fails fast with 400s.
  if (!p || typeof p !== "object" || Array.isArray(p)) return "Request body must be a JSON object";
  for (const f of ["age", "height_cm", "weight_kg"]) {
    if (p[f] === undefined || typeof p[f] !== "number" || !(p[f] > 0)) return `${f} must be a positive number`;
  }
  if (p.age < 5 || p.age > 100) return "age must be between 5 and 100";
  if (p.height_cm < 50 || p.height_cm > 250) return "height_cm must be between 50 and 250";
  if (p.weight_kg < 20 || p.weight_kg > 300) return "weight_kg must be between 20 and 300";
  const norm = (v) => String(v ?? "").trim().toLowerCase();
  if (!["female", "male"].includes(norm(p.gender))) return "gender must be one of: Female, Male";
  const GOALS = ["weight loss", "muscle gain", "general health", "strength",
    "endurance", "tone up", "powerlifting", "flexibility", "crossfit",
    "athletic performance", "marathon training"];
  if (!GOALS.includes(norm(p.goal)))
    return `goal must be one of: ${GOALS.join(", ")}`;
  const EQUIPMENT = ["bodyweight only", "yoga mat", "home dumbbells", "full home gym", "gym membership"];
  if (!EQUIPMENT.includes(norm(p.equipment)))
    return `equipment must be one of: ${EQUIPMENT.join(", ")}`;
  if (p.workout_duration_minutes === undefined || typeof p.workout_duration_minutes !== "number" || !(p.workout_duration_minutes > 0))
    return "workout_duration_minutes must be a positive number";
  if (p.fitness_level !== undefined && !["beginner", "intermediate", "advanced"].includes(norm(p.fitness_level)))
    return "fitness_level must be one of: beginner, intermediate, advanced";
  if (p.activity_level !== undefined && !["sedentary", "lightly active", "moderately active", "very active"].includes(norm(p.activity_level)))
    return "activity_level must be one of: sedentary, lightly active, moderately active, very active";
  if (p.workout_days_per_week !== undefined && (!Number.isInteger(p.workout_days_per_week) || p.workout_days_per_week < 1 || p.workout_days_per_week > 7))
    return "workout_days_per_week must be an integer between 1 and 7";
  if (p.dietary_preference !== undefined && !["any", "omnivore", "vegetarian", "vegan"].includes(norm(p.dietary_preference)))
    return "dietary_preference must be one of: any, omnivore, vegetarian, vegan";
  if (p.allergies !== undefined && !Array.isArray(p.allergies)) return "allergies must be an array";
  if (p.injuries_or_limitations !== undefined && !["none", "knee", "ankle", "shoulder", "back"].includes(norm(p.injuries_or_limitations)))
    return "injuries_or_limitations must be one of: none, knee, ankle, shoulder, back";
  return null;
}

function validateWorkout(p) {
  if (!p || typeof p !== "object" || Array.isArray(p)) return "Request body must be a JSON object";
  if (p.top_n !== undefined && (!Number.isInteger(p.top_n) || p.top_n < 1 || p.top_n > 4))
    return "top_n must be an integer between 1 and 4 (1 primary plan + up to 3 alternatives)";
  if (p.available_minutes !== undefined && (typeof p.available_minutes !== "number" || !(p.available_minutes > 0)))
    return "available_minutes must be a positive number";
  if (p.equipment !== undefined && !Array.isArray(p.equipment)) return "equipment must be an array";
  return null;
}

function validateDiet(p) {
  if (!p || typeof p !== "object" || Array.isArray(p)) return "Request body must be a JSON object";
  if (p.top_k !== undefined && (!Number.isInteger(p.top_k) || p.top_k < 1 || p.top_k > 50))
    return "top_k must be an integer between 1 and 50";
  for (const f of ["age", "height_cm", "weight_kg", "Height_cm", "Weight_kg", "Age"]) {
    if (p[f] !== undefined && (typeof p[f] !== "number" || !(p[f] > 0))) return `${f} must be a positive number`;
  }
  for (const f of ["Activity Level", "activity_level"]) {
    if (p[f] !== undefined && !["Sedentary", "Lightly Active", "Moderately Active", "Very Active", "sedentary", "lightly active", "moderately active", "very active"].includes(String(p[f]).trim().toLowerCase()))
      return "activity_level must be one of: Sedentary, Lightly Active, Moderately Active, Very Active";
  }
  if (p.allergies !== undefined && !Array.isArray(p.allergies)) return "allergies must be an array";
  if (p.Dietary_Preference !== undefined || p.dietary_preference !== undefined) {
    const pref = String(p.Dietary_Preference ?? p.dietary_preference).trim().toLowerCase();
    if (!["omnivore", "vegetarian", "vegan", "any"].includes(pref))
      return "dietary_preference must be one of: Omnivore, Vegetarian, Vegan";
  }
  if (p.goal !== undefined) {
    const g = String(p.goal).trim().toLowerCase();
    if (!["weight loss", "muscle", "balanced"].includes(g))
      return "goal must be one of: weight loss, muscle, balanced";
  }
  return null;
}

async function forward(res, fetchImpl, path, body) {
  let r;
  try {
    r = await fetchWithTimeout(fetchImpl, `${ML_SERVICE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }, ML_TIMEOUT_MS);
  } catch (e) {
    return res.status(503).json({ success: false, error: "ML service unavailable" });
  }
  const data = await safeJson(r);
  if (!r.ok) {
    const status = r.status === 400 ? 400 : 502;
    return res.status(status).json({
      success: false,
      error: (data && data.error) || "ML service error",
    });
  }
  return res.status(200).json(data);
}

async function fetchWithTimeout(fetchImpl, url, opts, ms) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), ms);
  try {
    return await fetchImpl(url, { ...opts, signal: ctrl.signal });
  } finally {
    clearTimeout(t);
  }
}

async function safeJson(r) {
  try {
    return await r.json();
  } catch (e) {
    return null;
  }
}

if (require.main === module) {
  const server = createApp().listen(PORT, () => console.log(`backend listening on :${PORT}, ml=${ML_SERVICE_URL}`));
  server.on("error", (e) => {
    if (e.code === "EADDRINUSE") {
      console.error(`Port ${PORT} is already in use — another backend instance may be running. Kill it or set PORT=.`);
    } else {
      console.error(`Failed to start backend: ${e.message}`);
    }
    process.exit(1);
  });
}

module.exports = { createApp, validateWorkout, validateDiet, validateUnified };
