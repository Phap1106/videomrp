"use client";

import { useEffect, useMemo, useState } from "react";
import { api, type Platform, type VideoType, type VideoCreateRequest, type PlatformSettings } from "@/lib/api";

export function JobCreateForm({ onCreated }: { onCreated: () => void }) {
  const [platforms, setPlatforms] = useState<PlatformSettings[]>([]);
  const [loading, setLoading] = useState(false);

  const [source_url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDesc] = useState("");

  const [target_platform, setTargetPlatform] = useState<Platform>("tiktok");
  const [video_type, setVideoType] = useState<VideoType>("short");
  const [duration, setDuration] = useState(60);

  const [add_subtitles, setAddSubtitles] = useState(true);
  const [change_music, setChangeMusic] = useState(true);
  const [remove_watermark, setRemoveWatermark] = useState(true);
  const [add_effects, setAddEffects] = useState(true);
  const [meme_template, setMemeTemplate] = useState("");

  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.platforms().then(setPlatforms).catch(() => setPlatforms([]));
  }, []);

  const maxDuration = useMemo(() => {
    const p = platforms.find(x => x.platform === target_platform);
    return p?.max_duration || 600;
  }, [platforms, target_platform]);

  async function submit() {
    setErr(null);
    setLoading(true);
    try {
      const body: VideoCreateRequest = {
        source_url: source_url.trim(),
        title: title.trim() || undefined,
        description: description.trim() || undefined,
        target_platform,
        video_type,
        duration: Math.max(5, Math.min(duration, 600)),
        add_subtitles,
        change_music,
        remove_watermark,
        add_effects,
        meme_template: meme_template.trim() || undefined
      };
      await api.createJob(body);
      setUrl("");
      setTitle("");
      setDesc("");
      onCreated();
    } catch (e: any) {
      setErr(e?.message || "Create job failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="row">
        <div style={{ flex: 1, minWidth: 300 }}>
          <div className="label">Source URL (bắt buộc)</div>
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
          <div className="small" style={{ marginTop: 6 }}>Max duration: {maxDuration}s</div>
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
          <div className="label">Duration (5-600s)</div>
          <input
            className="input"
            type="number"
            value={duration}
            min={5}
            max={Math.min(600, maxDuration)}
            onChange={(e) => setDuration(Number(e.target.value || 0))}
          />
        </div>
      </div>

      <div className="hr" />

      <div className="row">
        <div style={{ flex: 1, minWidth: 240 }}>
          <div className="label">Title</div>
          <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Optional" />
        </div>
        <div style={{ flex: 2, minWidth: 320 }}>
          <div className="label">Description</div>
          <input className="input" value={description} onChange={(e) => setDesc(e.target.value)} placeholder="Optional" />
        </div>
        <div style={{ width: 220, minWidth: 200 }}>
          <div className="label">Meme template (optional)</div>
          <input className="input" value={meme_template} onChange={(e) => setMemeTemplate(e.target.value)} placeholder="vd: drake, two_buttons..." />
        </div>
      </div>

      <div className="row" style={{ marginTop: 10 }}>
        <label className="small"><input type="checkbox" checked={add_subtitles} onChange={(e) => setAddSubtitles(e.target.checked)} /> Add subtitles</label>
        <label className="small"><input type="checkbox" checked={change_music} onChange={(e) => setChangeMusic(e.target.checked)} /> Change music</label>
        <label className="small"><input type="checkbox" checked={remove_watermark} onChange={(e) => setRemoveWatermark(e.target.checked)} /> Remove watermark</label>
        <label className="small"><input type="checkbox" checked={add_effects} onChange={(e) => setAddEffects(e.target.checked)} /> Add effects</label>
      </div>

      {err && <div style={{ marginTop: 10, padding: 10, borderRadius: 10, border: "1px solid #ffd0d0", background: "#fff0f0" }}>{err}</div>}

      <div style={{ marginTop: 12 }}>
        <button className="btn" disabled={loading || !source_url.trim()} onClick={submit}>
          {loading ? "Creating..." : "Create job"}
        </button>
      </div>
    </div>
  );
}
