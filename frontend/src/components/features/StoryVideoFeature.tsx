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
    if (!storyTopic. trim()) {
      toast.error('Vui lòng nhập chủ đề câu chuyện');
      return;
    }

    try {
      setIsGeneratingStory(true);
      const result = await apiClient.generateStory(
        storyTopic,
        storyOptions. duration * 3,
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

      const result = await apiClient. processStoryVideo({
        source_url: videoUrl,
        title:  title || 'Story Video',
        story_topic: storyTopic,
        duration: storyOptions.duration,
        story_style: storyOptions.storyStyle,
        font_size:  storyOptions.fontSizeoverlay,
        font_color:  storyOptions.fontColor,
        text_position: storyOptions.textPosition,
        tts_voice: storyOptions. selectedVoice,
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
      <div className="p-6 bg-white border border-gray-200 border-gray-700 rounded-lg dark:bg-gray-900 dark:">
        <h2 className="flex items-center gap-2 mb-6 text-2xl font-bold">
          <BookOpen className="w-6 h-6" />
          Tạo Video Câu Chuyện
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium">URL Video Gốc</label>
            <input
              type="url"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-4 py-3 border rounded-lg dark:bg-gray-800 dark:border-gray-700 focus:ring-2 focus: ring-purple-500"
            />
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium">Tiêu Đề Video</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Tiêu đề video câu chuyện"
              className="w-full px-4 py-3 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
            />
          </div>
        </div>
      </div>

      {/* Story Generation */}
      <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
        <h3 className="flex items-center gap-2 mb-6 text-xl font-semibold">
          <Zap className="w-5 h-5" />
          Tạo Câu Chuyện AI
        </h3>

        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium">Chủ Đề Câu Chuyện</label>
            <textarea
              value={storyTopic}
              onChange={(e) => setStoryTopic(e. target.value)}
              placeholder="Mô tả chủ đề câu chuyện mà bạn muốn tạo (ví dụ: một người phiêu lưu tìm kiếm kho báu)..."
              rows={3}
              className="w-full px-4 py-3 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block mb-2 text-sm font-medium">Kiểu Câu Chuyện</label>
              <select
                value={storyOptions. storyStyle}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    storyStyle: e.target.value as any,
                  })
                }
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                <option value="narrative">Tường Thuật</option>
                <option value="dramatic">Kịch Tính</option>
                <option value="humorous">Hài Hước</option>
                <option value="educational">Giáo Dục</option>
              </select>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium">Thời Lượng (giây): {storyOptions.duration}</label>
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
              <label className="block mb-2 text-sm font-medium">AI Provider</label>
              <select
                value={storyOptions.aiProvider}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    aiProvider: e.target.value as any,
                  })
                }
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
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
              'w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition',
              isGeneratingStory || !storyTopic
                ?  'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover: from-purple-700 hover: to-blue-700'
            )}
          >
            {isGeneratingStory && <Loader className="w-5 h-5 animate-spin" />}
            {isGeneratingStory ? 'Đang Tạo Câu Chuyện...' : 'Tạo Câu Chuyện'}
          </button>

          {generatedStory && (
            <div className="p-4 border border-gray-200 border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 dark:">
              <h4 className="mb-2 font-semibold">Câu Chuyện Đã Tạo:</h4>
              <p className="leading-relaxed text-gray-700 dark:text-gray-300">{generatedStory}</p>
            </div>
          )}
        </div>
      </div>

      {/* Voice Selection */}
      {generatedStory && (
        <div className="p-6 bg-white bg-gray-900 border border-gray-200 rounded-lg dark: dark:border-gray-700">
          <VoiceSelector
            aiProvider={storyOptions.aiProvider}
            onVoiceSelect={(voice) =>
              setStoryOptions({ ...storyOptions, selectedVoice: voice })
            }
          />
        </div>
      )}

      {/* Text Styling */}
      {generatedStory && (
        <div className="p-6 bg-white bg-gray-900 border border-gray-200 rounded-lg dark: dark:border-gray-700">
          <h3 className="mb-4 text-lg font-semibold">Cài Đặt Chữ</h3>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="block mb-2 text-sm font-medium">
                Kích Thước:  {storyOptions.fontSizeoverlay}px
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
              <label className="block mb-2 text-sm font-medium">Màu Chữ</label>
              <div className="flex gap-2">
                <input
                  type="color"
                  value={`#${storyOptions.fontColor}`}
                  onChange={(e) =>
                    setStoryOptions({
                      ...storyOptions,
                      fontColor:  e.target.value. substring(1).toUpperCase(),
                    })
                  }
                  className="w-16 h-10 border rounded cursor-pointer"
                />
                <input
                  type="text"
                  value={storyOptions.fontColor}
                  onChange={(e) =>
                    setStoryOptions({
                      ...storyOptions,
                      fontColor: e.target.value. toUpperCase(),
                    })
                  }
                  className="flex-1 px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700"
                />
              </div>
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium">Vị Trí</label>
              <select
                value={storyOptions.textPosition}
                onChange={(e) =>
                  setStoryOptions({
                    ...storyOptions,
                    textPosition: e. target.value as any,
                  })
                }
                className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
              >
                <option value="top">Trên Cùng</option>
                <option value="center">Giữa</option>
                <option value="bottom">Dưới Cùng</option>
              </select>
            </div>
          </div>

          {/* Preview */}
          <div
            className="p-6 mt-6 text-2xl font-bold text-center text-white bg-black rounded-lg"
            style={{
              color: `#${storyOptions.fontColor}`,
              fontSize: `${storyOptions.fontSizeoverlay}px`,
            }}
          >
            Xem trước câu chuyện
          </div>
        </div>
      )}

      {/* Process Button */}
      {generatedStory && (
        <button
          onClick={handleProcessStory}
          disabled={isProcessing || !videoUrl}
          className={clsx(
            'w-full flex items-center justify-center gap-2 px-6 py-4 rounded-lg font-semibold transition text-lg',
            isProcessing || ! videoUrl
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-gradient-to-r from-green-600 to-emerald-600 text-white hover:from-green-700 hover:to-emerald-700'
          )}
        >
          {isProcessing && <Loader className="w-6 h-6 animate-spin" />}
          {isProcessing ? 'Đang Tạo Video...' : 'Tạo Video Câu Chuyện'}
        </button>
      )}

      {/* Job Status */}
      {jobStatus && (
        <div className="p-4 border border-blue-200 border-blue-700 rounded-lg bg-blue-50 dark:bg-blue-900/20 dark:">
          <h4 className="mb-2 font-semibold">Trạng Thái Công Việc</h4>
          <div className="space-y-2 text-sm">
            <div>
              <strong>Trạng Thái:</strong>{' '}
              <span
                className={clsx(
                  'px-2 py-1 rounded text-xs font-medium ml-2',
                  {
                    'bg-yellow-200 text-yellow-800': jobStatus. status === 'pending',
                    'bg-blue-200 text-blue-800': jobStatus.status === 'processing',
                    'bg-green-200 text-green-800': jobStatus.status === 'completed',
                    'bg-red-200 text-red-800': jobStatus.status === 'failed',
                  }
                )}
              >
                {jobStatus.status. toUpperCase()}
              </span>
            </div>
            <div>
              <strong>Bước Hiện Tại:</strong> {jobStatus.current_step}
            </div>
            <div>
              <strong>Tiến Độ:</strong> {jobStatus. progress}%
            </div>
            {jobStatus.error_message && (
              <div className="mt-2 text-red-600">
                <strong>Lỗi:</strong> {jobStatus.error_message}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Video Preview */}
      {showPreview && currentJobId && (
        <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
          <VideoPreview
            jobId={currentJobId}
            onClose={() => setShowPreview(false)}
          />
        </div>
      )}
    </div>
  );
}