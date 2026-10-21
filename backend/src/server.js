// Express API: input validation + forwarding to the Python ML service.
// No ML logic here. Never exposes stack traces or local paths to the browser.
const express = require("express");
const cors = require("cors");

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || "http://localhost:8000";
// comma-separated allowlist, e.g. "http://localhost:5173,http://localhost:5174"
const FRONTEND_ORIGINS = (process.env.FRONTEND_ORIGIN || "http://localhost:5173,http://localhost:5174")
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
  if (!["weight loss", "muscle gain", "general fitness"].includes(norm(p.goal)))
    return "goal must be one of: weight loss, muscle gain, general fitness";
  if (!["bodyweight", "dumbbells", "full gym"].includes(norm(p.equipment)))
    return "equipment must be one of: bodyweight, dumbbells, full gym";
  if (p.workout_duration_minutes === undefined || typeof p.workout_duration_minutes !== "number" || !(p.workout_duration_minutes > 0))
    return "workout_duration_minutes must be a positive number";
  if (p.fitness_level !== undefined && !["beginner", "intermediate", "advanced"].includes(norm(p.fitness_level)))
    return "fitness_level must be one of: beginner, intermediate, advanced";
  if (p.activity_level !== undefined && !["sedentary", "moderate", "active"].includes(norm(p.activity_level)))
    return "activity_level must be one of: sedentary, moderate, active";
  if (p.workout_days_per_week !== undefined && (!Number.isInteger(p.workout_days_per_week) || p.workout_days_per_week < 1 || p.workout_days_per_week > 7))
    return "workout_days_per_week must be an integer between 1 and 7";
  if (p.dietary_preference !== undefined && !["any", "vegetarian", "non vegetarian"].includes(norm(p.dietary_preference)))
    return "dietary_preference must be one of: any, vegetarian, non vegetarian";
  if (p.allergies !== undefined && !Array.isArray(p.allergies)) return "allergies must be an array";
  if (p.injuries_or_limitations !== undefined && typeof p.injuries_or_limitations !== "string")
    return "injuries_or_limitations must be a string";
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
  for (const f of ["Age", "Weight_kg", "Height_cm"]) {
    if (p[f] !== undefined && (typeof p[f] !== "number" || !(p[f] > 0))) return `${f} must be a positive number`;
  }
  for (const f of ["allergies", "dietary_restrictions"]) {
    if (p[f] !== undefined && !Array.isArray(p[f])) return `${f} must be an array`;
  }
  // Recipe options (synced with indian_food.csv via GET /api/options/diet)
  if (p.course !== undefined && typeof p.course !== "string")
    return "course must be a string";
  if (p.course !== undefined && !["", "any", "main course", "dessert", "snack", "starter"].includes(p.course.trim().toLowerCase()))
    return "course must be one of: any, main course, dessert, snack, starter";
  if (p.diet_preference !== undefined && !["any", "vegetarian", "non vegetarian"].includes(String(p.diet_preference).trim().toLowerCase()))
    return "diet_preference must be one of: any, vegetarian, non vegetarian";
  if (p.max_time_min !== undefined && (typeof p.max_time_min !== "number" || !(p.max_time_min > 0)))
    return "max_time_min must be a positive number";
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
