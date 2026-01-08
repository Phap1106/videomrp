'use client';

import { useState, useEffect } from 'react';
import { Video, Clock, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface VideoItem {
  id: string;
  title: string;
  url: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
    processed_url?: string; // optional vì chỉ có khi status là 'completed'
  current_step?: string;  // optional
  progress?: number;      // optional
}

export default function Dashboard() {
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchVideos = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/videos');
      setVideos(response.data);
    } catch (error) {
      console.error('Error fetching videos:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
    // Refresh every 10 seconds
    const interval = setInterval(fetchVideos, 10000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return 'Hoàn thành';
      case 'processing': return 'Đang xử lý';
      case 'failed': return 'Thất bại';
      default: return 'Chờ xử lý';
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Video Dashboard</h2>
        <button
          onClick={fetchVideos}
          className="flex items-center gap-2 px-4 py-2 transition bg-gray-700 rounded-lg hover:bg-gray-600"
        >
          <RefreshCw size={18} />
          Làm mới
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      ) : videos.length === 0 ? (
        <div className="py-12 text-center text-gray-400">
          <Video className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>Chưa có video nào</p>
          <p className="mt-2 text-sm">Thêm video để bắt đầu xử lý</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="px-4 py-3 text-left">Video</th>
                <th className="px-4 py-3 text-left">Trạng thái</th>
                <th className="px-4 py-3 text-left">Thời gian</th>
                <th className="px-4 py-3 text-left">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {videos.map((video) => (
                <tr key={video.id} className="border-b border-gray-800 hover:bg-gray-800/50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-12 h-12 bg-gray-700 rounded-lg">
                        <Video size={24} />
                      </div>
                      <div>
                        <p className="max-w-xs font-medium truncate">{video.title}</p>
                        <p className="max-w-xs text-sm text-gray-400 truncate">{video.url}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(video.status)}
                      <span>{getStatusText(video.status)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-400">
                    {new Date(video.created_at).toLocaleDateString('vi-VN')}
                  </td>
                  <td className="px-4 py-3">
                    {video.status === 'pending' && (
                      <button className="px-4 py-1 text-sm transition bg-blue-600 rounded-lg hover:bg-blue-700">
                        Xử lý
                      </button>
                    )}
                    {video.status === 'completed' && (
                      <button className="px-4 py-1 text-sm transition bg-green-600 rounded-lg hover:bg-green-700">
                        Tải về
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="p-4 mt-8 rounded-lg bg-gray-800/50">
        <h4 className="mb-3 font-semibold">Thống kê</h4>
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="p-4 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400">Tổng video</p>
            <p className="text-2xl font-bold">{videos.length}</p>
          </div>
          <div className="p-4 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400">Đã xử lý</p>
            <p className="text-2xl font-bold text-green-500">
              {videos.filter(v => v.status === 'completed').length}
            </p>
          </div>
          <div className="p-4 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400">Đang xử lý</p>
            <p className="text-2xl font-bold text-blue-500">
              {videos.filter(v => v.status === 'processing').length}
            </p>
          </div>
          <div className="p-4 bg-gray-900 rounded-lg">
            <p className="text-sm text-gray-400">Lỗi</p>
            <p className="text-2xl font-bold text-red-500">
              {videos.filter(v => v.status === 'failed').length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}