'use client';

import { useState } from 'react';
import { Scissors, Loader, Download, Sparkles, Play, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import clsx from 'clsx';

interface HighlightSegment {
    start: number;
    end: number;
    score: number;
    reason: string;
}

export function HighlightFeature() {
    const [videoUrl, setVideoUrl] = useState('');
    const [targetDuration, setTargetDuration] = useState(60);
    const [numHighlights, setNumHighlights] = useState(5);
    const [style, setStyle] = useState('engaging');
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<{
        success: boolean;
        output_url?: string;
        highlights?: HighlightSegment[];
        duration?: number;
        error?: string;
    } | null>(null);

    const styles = [
        { id: 'engaging', name: '🎯 Hấp dẫn', description: 'Đoạn lôi cuốn người xem' },
        { id: 'dramatic', name: '🎭 Kịch tính', description: 'Đoạn có cảm xúc mạnh' },
        { id: 'funny', name: '😂 Hài hước', description: 'Đoạn vui nhộn' },
        { id: 'informative', name: '📚 Thông tin', description: 'Đoạn có giá trị' },
    ];

    const handleExtract = async () => {
        if (!videoUrl.trim()) {
            toast.error('Vui lòng nhập URL video');
            return;
        }

        setIsProcessing(true);
        setResult(null);

        try {
            const response = await fetch(
                `/api/videos/extract-highlights?` +
                `source_url=${encodeURIComponent(videoUrl)}&` +
                `target_duration=${targetDuration}&` +
                `num_highlights=${numHighlights}&` +
                `style=${style}`,
                { method: 'POST' }
            );

            const data = await response.json();

            if (data.success) {
                setResult(data);
                toast.success('Đã trích xuất highlight thành công!');
            } else {
                throw new Error(data.error || 'Extraction failed');
            }
        } catch (error: any) {
            toast.error(error.message || 'Lỗi khi trích xuất');
            setResult({ success: false, error: error.message });
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Input URL */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">URL Video Dài</label>
                <input
                    type="url"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    placeholder="https://youtube.com/watch?v=..."
                    className="app-control"
                    disabled={isProcessing}
                />
                <p className="text-xs text-gray-500">Video từ YouTube, TikTok, Instagram...</p>
            </div>

            {/* Duration Settings */}
            <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        Thời lượng output: {targetDuration}s
                    </label>
                    <input
                        type="range"
                        min={15}
                        max={180}
                        value={targetDuration}
                        onChange={(e) => setTargetDuration(parseInt(e.target.value))}
                        className="w-full"
                        disabled={isProcessing}
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                        <span>15s</span>
                        <span>180s</span>
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        Số đoạn highlight: {numHighlights}
                    </label>
                    <input
                        type="range"
                        min={1}
                        max={10}
                        value={numHighlights}
                        onChange={(e) => setNumHighlights(parseInt(e.target.value))}
                        className="w-full"
                        disabled={isProcessing}
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                        <span>1</span>
                        <span>10</span>
                    </div>
                </div>
            </div>

            {/* Style Selection */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Phong cách</label>
                <div className="grid grid-cols-2 gap-2">
                    {styles.map((s) => (
                        <button
                            key={s.id}
                            onClick={() => setStyle(s.id)}
                            disabled={isProcessing}
                            className={clsx(
                                'p-3 rounded-xl text-left transition-all',
                                style === s.id
                                    ? 'bg-purple-500/20 border-2 border-purple-500'
                                    : 'bg-white/5 border border-white/10 hover:bg-white/10'
                            )}
                        >
                            <div className="font-medium">{s.name}</div>
                            <div className="text-xs text-gray-400">{s.description}</div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Extract Button */}
            <button
                onClick={handleExtract}
                disabled={isProcessing || !videoUrl.trim()}
                className="app-btn-primary w-full"
            >
                {isProcessing ? (
                    <>
                        <Loader className="w-5 h-5 animate-spin" />
                        Đang xử lý... (có thể mất vài phút)
                    </>
                ) : (
                    <>
                        <Scissors className="w-5 h-5" />
                        Trích Xuất Highlight
                    </>
                )}
            </button>

            {/* Results */}
            {result && result.success && (
                <div className="p-4 space-y-4 rounded-xl bg-green-500/10 border border-green-500/30">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-green-400">
                            <Sparkles className="w-5 h-5" />
                            <span className="font-medium">Đã trích xuất thành công!</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-400">
                            <Clock className="w-4 h-4" />
                            {result.duration?.toFixed(1)}s
                        </div>
                    </div>

                    {/* Highlights list */}
                    {result.highlights && result.highlights.length > 0 && (
                        <div className="space-y-2">
                            <p className="text-sm text-gray-400">Các đoạn đã chọn:</p>
                            <div className="max-h-40 overflow-y-auto space-y-1">
                                {result.highlights.map((h, i) => (
                                    <div
                                        key={i}
                                        className="flex items-center justify-between px-3 py-2 text-sm rounded-lg bg-white/5"
                                    >
                                        <span className="text-gray-300">
                                            {h.start.toFixed(1)}s - {h.end.toFixed(1)}s
                                        </span>
                                        <span className="text-xs text-gray-500">{h.reason}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Download button */}
                    <a
                        href={result.output_url}
                        download
                        className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-green-600 text-white font-medium hover:bg-green-500 transition"
                    >
                        <Download className="w-5 h-5" />
                        Tải Video Highlight
                    </a>
                </div>
            )}

            {/* Error */}
            {result && !result.success && (
                <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                    <p className="text-red-400">{result.error}</p>
                </div>
            )}
        </div>
    );
}
