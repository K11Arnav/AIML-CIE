// Backend tests: validation, forwarding, timeout, error mapping. No network.
const { test, describe } = require("node:test");
const assert = require("node:assert/strict");
const { createApp, validateWorkout, validateDiet, validateUnified } = require("../src/server.js");

function fakeFetch(handler) {
  return async (url, opts) => handler(url, opts);
}
function jsonResponse(status, body) {
  return { ok: status >= 200 && status < 300, status, json: async () => body };
}
async function post(app, path, body) {
  return new Promise((resolve, reject) => {
    const server = app.listen(0, async () => {
      try {
        const r = await fetch(`http://localhost:${server.address().port}${path}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        resolve({ status: r.status, body: await r.json() });
      } catch (e) {
        reject(e);
      } finally {
        server.close();
      }
    });
  });
}

describe("validation", () => {
  test("workout rejects bad top_n", () => {
    assert.match(validateWorkout({ top_n: 0 }), /top_n/);
    assert.equal(validateWorkout({ top_n: 3 }), null);
    assert.match(validateWorkout([1]), /object/);
  });
  test("diet rejects bad top_k and fields", () => {
    assert.match(validateDiet({ top_k: 99 }), /top_k/);
    assert.match(validateDiet({ Age: -5 }), /Age/);
    assert.match(validateDiet({ allergies: "Peanuts" }), /allergies/);
    assert.equal(validateDiet({ top_k: 5 }), null);
  });
  test("diet rejects bad course, diet_preference, max_time", () => {
    assert.match(validateDiet({ course: "breakfast" }), /course/);
    assert.match(validateDiet({ diet_preference: "vegan" }), /diet_preference/);
    assert.match(validateDiet({ max_time_min: -5 }), /max_time_min/);
    assert.equal(validateDiet({ course: "dessert", diet_preference: "vegetarian", max_time_min: 45 }), null);
  });
  test("unified validates canonical profile", () => {
    const ok = { age: 30, height_cm: 165, weight_kg: 65, gender: "Female", goal: "weight loss", equipment: "dumbbells", workout_duration_minutes: 45 };
    assert.equal(validateUnified(ok), null);
    assert.equal(validateUnified({ ...ok, fitness_level: "beginner", activity_level: "active", workout_days_per_week: 4, dietary_preference: "vegetarian", allergies: [] }), null);
    assert.match(validateUnified({}), /age/);
    assert.match(validateUnified({ ...ok, age: -1 }), /age/);
    assert.match(validateUnified({ ...ok, goal: "marathon" }), /goal/);
    assert.match(validateUnified({ ...ok, equipment: "barbell" }), /equipment/);
    assert.match(validateUnified({ ...ok, workout_days_per_week: 9 }), /workout_days_per_week/);
    assert.match(validateUnified([1]), /object/);
  });
});

describe("options forwarding", () => {
  test("GET /api/options/workout forwards ML options", async () => {
    const mlBody = { success: true, goals: ["Bodybuilding"], defaults: { goal: "Bodybuilding" } };
    const app = createApp(fakeFetch(async () => jsonResponse(200, mlBody)));
    const got = await new Promise((resolve, reject) => {
      const server = app.listen(0, async () => {
        try {
          const r = await fetch(`http://localhost:${server.address().port}/api/options/workout`);
          resolve({ status: r.status, body: await r.json() });
        } catch (e) { reject(e); } finally { server.close(); }
      });
    });
    assert.equal(got.status, 200);
    assert.equal(got.body.goals[0], "Bodybuilding");
  });
  test("options ML down maps to 503", async () => {
    const app = createApp(fakeFetch(async () => { throw new Error("down"); }));
    const got = await new Promise((resolve, reject) => {
      const server = app.listen(0, async () => {
        try {
          const r = await fetch(`http://localhost:${server.address().port}/api/options/diet`);
          resolve({ status: r.status, body: await r.json() });
        } catch (e) { reject(e); } finally { server.close(); }
      });
    });
    assert.equal(got.status, 503);
    assert.equal(got.body.success, false);
  });
});

describe("forwarding", () => {
  test("workout forwards ML result", async () => {
    const mlBody = { success: true, recommendation_type: "workout", programs: [{ program: "P" }] };
    const app = createApp(fakeFetch(async () => jsonResponse(200, mlBody)));
    const r = await post(app, "/api/recommendations/workout", { goal: "Bodybuilding" });
    assert.equal(r.status, 200);
    assert.equal(r.body.programs[0].program, "P");
  });
  test("diet forwards ML result", async () => {
    const mlBody = { success: true, recommendation_type: "diet", items: [] };
    const app = createApp(fakeFetch(async () => jsonResponse(200, mlBody)));
    const r = await post(app, "/api/recommendations/diet", { top_k: 5 });
    assert.equal(r.status, 200);
    assert.equal(r.body.recommendation_type, "diet");
  });
  test("ML 400 maps to 400 with message", async () => {
    const app = createApp(fakeFetch(async () => jsonResponse(400, { success: false, error: "bad top_k" })));
    const r = await post(app, "/api/recommendations/diet", { top_k: 5 });
    assert.equal(r.status, 400);
    assert.match(r.body.error, /bad top_k/);
  });
  test("ML down maps to 503 without leaking internals", async () => {
    const app = createApp(fakeFetch(async () => { throw new Error("ECONNREFUSED /tmp/secret-path"); }));
    const r = await post(app, "/api/recommendations/diet", { top_k: 5 });
    assert.equal(r.status, 503);
    assert.equal(r.body.error, "ML service unavailable");
    assert.ok(!JSON.stringify(r.body).includes("secret-path"));
  });
  test("unified forwards combined result", async () => {
    const mlBody = { success: true, recommendation_type: "unified", diet: { items: [] }, workout: { primary: null } };
    const app = createApp(fakeFetch(async () => jsonResponse(200, mlBody)));
    const r = await post(app, "/api/recommendations/unified", { age: 30, height_cm: 165, weight_kg: 65, gender: "Female", goal: "general fitness", equipment: "full gym", workout_duration_minutes: 60 });
    assert.equal(r.status, 200);
    assert.equal(r.body.recommendation_type, "unified");
  });
  test("unified local validation rejects before forwarding", async () => {
    let called = false;
    const app = createApp(fakeFetch(async () => { called = true; return jsonResponse(200, {}); }));
    const r = await post(app, "/api/recommendations/diet", { top_k: 999 });
    assert.equal(r.status, 400);
    assert.equal(called, false);
  });
});
