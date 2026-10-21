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

export async function fetchUnified(profile) {
  return postJson("/api/recommendations/unified", profile);
}

export async function fetchUnifiedOptions() {
  const r = await fetch(`${API_BASE}/api/options/unified`);
  const data = await r.json().catch(() => null);
  if (!r.ok || !data?.success) throw new Error((data && data.error) || "Options unavailable");
  return data;
}

export async function fetchHealth() {
  const r = await fetch(`${API_BASE}/api/health`);
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new Error("Backend unavailable");
  return data;
}
