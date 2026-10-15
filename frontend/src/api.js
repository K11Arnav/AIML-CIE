const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

async function postJson(path, body) {
  const r = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new Error((data && data.error) || `Request failed (${r.status})`);
  return data;
}

export async function fetchWorkout(profile) {
  return postJson("/api/recommendations/workout", profile);
}

export async function fetchDiet(profile) {
  return postJson("/api/recommendations/diet", profile);
}

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/api/health`);
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new Error("Backend unavailable");
  return data;
}

export async function fetchOptions() {
  const [w, d] = await Promise.all([
    fetch(`${API_BASE}/api/options/workout`).then(async (r) => {
      const data = await r.json().catch(() => null);
      if (!r.ok || !data?.success) throw new Error((data && data.error) || "Workout options unavailable");
      return data;
    }),
    fetch(`${API_BASE}/api/options/diet`).then(async (r) => {
      const data = await r.json().catch(() => null);
      if (!r.ok || !data?.success) throw new Error((data && data.error) || "Diet options unavailable");
      return data;
    }),
  ]);
  return { workout: w, diet: d };
}
