'use client';

import { useState, useRef } from 'react';
import { Volume2, Download, Play, Pause } from 'lucide-react';
import axios from 'axios';

export default function TTSGenerator() {
  const [text, setText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    
    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:5000/api/tts', 
        { text },
        { responseType: 'blob' }
      );
      
      const url = URL.createObjectURL(response.data);
      setAudioUrl(url);
    } catch (error) {
      console.error('Error generating TTS:', error);
      alert('Lỗi khi tạo giọng nói');
    } finally {
      setIsLoading(false);
    }
  };

  const togglePlayback = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleDownload = () => {
    if (audioUrl) {
      const a = document.createElement('a');
      a.href = audioUrl;
      a.download = 'tts-output.wav';
      a.click();
    }
  };

  return (
    <div>
      <div className="flex items-center mb-6">
        <Volume2 className="w-8 h-8 mr-3 text-purple-400" />
        <h3 className="text-2xl font-bold">Valtec-TTS Generator</h3>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            Nhập văn bản cần chuyển đổi
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="w-full h-32 p-3 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Nhập văn bản tại đây..."
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={isLoading || !text.trim()}
          className="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg font-semibold hover:opacity-90 transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? 'Đang xử lý...' : 'Tạo giọng nói'}
        </button>

        {audioUrl && (
          <div className="mt-6 p-4 bg-gray-900/50 rounded-lg border border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold">Kết quả</h4>
              <div className="flex gap-2">
                <button
                  onClick={togglePlayback}
                  className="p-2 bg-purple-600 rounded-full hover:bg-purple-700 transition"
                >
                  {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                </button>
                <button
                  onClick={handleDownload}
                  className="p-2 bg-blue-600 rounded-full hover:bg-blue-700 transition"
                >
                  <Download size={20} />
                </button>
              </div>
            </div>
            
            <audio
              ref={audioRef}
              src={audioUrl}
              onEnded={() => setIsPlaying(false)}
              className="w-full"
            />
            
            <div className="mt-4 text-sm text-gray-400">
              <p className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                Sẵn sàng phát
              </p>
              <p className="mt-2">Định dạng: WAV 16kHz</p>
              <p className="text-xs text-gray-500 mt-1">
                Lưu ý: Tập tin sẽ tự động tải về khi nhấn nút Download
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}