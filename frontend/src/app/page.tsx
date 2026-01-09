"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type Job, type JobStatus, type Platform, type SystemStatus } from "@/lib/api";
import { Tabs } from "@/components/Tabs";
import { JobCreateForm } from "@/components/JobCreateForm";
import { AnalyzeForm } from "@/components/AnalyzeForm";
import { UploadForm } from "@/components/UploadForm";
import { JobsTable } from "@/components/JobsTable";

type TabKey = "create" | "analyze" | "upload";

export default function Page() {
  const [tab, setTab] = useState<TabKey>("create");

  const [health, setHealth] = useState<SystemStatus | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [page, setPage] = useState(1);
  const [size] = useState(20);
  const [pages, setPages] = useState(1);

  const [status, setStatus] = useState<JobStatus | "">("");
  const [platform, setPlatform] = useState<Platform | "">("");

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function refresh() {
    setErr(null);
    setLoading(true);
    try {
      const [h, list] = await Promise.all([
        api.health().catch(() => null),
        api.listJobs({ page, size, status, platform })
      ]);
      setHealth(h);
      setJobs(list.items);
      setPages(list.pages);
    } catch (e: any) {
      setErr(e?.message || "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, [page, status, platform]);

  // Poll các job đang chạy
  const hasRunning = useMemo(
    () => jobs.some(j => j.status === "pending" || j.status === "downloading" || j.status === "analyzing" || j.status === "processing"),
    [jobs]
  );

  useEffect(() => {
    if (!hasRunning) return;
    const t = setInterval(() => refresh(), 2000);
    return () => clearInterval(t);
  }, [hasRunning, page, status, platform]);

  return (
    <main className="container">
      <div className="row" style={{ alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800 }}>VideoMRP</div>
          <div className="small">Backend: <span className="mono">{api.base}</span></div>
          {health && (
            <div className="small" style={{ marginTop: 6 }}>
              Health: {health.api ? "OK" : "NO"} • DB: {health.database ? "OK" : "NO"} • Redis: {health.redis ? "OK" : "NO"} • Storage: {health.storage ? "OK" : "NO"}
            </div>
          )}
        </div>

        <div className="row">
          <button className="btn secondary" onClick={() => refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <Tabs
          value={tab}
          onChange={setTab}
          tabs={[
            { key: "create", label: "Create job" },
            { key: "analyze", label: "Analyze only" },
            { key: "upload", label: "Upload" }
          ]}
        />
      </div>

      <div style={{ marginTop: 12 }}>
        {tab === "create" && <JobCreateForm onCreated={() => { setPage(1); refresh(); }} />}
        {tab === "analyze" && <AnalyzeForm />}
        {tab === "upload" && <UploadForm onUploaded={() => { setPage(1); refresh(); }} />}
      </div>

      {err && (
        <div className="card" style={{ marginTop: 12, borderColor: "#ffd0d0", background: "#fff0f0" }}>
          <b>Error:</b> {err}
        </div>
      )}

      <div style={{ marginTop: 16 }} className="row">
        <div style={{ width: 220, minWidth: 200 }}>
          <div className="label">Filter status</div>
          <select className="select" value={status} onChange={(e) => { setPage(1); setStatus(e.target.value as any); }}>
            <option value="">all</option>
            <option value="pending">pending</option>
            <option value="downloading">downloading</option>
            <option value="analyzing">analyzing</option>
            <option value="processing">processing</option>
            <option value="completed">completed</option>
            <option value="failed">failed</option>
            <option value="cancelled">cancelled</option>
          </select>
        </div>

        <div style={{ width: 220, minWidth: 200 }}>
          <div className="label">Filter platform</div>
          <select className="select" value={platform} onChange={(e) => { setPage(1); setPlatform(e.target.value as any); }}>
            <option value="">all</option>
            <option value="tiktok">tiktok</option>
            <option value="youtube">youtube</option>
            <option value="facebook">facebook</option>
            <option value="instagram">instagram</option>
            <option value="douyin">douyin</option>
            <option value="twitter">twitter</option>
          </select>
        </div>

        <div style={{ display: "flex", alignItems: "end", gap: 8 }}>
          <button className="btn secondary" disabled={page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))}>Prev</button>
          <div className="small">Page {page}/{pages}</div>
          <button className="btn secondary" disabled={page >= pages} onClick={() => setPage(p => Math.min(pages, p + 1))}>Next</button>
        </div>
      </div>

      <div style={{ marginTop: 12 }}>
        <JobsTable data={jobs} onRefresh={refresh} />
      </div>

      
    </main>
  );
}
