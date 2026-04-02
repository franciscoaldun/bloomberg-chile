const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchDashboard() {
  const res = await fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Dashboard fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchSeries(
  panelId: string,
  from?: string,
  to?: string
) {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_BASE}/api/series/${panelId}${qs}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Series fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Health fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchCorrelations() {
  const res = await fetch(`${API_BASE}/api/correlations`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Correlations fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchSimulator(amount = 1000000, from?: string, to?: string) {
  const params = new URLSearchParams();
  params.set("amount", String(amount));
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const res = await fetch(`${API_BASE}/api/simulator?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Simulator fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchAnalysis() {
  const res = await fetch(`${API_BASE}/api/analysis`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Analysis fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchCobre() {
  const res = await fetch(`${API_BASE}/api/cobre`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Cobre fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchLatamFx(from?: string, to?: string) {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_BASE}/api/fx/latam${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Latam FX fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchFxMonitor() {
  const res = await fetch(`${API_BASE}/api/fx/monitor`, { cache: "no-store" });
  if (!res.ok) throw new Error(`FX Monitor fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchYieldCurve() {
  const res = await fetch(`${API_BASE}/api/yield-curve`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Yield curve fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchTpmDecisions(limit = 20) {
  const res = await fetch(`${API_BASE}/api/tpm-decisions?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`TPM decisions fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchEof(from?: string, to?: string) {
  const params = new URLSearchParams();
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await fetch(`${API_BASE}/api/eof${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`EOF fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchMacroAnalysis() {
  const res = await fetch(`${API_BASE}/api/macro-analysis`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Macro analysis fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchMacroSynthesis() {
  const res = await fetch(`${API_BASE}/api/macro-synthesis`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Macro synthesis fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchSma(panelId: string, windows = "20,50,200", from?: string, to?: string) {
  const params = new URLSearchParams();
  params.set("windows", windows);
  if (from) params.set("from", from);
  if (to) params.set("to", to);
  const res = await fetch(`${API_BASE}/api/series/${panelId}/sma?${params.toString()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`SMA fetch failed: ${res.status}`);
  return res.json();
}
