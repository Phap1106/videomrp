"use client";

import { useState } from "react";
import { Upload, Settings, Play } from "lucide-react";
import toast from "react-hot-toast";
import { apiClient } from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import { VoiceSelector } from "../VoiceSelector";
import { VideoPreview } from "../VideoPreview";
import { TextEditor } from "../TextEditor";
import clsx from "clsx";

export function ReupVideoFeature() {
  const [videoUrl, setVideoUrl] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  const currentOptions = useAppStore((s) => s.currentOptions);
  const setCurrentOptions = useAppStore((s) => s.setCurrentOptions);
  const selectedVoice = useAppStore((s) => s.selectedVoice);

  const pollJobStatus = (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiClient.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === "completed" || status.status === "failed") {
          clearInterval(pollInterval);
          if (status.status === "completed") {
            toast.success("Video đã được xử lý thành công!");
            setShowPreview(true);
          } else {
            toast.error(status.error_message || "Lỗi khi xử lý video");
          }
        }
      } catch {
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const handleProcessVideo = async () => {
    if (!videoUrl.trim()) {
      toast.error("Vui lòng nhập URL video");
      return;
    }

    try {
      setIsProcessing(true);

      const result = await apiClient.processReupVideo({
        source_url: videoUrl.trim(),
        title: title || "Reup Video",
        description,
        target_platform: currentOptions.targetPlatform,
        video_type: currentOptions.videoType,
        duration: currentOptions.duration,
        add_subtitles: currentOptions.addSubtitles,
        add_ai_narration: currentOptions.addAiNarration,
        add_text_overlay: currentOptions.addTextOverlay,
        remove_watermark: currentOptions.removeWatermark,
        ai_provider: currentOptions.aiProvider,
        tts_voice: selectedVoice,
        narration_style: currentOptions.narrationStyle,
        processing_flow: currentOptions.processingFlow,
      });

      if (result?.success) {
        setCurrentJobId(result.job_id);
        toast.success("Video đã được thêm vào hàng đợi xử lý");
        pollJobStatus(result.job_id);
      } else {
        toast.error("Không tạo được job xử lý");
      }
    } catch {
      toast.error("Lỗi khi xử lý video");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Video Input */}
      <section className="app-card">
        <h2 className="app-section-title">
          <Upload className="w-6 h-6 text-purple-400" />
          Tính năng Reup Video
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">
              URL Video (YouTube, TikTok, Instagram, v.v.)
            </label>
            <input
              type="url"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="app-control"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Tiêu đề (tùy chọn)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Tiêu đề video"
                className="app-control"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Mô tả (tùy chọn)</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Mô tả video"
                className="app-control"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Options */}
      <section className="app-card">
        <h3 className="app-section-title">
          <Settings className="w-5 h-5 text-purple-400" />
          Cài đặt Xử lý
        </h3>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Nền tảng đích</label>
            <select
              value={currentOptions.targetPlatform}
              onChange={(e) => setCurrentOptions({ targetPlatform: e.target.value as any })}
              className="app-control"
            >
              <option value="tiktok">TikTok</option>
              <option value="youtube">YouTube</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="douyin">Douyin</option>
              <option value="twitter">Twitter/X</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Loại video</label>
            <select
              value={currentOptions.videoType}
              onChange={(e) => setCurrentOptions({ videoType: e.target.value as any })}
              className="app-control"
            >
              <option value="short">Short (15-60s)</option>
              <option value="highlight">Highlight (2-5m)</option>
              <option value="viral">Viral (30-90s)</option>
              <option value="meme">Meme (15-30s)</option>
              <option value="full">Full</option>
              <option value="reel">Reel (15-90s)</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">
              Thời lượng (giây): <span className="text-purple-300">{currentOptions.duration}</span>
            </label>
            <input
              type="range"
              min={15}
              max={600}
              value={currentOptions.duration}
              onChange={(e) => setCurrentOptions({ duration: parseInt(e.target.value, 10) })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Quy trình xử lý</label>
            <select
              value={currentOptions.processingFlow}
              onChange={(e) => setCurrentOptions({ processingFlow: e.target.value as any })}
              className="app-control"
            >
              <option value="auto">Auto (Khuyến nghị)</option>
              <option value="fast">Nhanh</option>
              <option value="ai">AI-Enhanced</option>
              <option value="full">Đầy đủ</option>
              <option value="custom">Tùy chỉnh</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Kiểu lời thoại</label>
            <select
              value={currentOptions.narrationStyle}
              onChange={(e) => setCurrentOptions({ narrationStyle: e.target.value as any })}
              className="app-control"
            >
              <option value="professional">Chuyên nghiệp</option>
              <option value="casual">Bình thường</option>
              <option value="dramatic">Kịch tính</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Nhà cung cấp AI</label>
            <select
              value={currentOptions.aiProvider}
              onChange={(e) => setCurrentOptions({ aiProvider: e.target.value as any })}
              className="app-control"
            >
              <option value="auto">Auto</option>
              <option value="openai">OpenAI</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>
        </div>

        {/* Toggles */}
        <div className="grid grid-cols-1 gap-4 mt-6 md:grid-cols-2">
          {[
            { key: "addSubtitles", label: "Thêm phụ đề" },
            { key: "addAiNarration", label: "Thêm lời thoại AI" },
            { key: "addTextOverlay", label: "Thêm chèn chữ" },
            { key: "removeWatermark", label: "Xóa watermark" },
          ].map((feature) => (
            <label
              key={feature.key}
              className="flex items-center gap-3 p-3 border cursor-pointer rounded-xl border-white/10 bg-white/5 hover:bg-white/10"
            >
              <input
                type="checkbox"
                checked={(currentOptions as any)[feature.key]}
                onChange={(e) => setCurrentOptions({ [feature.key]: e.target.checked } as any)}
                className="w-5 h-5"
              />
              <span className="font-medium text-gray-200">{feature.label}</span>
            </label>
          ))}
        </div>
      </section>

      {/* Voice Selection */}
      <section className="app-card">
        <VoiceSelector aiProvider={currentOptions.aiProvider} onVoiceSelect={() => { }} />
      </section>

      {/* Text Editor */}
      {currentOptions.addTextOverlay && (
        <section className="app-card">
          <TextEditor />
        </section>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-4 md:flex-row">
        <button
          onClick={handleProcessVideo}
          disabled={isProcessing || !videoUrl.trim()}
          className={clsx(
            "app-btn-primary flex-1",
            (isProcessing || !videoUrl.trim()) && "opacity-50 cursor-not-allowed shadow-none"
          )}
        >
          <Upload className="w-5 h-5" />
          {isProcessing ? "Đang xử lý..." : "Bắt đầu xử lý"}
        </button>

        {currentJobId && (
          <button
            onClick={() => setShowPreview(true)}
            className="flex items-center justify-center gap-2 px-6 py-3 text-white bg-green-600 rounded-xl hover:bg-green-700 shadow-lg shadow-green-500/20"
          >
            <Play className="w-5 h-5" />
            Xem trước
          </button>
        )}
      </div>

      {/* Job Status */}
      {jobStatus && (
        <section className="app-card border-blue-500/30 bg-blue-500/5">
          <h4 className="mb-2 font-semibold text-white">Trạng thái công việc</h4>
          <div className="space-y-2 text-sm text-gray-200">
            <div>
              <strong>Trạng thái:</strong>{" "}
              <span
                className={clsx("rounded px-2 py-1 text-xs font-medium", {
                  "bg-yellow-500/20 text-yellow-300": jobStatus.status === "pending",
                  "bg-blue-500/20 text-blue-300": jobStatus.status === "processing",
                  "bg-green-500/20 text-green-300": jobStatus.status === "completed",
                  "bg-red-500/20 text-red-300": jobStatus.status === "failed",
                })}
              >
                {jobStatus.status}
              </span>
            </div>
            <div>
              <strong>Bước hiện tại:</strong> {jobStatus.current_step}
            </div>
            <div>
              <strong>Tiến độ:</strong> {jobStatus.progress}%
            </div>
            {jobStatus.error_message && (
              <div className="text-red-300">
                <strong>Lỗi:</strong> {jobStatus.error_message}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Preview */}
      {showPreview && currentJobId && (
        <section className="app-card">
          <VideoPreview jobId={currentJobId} onClose={() => setShowPreview(false)} />
        </section>
      )}
    </div>
  );
}
