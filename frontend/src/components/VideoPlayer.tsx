'use client';

import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Volume2, VolumeX, Maximize2, Download, X } from 'lucide-react';
import clsx from 'clsx';

interface VideoPlayerProps {
    src?: string;
    poster?: string;
    onClose?: () => void;
    showDownload?: boolean;
    title?: string;
}

export function VideoPlayer({
    src,
    poster,
    onClose,
    showDownload = true,
    title = 'Video Preview'
}: VideoPlayerProps) {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return;

        const handleTimeUpdate = () => setCurrentTime(video.currentTime);
        const handleLoadedMetadata = () => setDuration(video.duration);
        const handleEnded = () => setIsPlaying(false);

        video.addEventListener('timeupdate', handleTimeUpdate);
        video.addEventListener('loadedmetadata', handleLoadedMetadata);
        video.addEventListener('ended', handleEnded);

        return () => {
            video.removeEventListener('timeupdate', handleTimeUpdate);
            video.removeEventListener('loadedmetadata', handleLoadedMetadata);
            video.removeEventListener('ended', handleEnded);
        };
    }, [src]);

    const togglePlay = () => {
        const video = videoRef.current;
        if (!video) return;

        if (isPlaying) {
            video.pause();
        } else {
            video.play();
        }
        setIsPlaying(!isPlaying);
    };

    const toggleMute = () => {
        const video = videoRef.current;
        if (!video) return;
        video.muted = !isMuted;
        setIsMuted(!isMuted);
    };

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        const video = videoRef.current;
        if (!video) return;
        const time = parseFloat(e.target.value);
        video.currentTime = time;
        setCurrentTime(time);
    };

    const toggleFullscreen = () => {
        const container = videoRef.current?.parentElement;
        if (!container) return;

        if (!isFullscreen) {
            container.requestFullscreen?.();
        } else {
            document.exitFullscreen?.();
        }
        setIsFullscreen(!isFullscreen);
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const handleDownload = () => {
        if (!src) return;
        const a = document.createElement('a');
        a.href = src;
        a.download = 'video.mp4';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    return (
        <div className="relative flex flex-col w-full h-full bg-black rounded-xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-900/80 backdrop-blur-sm">
                <h3 className="font-semibold text-white truncate">{title}</h3>
                <div className="flex items-center gap-2">
                    {showDownload && src && (
                        <button
                            onClick={handleDownload}
                            className="p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition"
                            title="Tải xuống"
                        >
                            <Download className="w-5 h-5" />
                        </button>
                    )}
                    {onClose && (
                        <button
                            onClick={onClose}
                            className="p-2 text-white/70 hover:text-white hover:bg-white/10 rounded-lg transition"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    )}
                </div>
            </div>

            {/* Video Container */}
            <div className="relative flex-1 flex items-center justify-center bg-black">
                {src ? (
                    <>
                        <video
                            ref={videoRef}
                            src={src}
                            poster={poster}
                            className="max-w-full max-h-full object-contain"
                            onClick={togglePlay}
                        />

                        {/* Play/Pause overlay */}
                        {!isPlaying && (
                            <button
                                onClick={togglePlay}
                                className="absolute inset-0 flex items-center justify-center bg-black/30 hover:bg-black/40 transition"
                            >
                                <div className="w-20 h-20 flex items-center justify-center bg-white/20 backdrop-blur-sm rounded-full">
                                    <Play className="w-10 h-10 text-white ml-1" />
                                </div>
                            </button>
                        )}
                    </>
                ) : (
                    <div className="flex flex-col items-center justify-center text-gray-500">
                        <Play className="w-16 h-16 mb-4 opacity-30" />
                        <p className="text-lg">Chưa có video</p>
                        <p className="text-sm text-gray-600 mt-1">Video sẽ hiển thị sau khi xử lý xong</p>
                    </div>
                )}
            </div>

            {/* Controls */}
            {src && (
                <div className="px-4 py-3 bg-gray-900/80 backdrop-blur-sm">
                    {/* Progress bar */}
                    <div className="flex items-center gap-3 mb-3">
                        <span className="text-xs text-gray-400 w-12">{formatTime(currentTime)}</span>
                        <input
                            type="range"
                            min={0}
                            max={duration || 0}
                            value={currentTime}
                            onChange={handleSeek}
                            className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-purple-500 [&::-webkit-slider-thumb]:rounded-full"
                        />
                        <span className="text-xs text-gray-400 w-12 text-right">{formatTime(duration)}</span>
                    </div>

                    {/* Control buttons */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <button
                                onClick={togglePlay}
                                className="p-2 text-white hover:bg-white/10 rounded-lg transition"
                            >
                                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                            </button>
                            <button
                                onClick={toggleMute}
                                className="p-2 text-white hover:bg-white/10 rounded-lg transition"
                            >
                                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                            </button>
                        </div>
                        <button
                            onClick={toggleFullscreen}
                            className="p-2 text-white hover:bg-white/10 rounded-lg transition"
                        >
                            <Maximize2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
