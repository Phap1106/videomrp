"use client";

import { useState } from "react";
import { api, type Platform } from "@/lib/api";

export function AnalyzeForm() {
  const [source_url, setUrl] = useState("");
  const [target_platform, setTargetPlatform] = useState<Platform>("tiktok");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await api.analyze({
        source_url: source_url.trim(),
        target_platform,
        analyze_content: true,
        detect_scenes: true,
        check_copyright: true
      });
      setResult(data);
    } catch (e: any) {
      setErr(e?.message || "Analyze failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="row">
        <div style={{ flex: 1, minWidth: 320 }}>
          <div className="label">Source URL</div>
          <input className="input" value={source_url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." />
        </div>
        <div style={{ width: 220, minWidth: 200 }}>
          <div className="label">Target platform</div>
          <select className="select" value={target_platform} onChange={(e) => setTargetPlatform(e.target.value as any)}>
            <option value="tiktok">tiktok</option>
            <option value="youtube">youtube</option>
            <option value="facebook">facebook</option>
            <option value="instagram">instagram</option>
            <option value="douyin">douyin</option>
            <option value="twitter">twitter</option>
          </select>
        </div>
        <div style={{ display: "flex", alignItems: "end" }}>
          <button className="btn" disabled={loading || !source_url.trim()} onClick={submit}>
            {loading ? "Analyzing..." : "Analyze only"}
          </button>
        </div>
      </div>

      {err && <div style={{ marginTop: 10, padding: 10, borderRadius: 10, border: "1px solid #ffd0d0", background: "#fff0f0" }}>{err}</div>}

      {result && (
        <div style={{ marginTop: 12 }}>
          <div className="label">Result (JSON)</div>
          <pre className="mono" style={{ whiteSpace: "pre-wrap", background: "#fafafa", border: "1px solid #eee", borderRadius: 12, padding: 12 }}>
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
