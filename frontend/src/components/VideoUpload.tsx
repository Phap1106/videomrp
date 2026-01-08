'use client';

import { useState } from 'react';
import { Upload, Video, Link } from 'lucide-react';
import axios from 'axios';

export default function VideoUpload() {
  const [url, setUrl] = useState('');
  const [title, setTitle] = useState('');
  const [isUploading, setIsUploading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsUploading(true);
    try {
      await axios.post('http://localhost:5000/api/videos', {
        url,
        title: title || `Video ${new Date().toLocaleDateString()}`
      });
      
      setUrl('');
      setTitle('');
      alert('Video đã được thêm thành công!');
    } catch (error) {
      console.error('Error adding video:', error);
      alert('Lỗi khi thêm video');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-2">
            <Link className="inline-block w-4 h-4 mr-2" />
            URL Video (YouTube, TikTok, v.v.)
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full p-3 bg-gray-900 border border-gray-700 rounded-lg"
            placeholder="https://www.youtube.com/watch?v=..."
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            <Video className="inline-block w-4 h-4 mr-2" />
            Tiêu đề (tùy chọn)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-3 bg-gray-900 border border-gray-700 rounded-lg"
            placeholder="Nhập tiêu đề video..."
          />
        </div>

        <button
          type="submit"
          disabled={isUploading || !url.trim()}
          className="flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-green-600 to-emerald-600 rounded-lg font-semibold hover:opacity-90 transition disabled:opacity-50"
        >
          <Upload size={20} />
          {isUploading ? 'Đang tải lên...' : 'Thêm Video'}
        </button>
      </form>

      <div className="mt-6 pt-6 border-t border-gray-700">
        <h4 className="font-semibold mb-3">Hướng dẫn</h4>
        <ul className="text-sm text-gray-400 space-y-2">
          <li>• Hỗ trợ YouTube, TikTok, Facebook Video</li>
          <li>• Video sẽ được tải về và xử lý tự động</li>
          <li>• Sử dụng AI để nâng cấp chất lượng</li>
          <li>• Tích hợp Valtec-TTS cho phụ đề</li>
        </ul>
      </div>
    </div>
  );
}