"use client";
import type { JobStatus } from "@/lib/api";

export function StatusPill({ status }: { status: JobStatus }) {
  const map: Record<JobStatus, { bg: string; bd: string }> = {
    pending: { bg: "#f4f4f4", bd: "#e5e5e5" },
    downloading: { bg: "#eef7ff", bd: "#cfe8ff" },
    analyzing: { bg: "#fff7e8", bd: "#ffe4b8" },
    processing: { bg: "#f0f0ff", bd: "#d9d9ff" },
    completed: { bg: "#eafff0", bd: "#bff0d3" },
    failed: { bg: "#fff0f0", bd: "#ffd0d0" },
    cancelled: { bg: "#f4f4f4", bd: "#e5e5e5" }
  };

  const s = map[status] || map.pending;

  return (
    <span className="badge" style={{ background: s.bg, borderColor: s.bd }}>
      {status}
    </span>
  );
}
