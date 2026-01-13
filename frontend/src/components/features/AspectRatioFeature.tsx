'use client';

import { useState, useEffect } from 'react';
import { Maximize2, Loader, Download, Monitor, Smartphone, Square, Image } from 'lucide-react';
import toast from 'react-hot-toast';
import clsx from 'clsx';

interface AspectRatioInfo {
    id: string;
    name: string;
    width: number;
    height: number;
    icon: React.ReactNode;
}

export function AspectRatioFeature() {
    const [videoUrl, setVideoUrl] = useState('');
    const [targetRatio, setTargetRatio] = useState('9:16');
    const [method, setMethod] = useState('pad');
    const [bgColor, setBgColor] = useState('000000');
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<{
        success: boolean;
        output_url?: string;
        original?: { width: number; height: number };
        result?: { width: number; height: number; duration: number };
        error?: string;
    } | null>(null);

    const ratios: AspectRatioInfo[] = [
        { id: '9:16', name: 'TikTok / Reels', width: 1080, height: 1920, icon: <Smartphone className="w-5 h-5" /> },
        { id: '16:9', name: 'YouTube', width: 1920, height: 1080, icon: <Monitor className="w-5 h-5" /> },
        { id: '1:1', name: 'Instagram', width: 1080, height: 1080, icon: <Square className="w-5 h-5" /> },
        { id: '4:5', name: 'Instagram Portrait', width: 1080, height: 1350, icon: <Image className="w-5 h-5" /> },
    ];

    const methods = [
        { id: 'pad', name: 'Thêm viền', description: 'Giữ nguyên nội dung, thêm viền đen' },
        { id: 'crop', name: 'Cắt bỏ', description: 'Cắt để lấp đầy khung (có thể mất nội dung)' },
        { id: 'fit', name: 'Vừa khung', description: 'Thu nhỏ để vừa khung' },
    ];

    const handleConvert = async () => {
        if (!videoUrl.trim()) {
            toast.error('Vui lòng nhập URL video');
            return;
        }

        setIsProcessing(true);
        setResult(null);

        try {
            const response = await fetch(
                `/api/videos/convert-aspect-ratio?` +
                `source_url=${encodeURIComponent(videoUrl)}&` +
                `target_ratio=${targetRatio}&` +
                `method=${method}&` +
                `bg_color=${bgColor}`,
                { method: 'POST' }
            );

            const data = await response.json();

            if (data.success) {
                setResult(data);
                toast.success('Đã chuyển đổi thành công!');
            } else {
                throw new Error(data.error || 'Conversion failed');
            }
        } catch (error: any) {
            toast.error(error.message || 'Lỗi khi chuyển đổi');
            setResult({ success: false, error: error.message });
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Input URL */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">URL Video</label>
                <input
                    type="url"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    placeholder="https://..."
                    className="app-control"
                    disabled={isProcessing}
                />
            </div>

            {/* Aspect Ratio Selection */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Tỉ lệ khung hình</label>
                <div className="grid grid-cols-2 gap-2">
                    {ratios.map((r) => (
                        <button
                            key={r.id}
                            onClick={() => setTargetRatio(r.id)}
                            disabled={isProcessing}
                            className={clsx(
                                'flex items-center gap-3 p-3 rounded-xl transition-all',
                                targetRatio === r.id
                                    ? 'bg-purple-500/20 border-2 border-purple-500'
                                    : 'bg-white/5 border border-white/10 hover:bg-white/10'
                            )}
                        >
                            <div className={clsx(
                                'flex items-center justify-center rounded-lg p-2',
                                targetRatio === r.id ? 'bg-purple-500/30' : 'bg-white/10'
                            )}>
                                {r.icon}
                            </div>
                            <div className="text-left">
                                <div className="font-medium text-sm">{r.id}</div>
                                <div className="text-xs text-gray-400">{r.name}</div>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Method Selection */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Phương pháp</label>
                <div className="space-y-2">
                    {methods.map((m) => (
                        <button
                            key={m.id}
                            onClick={() => setMethod(m.id)}
                            disabled={isProcessing}
                            className={clsx(
                                'w-full flex items-center justify-between p-3 rounded-xl transition-all text-left',
                                method === m.id
                                    ? 'bg-purple-500/20 border-2 border-purple-500'
                                    : 'bg-white/5 border border-white/10 hover:bg-white/10'
                            )}
                        >
                            <div>
                                <div className="font-medium text-sm">{m.name}</div>
                                <div className="text-xs text-gray-400">{m.description}</div>
                            </div>
                            <div className={clsx(
                                'w-4 h-4 rounded-full border-2',
                                method === m.id
                                    ? 'border-purple-500 bg-purple-500'
                                    : 'border-gray-500'
                            )} />
                        </button>
                    ))}
                </div>
            </div>

            {/* Background Color (for pad method) */}
            {method === 'pad' && (
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">Màu nền viền</label>
                    <div className="flex gap-2">
                        {['000000', 'FFFFFF', '1a1a2e', '16213e', '0f3460'].map((color) => (
                            <button
                                key={color}
                                onClick={() => setBgColor(color)}
                                disabled={isProcessing}
                                className={clsx(
                                    'w-10 h-10 rounded-lg border-2 transition-all',
                                    bgColor === color ? 'border-purple-500 scale-110' : 'border-transparent'
                                )}
                                style={{ backgroundColor: `#${color}` }}
                                title={`#${color}`}
                            />
                        ))}
                        <input
                            type="color"
                            value={`#${bgColor}`}
                            onChange={(e) => setBgColor(e.target.value.replace('#', ''))}
                            className="w-10 h-10 rounded-lg cursor-pointer"
                            disabled={isProcessing}
                        />
                    </div>
                </div>
            )}

            {/* Preview */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-sm text-gray-400 mb-3">Xem trước kết quả:</p>
                <div className="flex justify-center">
                    <div
                        className="relative bg-gray-800 rounded-lg overflow-hidden"
                        style={{
                            width: '120px',
                            aspectRatio: targetRatio.replace(':', '/'),
                            backgroundColor: method === 'pad' ? `#${bgColor}` : undefined,
                        }}
                    >
                        <div className="absolute inset-0 flex items-center justify-center">
                            <div
                                className="bg-purple-500/30 border border-purple-500/50 rounded"
                                style={{
                                    width: method === 'pad' ? '60%' : '100%',
                                    height: method === 'pad' ? '60%' : '100%',
                                }}
                            >
                                <div className="flex items-center justify-center h-full text-xs text-purple-300">
                                    Video
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="text-center mt-3 text-xs text-gray-500">
                    {ratios.find(r => r.id === targetRatio)?.width} x {ratios.find(r => r.id === targetRatio)?.height}
                </div>
            </div>

            {/* Convert Button */}
            <button
                onClick={handleConvert}
                disabled={isProcessing || !videoUrl.trim()}
                className="app-btn-primary w-full"
            >
                {isProcessing ? (
                    <>
                        <Loader className="w-5 h-5 animate-spin" />
                        Đang chuyển đổi...
                    </>
                ) : (
                    <>
                        <Maximize2 className="w-5 h-5" />
                        Chuyển Đổi Tỉ Lệ
                    </>
                )}
            </button>

            {/* Results */}
            {result && result.success && (
                <div className="p-4 space-y-4 rounded-xl bg-green-500/10 border border-green-500/30">
                    <div className="flex items-center gap-2 text-green-400">
                        <Maximize2 className="w-5 h-5" />
                        <span className="font-medium">Đã chuyển đổi thành công!</span>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div className="p-3 rounded-lg bg-white/5">
                            <p className="text-gray-400 mb-1">Gốc</p>
                            <p className="text-white">{result.original?.width} x {result.original?.height}</p>
                        </div>
                        <div className="p-3 rounded-lg bg-white/5">
                            <p className="text-gray-400 mb-1">Kết quả</p>
                            <p className="text-white">{result.result?.width} x {result.result?.height}</p>
                        </div>
                    </div>

                    <a
                        href={result.output_url}
                        download
                        className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-green-600 text-white font-medium hover:bg-green-500 transition"
                    >
                        <Download className="w-5 h-5" />
                        Tải Video Đã Chuyển Đổi
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
