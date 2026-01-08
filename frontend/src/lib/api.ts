export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000";

export async function getJobs() {
  const r = await fetch(`${API_BASE}/api/jobs`, { cache: "no-store" });
  if (!r.ok) throw new Error("Failed to fetch jobs");
  return r.json();
}

export async function createJob(payload: any) {
  const r = await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data?.detail || "Failed to create job");
  return data;
}
