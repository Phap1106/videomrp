'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Video,
  Settings,
  AlertCircle,
  Loader,
  Upload,
  BookOpen,
  Play,
  Scissors,
  Layers,
  Sparkles,
  CheckCircle,
  XCircle,
  Maximize2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import { ReupVideoFeature } from '@/components/features/ReupVideoFeature';
import { StoryVideoFeature } from '@/components/features/StoryVideoFeature';
import { SeriesFeature } from '@/components/features/SeriesFeature';
import { HighlightFeature } from '@/components/features/HighlightFeature';
import { SplitScreenFeature } from '@/components/features/SplitScreenFeature';
import { AspectRatioFeature } from '@/components/features/AspectRatioFeature';
import { TTSSettings } from '@/components/TTSSettings';
import { VideoPlayer } from '@/components/VideoPlayer';
import { EOAChatbot } from '@/components/EOAChatbot';
import clsx from 'clsx';

type TabKey = 'reup' | 'story' | 'series' | 'highlight' | 'merge' | 'aspect' | 'tts';

interface HealthStatus {
  api?: boolean;
  database?: boolean;
  redis?: boolean;
  storage?: boolean;
}

interface JobInfo {
  id: string;
  status: string;
  progress: number;
  current_step: string;
  output_url?: string;
  error_message?: string;
}

export default function HomePage() {
  const [selectedTab, setSelectedTab] = useState<TabKey>('reup');
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [hasError, setHasError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Video preview state
  const [currentJob, setCurrentJob] = useState<JobInfo | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const status = await apiClient.getHealth();
      setHealthStatus(status);
      setHasError(false);
    } catch {
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  // Update video URL when job completes
  useEffect(() => {
    if (currentJob?.status === 'completed' && currentJob.output_url) {
      setVideoUrl(currentJob.output_url);
    }
  }, [currentJob]);

  const tabs = [
    { key: 'reup' as TabKey, label: '🎬 Reup', icon: Upload, description: 'Tải và xử lý video từ URL với AI' },
    { key: 'story' as TabKey, label: '📖 Story', icon: BookOpen, description: 'Tạo video câu chuyện AI với âm thanh' },
    { key: 'series' as TabKey, label: '📚 Series', icon: Layers, description: 'Tạo series kể chuyện dài kỳ (3-10 tập)' },
    { key: 'highlight' as TabKey, label: '✂️ Highlight', icon: Scissors, description: 'Trích xuất đoạn hay nhất từ video dài' },
    { key: 'merge' as TabKey, label: '🎞️ Split Screen', icon: Layers, description: 'Ghép 2 video split-screen' },
    { key: 'aspect' as TabKey, label: '📐 Tỉ lệ', icon: Maximize2, description: 'Chuyển đổi tỉ lệ khung hình' },
    { key: 'tts' as TabKey, label: '🎵 TTS', icon: Settings, description: 'Cài đặt giọng nói AI (Edge, ViettelAI, FPT, ElevenLabs...)' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
        <div className="text-center">
          <Loader className="w-12 h-12 mx-auto mb-4 text-purple-500 animate-spin" />
          <p className="text-lg font-semibold text-white">Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-gray-900/80 border-b border-white/10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <Video className="w-10 h-10 text-purple-400" />
                <Sparkles className="absolute w-4 h-4 text-yellow-400 -top-1 -right-1" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Video Factory AI</h1>
                <p className="text-sm text-gray-400">Công cụ xử lý video thông minh</p>
              </div>
            </div>

            {/* Health Status */}
            <div className="flex items-center gap-4">
              {healthStatus && !hasError ? (
                <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-green-500/10 border border-green-500/30">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-sm text-green-300">Hệ thống hoạt động</span>
                </div>
              ) : (
                <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/30">
                  <XCircle className="w-5 h-5 text-red-400" />
                  <span className="text-sm text-red-300">Lỗi kết nối</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - Split Screen */}
      <main className="flex min-h-[calc(100vh-80px)]">
        {/* Left Panel - Settings/Features */}
        <div className="w-1/2 border-r border-white/10 overflow-y-auto">
          <div className="p-6">
            {/* Tabs */}
            <div className="flex flex-wrap gap-2 mb-6">
              {tabs.map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setSelectedTab(tab.key)}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all',
                    selectedTab === tab.key
                      ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30'
                      : 'bg-white/5 text-gray-300 hover:bg-white/10 border border-white/10'
                  )}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Tab Description */}
            <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-purple-500/10 to-pink-500/10 border border-purple-500/20">
              <p className="text-gray-300">
                {tabs.find(t => t.key === selectedTab)?.description}
              </p>
            </div>

            {/* Feature Content */}
            <div className="space-y-6">
              {selectedTab === 'reup' && <ReupVideoFeature />}
              {selectedTab === 'story' && <StoryVideoFeature />}
              {selectedTab === 'series' && <SeriesFeature />}
              {selectedTab === 'highlight' && <HighlightFeature />}
              {selectedTab === 'merge' && <SplitScreenFeature />}
              {selectedTab === 'aspect' && <AspectRatioFeature />}
              {selectedTab === 'tts' && <TTSSettings />}
            </div>
          </div>
        </div>

        {/* Right Panel - Video Preview */}
        <div className="w-1/2 flex flex-col bg-black/20">
          <div className="p-6 flex-1 flex flex-col">
            <h2 className="flex items-center gap-2 mb-4 text-lg font-semibold text-white">
              <Play className="w-5 h-5 text-purple-400" />
              Video Preview
            </h2>

            {/* Video Player Area */}
            <div className="flex-1 rounded-xl overflow-hidden border border-white/10" style={{ minHeight: '400px' }}>
              <VideoPlayer
                src={videoUrl || undefined}
                title={currentJob?.id ? `Job: ${currentJob.id}` : 'Video Preview'}
                showDownload={!!videoUrl}
              />
            </div>

            {/* Job Status */}
            {currentJob && currentJob.status !== 'completed' && (
              <div className="mt-4 p-4 rounded-xl bg-white/5 border border-white/10">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium text-gray-300">Trạng thái xử lý</span>
                  <span className={clsx(
                    'px-3 py-1 rounded-full text-xs font-medium',
                    {
                      'bg-yellow-500/20 text-yellow-300': currentJob.status === 'pending',
                      'bg-blue-500/20 text-blue-300': currentJob.status === 'processing' || currentJob.status === 'downloading',
                      'bg-green-500/20 text-green-300': currentJob.status === 'completed',
                      'bg-red-500/20 text-red-300': currentJob.status === 'failed',
                    }
                  )}>
                    {currentJob.status}
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                    style={{ width: `${currentJob.progress}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-400">{currentJob.current_step}</span>
                  <span className="text-purple-400">{currentJob.progress}%</span>
                </div>

                {currentJob.error_message && (
                  <div className="mt-3 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                    <p className="text-sm text-red-300">{currentJob.error_message}</p>
                  </div>
                )}
              </div>
            )}

            {/* Quick Tips */}
            {!currentJob && !videoUrl && (
              <div className="mt-4 p-4 rounded-xl bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border border-blue-500/20">
                <h3 className="text-sm font-medium text-blue-300 mb-2">💡 Mẹo sử dụng</h3>
                <ul className="text-xs text-gray-400 space-y-1">
                  <li>• Nhập URL video từ YouTube, TikTok, Instagram...</li>
                  <li>• Chọn các tùy chọn xử lý bên trái</li>
                  <li>• Video đã xử lý sẽ hiển thị tại đây</li>
                  <li>• Sử dụng EOA Chat (góc phải dưới) để tạo nội dung AI</li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* EOA Chatbot - VIP Feature */}
      <EOAChatbot />
    </div>
  );
}

