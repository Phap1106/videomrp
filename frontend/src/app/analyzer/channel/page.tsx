'use client';

import { useState, useEffect } from 'react';
import {
    Users, TrendingUp, Video, Search, Filter, Download,
    Loader2, CheckCircle, AlertTriangle, ArrowUpRight,
    BarChart3, Clock, Eye, ThumbsUp
} from 'lucide-react';

interface ChannelInfo {
    id: string;
    title: string;
    subscribers: number;
    videos: number;
    total_views: number;
    thumbnail: string;
}

interface VideoItem {
    id: string;
    title: string;
    views: number;
    likes: number;
    duration: number;
    published: string;
    thumbnail: string;
}

interface ChannelResult {
    status: string;
    results?: {
        channel_info: ChannelInfo;
        videos: VideoItem[];
        metrics: {
            avg_views: number;
            viral_ratio: number;
            upload_frequency: number;
            growth_trend: string;
        };
        score: number;
        status: string;
        reasoning: string;
    };
    error?: string;
}

export default function ChannelPage() {
    const [channelUrl, setChannelUrl] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [result, setResult] = useState<ChannelResult | null>(null);
    const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());

    // Filters
    const [minViews, setMinViews] = useState(0);
    const [sortBy, setSortBy] = useState('views');

    // Poll for results
    useEffect(() => {
        if (!jobId || result?.status === 'completed' || result?.status === 'failed') return;

        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/youtube/channel/${jobId}`);
                const data = await response.json();
                setResult(data);

                if (data.status === 'completed' || data.status === 'failed') {
                    setIsAnalyzing(false);
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [jobId, result?.status]);

    const handleAnalyze = async () => {
        if (!channelUrl.trim()) return;

        setIsAnalyzing(true);
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/api/youtube/channel/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    channel_url: channelUrl,
                    max_videos: 50
                }),
            });

            const data = await response.json();
            if (data.success) {
                setJobId(data.job_id);
            }
        } catch (err) {
            console.error('Error:', err);
            setIsAnalyzing(false);
        }
    };

    const toggleVideoSelection = (videoId: string) => {
        const newSelection = new Set(selectedVideos);
        if (newSelection.has(videoId)) {
            newSelection.delete(videoId);
        } else {
            newSelection.add(videoId);
        }
        setSelectedVideos(newSelection);
    };

    const selectTopVideos = (count: number) => {
        const videos = result?.results?.videos || [];
        const sorted = [...videos].sort((a, b) => b.views - a.views);
        const topIds = sorted.slice(0, count).map(v => v.id);
        setSelectedVideos(new Set(topIds));
    };

    const handleBatchProcess = async () => {
        if (selectedVideos.size === 0) return;

        try {
            const response = await fetch('http://localhost:8000/api/youtube/batch/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    video_ids: Array.from(selectedVideos)
                }),
            });

            const data = await response.json();
            if (data.success) {
                alert(`Batch created: ${data.batch_id}. Redirecting to batch page...`);
                // Would redirect to batch page
            }
        } catch (err) {
            console.error('Error:', err);
        }
    };

    const formatNumber = (num: number) => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    const formatDuration = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    const getScoreColor = (score: number) => {
        if (score >= 8) return 'text-green-400';
        if (score >= 6) return 'text-cyan-400';
        if (score >= 4) return 'text-yellow-400';
        return 'text-red-400';
    };

    const filteredVideos = (result?.results?.videos || [])
        .filter(v => v.views >= minViews)
        .sort((a, b) => {
            if (sortBy === 'views') return b.views - a.views;
            if (sortBy === 'likes') return b.likes - a.likes;
            if (sortBy === 'date') return new Date(b.published).getTime() - new Date(a.published).getTime();
            return 0;
        });

    return (
        <div className="min-h-screen bg-[#0A0A0F] text-white p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold mb-2">
                        <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                            Channel Analyzer
                        </span>
                    </h1>
                    <p className="text-gray-400">Analyze YouTube channels and select videos for batch processing</p>
                </div>

                {/* Input Section */}
                <div className="bg-white/5 rounded-2xl p-6 border border-white/10 mb-8">
                    <div className="flex gap-4">
                        <input
                            type="text"
                            value={channelUrl}
                            onChange={(e) => setChannelUrl(e.target.value)}
                            placeholder="Enter channel URL or @handle..."
                            className="flex-1 px-4 py-3 rounded-xl bg-white/5 border border-white/10 
                       focus:border-purple-500/50 outline-none"
                            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                        />
                        <button
                            onClick={handleAnalyze}
                            disabled={isAnalyzing}
                            className="px-6 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500
                       hover:from-purple-400 hover:to-pink-400 font-medium
                       disabled:opacity-50 flex items-center gap-2"
                        >
                            {isAnalyzing ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <Users className="w-5 h-5" />
                                    Analyze Channel
                                </>
                            )}
                        </button>
                    </div>
                </div>

                {/* Results */}
                {result?.status === 'completed' && result.results && (
                    <div className="space-y-6">
                        {/* Channel Summary */}
                        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                            {/* Channel Info Card */}
                            <div className="lg:col-span-1 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-2xl p-6 border border-purple-500/20">
                                <div className="flex flex-col items-center text-center">
                                    {result.results.channel_info.thumbnail && (
                                        <img
                                            src={result.results.channel_info.thumbnail}
                                            alt={result.results.channel_info.title}
                                            className="w-24 h-24 rounded-full mb-4"
                                        />
                                    )}
                                    <h2 className="text-xl font-bold mb-2">{result.results.channel_info.title}</h2>
                                    <div className={`text-4xl font-bold ${getScoreColor(result.results.score)}`}>
                                        {result.results.score.toFixed(1)}
                                    </div>
                                    <div className="text-sm text-gray-400 mt-1">Channel Score</div>
                                    <div className={`mt-2 px-3 py-1 rounded-full text-sm ${result.results.status === 'growing' ? 'bg-green-500/20 text-green-400' :
                                            result.results.status === 'declining' ? 'bg-red-500/20 text-red-400' :
                                                'bg-gray-500/20 text-gray-400'
                                        }`}>
                                        {result.results.status}
                                    </div>
                                </div>
                            </div>

                            {/* Metrics Grid */}
                            <div className="lg:col-span-3 grid grid-cols-2 md:grid-cols-4 gap-4">
                                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                                        <Users className="w-4 h-4" />
                                        <span className="text-sm">Subscribers</span>
                                    </div>
                                    <div className="text-2xl font-bold">
                                        {formatNumber(result.results.channel_info.subscribers)}
                                    </div>
                                </div>
                                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                                        <Eye className="w-4 h-4" />
                                        <span className="text-sm">Avg Views</span>
                                    </div>
                                    <div className="text-2xl font-bold">
                                        {formatNumber(result.results.metrics.avg_views)}
                                    </div>
                                </div>
                                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                                        <TrendingUp className="w-4 h-4" />
                                        <span className="text-sm">Viral Ratio</span>
                                    </div>
                                    <div className="text-2xl font-bold">
                                        {(result.results.metrics.viral_ratio * 100).toFixed(0)}%
                                    </div>
                                </div>
                                <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                                    <div className="flex items-center gap-2 text-gray-400 mb-2">
                                        <Video className="w-4 h-4" />
                                        <span className="text-sm">Upload Freq</span>
                                    </div>
                                    <div className="text-2xl font-bold">
                                        {result.results.metrics.upload_frequency.toFixed(1)}/mo
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Video List */}
                        <div className="bg-white/5 rounded-2xl border border-white/10 overflow-hidden">
                            {/* Toolbar */}
                            <div className="p-4 border-b border-white/10 flex flex-wrap items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    <span className="text-gray-400">
                                        {selectedVideos.size} / {filteredVideos.length} selected
                                    </span>
                                    <button
                                        onClick={() => selectTopVideos(10)}
                                        className="text-sm text-cyan-400 hover:text-cyan-300"
                                    >
                                        Select Top 10
                                    </button>
                                    <button
                                        onClick={() => setSelectedVideos(new Set())}
                                        className="text-sm text-gray-400 hover:text-white"
                                    >
                                        Clear
                                    </button>
                                </div>

                                <div className="flex items-center gap-4">
                                    <div className="flex items-center gap-2">
                                        <Filter className="w-4 h-4 text-gray-400" />
                                        <input
                                            type="number"
                                            value={minViews}
                                            onChange={(e) => setMinViews(parseInt(e.target.value) || 0)}
                                            placeholder="Min views"
                                            className="w-24 px-2 py-1 rounded bg-white/5 border border-white/10 text-sm"
                                        />
                                    </div>
                                    <select
                                        value={sortBy}
                                        onChange={(e) => setSortBy(e.target.value)}
                                        className="px-3 py-1 rounded bg-white/5 border border-white/10 text-sm"
                                    >
                                        <option value="views">Sort by Views</option>
                                        <option value="likes">Sort by Likes</option>
                                        <option value="date">Sort by Date</option>
                                    </select>

                                    {selectedVideos.size > 0 && (
                                        <button
                                            onClick={handleBatchProcess}
                                            className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500
                               hover:from-cyan-400 hover:to-purple-400 text-sm font-medium
                               flex items-center gap-2"
                                        >
                                            <Download className="w-4 h-4" />
                                            Process Selected
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* Video Grid */}
                            <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto">
                                {filteredVideos.map((video) => (
                                    <div
                                        key={video.id}
                                        onClick={() => toggleVideoSelection(video.id)}
                                        className={`rounded-xl border cursor-pointer transition-all ${selectedVideos.has(video.id)
                                                ? 'border-cyan-500 bg-cyan-500/10'
                                                : 'border-white/10 bg-white/5 hover:border-white/20'
                                            }`}
                                    >
                                        <div className="relative">
                                            <img
                                                src={video.thumbnail}
                                                alt={video.title}
                                                className="w-full aspect-video object-cover rounded-t-xl"
                                            />
                                            <div className="absolute bottom-2 right-2 px-2 py-1 bg-black/80 rounded text-xs">
                                                {formatDuration(video.duration)}
                                            </div>
                                            {selectedVideos.has(video.id) && (
                                                <div className="absolute top-2 right-2 w-6 h-6 bg-cyan-500 rounded-full flex items-center justify-center">
                                                    <CheckCircle className="w-4 h-4" />
                                                </div>
                                            )}
                                        </div>
                                        <div className="p-3">
                                            <h3 className="font-medium text-sm line-clamp-2 mb-2">{video.title}</h3>
                                            <div className="flex items-center gap-3 text-xs text-gray-400">
                                                <span className="flex items-center gap-1">
                                                    <Eye className="w-3 h-3" />
                                                    {formatNumber(video.views)}
                                                </span>
                                                <span className="flex items-center gap-1">
                                                    <ThumbsUp className="w-3 h-3" />
                                                    {formatNumber(video.likes)}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
