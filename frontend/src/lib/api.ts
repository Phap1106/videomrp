const BASE = (process.env.NEXT_PUBLIC_BACKEND_BASE_URL || "http://localhost:8000").replace(/\/+$/, "");

export type Platform = "tiktok" | "youtube" | "facebook" | "instagram" | "douyin" | "twitter" | "generic";
export type VideoType = "short" | "highlight" | "viral" | "meme" | "full" | "reel";
export type JobStatus = "pending" | "downloading" | "analyzing" | "processing" | "completed" | "failed" | "cancelled";

export type Job = {
  id: string;
  title: string;
  status: JobStatus;
  progress: number;
  current_step: string;
  source_platform: Platform;
  target_platform: Platform;
  video_type: VideoType;
  duration: number;
  created_at: string;
  updated_at?: string | null;
  completed_at?: string | null;
  output_filename?: string | null;
  error_message?: string | null;
};

export type Paginated<T> = { items: T[]; total: number; page: number; size: number; pages: number };

export type VideoCreateRequest = {
  source_url: string;
  title?: string | null;
  description?: string | null;
  target_platform: Platform;
  video_type: VideoType;
  duration: number;
  add_subtitles: boolean;
  change_music: boolean;
  remove_watermark: boolean;
  add_effects: boolean;
  meme_template?: string | null;
};

export type PlatformSettings = {
  platform: Platform;
  name: string;
  max_duration: number;
  aspect_ratios: string[];
  watermark_allowed: boolean;
  copyright_strictness: string;
  recommended_formats: string[];
  max_size_mb: number;
  audio_requirements: Record<string, any>;
};

export type SystemStatus = {
  api: boolean;
  database: boolean;
  redis: boolean;
  storage: boolean;
  ai_services: Record<string, boolean>;
  queue_size: number;
  active_jobs: number;
  total_jobs: number;
  uptime: number;
  version: string;
  timestamp: number;
};

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  const ct = res.headers.get("content-type") || "";
  const data: any = ct.includes("application/json") ? await res.json().catch(() => ({})) : await res.text();

  if (!res.ok) {
    const msg = data?.detail || data?.message || res.statusText;
    throw new Error(`${res.status}: ${msg}`);
  }
  return data as T;
}

export const api = {
  base: BASE,

  health: () => req<SystemStatus>("/api/health"),
  platforms: () => req<PlatformSettings[]>("/api/platforms"),

  createJob: (body: VideoCreateRequest) =>
    req<Job>("/api/jobs", { method: "POST", body: JSON.stringify(body) }),

  listJobs: (opts: { page: number; size: number; status?: JobStatus | ""; platform?: Platform | "" }) => {
    const q = new URLSearchParams();
    q.set("page", String(opts.page));
    q.set("size", String(opts.size));
    if (opts.status) q.set("status", opts.status);
    if (opts.platform) q.set("platform", opts.platform);
    return req<Paginated<Job>>(`/api/jobs?${q.toString()}`);
  },

  getJob: (id: string) => req<Job>(`/api/jobs/${id}`),
  deleteJob: (id: string) => req<{ success: boolean; message: string }>(`/api/jobs/${id}`, { method: "DELETE" }),
  retryJob: (id: string) => req<Job>(`/api/jobs/${id}/retry`, { method: "POST" }),

  analyze: (body: { source_url: string; target_platform: Platform; analyze_content?: boolean; detect_scenes?: boolean; check_copyright?: boolean }) =>
    req<any>("/api/analyze", { method: "POST", body: JSON.stringify(body) }),

  stats: () => req<any>("/api/stats"),

  upload: async (file: File, fields: { target_platform: Platform; video_type: VideoType; duration: number }) => {
    const form = new FormData();
    form.append("file", file);
    form.append("target_platform", fields.target_platform);
    form.append("video_type", fields.video_type);
    form.append("duration", String(fields.duration));

    const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form, cache: "no-store" });
    const ct = res.headers.get("content-type") || "";
    const data: any = ct.includes("application/json") ? await res.json().catch(() => ({})) : await res.text();
    if (!res.ok) {
      const msg = data?.detail || data?.message || res.statusText;
      throw new Error(`${res.status}: ${msg}`);
    }
    return data as Job;
  },

  // Link tải output (ưu tiên static mount /processed theo đường dẫn thực tế)
  outputLinks: (job: Job) => {
    const fn = job.output_filename || "";
    if (!fn) return [];
    return [
      `${BASE}/processed/${job.id}/${fn}`,     // đúng theo output_path hiện tại
      `${BASE}/api/processed/${fn}`           // endpoint tồn tại nhưng có thể không khớp nested path
    ];
  }
};
