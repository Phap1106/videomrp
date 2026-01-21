
"use client";

import { useState } from "react";
import { BookOpen, Play, Upload, Layers } from "lucide-react";
import toast from "react-hot-toast";
import { apiClient } from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import clsx from "clsx";

export function SeriesFeature() {
    const [videoUrl, setVideoUrl] = useState("");
    const [topic, setTopic] = useState("");
    const [numParts, setNumParts] = useState(3);
    const [voiceStyle, setVoiceStyle] = useState("cynical");
    const [bgmStyle, setBgmStyle] = useState("dramatic");
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentJobId, setCurrentJobId] = useState<string | null>(null);

    const selectedVoice = useAppStore((s) => s.selectedVoice);

    const handleSubmit = async () => {
        if (!videoUrl || !topic) {
            toast.error("Vui lòng nhập Link Video và Chủ đề Series");
            return;
        }

        try {
            setIsProcessing(true);
            const result = await apiClient.createStorySeries({
                source_url: videoUrl,
                topic: topic,
                num_parts: numParts,
                voice_style: voiceStyle,
                bgm_style: bgmStyle,
                tts_voice: selectedVoice,
                target_platform: "tiktok"
            });

            if (result?.success) {
                setCurrentJobId(result.job_id);
                toast.success("Đã bắt đầu tạo Series! Vui lòng đợi...");
                pollJobStatus(result.job_id);
            } else {
                toast.error("Lỗi khởi tạo job");
            }
        } catch (error) {
            toast.error("Có lỗi xảy ra");
        } finally {
            setIsProcessing(false);
        }
    };

    const pollJobStatus = (jobId: string) => {
        const pollInterval = setInterval(async () => {
            try {
                const status = await apiClient.getJobStatus(jobId);
                if (status.status === "completed" || status.status === "failed") {
                    clearInterval(pollInterval);
                    if (status.status === "completed") {
                        toast.success("Series đã hoàn thành!");
                    } else {
                        toast.error(status.error_message || "Lỗi xử lý");
                    }
                }
            } catch {
                clearInterval(pollInterval);
            }
        }, 3000);
    };

    return (
        <div className="space-y-6">
            <section className="app-card">
                <h2 className="app-section-title">
                    <BookOpen className="w-6 h-6 text-pink-400" />
                    Kể Chuyện Dài Kỳ (Story Series)
                </h2>

                <div className="space-y-4">
                    {/* URL Input */}
                    <div>
                        <label className="text-sm font-medium text-gray-300 mb-1 block">Link Video Gốc</label>
                        <div className="relative">
                            <input
                                type="text"
                                value={videoUrl}
                                onChange={(e) => setVideoUrl(e.target.value)}
                                placeholder="https://tiktok.com/..."
                                className="app-input pl-10"
                            />
                            <Upload className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        </div>
                    </div>

                    {/* Topic Input */}
                    <div>
                        <label className="text-sm font-medium text-gray-300 mb-1 block">Chủ đề câu chuyện</label>
                        <div className="relative">
                            <input
                                type="text"
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                placeholder="Vụ án bí ẩn, Chuyến đi kinh hoàng..."
                                className="app-input"
                            />
                        </div>
                    </div>

                    {/* Num Parts Slider */}
                    <div>
                        <div className="flex justify-between mb-2">
                            <label className="text-sm font-medium text-gray-300">Số Tập: {numParts}</label>
                        </div>
                        <input
                            type="range"
                            min="2"
                            max="10"
                            value={numParts}
                            onChange={(e) => setNumParts(Number(e.target.value))}
                            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-pink-500"
                        />
                        <div className="flex justify-between text-xs text-gray-500 mt-1">
                            <span>2 tập</span>
                            <span>10 tập</span>
                        </div>
                    </div>

                    {/* Styles */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-sm font-medium text-gray-300 mb-1 block">Phong cách kể</label>
                            <select
                                value={voiceStyle}
                                onChange={(e) => setVoiceStyle(e.target.value)}
                                className="app-select"
                            >
                                <option value="cynical">The Cynical Observer (Trinh thám)</option>
                                <option value="weary">The Weary Traveler (Kinh dị)</option>
                                <option value="emotional">Emotional (Cảm động)</option>
                                <option value="viral">Viral Fast (Nhanh, cuốn)</option>
                            </select>
                        </div>
                        <div>
                            <label className="text-sm font-medium text-gray-300 mb-1 block">Nhạc nền</label>
                            <select
                                value={bgmStyle}
                                onChange={(e) => setBgmStyle(e.target.value)}
                                className="app-select"
                            >
                                <option value="dramatic">Kịch tính / Hồi hộp</option>
                                <option value="sad">Buồn / Sâu lắng</option>
                                <option value="horror">Kinh dị / Rùng rợn</option>
                                <option value="cheerful">Vui vẻ</option>
                            </select>
                        </div>
                    </div>

                    {/* Submit Button */}
                    <button
                        onClick={handleSubmit}
                        disabled={isProcessing}
                        className={clsx(
                            "w-full py-3 rounded-xl font-bold text-white shadow-lg transition-all",
                            isProcessing
                                ? "bg-gray-600 cursor-not-allowed"
                                : "bg-gradient-to-r from-pink-600 to-purple-600 hover:scale-[1.02] hover:shadow-pink-500/25"
                        )}
                    >
                        {isProcessing ? (
                            <span className="flex items-center justify-center gap-2">
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Đang Xử Lý Series...
                            </span>
                        ) : (
                            <span className="flex items-center justify-center gap-2">
                                <Layers className="w-5 h-5" />
                                Sản Xuất Series Ngay
                            </span>
                        )}
                    </button>
                </div>
            </section>

            {/* Helper Info */}
            <div className="p-4 rounded-xl bg-pink-500/10 border border-pink-500/20">
                <h3 className="text-sm font-bold text-pink-300 mb-1">💡 Cơ chế Story Series</h3>
                <ul className="text-xs text-gray-400 space-y-1 list-disc pl-4">
                    <li>AI sẽ tự động chia video thành <strong>{numParts} phần</strong> bằng nhau.</li>
                    <li>Tự động tạo kịch bản liên hoàn: <strong>Mở đầu - Thân bài - Kết thúc mở (Cliffhanger)</strong>.</li>
                    <li>Tự động thêm câu "Ở phần trước..." vào đầu mỗi tập sau.</li>
                    <li>Tự động chèn nhạc nền phù hợp với không khí câu chuyện.</li>
                </ul>
            </div>
        </div>
    );
}
