import { UNIFIED_OPTIONS, generateSimulatedRecommendation } from "./mockData.js";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:5000";

// Fast fetch with timeout to avoid long UI stalls when backend is offline
async function fetchWithTimeout(url, options = {}, timeoutMs = 2500) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(id);
    return res;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

export async function fetchHealth() {
  try {
    const r = await fetchWithTimeout(`${API_BASE}/api/health`, {}, 2000);
    const data = await r.json().catch(() => null);
    if (!r.ok || !data) {
      return { status: "simulated", mode: "offline_fallback" };
    }
    return { status: "online", detail: data };
  } catch {
    return { status: "simulated", mode: "offline_fallback" };
  }
}

export async function fetchUnifiedOptions() {
  try {
    const r = await fetchWithTimeout(`${API_BASE}/api/options/unified`, {}, 2500);
    const data = await r.json().catch(() => null);
    if (r.ok && data?.success) {
      return { source: "backend", ...data };
    }
    return { source: "simulated", ...UNIFIED_OPTIONS };
  } catch {
    // Graceful fallback to offline catalog options
    return { source: "simulated", ...UNIFIED_OPTIONS };
  }
}

export async function fetchUnified(profile) {
  try {
    const r = await fetchWithTimeout(`${API_BASE}/api/recommendations/unified`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    }, 4000);
    const data = await r.json().catch(() => null);
    if (r.ok && data?.success) {
      return { source: "backend", ...data };
    }
    // If backend returns 400 or other error, fallback to simulated with note
    console.warn("Backend response was not ok, falling back to simulated engine:", data?.error);
    return generateSimulatedRecommendation(profile);
  } catch (err) {
    console.info("Using simulated ML engine due to connection state:", err.message);
    return generateSimulatedRecommendation(profile);
  }
}
