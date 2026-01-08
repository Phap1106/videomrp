"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  Video,
  Upload,
  Download,
  Play,
  Pause,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw,
  XCircle,
  BarChart3,
  Volume2,
  VolumeX,
  Link,
  Eye,
  FileText,
  Settings,
  Zap,
  Brain,
  DollarSign,
  TrendingUp,
  Cpu,
  ChevronRight,
  Users,
  Server,
  Database,
  Shield,
  ExternalLink,
  Copy,
  Trash2,
  Maximize2,
  Minimize2,
  FastForward,
  Rewind,
  Sparkles,
  Camera,
  Filter,
  Zap as ZapIcon,
  Palette,
  Settings as SettingsIcon,
  PlayCircle,
    Film, 

} from "lucide-react";
import axios from "axios";

// Types
type VideoStatus = "pending" | "processing" | "completed" | "failed";
type ProcessingStep =
  | "initializing"
  | "face_detection"
  | "facial_landmarks"
  | "pose_estimation"
  | "face_enhancement"
  | "style_transfer"
  | "quality_enhancement"
  | "audio_sync"
  | "final_render";

interface VideoItem {
  id: string;
  title: string;
  url: string;
  status: VideoStatus;
  progress: number;
  current_step?: ProcessingStep;
  error_message?: string;
  created_at: string;
  updated_at: string;
  processed_filename?: string;
  processed_path?: string;
  thumbnail_url?: string;
  duration?: number;
  size?: number;
  metadata: {
    prompt?: string;
    ai_processed?: boolean;
    token_usage?: number;
    cost_estimate?: number;
    models_used?: string[];
    processing_mode?: string;
    style?: string;
    enhancement_level?: string;
  };
}

interface TokenUsage {
  total_tokens: number;
  total_cost: number;
  by_model: Record<string, number>;
  by_video: Record<string, number>;
  cost_estimate: Record<string, number>;
  daily_usage: Record<string, number>;
}

interface SystemLog {
  timestamp: string;
  level: string;
  message: string;
}

interface VideoAnalytics {
  processing_details: {
    mode: string;
    style: string;
    enhancement_level: string;
    face_detected: boolean;
    face_count: number;
    processing_stages: number;
    ai_models_used: string[];
  };
  quality_metrics: {
    resolution: string;
    bitrate: string;
    frame_rate: string;
    encoding: string;
    audio_codec: string;
    overall_quality: string;
  };
  ai_insights: {
    emotion_detected: string;
    engagement_score: number;
    visual_complexity: number;
    processing_efficiency: string;
  };
}

export default function Home() {
  // State
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [prompt, setPrompt] = useState(
    "Enhance video with cinematic style and face optimization"
  );
  const [uploading, setUploading] = useState(false);
  const [processingVideoId, setProcessingVideoId] = useState<string | null>(
    null
  );
  const [tokenUsage, setTokenUsage] = useState<TokenUsage>({
    total_tokens: 0,
    total_cost: 0,
    by_model: {},
    by_video: {},
    cost_estimate: {},
    daily_usage: {},
  });
  const [systemLogs, setSystemLogs] = useState<SystemLog[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoItem | null>(null);
  const [videoAnalytics, setVideoAnalytics] = useState<VideoAnalytics | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  
  // Video Player State
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(80);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  
  // UI State
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [processingMode, setProcessingMode] = useState<'standard' | 'enhanced'>('enhanced');
  
  // Refs
  const videoRef = useRef<HTMLVideoElement>(null);
  const playerContainerRef = useRef<HTMLDivElement>(null);

  // Helper function to get processed URL
  const getProcessedUrl = (video: VideoItem) => {
    if (video.processed_filename) {
      return `http://localhost:5000/processed/${video.processed_filename}`;
    }
    return video.metadata?.ai_processed ? `http://localhost:5000/api/videos/${video.id}/preview` : undefined;
  };

  // Fetch data
  const fetchVideos = useCallback(async () => {
    try {
      const response = await axios.get("http://localhost:5000/api/videos");
      const videosData = response.data.map((video: any) => ({
        ...video,
        processed_url: getProcessedUrl(video)
      }));
      setVideos(videosData);
      
      // Auto-select first video if none selected
      if (!selectedVideo && videosData.length > 0) {
        setSelectedVideo(videosData[0]);
      }
    } catch (error) {
      console.error("Error fetching videos:", error);
      setError("Failed to fetch videos. Please check if backend is running.");
    }
  }, [selectedVideo]);

  const fetchTokenUsage = useCallback(async () => {
    try {
      const response = await axios.get(
        "http://localhost:5000/api/tokens/usage"
      );
      setTokenUsage(response.data);
    } catch (error) {
      console.error("Error fetching token usage:", error);
    }
  }, []);

  const fetchSystemLogs = useCallback(async () => {
    try {
      const response = await axios.get("http://localhost:5000/api/logs");
      const logs = response.data.logs.map((line: any) => ({
        timestamp: line.timestamp || line.raw || '',
        level: line.level || 'INFO',
        message: line.message || line.raw || ''
      }));
      setSystemLogs(logs);
    } catch (error) {
      console.error("Error fetching logs:", error);
    }
  }, []);

  const fetchVideoAnalytics = useCallback(async (videoId: string) => {
    try {
      const response = await axios.get(`http://localhost:5000/api/videos/${videoId}/analytics`);
      setVideoAnalytics(response.data);
    } catch (error) {
      console.error("Error fetching video analytics:", error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchVideos(),
      fetchTokenUsage(),
      fetchSystemLogs(),
    ]).finally(() => setLoading(false));
  }, [fetchVideos, fetchTokenUsage, fetchSystemLogs]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchVideos();
      fetchTokenUsage();
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchVideos, fetchTokenUsage]);

  // Video player controls
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
      setDuration(video.duration || 0);
    };

    const handleLoadedData = () => {
      setDuration(video.duration || 0);
    };

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadeddata', handleLoadedData);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadeddata', handleLoadedData);
    };
  }, [selectedVideo]);

  // Handle fullscreen
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, []);

  const toggleFullscreen = () => {
    if (!playerContainerRef.current) return;

    if (!document.fullscreenElement) {
      playerContainerRef.current.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  // Format time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  // Add video
  const handleAddVideo = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!url.trim()) {
      setError("Please enter a video URL");
      return;
    }

    setUploading(true);
    try {
      const response = await axios.post("http://localhost:5000/api/videos", { 
        url, 
        title: title || `Video ${new Date().toISOString().replace(/[:.]/g, '-')}`,
        prompt: prompt
      });
      
      if (response.data.success) {
        await fetchVideos();
        setSuccessMessage(`Video "${response.data.video.title}" added successfully!`);
        setUrl("");
        setTitle("");
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.error || error.message || "Failed to add video";
      setError(`Error: ${errorMsg}`);
    } finally {
      setUploading(false);
    }
  };

  // Process video with AI
  const handleProcessVideo = async (videoId: string) => {
    setProcessingVideoId(videoId);
    setError(null);
    
    try {
      const endpoint = processingMode === 'enhanced' 
        ? `http://localhost:5000/api/process/${videoId}/enhanced`
        : `http://localhost:5000/api/process/${videoId}`;
      
      const response = await axios.post(endpoint, {
        prompt: prompt,
      });

      if (response.data.success) {
        setSuccessMessage(`Video processing started with ${processingMode} mode!`);
        
        // Start polling for progress
        const pollProgress = async () => {
          try {
            await fetchVideos();
            
            const video = videos.find(v => v.id === videoId);
            if (video?.status === 'processing') {
              setTimeout(pollProgress, 2000);
            } else if (video?.status === 'completed') {
              setSuccessMessage(`Video processing completed!`);
              fetchTokenUsage();
              if (video.id === selectedVideo?.id) {
                setSelectedVideo(video);
                fetchVideoAnalytics(video.id);
              }
            }
          } catch (error) {
            console.error("Error polling progress:", error);
          }
        };

        setTimeout(pollProgress, 1000);
      }
    } catch (error: any) {
      setError(`Processing error: ${error.response?.data?.error || error.message}`);
    } finally {
      setProcessingVideoId(null);
    }
  };

  // Download video
  const handleDownload = async (videoId: string, videoTitle: string) => {
    try {
      const video = videos.find(v => v.id === videoId);
      if (!video?.processed_filename) {
        setError("No processed video available for download");
        return;
      }

      window.open(`http://localhost:5000/api/videos/${videoId}/download`, '_blank');
      setSuccessMessage(`Downloading "${videoTitle}"...`);
    } catch (error: any) {
      setError(`Download error: ${error.message}`);
    }
  };

  // View video
  const handleViewVideo = (video: VideoItem) => {
    const url = getProcessedUrl(video);
    if (!url) {
      setError("No processed video available to view");
      return;
    }
    window.open(url, '_blank');
  };

  // Delete video
  const handleDeleteVideo = async (videoId: string) => {
    if (!confirm("Are you sure you want to delete this video?")) return;
    
    try {
      // Update UI immediately
      setVideos(prev => prev.filter(video => video.id !== videoId));
      if (selectedVideo?.id === videoId) {
        setSelectedVideo(videos.length > 1 ? videos[1] : null);
      }
      setSuccessMessage("Video deleted successfully");
    } catch (error) {
      setError("Failed to delete video");
    }
  };

  // Copy URL
  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setSuccessMessage("URL copied to clipboard!");
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  // Status helpers
  const getStatusInfo = (status: VideoStatus) => {
    switch (status) {
      case "pending":
        return {
          icon: Clock,
          color: "text-yellow-500",
          bg: "bg-yellow-500/10",
          text: "Pending",
        };
      case "processing":
        return {
          icon: RefreshCw,
          color: "text-blue-500",
          bg: "bg-blue-500/10",
          text: "Processing",
        };
      case "completed":
        return {
          icon: CheckCircle,
          color: "text-green-500",
          bg: "bg-green-500/10",
          text: "Completed",
        };
      case "failed":
        return {
          icon: XCircle,
          color: "text-red-500",
          bg: "bg-red-500/10",
          text: "Failed",
        };
    }
  };

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Format cost
  const formatCost = (cost: number | undefined) => {
    if (cost === undefined || cost === null) return '0.00';
    return cost.toFixed(4);
  };

  // Stats
  const stats = {
    total: videos.length,
    completed: videos.filter((v) => v.status === "completed").length,
    processing: videos.filter((v) => v.status === "processing").length,
    failed: videos.filter((v) => v.status === "failed").length,
    pending: videos.filter((v) => v.status === "pending").length,
    totalTokens: videos.reduce((sum, video) => sum + (video.metadata?.token_usage || 0), 0),
    totalCost: videos.reduce((sum, video) => sum + (video.metadata?.cost_estimate || 0), 0),
  };

  // Video player controls
  const togglePlay = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value);
    setCurrentTime(time);
    if (videoRef.current) {
      videoRef.current.currentTime = time;
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const vol = parseFloat(e.target.value);
    setVolume(vol);
    if (videoRef.current) {
      videoRef.current.volume = vol / 100;
      setIsMuted(vol === 0);
    }
  };

  const toggleMute = () => {
    if (videoRef.current) {
      videoRef.current.muted = !videoRef.current.muted;
      setIsMuted(!isMuted);
    }
  };

  const handlePlaybackRate = (rate: number) => {
    setPlaybackRate(rate);
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  };

  // Style options
  const styleOptions = [
    { id: 'cinematic', name: 'Cinematic', icon: Film, color: 'from-purple-600 to-blue-600' },
    { id: 'viral', name: 'Viral', icon: ZapIcon, color: 'from-pink-600 to-orange-600' },
    { id: 'professional', name: 'Professional', icon: SettingsIcon, color: 'from-emerald-600 to-cyan-600' },
  ];

  return (
    <div className="min-h-screen text-gray-100 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-50 px-4 py-3 border-b border-gray-700 bg-gray-900/90 backdrop-blur-lg">
        <div className="container flex items-center justify-between mx-auto">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-transparent bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text">
                AI Video Factory Pro v3.0
              </h1>
              <p className="text-xs text-gray-400">
                LivePortrait-Enhanced Video Processing
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="items-center hidden space-x-4 md:flex">
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800 rounded-lg">
                <Server className="w-4 h-4 text-green-500" />
                <span className="text-sm">API: Online</span>
              </div>
              
              <div className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800 rounded-lg">
                <Database className="w-4 h-4 text-blue-500" />
                <span className="text-sm">{videos.length} Videos</span>
              </div>
            </div>

            <button
              onClick={() => {
                fetchVideos();
                fetchTokenUsage();
                fetchSystemLogs();
                setSuccessMessage("System refreshed");
                setTimeout(() => setSuccessMessage(null), 3000);
              }}
              className="flex items-center space-x-2 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm transition"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Refresh</span>
            </button>

            <label className="flex items-center space-x-2 cursor-pointer">
              <div className="relative">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="sr-only"
                />
                <div
                  className={`w-10 h-5 rounded-full ${
                    autoRefresh ? "bg-green-500" : "bg-gray-700"
                  }`}
                >
                  <div
                    className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
                      autoRefresh ? "left-5" : "left-0.5"
                    }`}
                  />
                </div>
              </div>
              <span className="hidden text-sm md:inline">Auto-refresh</span>
            </label>
          </div>
        </div>
      </header>

      {/* Alerts */}
      {(error || successMessage) && (
        <div className="container px-4 py-2 mx-auto">
          {error && (
            <div className="flex items-center justify-between p-3 mb-3 border rounded-lg bg-red-500/20 border-red-500/30">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 mr-2 text-red-400" />
                <span className="text-red-300">{error}</span>
              </div>
              <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
                ×
              </button>
            </div>
          )}
          {successMessage && (
            <div className="flex items-center justify-between p-3 mb-3 border rounded-lg bg-green-500/20 border-green-500/30">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                <span className="text-green-300">{successMessage}</span>
              </div>
              <button onClick={() => setSuccessMessage(null)} className="text-green-400 hover:text-green-300">
                ×
              </button>
            </div>
          )}
        </div>
      )}

      <main className="container px-4 py-6 mx-auto">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
          {/* Left Column - Upload & Controls */}
          <div className="space-y-6 lg:col-span-1">
            {/* Upload Card */}
            <div className="p-5 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
              <div className="flex items-center mb-5">
                <div className="p-2 mr-3 rounded-lg bg-gradient-to-r from-emerald-600 to-green-500">
                  <Upload className="w-5 h-5" />
                </div>
                <h2 className="text-lg font-semibold">Upload Video</h2>
              </div>

              <form onSubmit={handleAddVideo} className="space-y-4">
                <div>
                  <label className="block mb-2 text-sm font-medium">
                    <Link className="inline w-4 h-4 mr-1" />
                    Video URL
                  </label>
                  <input
                    type="url"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="w-full px-3 py-2.5 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
                    placeholder="https://example.com/video.mp4"
                    required
                  />
                  <div className="mt-1 text-xs text-gray-500">
                    Supports: MP4, MOV, AVI, MKV, WEBM
                  </div>
                </div>

                <div>
                  <label className="block mb-2 text-sm font-medium">
                    <FileText className="inline w-4 h-4 mr-1" />
                    Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full px-3 py-2.5 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
                    placeholder="My Awesome Video"
                  />
                </div>

                {/* Processing Mode Selector */}
                <div>
                  <label className="block mb-2 text-sm font-medium">
                    <Zap className="inline w-4 h-4 mr-1" />
                    Processing Mode
                  </label>
                  <div className="flex space-x-2">
                    <button
                      type="button"
                      onClick={() => setProcessingMode('standard')}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
                        processingMode === 'standard'
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      Standard
                    </button>
                    <button
                      type="button"
                      onClick={() => setProcessingMode('enhanced')}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition ${
                        processingMode === 'enhanced'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                      }`}
                    >
                      <div className="flex items-center justify-center">
                        <Sparkles className="w-4 h-4 mr-2" />
                        Enhanced
                      </div>
                    </button>
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    {processingMode === 'enhanced' 
                      ? 'With LivePortrait face enhancement & style transfer'
                      : 'Basic AI processing'}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={uploading || !url.trim()}
                  className="w-full py-2.5 bg-gradient-to-r from-emerald-600 to-green-500 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium text-sm transition flex items-center justify-center space-x-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Adding Video...</span>
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      <span>Add to Queue</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* AI Prompt & Style Card */}
            <div className="p-5 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
              <div className="flex items-center mb-5">
                <div className="p-2 mr-3 rounded-lg bg-gradient-to-r from-purple-600 to-pink-500">
                  <Palette className="w-5 h-5" />
                </div>
                <h2 className="text-lg font-semibold">AI Style & Prompt</h2>
              </div>

              <div className="space-y-4">
                {/* Style Selection */}
                <div>
                  <label className="block mb-2 text-sm font-medium">
                    <Filter className="inline w-4 h-4 mr-1" />
                    Video Style
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {styleOptions.map((style) => (
                      <button
                        key={style.id}
                        type="button"
                        onClick={() => setPrompt(`Enhance video with ${style.name.toLowerCase()} style`)}
                        className={`p-3 rounded-lg text-xs font-medium transition ${
                          prompt.includes(style.name)
                            ? `bg-gradient-to-r ${style.color} text-white`
                            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                        }`}
                      >
                        <style.icon className="w-4 h-4 mx-auto mb-1" />
                        {style.name}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block mb-2 text-sm font-medium">
                    <Brain className="inline w-4 h-4 mr-1" />
                    Processing Prompt
                  </label>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="w-full h-32 px-3 py-2.5 bg-gray-900/50 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm resize-none"
                    placeholder="Describe how you want the video processed..."
                  />
                </div>

                <div className="space-y-1 text-xs text-gray-400">
                  <p className="flex items-center">
                    <Camera className="w-3 h-3 mr-1" />
                    Enhanced mode includes: Face detection, facial enhancement, style transfer
                  </p>
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="p-5 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
              <h3 className="flex items-center mb-4 font-semibold">
                <BarChart3 className="w-4 h-4 mr-2" />
                Quick Stats
              </h3>

              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Total Videos</span>
                  <span className="text-lg font-bold">{stats.total}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Processing</span>
                  <span className="text-lg font-bold text-blue-500">{stats.processing}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Total Tokens</span>
                  <span className="text-lg font-bold text-amber-500">
                    {stats.totalTokens.toLocaleString()}
                  </span>
                </div>
                <div className="pt-3 border-t border-gray-700">
                  <div className="space-y-2 text-xs text-gray-400">
                    <div className="flex justify-between">
                      <span>LivePortrait:</span>
                      <span className="text-green-500">Active</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Processing Mode:</span>
                      <span className="text-purple-500">{processingMode}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column - Video Player & List */}
          <div className="space-y-6 lg:col-span-2">
            {/* Video Player */}
            {selectedVideo ? (
              <div className="overflow-hidden border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                {/* Player Header */}
                <div className="p-4 border-b border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Video className="w-5 h-5 text-blue-400" />
                      <h2 className="text-lg font-semibold truncate">
                        {selectedVideo.title}
                      </h2>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        selectedVideo.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        selectedVideo.status === 'processing' ? 'bg-blue-500/20 text-blue-400' :
                        selectedVideo.status === 'pending' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-red-500/20 text-red-400'
                      }`}>
                        {selectedVideo.status.charAt(0).toUpperCase() + selectedVideo.status.slice(1)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewVideo(selectedVideo)}
                        className="flex items-center px-3 py-1 text-sm transition bg-blue-600 rounded-lg hover:bg-blue-700"
                        title="Open in new tab"
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        Open
                      </button>
                      <button
                        onClick={toggleFullscreen}
                        className="p-2 transition bg-gray-700 rounded-lg hover:bg-gray-600"
                        title="Fullscreen"
                      >
                        {isFullscreen ? (
                          <Minimize2 className="w-4 h-4" />
                        ) : (
                          <Maximize2 className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>

{/* Video Container */}
<div ref={playerContainerRef} className="relative bg-black">
  {selectedVideo.status === 'completed' && (selectedVideo as any).processed_url ? (
    <>
      <video
        ref={videoRef}
        src={(selectedVideo as any).processed_url}
        className="w-full aspect-video"
        controls={false}
        playsInline
        preload="metadata"
      />
      {/* ... phần còn lại của code ... */}
    </>
  ) : selectedVideo.status === 'processing' ? (
    <div className="flex items-center justify-center aspect-video">
      <div className="text-center">
        <RefreshCw className="w-12 h-12 mx-auto mb-4 text-blue-500 animate-spin" />
        <h3 className="mb-2 text-xl font-semibold">Processing Video</h3>
        <p className="mb-4 text-gray-400">
          {(selectedVideo as any).current_step || 'Initializing...'}
        </p>
        <div className="w-64 mx-auto">
          <div className="h-2 overflow-hidden bg-gray-700 rounded-full">
            <div
              className="h-full transition-all duration-300 bg-gradient-to-r from-blue-500 to-purple-500"
              style={{ width: `${(selectedVideo as any).progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-2 text-sm text-gray-400">
            <span>{(selectedVideo as any).progress}%</span>
            <span>LivePortrait AI</span>
          </div>
        </div>
      </div>
    </div>
  ) : (
    <div className="flex items-center justify-center aspect-video">
      <div className="text-center">
        <Video className="w-16 h-16 mx-auto mb-4 text-gray-600" />
        <p className="text-gray-400">Video not processed yet</p>
        <button
          onClick={() => handleProcessVideo(selectedVideo.id)}
          disabled={processingVideoId === selectedVideo.id}
          className="px-4 py-2 mt-4 text-sm font-medium transition rounded-lg bg-gradient-to-r from-purple-600 to-pink-500 hover:opacity-90 disabled:opacity-50"
        >
          {processingVideoId === selectedVideo.id ? (
            <>
              <RefreshCw className="inline w-4 h-4 mr-2 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Sparkles className="inline w-4 h-4 mr-2" />
              Process with AI
            </>
          )}
        </button>
      </div>
    </div>
  )}
</div>
                {/* Video Info & Actions */}
                <div className="p-4">
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-3 rounded-lg bg-gray-900/50">
                      <p className="text-xs text-gray-400">AI Models Used</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(selectedVideo.metadata?.models_used || ['GPT-4', 'MediaPipe']).slice(0, 3).map((model, idx) => (
                          <span key={idx} className="px-2 py-1 text-xs bg-gray-800 rounded">
                            {model}
                          </span>
                        ))}
                        {selectedVideo.metadata?.models_used && selectedVideo.metadata.models_used.length > 3 && (
                          <span className="px-2 py-1 text-xs bg-gray-800 rounded">
                            +{selectedVideo.metadata.models_used.length - 3}
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <div className="p-3 rounded-lg bg-gray-900/50">
                      <p className="text-xs text-gray-400">AI Tokens Used</p>
                      <p className="mt-1 text-lg font-bold text-amber-500">
                        {(selectedVideo.metadata?.token_usage || 0).toLocaleString()}
                      </p>
                      <p className="mt-1 text-xs text-gray-400">
                        Cost: ${formatCost(selectedVideo.metadata?.cost_estimate)}
                      </p>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-3">
                    {selectedVideo.status === 'completed' && (
                      <>
                        <button
                          onClick={() => handleDownload(selectedVideo.id, selectedVideo.title)}
                          className="flex-1 py-2.5 bg-gradient-to-r from-green-600 to-emerald-500 hover:opacity-90 rounded-lg font-medium text-sm transition flex items-center justify-center space-x-2"
                        >
                          <Download className="w-4 h-4" />
                          <span>Download Video</span>
                        </button>
                        
                        <button
                          onClick={() => {
                            fetchVideoAnalytics(selectedVideo.id);
                          }}
                          className="px-4 py-2.5 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium text-sm transition"
                        >
                          <BarChart3 className="w-4 h-4" />
                        </button>
                      </>
                    )}
                    
                    {selectedVideo.status === 'pending' && (
                      <button
                        onClick={() => handleProcessVideo(selectedVideo.id)}
                        disabled={processingVideoId === selectedVideo.id}
                        className="flex-1 py-2.5 bg-gradient-to-r from-purple-600 to-pink-500 hover:opacity-90 disabled:opacity-50 rounded-lg font-medium text-sm transition flex items-center justify-center space-x-2"
                      >
                        {processingVideoId === selectedVideo.id ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            <span>Processing...</span>
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            <span>Process with LivePortrait AI</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                <Video className="w-16 h-16 mx-auto mb-4 text-gray-600" />
                <h3 className="mb-2 text-lg font-semibold">No Video Selected</h3>
                <p className="text-gray-400">Select a video from the queue to view details</p>
              </div>
            )}

            {/* Video Analytics */}
            {videoAnalytics && selectedVideo?.status === 'completed' && (
              <div className="p-5 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
                <h3 className="flex items-center mb-4 text-lg font-semibold">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Video Analytics
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-3 rounded-lg bg-gray-900/50">
                    <p className="text-xs text-gray-400">Style Applied</p>
                    <p className="mt-1 text-sm font-medium">{videoAnalytics.processing_details.style}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900/50">
                    <p className="text-xs text-gray-400">Face Detection</p>
                    <p className="mt-1 text-sm font-medium">
                      {videoAnalytics.processing_details.face_detected ? '✅ Detected' : '❌ Not detected'}
                    </p>
                  </div>
                  <div className="p-3 rounded-lg bg-gray-900/50">
                    <p className="text-xs text-gray-400">Quality</p>
                    <p className="mt-1 text-sm font-medium">{videoAnalytics.quality_metrics.overall_quality}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Video Queue Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold">Video Queue</h2>
                <p className="text-sm text-gray-400">
                  {stats.total} videos • {stats.processing} processing • {stats.completed} ready
                </p>
              </div>
              
              <div className="flex items-center space-x-2">
                <div className="flex p-1 bg-gray-800 rounded-lg">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`px-3 py-1 rounded text-sm ${
                      viewMode === 'grid' ? 'bg-gray-700' : ''
                    }`}
                  >
                    Grid
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`px-3 py-1 rounded text-sm ${
                      viewMode === 'list' ? 'bg-gray-700' : ''
                    }`}
                  >
                    List
                  </button>
                </div>
              </div>
            </div>

            {/* Video List */}
            {loading ? (
              <div className="flex justify-center py-12">
                <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
              </div>
            ) : videos.length === 0 ? (
              <div className="py-12 text-center bg-gray-800/50 rounded-xl">
                <Video className="w-12 h-12 mx-auto mb-4 text-gray-600" />
                <p className="text-gray-400">No videos in queue</p>
                <p className="mt-1 text-sm text-gray-500">
                  Add a video URL above to get started
                </p>
              </div>
            ) : (
              <div className={viewMode === 'grid' 
                ? "grid grid-cols-1 md:grid-cols-2 gap-4"
                : "space-y-3"
              }>
                {videos.map((video) => {
                  const StatusIcon = getStatusInfo(video.status).icon;
                  const statusColor = getStatusInfo(video.status).color;
                  const statusBg = getStatusInfo(video.status).bg;

                  return (
                    <div
                      key={video.id}
                      className={`bg-gray-800/50 backdrop-blur-sm rounded-lg border ${
                        selectedVideo?.id === video.id ? 'border-blue-500' : 'border-gray-700'
                      } p-4 transition-all hover:bg-gray-800 cursor-pointer`}
                      onClick={() => {
                        setSelectedVideo(video);
                        if (video.status === 'completed') {
                          fetchVideoAnalytics(video.id);
                        }
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center flex-1 min-w-0 space-x-3">
                          <div className={`p-2 rounded-lg ${statusBg}`}>
                            <StatusIcon className={`w-4 h-4 ${statusColor}`} />
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <h3 className="text-sm font-semibold truncate">
                                {video.title}
                              </h3>
                              {video.duration && (
                                <span className="ml-2 text-xs text-gray-400">
                                  {formatTime(video.duration)}
                                </span>
                              )}
                            </div>
                            
                            <div className="flex items-center mt-1 space-x-2">
                              <span className="px-2 py-1 text-xs bg-gray-700 rounded-full">
                                {getStatusInfo(video.status).text}
                              </span>
                              
                              {video.metadata?.token_usage && (
                                <span className="text-xs text-amber-500">
                                  {video.metadata.token_usage.toLocaleString()} tokens
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center ml-4 space-x-2">
                          {video.status === 'completed' && (
                            <>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleViewVideo(video);
                                }}
                                className="flex items-center px-3 py-1 text-xs font-medium transition bg-blue-600 rounded hover:bg-blue-700"
                              >
                                <Play className="w-3 h-3 mr-1" />
                                Play
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDownload(video.id, video.title);
                                }}
                                className="flex items-center px-3 py-1 text-xs font-medium transition bg-green-600 rounded hover:bg-green-700"
                              >
                                <Download className="w-3 h-3 mr-1" />
                                Download
                              </button>
                            </>
                          )}
                          
                          {video.status === 'pending' && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleProcessVideo(video.id);
                              }}
                              disabled={processingVideoId === video.id}
                              className="px-3 py-1 text-xs font-medium transition rounded bg-gradient-to-r from-purple-600 to-pink-500 hover:opacity-90 disabled:opacity-50"
                            >
                              {processingVideoId === video.id ? 'Processing...' : 'Process'}
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Right Column - AI Tokens & Logs */}
          <div className="space-y-6 lg:col-span-1">
            {/* AI Token Usage Dashboard */}
            <div className="p-5 border bg-gradient-to-b from-purple-900/30 to-blue-900/30 backdrop-blur-sm rounded-xl border-purple-500/20">
              <div className="flex items-center mb-5">
                <div className="p-2 mr-3 rounded-lg bg-gradient-to-r from-amber-600 to-orange-500">
                  <DollarSign className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold">AI Token Usage</h2>
                  <p className="text-xs text-gray-400">LivePortrait Tracking</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 rounded-lg bg-gray-900/50">
                  <div className="mb-3 text-center">
                    <div className="mb-1 text-3xl font-bold text-amber-500">
                      {(tokenUsage?.total_tokens || 0).toLocaleString()}
                    </div>
                    <div className="text-sm text-gray-400">Total Tokens Used</div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-2xl font-bold text-green-500">
                        ${formatCost(tokenUsage?.total_cost)}
                      </div>
                      <div className="text-xs text-gray-400">Total Cost</div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold">
                        {stats.completed}
                      </div>
                      <div className="text-xs text-gray-400">Videos Processed</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="flex items-center mb-2 text-sm font-medium">
                    <Cpu className="w-4 h-4 mr-2" />
                    By Model
                  </h4>
                  <div className="space-y-2">
                    {Object.entries(tokenUsage?.by_model || {}).map(
                      ([model, tokens]) => (
                        <div
                          key={model}
                          className="flex items-center justify-between p-2 rounded bg-gray-900/30"
                        >
                          <span className="text-sm text-gray-300 truncate">
                            {model}
                          </span>
                          <div className="text-right">
                            <div className="font-medium text-amber-500">
                              {(tokens || 0).toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-400">
                              ${formatCost(tokenUsage?.cost_estimate?.[model])}
                            </div>
                          </div>
                        </div>
                      )
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* System Logs */}
            <div className="p-5 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className="p-1.5 bg-gray-700 rounded mr-2">
                    <Database className="w-4 h-4" />
                  </div>
                  <h3 className="font-semibold">System Logs</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={fetchSystemLogs}
                    className="p-1 rounded hover:bg-gray-700"
                    title="Refresh logs"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <span className="text-xs text-gray-400">
                    {systemLogs.length} entries
                  </span>
                </div>
              </div>

              <div className="space-y-2 overflow-y-auto max-h-80">
                {systemLogs.length > 0 ? (
                  systemLogs.slice(0, 8).map((log, idx) => (
                    <div
                      key={idx}
                      className={`text-xs p-2 rounded transition hover:bg-gray-900/50 ${
                        log.level.includes("ERROR")
                          ? "bg-red-500/10 text-red-400 border border-red-500/20"
                          : log.level.includes("WARN")
                          ? "bg-yellow-500/10 text-yellow-400 border border-yellow-500/20"
                          : log.level.includes("INFO")
                          ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                          : "bg-gray-900/30 text-gray-300"
                      }`}
                    >
                      <div className="flex justify-between mb-1">
                        <span className="font-medium">{log.level}</span>
                        <span className="text-xs text-gray-500">
                          {log.timestamp?.split(' ')[1] || ''}
                        </span>
                      </div>
                      <p className="truncate">{log.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="py-4 text-sm text-center text-gray-500">
                    <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    No recent logs
                  </div>
                )}
              </div>
            </div>

            {/* LivePortrait Features */}
            <div className="p-5 border border-gray-700 bg-gray-800/50 backdrop-blur-sm rounded-xl">
              <h3 className="flex items-center mb-3 font-semibold">
                <Sparkles className="w-4 h-4 mr-2" />
                LivePortrait Features
              </h3>
              <div className="space-y-3">
                <div className="flex items-start space-x-2">
                  <div className="p-1 bg-blue-500/20 rounded mt-0.5">
                    <Camera className="w-3 h-3 text-blue-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium">Face Detection</span>
                    <p className="text-xs text-gray-400">Real-time facial landmark tracking</p>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="p-1 bg-purple-500/20 rounded mt-0.5">
                    <Filter className="w-3 h-3 text-purple-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium">Style Transfer</span>
                    <p className="text-xs text-gray-400">Cinematic, viral & professional styles</p>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <div className="p-1 bg-green-500/20 rounded mt-0.5">
                    <Zap className="w-3 h-3 text-green-400" />
                  </div>
                  <div>
                    <span className="text-sm font-medium">Quality Enhancement</span>
                    <p className="text-xs text-gray-400">AI-powered video upscaling</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="pt-6 mt-8 border-t border-gray-800">
        <div className="container px-4 mx-auto">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div>
              <h4 className="mb-2 font-semibold">AI Video Factory Pro v3.0</h4>
              <p className="text-sm text-gray-400">
                LivePortrait-Enhanced Video Processing Platform
              </p>
            </div>
            
            <div className="text-center">
              <p className="text-sm text-gray-500">
                © {new Date().getFullYear()} AI Video Factory - Enhanced Edition
              </p>
              <p className="mt-1 text-xs text-gray-600">
                Total Tokens: {(tokenUsage?.total_tokens || 0).toLocaleString()} • 
                LivePortrait: Active • Videos: {stats.total}
              </p>
            </div>
            
            <div className="text-right">
              <div className="flex items-center justify-end space-x-4">
                <span className="text-xs text-gray-500">Status:</span>
                <div className="flex items-center">
                  <div className="w-2 h-2 mr-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-500">All Systems Operational</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}