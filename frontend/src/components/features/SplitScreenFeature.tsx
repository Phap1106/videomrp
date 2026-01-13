'use client';

import { useState } from 'react';
import { Layers, Loader, Download, ArrowLeftRight, ArrowUpDown } from 'lucide-react';
import toast from 'react-hot-toast';
import clsx from 'clsx';

export function SplitScreenFeature() {
    const [video1Url, setVideo1Url] = useState('');
    const [video2Url, setVideo2Url] = useState('');
    const [layout, setLayout] = useState<'horizontal' | 'vertical'>('horizontal');
    const [ratio, setRatio] = useState('1:1');
    const [outputRatio, setOutputRatio] = useState('9:16');
    const [audioSource, setAudioSource] = useState('both');
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<{
        success: boolean;
        output_url?: string;
        duration?: number;
        error?: string;
    } | null>(null);

    const ratioOptions = [
        { id: '1:1', name: '50% - 50%' },
        { id: '2:1', name: '66% - 33%' },
        { id: '1:2', name: '33% - 66%' },
    ];

    const outputRatioOptions = [
        { id: '9:16', name: '9:16 (TikTok/Reels)' },
        { id: '16:9', name: '16:9 (YouTube)' },
        { id: '1:1', name: '1:1 (Instagram)' },
    ];

    const audioOptions = [
        { id: 'both', name: 'Cả hai video' },
        { id: 'video1', name: 'Chỉ Video 1' },
        { id: 'video2', name: 'Chỉ Video 2' },
        { id: 'none', name: 'Không âm thanh' },
    ];

    const handleMerge = async () => {
        if (!video1Url.trim() || !video2Url.trim()) {
            toast.error('Vui lòng nhập URL cho cả hai video');
            return;
        }

        setIsProcessing(true);
        setResult(null);

        try {
            const response = await fetch(
                `/api/videos/merge-split-screen?` +
                `video1_url=${encodeURIComponent(video1Url)}&` +
                `video2_url=${encodeURIComponent(video2Url)}&` +
                `layout=${layout}&` +
                `ratio=${ratio}&` +
                `output_ratio=${outputRatio}&` +
                `audio_source=${audioSource}`,
                { method: 'POST' }
            );

            const data = await response.json();

            if (data.success) {
                setResult(data);
                toast.success('Đã ghép video thành công!');
            } else {
                throw new Error(data.error || 'Merge failed');
            }
        } catch (error: any) {
            toast.error(error.message || 'Lỗi khi ghép video');
            setResult({ success: false, error: error.message });
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="space-y-6">
            {/* Video URLs */}
            <div className="grid grid-cols-1 gap-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        Video 1 {layout === 'horizontal' ? '(Trái)' : '(Trên)'}
                    </label>
                    <input
                        type="url"
                        value={video1Url}
                        onChange={(e) => setVideo1Url(e.target.value)}
                        placeholder="https://..."
                        className="app-control"
                        disabled={isProcessing}
                    />
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-300">
                        Video 2 {layout === 'horizontal' ? '(Phải)' : '(Dưới)'}
                    </label>
                    <input
                        type="url"
                        value={video2Url}
                        onChange={(e) => setVideo2Url(e.target.value)}
                        placeholder="https://..."
                        className="app-control"
                        disabled={isProcessing}
                    />
                </div>
            </div>

            {/* Layout Selection */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Bố cục</label>
                <div className="grid grid-cols-2 gap-2">
                    <button
                        onClick={() => setLayout('horizontal')}
                        disabled={isProcessing}
                        className={clsx(
                            'flex items-center justify-center gap-2 p-4 rounded-xl transition-all',
                            layout === 'horizontal'
                                ? 'bg-purple-500/20 border-2 border-purple-500'
                                : 'bg-white/5 border border-white/10 hover:bg-white/10'
                        )}
                    >
                        <ArrowLeftRight className="w-5 h-5" />
                        <span>Ngang (Trái-Phải)</span>
                    </button>
                    <button
                        onClick={() => setLayout('vertical')}
                        disabled={isProcessing}
                        className={clsx(
                            'flex items-center justify-center gap-2 p-4 rounded-xl transition-all',
                            layout === 'vertical'
                                ? 'bg-purple-500/20 border-2 border-purple-500'
                                : 'bg-white/5 border border-white/10 hover:bg-white/10'
                        )}
                    >
                        <ArrowUpDown className="w-5 h-5" />
                        <span>Dọc (Trên-Dưới)</span>
                    </button>
                </div>
            </div>

            {/* Split Ratio */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Tỉ lệ chia</label>
                <div className="flex gap-2">
                    {ratioOptions.map((opt) => (
                        <button
                            key={opt.id}
                            onClick={() => setRatio(opt.id)}
                            disabled={isProcessing}
                            className={clsx(
                                'flex-1 px-4 py-2 rounded-lg transition-all text-sm',
                                ratio === opt.id
                                    ? 'bg-purple-500 text-white'
                                    : 'bg-white/5 text-gray-300 hover:bg-white/10'
                            )}
                        >
                            {opt.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* Output Aspect Ratio */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Tỉ lệ output</label>
                <select
                    value={outputRatio}
                    onChange={(e) => setOutputRatio(e.target.value)}
                    className="app-control"
                    disabled={isProcessing}
                >
                    {outputRatioOptions.map((opt) => (
                        <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                </select>
            </div>

            {/* Audio Source */}
            <div className="space-y-2">
                <label className="text-sm font-medium text-gray-300">Nguồn âm thanh</label>
                <select
                    value={audioSource}
                    onChange={(e) => setAudioSource(e.target.value)}
                    className="app-control"
                    disabled={isProcessing}
                >
                    {audioOptions.map((opt) => (
                        <option key={opt.id} value={opt.id}>{opt.name}</option>
                    ))}
                </select>
            </div>

            {/* Preview Layout */}
            <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                <p className="text-sm text-gray-400 mb-3">Xem trước bố cục:</p>
                <div
                    className={clsx(
                        'flex gap-1 mx-auto',
                        layout === 'horizontal' ? 'flex-row' : 'flex-col',
                        outputRatio === '9:16' ? 'w-24' : outputRatio === '1:1' ? 'w-32' : 'w-48'
                    )}
                    style={{
                        aspectRatio: outputRatio.replace(':', '/'),
                    }}
                >
                    <div
                        className="bg-purple-500/30 rounded flex items-center justify-center text-xs text-purple-300"
                        style={{
                            flex: layout === 'horizontal'
                                ? `${ratio.split(':')[0]}`
                                : ratio.split(':')[0],
                        }}
                    >
                        V1
                    </div>
                    <div
                        className="bg-pink-500/30 rounded flex items-center justify-center text-xs text-pink-300"
                        style={{
                            flex: layout === 'horizontal'
                                ? `${ratio.split(':')[1]}`
                                : ratio.split(':')[1],
                        }}
                    >
                        V2
                    </div>
                </div>
            </div>

            {/* Merge Button */}
            <button
                onClick={handleMerge}
                disabled={isProcessing || !video1Url.trim() || !video2Url.trim()}
                className="app-btn-primary w-full"
            >
                {isProcessing ? (
                    <>
                        <Loader className="w-5 h-5 animate-spin" />
                        Đang ghép video...
                    </>
                ) : (
                    <>
                        <Layers className="w-5 h-5" />
                        Ghép Video Split-Screen
                    </>
                )}
            </button>

            {/* Results */}
            {result && result.success && (
                <div className="p-4 space-y-4 rounded-xl bg-green-500/10 border border-green-500/30">
                    <div className="flex items-center gap-2 text-green-400">
                        <Layers className="w-5 h-5" />
                        <span className="font-medium">Đã ghép video thành công!</span>
                    </div>

                    <a
                        href={result.output_url}
                        download
                        className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-green-600 text-white font-medium hover:bg-green-500 transition"
                    >
                        <Download className="w-5 h-5" />
                        Tải Video Đã Ghép
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
