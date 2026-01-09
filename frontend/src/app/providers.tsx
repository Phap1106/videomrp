'use client'

import { useState, useEffect, useRef } from 'react'
import {
  Upload, Link, Film, Globe, Scissors, Type, Music, Zap, Sparkles,
  Download, Clock, Play, Pause, Settings, RefreshCw, Check, X,
  ChevronRight, AlertCircle, BarChart, Hash, FileText, Video
} from 'lucide-react'

type Platform = 'tiktok' | 'youtube' | 'facebook' | 'instagram' | 'douyin' | 'twitter' | 'generic'
type VideoType = 'short' | 'highlight' | 'viral' | 'meme' | 'full' | 'reel'
type JobStatus = 'pending' | 'downloading' | 'analyzing' | 'processing' | 'completed' | 'failed' | 'cancelled'

interface VideoJob {
  id: string
  title: string
  status: JobStatus
  progress: number
  current_step: string
  source_platform: string
  target_platform: string
  video_type: string
  duration: number
  created_at: string
  updated_at?: string
  completed_at?: string
  output_filename?: string
  error_message?: string
}

interface AnalysisResult {
  job_id: string
  summary: string
  category: string
  mood: string
  duration: number
  key_moments: any[]
  scenes: any[]
  copyright_risks: any[]
  suggestions: any
  hashtags: string[]
  titles: string[]
  viral_score: number
  processing_time: number
}

interface PlatformSetting {
  platform: Platform
  name: string
  max_duration: number
  aspect_ratios: string[]
  watermark_allowed: boolean
  copyright_strictness: string
  recommended_formats: string[]
  max_size_mb: number
  audio_requirements: any
}

export default function VideoEditorPage() {
  // State for video input
  const [videoUrl, setVideoUrl] = useState('')
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  
  // State for editing options
  const [targetPlatform, setTargetPlatform] = useState<Platform>('tiktok')
  const [videoType, setVideoType] = useState<VideoType>('short')
  const [duration, setDuration] = useState(60)
  const [addSubtitles, setAddSubtitles] = useState(true)
  const [changeMusic, setChangeMusic] = useState(true)
  const [removeWatermark, setRemoveWatermark] = useState(true)
  const [addEffects, setAddEffects] = useState(true)
  const [memeTemplate, setMemeTemplate] = useState('')
  
  // State for jobs and results
  const [jobs, setJobs] = useState<VideoJob[]>([])
  const [selectedJob, setSelectedJob] = useState<VideoJob | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [platformSettings, setPlatformSettings] = useState<PlatformSetting[]>([])
  
  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'upload' | 'jobs' | 'analysis'>('upload')
  const [videoPreview, setVideoPreview] = useState<string | null>(null)
  
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Fetch platform settings on mount
  useEffect(() => {
    fetchPlatformSettings()
    fetchJobs()
  }, [])

  // Fetch platform settings from backend
  const fetchPlatformSettings = async () => {
    try {
      const response = await fetch('/api/platforms')
      const data = await response.json()
      setPlatformSettings(data)
    } catch (error) {
      console.error('Failed to fetch platform settings:', error)
    }
  }

  // Fetch jobs from backend
  const fetchJobs = async () => {
    try {
      const response = await fetch('/api/jobs')
      const data = await response.json()
      setJobs(data.items || [])
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
    }
  }

  // Handle file upload
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      setVideoUrl('')
      
      // Create preview URL
      const previewUrl = URL.createObjectURL(file)
      setVideoPreview(previewUrl)
    }
  }

  // Handle URL input
  const handleUrlSubmit = () => {
    if (videoUrl) {
      setVideoFile(null)
      setVideoPreview(videoUrl)
    }
  }

  // Create a new video job
  const createJob = async () => {
    if (!videoUrl && !videoFile) {
      alert('Please provide a video URL or file')
      return
    }

    setIsLoading(true)
    
    try {
      let jobData
      
      if (videoFile) {
        // Upload file
        const formData = new FormData()
        formData.append('file', videoFile)
        formData.append('target_platform', targetPlatform)
        formData.append('video_type', videoType)
        formData.append('duration', duration.toString())
        formData.append('add_subtitles', addSubtitles.toString())
        formData.append('change_music', changeMusic.toString())
        formData.append('remove_watermark', removeWatermark.toString())
        formData.append('add_effects', addEffects.toString())
        
        if (memeTemplate) {
          formData.append('meme_template', memeTemplate)
        }
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        })
        
        jobData = await response.json()
      } else {
        // Use URL
        const requestBody = {
          source_url: videoUrl,
          target_platform: targetPlatform,
          video_type: videoType,
          duration,
          add_subtitles: addSubtitles,
          change_music: changeMusic,
          remove_watermark: removeWatermark,
          add_effects: addEffects,
          meme_template: memeTemplate || undefined,
        }
        
        const response = await fetch('/api/jobs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        })
        
        jobData = await response.json()
      }
      
      // Add new job to list
      setJobs(prev => [jobData, ...prev])
      setSelectedJob(jobData)
      setActiveTab('jobs')
      
      // Start polling for job updates
      pollJobStatus(jobData.id)
      
    } catch (error) {
      console.error('Failed to create job:', error)
      alert('Failed to create job. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  // Poll job status until completed
  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/jobs/${jobId}`)
        const job = await response.json()
        
        setJobs(prev => prev.map(j => j.id === jobId ? job : j))
        
        if (selectedJob?.id === jobId) {
          setSelectedJob(job)
        }
        
        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(interval)
          
          // If completed, fetch analysis if available
          if (job.status === 'completed') {
            try {
              const analysisResponse = await fetch(`/api/analyze?job_id=${jobId}`)
              const analysis = await analysisResponse.json()
              setAnalysisResult(analysis)
              setActiveTab('analysis')
            } catch (error) {
              console.error('Failed to fetch analysis:', error)
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll job status:', error)
        clearInterval(interval)
      }
    }, 2000) // Poll every 2 seconds
    
    // Cleanup after 5 minutes
    setTimeout(() => clearInterval(interval), 5 * 60 * 1000)
  }

  // Analyze video without processing
  const analyzeVideo = async () => {
    if (!videoUrl && !videoFile) {
      alert('Please provide a video URL or file')
      return
    }
    
    setIsLoading(true)
    
    try {
      const requestBody = {
        source_url: videoUrl || URL.createObjectURL(videoFile!),
        target_platform: targetPlatform,
        analyze_content: true,
        detect_scenes: true,
        check_copyright: true,
      }
      
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      })
      
      const result = await response.json()
      setAnalysisResult(result)
      setActiveTab('analysis')
      
    } catch (error) {
      console.error('Failed to analyze video:', error)
      alert('Failed to analyze video. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  // Download processed video
  const downloadVideo = async (jobId: string, filename: string) => {
    try {
      const response = await fetch(`/api/processed/${filename}`)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download video:', error)
      alert('Failed to download video.')
    }
  }

  // Get platform icon
  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'tiktok': return '🎵'
      case 'youtube': return '▶️'
      case 'facebook': return '📘'
      case 'instagram': return '📷'
      case 'douyin': return '🎵'
      case 'twitter': return '🐦'
      default: return '🎬'
    }
  }

  // Get status color
  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed': return 'bg-green-500'
      case 'failed': return 'bg-red-500'
      case 'processing': return 'bg-blue-500'
      default: return 'bg-yellow-500'
    }
  }

  return (
    <div className="min-h-screen p-4 text-white bg-gradient-to-br from-gray-900 to-black md:p-6">
      {/* Header */}
      <header className="mb-8">
        <h1 className="mb-2 text-3xl font-bold md:text-4xl">
          <span className="text-transparent bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text">
            AI Video Editor Pro
          </span>
        </h1>
        <p className="text-gray-400">Transform videos for any platform with AI-powered editing</p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column - Upload & Settings */}
        <div className="space-y-6 lg:col-span-2">
          {/* Upload Card */}
          <div className="p-6 border bg-gray-800/50 backdrop-blur-sm rounded-xl border-gray-700/50">
            <div className="flex items-center gap-3 mb-6">
              <Upload className="text-blue-400" />
              <h2 className="text-xl font-semibold">Upload Video</h2>
            </div>

            <div className="space-y-4">
              {/* URL Input */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <Link size={16} />
                  Video URL
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    placeholder="https://tiktok.com/@user/video/123456"
                    className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleUrlSubmit}
                    className="px-4 py-3 font-medium transition-colors bg-blue-500 rounded-lg hover:bg-blue-600"
                  >
                    Load
                  </button>
                </div>
              </div>

              {/* File Upload */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <Video size={16} />
                  Or Upload File
                </label>
                <div
                  className="p-8 text-center transition-colors border-2 border-gray-700 border-dashed cursor-pointer rounded-xl hover:border-blue-500"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Upload className="mx-auto mb-3 text-gray-400" size={32} />
                  <p className="text-gray-400">Click to upload video file</p>
                  <p className="mt-1 text-sm text-gray-500">MP4, MOV, AVI, MKV up to 500MB</p>
                  {videoFile && (
                    <p className="mt-2 text-green-400">{videoFile.name}</p>
                  )}
                </div>
              </div>

              {/* Video Preview */}
              {videoPreview && (
                <div className="space-y-2">
                  <label className="text-sm text-gray-300">Preview</label>
                  <div className="relative overflow-hidden bg-black rounded-lg">
                    <video
                      src={videoPreview}
                      controls
                      className="object-contain w-full h-48"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Settings Card */}
          <div className="p-6 border bg-gray-800/50 backdrop-blur-sm rounded-xl border-gray-700/50">
            <div className="flex items-center gap-3 mb-6">
              <Settings className="text-purple-400" />
              <h2 className="text-xl font-semibold">Editing Settings</h2>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {/* Platform Selection */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <Globe size={16} />
                  Target Platform
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {platformSettings.map((platform) => (
                    <button
                      key={platform.platform}
                      onClick={() => setTargetPlatform(platform.platform)}
                      className={`p-3 rounded-lg flex flex-col items-center justify-center gap-2 transition-all ${targetPlatform === platform.platform ? 'bg-blue-500/20 border border-blue-500' : 'bg-gray-900 hover:bg-gray-800'}`}
                    >
                      <span className="text-2xl">{getPlatformIcon(platform.platform)}</span>
                      <span className="text-sm">{platform.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Video Type */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <Film size={16} />
                  Video Type
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(['short', 'highlight', 'viral', 'meme', 'full', 'reel'] as VideoType[]).map((type) => (
                    <button
                      key={type}
                      onClick={() => setVideoType(type)}
                      className={`p-3 rounded-lg text-center transition-all ${videoType === type ? 'bg-purple-500/20 border border-purple-500' : 'bg-gray-900 hover:bg-gray-800'}`}
                    >
                      <span className="text-sm capitalize">{type}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration */}
              <div className="space-y-3">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <Clock size={16} />
                  Duration: {duration}s
                </label>
                <input
                  type="range"
                  min="5"
                  max="600"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>5s</span>
                  <span>60s</span>
                  <span>600s</span>
                </div>
              </div>

              {/* Editing Options */}
              <div className="space-y-4">
                <label className="text-sm text-gray-300">Editing Options</label>
                <div className="space-y-3">
                  {[
                    { label: 'Add Subtitles', icon: Type, checked: addSubtitles, setter: setAddSubtitles },
                    { label: 'Change Music', icon: Music, checked: changeMusic, setter: setChangeMusic },
                    { label: 'Remove Watermark', icon: Scissors, checked: removeWatermark, setter: setRemoveWatermark },
                    { label: 'Add Effects', icon: Sparkles, checked: addEffects, setter: setAddEffects },
                  ].map((option) => (
                    <label key={option.label} className="flex items-center justify-between p-3 bg-gray-900 rounded-lg cursor-pointer hover:bg-gray-800">
                      <div className="flex items-center gap-3">
                        <option.icon size={18} className="text-gray-400" />
                        <span>{option.label}</span>
                      </div>
                      <div className="relative">
                        <input
                          type="checkbox"
                          checked={option.checked}
                          onChange={(e) => option.setter(e.target.checked)}
                          className="sr-only"
                        />
                        <div className={`w-10 h-6 rounded-full transition-colors ${option.checked ? 'bg-blue-500' : 'bg-gray-700'}`}>
                          <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${option.checked ? 'translate-x-5' : 'translate-x-1'}`} />
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3 pt-6 mt-8 border-t border-gray-700/50">
              <button
                onClick={analyzeVideo}
                disabled={isLoading || (!videoUrl && !videoFile)}
                className="flex items-center justify-center flex-1 gap-2 px-6 py-3 font-medium transition-colors bg-gray-800 rounded-lg md:flex-none hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <BarChart size={18} />
                Analyze Only
              </button>
              <button
                onClick={createJob}
                disabled={isLoading || (!videoUrl && !videoFile)}
                className="flex items-center justify-center flex-1 gap-2 px-6 py-3 font-medium transition-all rounded-lg md:flex-none bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Zap size={18} />
                {isLoading ? 'Processing...' : 'Start Editing'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Jobs & Results */}
        <div className="space-y-6">
          {/* Tabs */}
          <div className="border bg-gray-800/50 backdrop-blur-sm rounded-xl border-gray-700/50">
            <div className="flex border-b border-gray-700/50">
              {[
                { id: 'jobs', label: 'Jobs', icon: Film },
                { id: 'analysis', label: 'Analysis', icon: BarChart },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${activeTab === tab.id ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400 hover:text-white'}`}
                >
                  <tab.icon size={16} />
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Jobs List */}
            {activeTab === 'jobs' && (
              <div className="max-h-[600px] overflow-y-auto p-4">
                {jobs.length === 0 ? (
                  <div className="py-8 text-center text-gray-500">
                    <Film className="mx-auto mb-3" size={32} />
                    <p>No jobs yet</p>
                    <p className="text-sm">Upload a video to get started</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {jobs.map((job) => (
                      <div
                        key={job.id}
                        onClick={() => setSelectedJob(job)}
                        className={`p-4 rounded-lg cursor-pointer transition-all ${selectedJob?.id === job.id ? 'bg-blue-500/10 border border-blue-500/30' : 'bg-gray-900 hover:bg-gray-800'}`}
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{getPlatformIcon(job.target_platform)}</span>
                            <div>
                              <h3 className="font-medium truncate max-w-[180px]">{job.title}</h3>
                              <p className="text-xs text-gray-400 capitalize">{job.video_type} • {job.target_platform}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${getStatusColor(job.status)}`} />
                            <span className="text-xs capitalize">{job.status}</span>
                          </div>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between text-xs text-gray-400">
                            <span>{job.current_step}</span>
                            <span>{job.progress}%</span>
                          </div>
                          <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className="h-full transition-all bg-gradient-to-r from-blue-500 to-purple-500"
                              style={{ width: `${job.progress}%` }}
                            />
                          </div>
                          
                          {job.status === 'completed' && job.output_filename && (
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                downloadVideo(job.id, job.output_filename!)
                              }}
                              className="flex items-center justify-center w-full gap-2 py-2 mt-2 text-sm text-green-400 transition-colors rounded-lg bg-green-500/20 hover:bg-green-500/30"
                            >
                              <Download size={14} />
                              Download Video
                            </button>
                          )}
                          
                          {job.status === 'failed' && (
                            <div className="flex items-center gap-2 text-sm text-red-400">
                              <AlertCircle size={14} />
                              <span className="truncate">{job.error_message}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Analysis Results */}
            {activeTab === 'analysis' && analysisResult && (
              <div className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
                {/* Summary */}
                <div className="space-y-3">
                  <h3 className="flex items-center gap-2 font-semibold">
                    <FileText size={16} />
                    Summary
                  </h3>
                  <p className="text-sm text-gray-300">{analysisResult.summary}</p>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-gray-900 rounded-lg">
                      <p className="text-xs text-gray-400">Category</p>
                      <p className="font-medium capitalize">{analysisResult.category}</p>
                    </div>
                    <div className="p-3 bg-gray-900 rounded-lg">
                      <p className="text-xs text-gray-400">Mood</p>
                      <p className="font-medium capitalize">{analysisResult.mood}</p>
                    </div>
                    <div className="p-3 bg-gray-900 rounded-lg">
                      <p className="text-xs text-gray-400">Viral Score</p>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 overflow-hidden bg-gray-800 rounded-full">
                          <div
                            className="h-full bg-gradient-to-r from-green-500 to-yellow-500"
                            style={{ width: `${analysisResult.viral_score}%` }}
                          />
                        </div>
                        <span className="font-medium">{analysisResult.viral_score}%</span>
                      </div>
                    </div>
                    <div className="p-3 bg-gray-900 rounded-lg">
                      <p className="text-xs text-gray-400">Duration</p>
                      <p className="font-medium">{analysisResult.duration}s</p>
                    </div>
                  </div>
                </div>

                {/* Key Moments */}
                {analysisResult.key_moments?.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-semibold">Key Moments</h3>
                    <div className="space-y-2">
                      {analysisResult.key_moments.slice(0, 3).map((moment: any, index: number) => (
                        <div key={index} className="p-3 bg-gray-900 rounded-lg">
                          <div className="flex items-start justify-between mb-2">
                            <span className="text-sm font-medium">{moment.description}</span>
                            <span className="px-2 py-1 text-xs text-blue-400 rounded bg-blue-500/20">
                              {moment.start}s - {moment.end}s
                            </span>
                          </div>
                          <p className="text-xs text-gray-400">{moment.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Hashtags */}
                {analysisResult.hashtags?.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="flex items-center gap-2 font-semibold">
                      <Hash size={16} />
                      Hashtags
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {analysisResult.hashtags.map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="bg-gray-900 hover:bg-gray-800 px-3 py-1.5 rounded-lg text-sm transition-colors cursor-pointer"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Copyright Risks */}
                {analysisResult.copyright_risks?.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="flex items-center gap-2 font-semibold text-red-400">
                      <AlertCircle size={16} />
                      Copyright Risks
                    </h3>
                    <div className="space-y-2">
                      {analysisResult.copyright_risks.map((risk: any, index: number) => (
                        <div key={index} className="p-3 border rounded-lg bg-red-500/10 border-red-500/30">
                          <div className="flex items-start justify-between mb-1">
                            <span className="text-sm font-medium capitalize">{risk.type}</span>
                            <span className="px-2 py-1 text-xs text-red-400 capitalize rounded bg-red-500/20">
                              {risk.severity}
                            </span>
                          </div>
                          <p className="text-xs text-gray-300">{risk.description}</p>
                          <p className="mt-2 text-xs text-red-400">{risk.suggestion}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Platform Info */}
          {platformSettings.length > 0 && (
            <div className="p-4 border bg-gray-800/50 backdrop-blur-sm rounded-xl border-gray-700/50">
              <h3 className="flex items-center gap-2 mb-3 font-semibold">
                <Globe size={16} />
                Platform Requirements
              </h3>
              
              {platformSettings
                .filter(p => p.platform === targetPlatform)
                .map((platform) => (
                  <div key={platform.platform} className="space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getPlatformIcon(platform.platform)}</span>
                      <div>
                        <h4 className="font-medium">{platform.name}</h4>
                        <p className="text-xs text-gray-400">Max duration: {platform.max_duration}s</p>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 bg-gray-900 rounded">
                        <p className="text-xs text-gray-400">Aspect Ratio</p>
                        <p className="text-sm">{platform.aspect_ratios.join(', ')}</p>
                      </div>
                      <div className="p-2 bg-gray-900 rounded">
                        <p className="text-xs text-gray-400">Max Size</p>
                        <p className="text-sm">{platform.max_size_mb}MB</p>
                      </div>
                    </div>
                    
                    <div className="p-2 bg-gray-900 rounded">
                      <p className="text-xs text-gray-400">Copyright</p>
                      <p className="text-sm capitalize">{platform.copyright_strictness}</p>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Footer Stats */}
      <div className="pt-6 mt-8 border-t border-gray-800/50">
        <div className="flex flex-wrap items-center justify-between text-sm text-gray-400">
          <div className="flex items-center gap-4">
            <span>Total Jobs: {jobs.length}</span>
            <span>Completed: {jobs.filter(j => j.status === 'completed').length}</span>
            <span>Active: {jobs.filter(j => ['pending', 'downloading', 'analyzing', 'processing'].includes(j.status)).length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span>API Status: Online</span>
          </div>
        </div>
      </div>
    </div>
  )
}