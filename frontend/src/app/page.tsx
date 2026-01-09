'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  Upload, Scissors, RotateCw, Type, Volume2, Film, 
  Image, Sparkles, Download, Play, Pause, Settings,
  Grid3X3, Zap, Palette, Music, MessageSquare,
  Clock, Users, Eye, Share2, Save, Heart
} from 'lucide-react'

export default function VideoEditor() {
  // State quản lý video và các tính năng
  const [videoFile, setVideoFile] = useState<File | null>(null)
  const [videoUrl, setVideoUrl] = useState<string>('')
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [activeTool, setActiveTool] = useState<string>('trim')
  const [editorSettings, setEditorSettings] = useState({
    brightness: 100,
    contrast: 100,
    saturation: 100,
    volume: 80,
    playbackSpeed: 1.0,
    aspectRatio: '16:9'
  })
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Các tính năng chỉnh sửa theo thư mục [citation:1][citation:3][citation:5]
  const editingFeatures = {
    basic: [
      { id: 'trim', name: 'Cắt video', icon: <Scissors size={20} />, desc: 'Cắt và chia nhỏ video' },
      { id: 'rotate', name: 'Xoay & Crop', icon: <RotateCw size={20} />, desc: 'Điều chỉnh hướng và khung hình' },
      { id: 'speed', name: 'Tốc độ', icon: <Zap size={20} />, desc: 'Điều chỉnh tốc độ phát' },
      { id: 'volume', name: 'Âm thanh', icon: <Volume2 size={20} />, desc: 'Chỉnh âm lượng và hiệu ứng' }
    ],
    enhance: [
      { id: 'text', name: 'Thêm chữ', icon: <Type size={20} />, desc: 'Chèn tiêu đề và phụ đề' },
      { id: 'filters', name: 'Bộ lọc', icon: <Image size={20} />, desc: 'Áp dụng bộ lọc màu sắc' },
      { id: 'effects', name: 'Hiệu ứng', icon: <Film size={20} />, desc: 'Hiệu ứng chuyển cảnh & động' },
      { id: 'color', name: 'Màu sắc', icon: <Palette size={20} />, desc: 'Chỉnh độ sáng, tương phản' }
    ],
    aiTools: [
      { id: 'ai-enhance', name: 'Nâng cấp AI', icon: <Sparkles size={20} />, desc: 'Tự động cải thiện chất lượng' },
      { id: 'background', name: 'Xóa phông', icon: <Grid3X3 size={20} />, desc: 'Xóa hoặc thay đổi nền' },
      { id: 'auto-sub', name: 'Phụ đề tự động', icon: <MessageSquare size={20} />, desc: 'Tạo phụ đề thông minh' },
      { id: 'music', name: 'Nhạc nền AI', icon: <Music size={20} />, desc: 'Gợi ý nhạc phù hợp' }
    ]
  }

  // Xử lý upload video
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file && file.type.startsWith('video/')) {
      setVideoFile(file)
      const url = URL.createObjectURL(file)
      setVideoUrl(url)
    }
  }

  // Điều khiển video
  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause()
      } else {
        videoRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  // Cập nhật timeline
  const handleTimeUpdate = () => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime)
    }
  }

  // Định dạng thời gian
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`
  }

  // Xử lý thay đổi cài đặt
  const handleSettingChange = (key: string, value: number | string) => {
    setEditorSettings(prev => ({ ...prev, [key]: value }))
    
    // Áp dụng thay đổi lên video
    if (videoRef.current && key === 'volume') {
      videoRef.current.volume = (value as number) / 100
    }
  }

  // Xuất video
  const handleExport = () => {
    // Gọi API export từ backend
    alert(`Xuất video với cài đặt: ${JSON.stringify(editorSettings)}`)
  }

  return (
    <div className="min-h-screen p-4 text-gray-100 bg-gradient-to-br from-gray-900 to-black md:p-6">
      {/* Header */}
      <header className="flex flex-col items-start justify-between gap-4 mb-6 md:flex-row md:items-center md:mb-8">
        <div>
          <h1 className="text-2xl font-bold text-transparent md:text-3xl bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text">
            Video Editor Pro
          </h1>
          <p className="text-sm text-gray-400 md:text-base">Công cụ chỉnh sửa video chuyên nghiệp & dễ sử dụng</p>
        </div>
        
        <div className="flex flex-wrap gap-2 md:gap-3">
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 px-4 py-2 md:px-5 md:py-2.5 rounded-lg font-medium transition-all duration-200"
          >
            <Upload size={18} />
            Tải video lên
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          
          <button 
            onClick={handleExport}
            disabled={!videoFile}
            className={`flex items-center gap-2 px-4 py-2 md:px-5 md:py-2.5 rounded-lg font-medium transition-all duration-200 ${!videoFile ? 'bg-gray-700 cursor-not-allowed' : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700'}`}
          >
            <Download size={18} />
            Xuất video
          </button>
          
          <button className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-3 py-2 md:px-4 md:py-2.5 rounded-lg transition-colors duration-200">
            <Settings size={18} />
            <span className="hidden md:inline">Cài đặt</span>
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Sidebar trái - Công cụ chỉnh sửa */}
        <div className="space-y-6 lg:col-span-1">
          {/* Nhóm công cụ cơ bản */}
          <div className="p-4 border bg-gray-800/50 backdrop-blur-sm rounded-xl border-gray-700/50">
            <h3 className="flex items-center gap-2 mb-3 text-lg font-semibold">
              <Scissors size={18} />
              Công cụ cơ bản
            </h3>
            <div className="space-y-2">
              {editingFeatures.basic.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTool(tool.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${activeTool === tool.id ? 'bg-gradient-to-r from-blue-500/20 to-blue-600/20 border border-blue-500/30' : 'hover:bg-gray-700/50'}`}
                >
                  <div className={`p-2 rounded-md ${activeTool === tool.id ? 'bg-blue-500' : 'bg-gray-700'}`}>
                    {tool.icon}
                  </div>
                  <div className="text-left">
                    <div className="font-medium">{tool.name}</div>
                    <div className="text-xs text-gray-400">{tool.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Nhóm công cụ nâng cao */}
          <div className="p-4 border bg-gray-800/50 backdrop-blur-sm rounded-xl border-gray-700/50">
            <h3 className="flex items-center gap-2 mb-3 text-lg font-semibold">
              <Film size={18} />
              Nâng cao
            </h3>
            <div className="space-y-2">
              {editingFeatures.enhance.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTool(tool.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${activeTool === tool.id ? 'bg-gradient-to-r from-purple-500/20 to-purple-600/20 border border-purple-500/30' : 'hover:bg-gray-700/50'}`}
                >
                  <div className={`p-2 rounded-md ${activeTool === tool.id ? 'bg-purple-500' : 'bg-gray-700'}`}>
                    {tool.icon}
                  </div>
                  <div className="text-left">
                    <div className="font-medium">{tool.name}</div>
                    <div className="text-xs text-gray-400">{tool.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Công cụ AI [citation:1][citation:6] */}
          <div className="p-4 border bg-gradient-to-br from-purple-900/30 to-blue-900/30 backdrop-blur-sm rounded-xl border-purple-500/30">
            <h3 className="flex items-center gap-2 mb-3 text-lg font-semibold">
              <Sparkles size={18} />
              Công cụ AI
            </h3>
            <p className="mb-3 text-sm text-gray-300">Sức mạnh trí tuệ nhân tạo cho video của bạn</p>
            <div className="space-y-2">
              {editingFeatures.aiTools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => setActiveTool(tool.id)}
                  className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all duration-200 ${activeTool === tool.id ? 'bg-gradient-to-r from-purple-600/40 to-pink-600/40 border border-purple-400/50' : 'hover:bg-white/5'}`}
                >
                  <div className={`p-2 rounded-md ${activeTool === tool.id ? 'bg-gradient-to-r from-purple-500 to-pink-500' : 'bg-gray-700/70'}`}>
                    {tool.icon}
                  </div>
                  <div className="text-left">
                    <div className="font-medium">{tool.name}</div>
                    <div className="text-xs text-gray-300">{tool.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Khu vực chính - Preview và Timeline */}
        <div className="space-y-6 lg:col-span-3">
          {/* Khu vực preview video */}
          <div className="p-4 border bg-gray-900/80 backdrop-blur-sm rounded-2xl md:p-6 border-gray-700/50">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Preview</h2>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Clock size={16} />
                <span>{formatTime(currentTime)} / {formatTime(duration)}</span>
              </div>
            </div>
            
            <div className="relative flex items-center justify-center overflow-hidden bg-black rounded-xl aspect-video">
              {videoUrl ? (
                <>
                  <video
                    ref={videoRef}
                    src={videoUrl}
                    onTimeUpdate={handleTimeUpdate}
                    onLoadedMetadata={(e) => setDuration(e.currentTarget.duration)}
                    className="w-full h-full"
                  />
                  <button
                    onClick={handlePlayPause}
                    className="absolute inset-0 flex items-center justify-center transition-colors bg-black/30 hover:bg-black/40"
                  >
                    <div className="p-4 transition-colors rounded-full bg-black/60 hover:bg-black/80">
                      {isPlaying ? <Pause size={32} /> : <Play size={32} />}
                    </div>
                  </button>
                </>
              ) : (
                <div className="p-8 text-center">
                  <div className="inline-block p-6 mb-4 bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl">
                    <Film size={48} className="text-gray-500" />
                  </div>
                  <p className="mb-4 text-gray-400">Chưa có video nào được tải lên</p>
                  <button 
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center gap-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 px-5 py-2.5 rounded-lg font-medium transition-all duration-200"
                  >
                    <Upload size={18} />
                    Tải video lên để bắt đầu chỉnh sửa
                  </button>
                </div>
              )}
            </div>

            {/* Thanh điều khiển video */}
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-4">
                  <button 
                    onClick={handlePlayPause}
                    className="flex items-center gap-2 px-4 py-2 transition-colors bg-gray-800 rounded-lg hover:bg-gray-700"
                  >
                    {isPlaying ? <Pause size={18} /> : <Play size={18} />}
                    {isPlaying ? 'Tạm dừng' : 'Phát'}
                  </button>
                  
                  <div className="flex items-center gap-2">
                    <Volume2 size={18} />
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={editorSettings.volume}
                      onChange={(e) => handleSettingChange('volume', parseInt(e.target.value))}
                      className="w-24 accent-blue-500"
                    />
                  </div>
                </div>
                
                <div className="text-sm text-gray-400">
                  Tỷ lệ: {editorSettings.aspectRatio}
                </div>
              </div>
              
              {/* Timeline */}
              <div className="space-y-2">
                <div className="h-2 overflow-hidden bg-gray-800 rounded-full">
                  <div 
                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                    style={{ width: `${(currentTime / duration) * 100 || 0}%` }}
                  />
                </div>
                <div className="flex justify-between text-sm text-gray-400">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Cài đặt chi tiết cho công cụ đang chọn */}
          <div className="p-4 border bg-gray-800/50 backdrop-blur-sm rounded-xl md:p-6 border-gray-700/50">
            <h3 className="flex items-center gap-2 mb-4 text-lg font-semibold">
              <Settings size={18} />
              Cài đặt chi tiết
            </h3>
            
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              {/* Độ sáng */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-400">
                  <Eye size={14} />
                  Độ sáng
                </label>
                <div className="flex items-center gap-3">
                  <span className="text-xs">0</span>
                  <input
                    type="range"
                    min="0"
                    max="200"
                    value={editorSettings.brightness}
                    onChange={(e) => handleSettingChange('brightness', parseInt(e.target.value))}
                    className="flex-1 accent-blue-500"
                  />
                  <span className="text-xs">200%</span>
                </div>
                <div className="text-sm text-right">{editorSettings.brightness}%</div>
              </div>

              {/* Độ tương phản */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-400">
                  <Image size={14} />
                  Độ tương phản
                </label>
                <div className="flex items-center gap-3">
                  <span className="text-xs">0</span>
                  <input
                    type="range"
                    min="0"
                    max="200"
                    value={editorSettings.contrast}
                    onChange={(e) => handleSettingChange('contrast', parseInt(e.target.value))}
                    className="flex-1 accent-purple-500"
                  />
                  <span className="text-xs">200%</span>
                </div>
                <div className="text-sm text-right">{editorSettings.contrast}%</div>
              </div>

              {/* Tốc độ phát */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-400">
                  <Zap size={14} />
                  Tốc độ
                </label>
                <select
                  value={editorSettings.playbackSpeed}
                  onChange={(e) => handleSettingChange('playbackSpeed', parseFloat(e.target.value))}
                  className="w-full px-3 py-2 text-sm bg-gray-900 border border-gray-700 rounded-lg"
                >
                  <option value="0.25">0.25x (Rất chậm)</option>
                  <option value="0.5">0.5x (Chậm)</option>
                  <option value="0.75">0.75x (Hơi chậm)</option>
                  <option value="1.0">1.0x (Bình thường)</option>
                  <option value="1.5">1.5x (Nhanh)</option>
                  <option value="2.0">2.0x (Rất nhanh)</option>
                </select>
              </div>

              {/* Tỷ lệ khung hình [citation:3] */}
              <div className="space-y-2">
                <label className="flex items-center gap-2 text-sm text-gray-400">
                  <Grid3X3 size={14} />
                  Tỷ lệ
                </label>
                <select
                  value={editorSettings.aspectRatio}
                  onChange={(e) => handleSettingChange('aspectRatio', e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-gray-900 border border-gray-700 rounded-lg"
                >
                  <option value="16:9">16:9 (YouTube)</option>
                  <option value="9:16">9:16 (TikTok/Reels)</option>
                  <option value="1:1">1:1 (Instagram)</option>
                  <option value="4:5">4:5 (Facebook)</option>
                  <option value="21:9">21:9 (Cinema)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Thanh công cụ nhanh */}
          <div className="flex flex-wrap gap-3">
            <button className="flex items-center justify-center flex-1 gap-2 px-4 py-3 transition-colors duration-200 bg-gray-800 md:flex-none hover:bg-gray-700 rounded-xl">
              <Save size={18} />
              Lưu dự án
            </button>
            <button className="flex items-center justify-center flex-1 gap-2 px-4 py-3 transition-colors duration-200 bg-gray-800 md:flex-none hover:bg-gray-700 rounded-xl">
              <Users size={18} />
              Chia sẻ
            </button>
            <button className="flex items-center justify-center flex-1 gap-2 px-4 py-3 transition-colors duration-200 bg-gray-800 md:flex-none hover:bg-gray-700 rounded-xl">
              <Share2 size={18} />
              Xuất ra MXH
            </button>
            <button className="flex items-center justify-center flex-1 gap-2 px-4 py-3 transition-all duration-200 md:flex-none bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 rounded-xl">
              <Heart size={18} />
              Yêu thích
            </button>
          </div>
        </div>
      </div>

      {/* Thông tin thêm */}
      <div className="mt-8 text-sm text-center text-gray-500">
        <p>Video Editor Pro • Hỗ trợ đa định dạng • Không giới hạn thời lượng • Xuất không watermark [citation:3]</p>
        <p className="mt-1">Sử dụng AI để tự động hóa quy trình chỉnh sửa và tạo video chuyên nghiệp [citation:1][citation:6]</p>
      </div>
    </div>
  )
}