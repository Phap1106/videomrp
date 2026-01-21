'use client';

import { useState, useEffect } from 'react';
import {
    Play, Pause, RefreshCw, CheckCircle, XCircle,
    Loader2, Upload, FolderOpen, Clock, Video,
    TrendingUp, AlertTriangle
} from 'lucide-react';

interface BatchVideo {
    video_id: string;
    title: string;
    status: string;
    score: number;
    error?: string;
}

interface BatchStatus {
    batch_id: string;
    status: string;
    progress: number;
    total: number;
    analyzed: number;
    processed: number;
    failed: number;
    recommended: number;
    videos: BatchVideo[];
}

export default function BatchPage() {
    const [batchId, setBatchId] = useState('');
    const [videoIds, setVideoIds] = useState('');
    const [batchStatus, setBatchStatus] = useState<BatchStatus | null>(null);
    const [isPolling, setIsPolling] = useState(false);

    // Poll for batch status
    useEffect(() => {
        if (!batchId || !isPolling) return;

        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/youtube/batch/${batchId}`);
                const data = await response.json();
                setBatchStatus(data);

                if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
                    setIsPolling(false);
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [batchId, isPolling]);

    const handleCreateBatch = async () => {
        const ids = videoIds.split('\n').map(id => id.trim()).filter(Boolean);
        if (ids.length === 0) return;

        try {
            const response = await fetch('http://localhost:8000/api/youtube/batch/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_ids: ids }),
            });

            const data = await response.json();
            if (data.success) {
                setBatchId(data.batch_id);
            }
        } catch (err) {
            console.error('Error:', err);
        }
    };

    const handleStartBatch = async () => {
        if (!batchId) return;

        try {
            const response = await fetch(`http://localhost:8000/api/youtube/batch/${batchId}/start`, {
                method: 'POST',
            });

            const data = await response.json();
            if (data.success) {
                setIsPolling(true);
            }
        } catch (err) {
            console.error('Error:', err);
        }
    };

    const handleCancelBatch = async () => {
        if (!batchId) return;

        try {
            await fetch(`http://localhost:8000/api/youtube/batch/${batchId}/cancel`, {
                method: 'POST',
            });
            setIsPolling(false);
        } catch (err) {
            console.error('Error:', err);
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
            case 'analyzed':
                return <CheckCircle className="w-4 h-4 text-green-400" />;
            case 'failed':
                return <XCircle className="w-4 h-4 text-red-400" />;
            case 'analyzing':
            case 'processing':
                return <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />;
            case 'queued':
                return <Clock className="w-4 h-4 text-gray-400" />;
            default:
                return <Clock className="w-4 h-4 text-gray-400" />;
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 8) return 'text-green-400 bg-green-400/10';
        if (score >= 6) return 'text-cyan-400 bg-cyan-400/10';
        if (score >= 4) return 'text-yellow-400 bg-yellow-400/10';
        return 'text-red-400 bg-red-400/10';
    };

    return (
        <div className="min-h-screen bg-[#0A0A0F] text-white p-6">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">
                        <span className="bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
                            Batch Processor
                        </span>
                    </h1>
                    <p className="text-gray-400">Analyze and process multiple videos at once</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Input Panel */}
                    <div className="lg:col-span-1 space-y-6">
                        {/* Video IDs Input */}
                        <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                <Video className="w-5 h-5 text-cyan-400" />
                                Video IDs
                            </h3>
                            <textarea
                                value={videoIds}
                                onChange={(e) => setVideoIds(e.target.value)}
                                placeholder="Enter video IDs (one per line)&#10;e.g., dQw4w9WgXcQ&#10;     abc123xyz"
                                className="w-full h-40 px-4 py-3 rounded-xl bg-white/5 border border-white/10 
                         focus:border-cyan-500/50 outline-none resize-none text-sm"
                            />
                            <button
                                onClick={handleCreateBatch}
                                disabled={!videoIds.trim()}
                                className="w-full mt-4 px-4 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-green-500
                         hover:from-cyan-400 hover:to-green-400 font-medium
                         disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Create Batch
                            </button>
                        </div>

                        {/* Batch Controls */}
                        {batchId && (
                            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                                <h3 className="text-lg font-semibold mb-4">Batch Controls</h3>
                                <div className="space-y-3">
                                    <div className="text-sm text-gray-400">
                                        Batch ID: <span className="text-white font-mono">{batchId}</span>
                                    </div>

                                    <div className="flex gap-2">
                                        <button
                                            onClick={handleStartBatch}
                                            disabled={isPolling}
                                            className="flex-1 px-4 py-2 rounded-lg bg-green-500/20 text-green-400 
                               hover:bg-green-500/30 flex items-center justify-center gap-2
                               disabled:opacity-50"
                                        >
                                            <Play className="w-4 h-4" />
                                            Start
                                        </button>
                                        <button
                                            onClick={handleCancelBatch}
                                            disabled={!isPolling}
                                            className="flex-1 px-4 py-2 rounded-lg bg-red-500/20 text-red-400 
                               hover:bg-red-500/30 flex items-center justify-center gap-2
                               disabled:opacity-50"
                                        >
                                            <Pause className="w-4 h-4" />
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Status Panel */}
                    <div className="lg:col-span-2">
                        {batchStatus && (
                            <div className="space-y-6">
                                {/* Progress */}
                                <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-lg font-semibold">Progress</h3>
                                        <span className={`px-3 py-1 rounded-full text-sm ${batchStatus.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                                                batchStatus.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                                                    batchStatus.status === 'running' ? 'bg-cyan-500/20 text-cyan-400' :
                                                        'bg-gray-500/20 text-gray-400'
                                            }`}>
                                            {batchStatus.status}
                                        </span>
                                    </div>

                                    <div className="h-3 bg-white/10 rounded-full overflow-hidden mb-4">
                                        <div
                                            className="h-full bg-gradient-to-r from-cyan-500 to-green-500 transition-all duration-500"
                                            style={{ width: `${batchStatus.progress}%` }}
                                        />
                                    </div>

                                    <div className="grid grid-cols-4 gap-4 text-center">
                                        <div>
                                            <div className="text-2xl font-bold">{batchStatus.total}</div>
                                            <div className="text-xs text-gray-400">Total</div>
                                        </div>
                                        <div>
                                            <div className="text-2xl font-bold text-cyan-400">{batchStatus.analyzed}</div>
                                            <div className="text-xs text-gray-400">Analyzed</div>
                                        </div>
                                        <div>
                                            <div className="text-2xl font-bold text-green-400">{batchStatus.recommended}</div>
                                            <div className="text-xs text-gray-400">Recommended</div>
                                        </div>
                                        <div>
                                            <div className="text-2xl font-bold text-red-400">{batchStatus.failed}</div>
                                            <div className="text-xs text-gray-400">Failed</div>
                                        </div>
                                    </div>
                                </div>

                                {/* Video List */}
                                <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
                                    <div className="p-4 border-b border-white/10">
                                        <h3 className="font-semibold">Videos</h3>
                                    </div>
                                    <div className="max-h-[400px] overflow-y-auto">
                                        {batchStatus.videos.map((video) => (
                                            <div
                                                key={video.video_id}
                                                className="flex items-center gap-4 p-4 border-b border-white/5 hover:bg-white/5"
                                            >
                                                <div className="flex-shrink-0">
                                                    {getStatusIcon(video.status)}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-medium truncate">
                                                        {video.title || video.video_id}
                                                    </div>
                                                    {video.error && (
                                                        <div className="text-xs text-red-400 truncate">{video.error}</div>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm text-gray-400">{video.status}</span>
                                                    {video.score > 0 && (
                                                        <span className={`px-2 py-1 rounded text-sm font-medium ${getScoreColor(video.score)}`}>
                                                            {video.score.toFixed(1)}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Actions */}
                                {batchStatus.status === 'completed' && batchStatus.recommended > 0 && (
                                    <div className="bg-gradient-to-r from-cyan-500/10 to-green-500/10 rounded-2xl p-6 border border-cyan-500/20">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <h3 className="font-semibold mb-1">Ready for Export</h3>
                                                <p className="text-sm text-gray-400">
                                                    {batchStatus.recommended} videos recommended for download
                                                </p>
                                            </div>
                                            <button className="px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-green-500
                                       hover:from-cyan-400 hover:to-green-400 font-medium
                                       flex items-center gap-2">
                                                <Upload className="w-5 h-5" />
                                                Upload to Drive
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {!batchStatus && batchId && (
                            <div className="bg-white/5 rounded-2xl p-12 border border-white/10 text-center">
                                <RefreshCw className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                                <p className="text-gray-400">Click "Start" to begin batch analysis</p>
                            </div>
                        )}

                        {!batchId && (
                            <div className="bg-white/5 rounded-2xl p-12 border border-white/10 text-center">
                                <Video className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                                <p className="text-gray-400">Enter video IDs and create a batch to get started</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
