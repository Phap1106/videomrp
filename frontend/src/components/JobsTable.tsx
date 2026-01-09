"use client";

import { useMemo } from "react";
import { api, type Job, type JobStatus, type Platform } from "@/lib/api";
import { StatusPill } from "./StatusPill";

export function JobsTable({
  data,
  onRefresh
}: {
  data: Job[];
  onRefresh: () => void;
}) {
  async function doDelete(id: string) {
    if (!confirm("Delete job?")) return;
    await api.deleteJob(id);
    onRefresh();
  }

  async function doRetry(id: string) {
    await api.retryJob(id);
    onRefresh();
  }

  const rows = useMemo(() => data || [], [data]);

  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            <th>Job</th>
            <th>Status</th>
            <th>Progress</th>
            <th>Target</th>
            <th>Output</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((j) => {
            const links = api.outputLinks(j);
            return (
              <tr key={j.id}>
                <td>
                  <div style={{ fontWeight: 700 }}>{j.title}</div>
                  <div className="mono">{j.id}</div>
                  {j.error_message && <div style={{ marginTop: 6, color: "#b00020" }}>{j.error_message}</div>}
                </td>
                <td><StatusPill status={j.status} /></td>
                <td>
                  <div>{Math.round(j.progress || 0)}%</div>
                  <div className="small">{j.current_step}</div>
                </td>
                <td>
                  <div className="mono">{j.target_platform}</div>
                  <div className="small">{j.video_type} • {j.duration}s</div>
                </td>
                <td>
                  {j.output_filename ? (
                    <div style={{ display: "grid", gap: 6 }}>
                      <div className="mono">{j.output_filename}</div>
                      {links.map((u) => (
                        <a key={u} href={u} target="_blank" rel="noreferrer" className="small">
                          Download: {u}
                        </a>
                      ))}
                    </div>
                  ) : (
                    <span className="small">—</span>
                  )}
                </td>
                <td>
                  <div className="row" style={{ gap: 8 }}>
                    <button className="btn secondary" onClick={() => navigator.clipboard.writeText(j.id)}>Copy ID</button>
                    {j.status === "failed" && <button className="btn" onClick={() => doRetry(j.id)}>Retry</button>}
                    <button className="btn secondary" onClick={() => doDelete(j.id)}>Delete</button>
                  </div>
                </td>
              </tr>
            );
          })}
          {rows.length === 0 && (
            <tr><td colSpan={6} className="small">No jobs</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
