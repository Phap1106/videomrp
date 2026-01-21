'use client';

import { useEffect, useRef, useState } from 'react';
import { Play, Pause, Download, X } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import clsx from 'clsx';

interface VideoPreviewProps {
  jobId: string;
  videoUrl?: string;
  onClose?: () => void;
}

export function VideoPreview({ jobId, videoUrl, onClose }: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [currentTime, setCurrentTime] = useState(0);
  const [isDownloading, setIsDownloading] = useState(false);

  // Construct source URL if not provided directly
  const sourceUrl = videoUrl || (jobId ? `/api/videos/download/${jobId}` : '');

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedMetadata = () => {
      setDuration(video.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, []);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
    }
  };

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      const blob = await apiClient.downloadVideo(jobId);

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `video_${jobId}. mp4`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      toast.success('Video đã tải xuống thành công');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Lỗi khi tải video');
    } finally {
      setIsDownloading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs
        .toString()
        .padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold">Xem trước video</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      <div className="relative mb-4 overflow-hidden bg-black rounded-lg aspect-video">
        <video
          ref={videoRef}
          src={sourceUrl}
          className="w-full h-full"
          controls={false}
          playsInline
        />

        {!isPlaying && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <button
              onClick={handlePlayPause}
              className="p-4 transition bg-white rounded-full hover:bg-gray-200"
            >
              <Play className="w-8 h-8 text-black fill-black" />
            </button>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="space-y-4">
        {/* Progress Bar */}
        <div>
          <input
            type="range"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={(e) => {
              const time = parseFloat(e.target.value);
              if (videoRef.current) {
                videoRef.current.currentTime = time;
              }
            }}
            className="w-full"
          />
          <div className="flex justify-between mt-1 text-sm text-gray-600 dark:text-gray-400">
            <span>{formatTime(currentTime)}</span>
            <span>{formatTime(duration)}</span>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handlePlayPause}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded font-medium transition',
              isPlaying
                ? 'bg-red-600 text-white hover: bg-red-700'
                : 'bg-green-600 text-white hover:bg-green-700'
            )}
          >
            {isPlaying ? (
              <>
                <Pause className="w-4 h-4" />
                Dừng
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Phát
              </>
            )}
          </button>

          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="flex items-center gap-2 px-4 py-2 text-white transition bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            {isDownloading ? 'Đang tải...' : 'Tải xuống'}
          </button>
        </div>
      </div>
    </div>
  );
}