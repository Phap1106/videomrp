'use client';

import { useState, useEffect } from 'react';
import { Search, TrendingUp, Shield, Sparkles, Download, FileText, Loader2, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { api } from '@/lib/api-client';

interface AnalysisResult {
    job_id: string;
    status: string;
    progress: number;
    video_info?: {
        title?: string;
        channel?: string;
        views?: number;
        duration?: number;
    };
    engagement?: {
        engagement_score?: number;
        reasoning?: string;
        metrics?: {
            like_view_ratio?: number;
            views_per_day?: number;
        };
    };
    nlp_analysis?: {
        keywords?: string[];
        sentiment?: string;
        summary?: string;
    };
    policy_check?: {
        policy_safe?: boolean;
        risk_level?: string;
        positive_value?: string[];
    };
    scoring?: {
        final_score?: number;
        grade?: string;
        explanation?: string;
        recommendation?: string;
        breakdown?: Record<string, { score: number; weight: number }>;
    };
    error?: string;
}

export default function AnalyzerPage() {
    const [url, setUrl] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [jobId, setJobId] = useState<string | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Poll for results
    useEffect(() => {
        if (!jobId || result?.status === 'completed' || result?.status === 'failed') return;

        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/api/youtube/analysis/${jobId}`);
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
        if (!url.trim()) return;

        setIsAnalyzing(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('http://localhost:8000/api/youtube/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ youtube_url: url }),
            });

            const data = await response.json();

            if (data.success) {
                setJobId(data.job_id);
            } else {
                setError(data.message || 'Failed to start analysis');
                setIsAnalyzing(false);
            }
        } catch (err) {
            setError('Failed to connect to server');
            setIsAnalyzing(false);
        }
    };

    const getScoreColor = (score: number) => {
        if (score >= 8) return 'text-green-400';
        if (score >= 6) return 'text-cyan-400';
        if (score >= 4) return 'text-yellow-400';
        return 'text-red-400';
    };

    const getRiskColor = (level: string) => {
        if (level === 'low') return 'text-green-400 bg-green-400/10';
        if (level === 'medium') return 'text-yellow-400 bg-yellow-400/10';
        return 'text-red-400 bg-red-400/10';
    };

    return (
        <div className="min-h-screen bg-[#0A0A0F] text-white">
            {/* Hero Section */}
            <div className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/10 via-purple-500/5 to-pink-500/10" />
                <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-20" />

                <div className="relative max-w-6xl mx-auto px-6 py-16">
                    <div className="text-center mb-12">
                        <h1 className="text-4xl md:text-5xl font-bold mb-4">
                            <span className="bg-gradient-to-r from-cyan-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                                YouTube Video Analyzer
                            </span>
                        </h1>
                        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
                            Phân tích video YouTube với AI. Đánh giá viral potential, policy compliance,
                            và content quality với điểm số minh bạch.
                        </p>
                    </div>

                    {/* URL Input */}
                    <div className="max-w-3xl mx-auto">
                        <div className="relative">
                            <input
                                type="text"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="Paste YouTube URL here..."
                                className="w-full px-6 py-4 pr-32 rounded-2xl bg-white/5 border border-white/10 
                         focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 
                         outline-none text-white placeholder-gray-500 text-lg"
                                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                            />
                            <button
                                onClick={handleAnalyze}
                                disabled={isAnalyzing || !url.trim()}
                                className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2.5 rounded-xl
                         bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-medium
                         hover:from-cyan-400 hover:to-purple-400 transition-all
                         disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            >
                                {isAnalyzing ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Analyzing...
                                    </>
                                ) : (
                                    <>
                                        <Search className="w-4 h-4" />
                                        Analyze
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Progress Bar */}
            {isAnalyzing && result && (
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-400">
                                {result.status === 'running' ? `Stage: ${(result as any).current_stage || 'Processing'}` : result.status}
                            </span>
                            <span className="text-sm text-cyan-400">{Math.round(result.progress || 0)}%</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-cyan-500 to-purple-500 transition-all duration-500"
                                style={{ width: `${result.progress || 0}%` }}
                            />
                        </div>
                    </div>
                </div>
            )}

            {/* Error Display */}
            {error && (
                <div className="max-w-6xl mx-auto px-6 py-4">
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400">
                        {error}
                    </div>
                </div>
            )}

            {/* Results Dashboard */}
            {result && result.status === 'completed' && (
                <div className="max-w-6xl mx-auto px-6 py-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                        {/* Main Score Card */}
                        <div className="lg:col-span-1">
                            <div className="bg-gradient-to-br from-white/5 to-white/[0.02] rounded-2xl p-6 border border-white/10 h-full">
                                <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-cyan-400" />
                                    Overall Score
                                </h3>

                                <div className="text-center mb-6">
                                    <div className={`text-7xl font-bold ${getScoreColor(result.scoring?.final_score || 0)}`}>
                                        {result.scoring?.final_score?.toFixed(1) || '0'}
                                    </div>
                                    <div className="text-2xl text-gray-400 mt-2">
                                        Grade: <span className="text-white font-semibold">{result.scoring?.grade || 'N/A'}</span>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    {/* Score Breakdown */}
                                    {result.scoring?.breakdown && Object.entries(result.scoring.breakdown).map(([key, value]: [string, any]) => (
                                        <div key={key}>
                                            <div className="flex justify-between text-sm mb-1">
                                                <span className="text-gray-400 capitalize">{key.replace('_', ' ')}</span>
                                                <span className={getScoreColor(value.score)}>{value.score?.toFixed(1)}</span>
                                            </div>
                                            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-gradient-to-r from-cyan-500 to-purple-500"
                                                    style={{ width: `${(value.score / 10) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Video Info & Analysis */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Video Info */}
                            <div className="bg-gradient-to-br from-white/5 to-white/[0.02] rounded-2xl p-6 border border-white/10">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <FileText className="w-5 h-5 text-purple-400" />
                                    Video Information
                                </h3>
                                <div className="space-y-2">
                                    <p className="text-xl font-medium">{result.video_info?.title || 'Unknown Title'}</p>
                                    <p className="text-gray-400">Channel: {result.video_info?.channel || 'Unknown'}</p>
                                    <div className="flex gap-4 text-sm text-gray-500">
                                        <span>{(result.video_info?.views || 0).toLocaleString()} views</span>
                                        <span>{Math.floor((result.video_info?.duration || 0) / 60)} minutes</span>
                                    </div>
                                </div>
                            </div>

                            {/* Policy Status */}
                            <div className="bg-gradient-to-br from-white/5 to-white/[0.02] rounded-2xl p-6 border border-white/10">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-green-400" />
                                    Policy Check
                                </h3>
                                <div className="flex items-center gap-4">
                                    <div className={`px-4 py-2 rounded-lg ${getRiskColor(result.policy_check?.risk_level || 'unknown')}`}>
                                        {result.policy_check?.policy_safe ? (
                                            <span className="flex items-center gap-2">
                                                <CheckCircle className="w-4 h-4" /> Safe
                                            </span>
                                        ) : (
                                            <span className="flex items-center gap-2">
                                                <AlertTriangle className="w-4 h-4" /> {result.policy_check?.risk_level || 'Unknown'}
                                            </span>
                                        )}
                                    </div>
                                    {result.policy_check?.positive_value && result.policy_check.positive_value.length > 0 && (
                                        <div className="flex gap-2">
                                            {result.policy_check.positive_value.map((val: string) => (
                                                <span key={val} className="px-3 py-1 bg-cyan-500/10 text-cyan-400 rounded-full text-sm">
                                                    {val}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Keywords & NLP */}
                            {result.nlp_analysis && (
                                <div className="bg-gradient-to-br from-white/5 to-white/[0.02] rounded-2xl p-6 border border-white/10">
                                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5 text-pink-400" />
                                        Content Analysis
                                    </h3>
                                    <div className="space-y-4">
                                        <div>
                                            <span className="text-sm text-gray-400">Sentiment:</span>
                                            <span className={`ml-2 capitalize ${result.nlp_analysis.sentiment === 'positive' ? 'text-green-400' :
                                                    result.nlp_analysis.sentiment === 'negative' ? 'text-red-400' : 'text-gray-400'
                                                }`}>
                                                {result.nlp_analysis.sentiment}
                                            </span>
                                        </div>
                                        {result.nlp_analysis.summary && (
                                            <p className="text-gray-300 text-sm">{result.nlp_analysis.summary}</p>
                                        )}
                                        {result.nlp_analysis.keywords && result.nlp_analysis.keywords.length > 0 && (
                                            <div className="flex flex-wrap gap-2">
                                                {result.nlp_analysis.keywords.slice(0, 10).map((kw: string) => (
                                                    <span key={kw} className="px-3 py-1 bg-white/5 rounded-full text-sm text-gray-300">
                                                        {kw}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Recommendation */}
                            {result.scoring?.recommendation && (
                                <div className="bg-gradient-to-r from-cyan-500/10 to-purple-500/10 rounded-2xl p-6 border border-cyan-500/20">
                                    <h3 className="text-lg font-semibold mb-2">📋 Recommendation</h3>
                                    <p className="text-gray-300">{result.scoring.recommendation}</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
