'use client';

import { useState } from 'react';
import { BookOpen, Zap, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import { VoiceSelector } from '../VoiceSelector';
import { VideoPreview } from '../VideoPreview';
import clsx from 'clsx';

export function StoryVideoFeature() {
  const [videoUrl, setVideoUrl] = useState('');
  const [title, setTitle] = useState('');
  const [storyTopic, setStoryTopic] = useState('');
  const [generatedStory, setGeneratedStory] = useState('');
  const [isGeneratingStory, setIsGeneratingStory] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  const [storyOptions, setStoryOptions] = useState({
    duration: 60,
    storyStyle: 'narrative' as 'narrative' | 'dramatic' | 'humorous' | 'educational',
    fontSizeoverlay: 60,
    fontColor: 'FFFFFF',
    textPosition: 'bottom' as 'top' | 'center' | 'bottom',
    selectedVoice: '',
    aiProvider: 'auto' as 'auto' | 'openai' | 'gemini',
  });

  const handleGenerateStory = async () => {
    if (!storyTopic.trim()) {
      toast.error('Vui lòng nhập chủ đề câu chuyện');
      return;
    }

    try {
      setIsGeneratingStory(true);
      const result = await apiClient.generateStory(
        storyTopic,
        storyOptions.duration * 3,
        storyOptions.storyStyle,
        'vi'
      );

      if (result.success) {
        setGeneratedStory(result.story);
        toast.success('Câu chuyện đã được tạo! ');
      }
    } catch (error) {
      toast.error('Lỗi khi tạo câu chuyện');
    } finally {
      setIsGeneratingStory(false);
    }
  };

  const handleProcessStory = async () => {
    if (!videoUrl.trim()) {
      toast.error('Vui lòng nhập URL video');
      return;
    }

    if (!generatedStory.trim()) {
      toast.error('Vui lòng tạo câu chuyện trước');
      return;
    }

    try {
      setIsProcessing(true);

      const result = await apiClient.processStoryVideo({
        source_url: videoUrl,
        title: title || 'Story Video',
        story_topic: storyTopic,
        duration: storyOptions.duration,
        story_style: storyOptions.storyStyle,
        font_size: storyOptions.fontSizeoverlay,
        font_color: storyOptions.fontColor,
        text_position: storyOptions.textPosition,
        tts_voice: storyOptions.selectedVoice,
      });

      if (result.success) {
        setCurrentJobId(result.job_id);
        toast.success('Video câu chuyện đã được thêm vào hàng đợi');
        pollJobStatus(result.job_id);
      }
    } catch (error) {
      toast.error('Lỗi khi xử lý video câu chuyện');
    } finally {
      setIsProcessing(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiClient.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval);
          if (status.status === 'completed') {
            toast.success('Video câu chuyện đã được tạo thành công!');
            setShowPreview(true);
          } else {
            toast.error(status.error_message || 'Lỗi khi tạo video');
          }
        }
      } catch (error) {
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {/* Video Input */}
      <section className="app-card">
        <h2 className="app-section-title">
          <BookOpen className="w-6 h-6 text-purple-400" />
          Tạo Video Câu Chuyện
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">URL Video Gốc</label>
            <input
              type="url"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="app-control"
            />
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Tiêu Đề Video</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Tiêu đề video câu chuyện"
              className="app-control"
            />
          </div>
        </div>
      </section>

      {/* Story Generation */}
      <section className="app-card">
        <h3 className="app-section-title">
          <Zap className="w-5 h-5 text-purple-400" />
          Tạo Câu Chuyện AI
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Chủ Đề Câu Chuyện</label>
            <textarea
              value={storyTopic}
              onChange={(e) => setStoryTopic(e.target.value)}
              placeholder="Mô tả chủ đề câu chuyện..."
              rows={3}
              className="app-control"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Kiểu Câu Chuyện</label>
              <select
                value={storyOptions.storyStyle}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    storyStyle: e.target.value as any,
                  })
                }
                className="app-control"
              >
                <option value="narrative">Tường Thuật</option>
                <option value="dramatic">Kịch Tính</option>
                <option value="humorous">Hài Hước</option>
                <option value="educational">Giáo Dục</option>
              </select>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">
                Thời Lượng (giây): <span className="text-purple-300">{storyOptions.duration}</span>
              </label>
              <input
                type="range"
                min="30"
                max="600"
                value={storyOptions.duration}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    duration: parseInt(e.target.value),
                  })
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">AI Provider</label>
              <select
                value={storyOptions.aiProvider}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    aiProvider: e.target.value as any,
                  })
                }
                className="app-control"
              >
                <option value="auto">Auto</option>
                <option value="openai">OpenAI</option>
                <option value="gemini">Google Gemini</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleGenerateStory}
            disabled={isGeneratingStory || !storyTopic}
            className={clsx(
              "app-btn-primary w-full",
              (isGeneratingStory || !storyTopic) && "opacity-50 cursor-not-allowed shadow-none"
            )}
          >
            {isGeneratingStory && <Loader className="w-5 h-5 animate-spin" />}
            {isGeneratingStory ? "Đang Tạo Câu Chuyện..." : "Tạo Câu Chuyện"}
          </button>

          {generatedStory && (
            <div className="p-4 border rounded-lg border-white/10 bg-white/5">
              <h4 className="mb-2 font-semibold text-white">Câu Chuyện Đã Tạo:</h4>
              <p className="leading-relaxed text-gray-300">{generatedStory}</p>
            </div>
          )}
        </div>
      </section>

      {/* Voice Selection */}
      {generatedStory && (
        <section className="app-card">
          <VoiceSelector
            aiProvider={storyOptions.aiProvider}
            onVoiceSelect={(voice) =>
              setStoryOptions({ ...storyOptions, selectedVoice: voice })
            }
          />
        </section>
      )}

      {/* Text Styling */}
      {generatedStory && (
        <section className="app-card">
          <h3 className="app-section-title">Cài Đặt Chữ</h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">
                Kích Thước: {storyOptions.fontSizeoverlay}px
              </label>
              <input
                type="range"
                min="30"
                max="120"
                value={storyOptions.fontSizeoverlay}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    fontSizeoverlay: parseInt(e.target.value),
                  })
                }
                className="w-full"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Màu Chữ</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={`#${storyOptions.fontColor}`}
                  onChange={(e) =>
                    setStoryOptions({
                      ...storyOptions,
                      fontColor: e.target.value.substring(1).toUpperCase(),
                    })
                  }
                  className="w-16 h-[46px] border border-white/10 rounded-lg cursor-pointer bg-transparent p-1"
                />
                <input
                  type="text"
                  value={storyOptions.fontColor}
                  onChange={(e) =>
                    setStoryOptions({
                      ...storyOptions,
                      fontColor: e.target.value.toUpperCase(),
                    })
                  }
                  className="app-control"
                />
              </div>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Vị Trí</label>
              <select
                value={storyOptions.textPosition}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    textPosition: e.target.value as any,
                  })
                }
                className="app-control"
              >
                <option value="top">Trên Cùng</option>
                <option value="center">Giữa</option>
                <option value="bottom">Dưới Cùng</option>
              </select>
            </div>
          </div>

          {/* Preview */}
          <div
            className="p-6 mt-6 text-2xl font-bold text-center text-white bg-black/50 rounded-xl backdrop-blur-sm border border-white/10"
            style={{
              color: `#${storyOptions.fontColor}`,
              fontSize: `${storyOptions.fontSizeoverlay}px`,
            }}
          >
            Xem trước câu chuyện
          </div>
        </section>
      )}

      {/* Process Button */}
      {generatedStory && (
        <button
          onClick={handleProcessStory}
          disabled={isProcessing || !videoUrl}
          className={clsx(
            "w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl font-semibold transition text-lg",
            isProcessing || !videoUrl
              ? "bg-white/10 text-gray-400 cursor-not-allowed"
              : "bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-500 hover:to-emerald-500 shadow-lg shadow-green-500/30"
          )}
        >
          {isProcessing && <Loader className="w-6 h-6 animate-spin" />}
          {isProcessing ? "Đang Tạo Video..." : "Tạo Video Câu Chuyện"}
        </button>
      )}

      {/* Job Status */}
      {jobStatus && (
        <section className="app-card border-blue-500/30 bg-blue-500/5">
          <h4 className="mb-2 font-semibold text-white">Trạng Thái Công Việc</h4>
          <div className="space-y-2 text-sm text-gray-200">
            <div>
              <strong>Trạng Thái:</strong>{" "}
              <span
                className={clsx("rounded px-2 py-1 text-xs font-medium ml-2", {
                  "bg-yellow-500/20 text-yellow-300": jobStatus.status === "pending",
                  "bg-blue-500/20 text-blue-300": jobStatus.status === "processing",
                  "bg-green-500/20 text-green-300": jobStatus.status === "completed",
                  "bg-red-500/20 text-red-300": jobStatus.status === "failed",
                })}
              >
                {jobStatus.status.toUpperCase()}
              </span>
            </div>
            <div>
              <strong>Bước Hiện Tại:</strong> {jobStatus.current_step}
            </div>
            <div>
              <strong>Tiến Độ:</strong> {jobStatus.progress}%
            </div>
            {jobStatus.error_message && (
              <div className="mt-2 text-red-300">
                <strong>Lỗi:</strong> {jobStatus.error_message}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Video Preview */}
      {showPreview && currentJobId && (
        <section className="app-card">
          <VideoPreview jobId={currentJobId} onClose={() => setShowPreview(false)} />
        </section>
      )}
    </div>
  );
}