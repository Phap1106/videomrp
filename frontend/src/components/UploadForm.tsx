"use client";

import { useState } from "react";
import { api, type Platform, type VideoType } from "@/lib/api";

export function UploadForm({ onUploaded }: { onUploaded: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [target_platform, setTargetPlatform] = useState<Platform>("tiktok");
  const [video_type, setVideoType] = useState<VideoType>("short");
  const [duration, setDuration] = useState(60);

  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    if (!file) return;
    setErr(null);
    setLoading(true);
    try {
      await api.upload(file, { target_platform, video_type, duration });
      setFile(null);
      onUploaded();
    } catch (e: any) {
      setErr(e?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="row">
        <div style={{ flex: 1, minWidth: 280 }}>
          <div className="label">Video file</div>
          <input className="input" type="file" accept=".mp4,.mov,.avi,.mkv,.webm" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          <div className="small" style={{ marginTop: 6 }}>{file ? `Selected: ${file.name}` : "Chọn file để upload"}</div>
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
        <div style={{ width: 200, minWidth: 180 }}>
          <div className="label">Video type</div>
          <select className="select" value={video_type} onChange={(e) => setVideoType(e.target.value as any)}>
            <option value="short">short</option>
            <option value="highlight">highlight</option>
            <option value="viral">viral</option>
            <option value="meme">meme</option>
            <option value="full">full</option>
            <option value="reel">reel</option>
          </select>
        </div>
        <div style={{ width: 160, minWidth: 140 }}>
          <div className="label">Duration</div>
          <input className="input" type="number" min={5} max={600} value={duration} onChange={(e) => setDuration(Number(e.target.value || 0))} />
        </div>
        <div style={{ display: "flex", alignItems: "end" }}>
          <button className="btn" disabled={loading || !file} onClick={submit}>
            {loading ? "Uploading..." : "Upload & process"}
          </button>
        </div>
      </div>

      {err && <div style={{ marginTop: 10, padding: 10, borderRadius: 10, border: "1px solid #ffd0d0", background: "#fff0f0" }}>{err}</div>}
    </div>
  );
}
