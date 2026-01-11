'use client';

import { useState } from 'react';
import { Type, Copy, Trash2, Plus } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAppStore } from '@/lib/store';
import clsx from 'clsx';

interface TextSegment {
  id: string;
  startTime: number;
  endTime:  number;
  text: string;
}

export function TextEditor() {
  const [segments, setSegments] = useState<TextSegment[]>([
    { id: '1', startTime: 0, endTime: 5, text: 'Đây là đoạn text đầu tiên' },
  ]);

  const textStyle = useAppStore((state) => state.currentTextOverlayStyle);
  const setTextStyle = useAppStore((state) => state.setCurrentTextOverlayStyle);

  const addSegment = () => {
    const lastSegment = segments[segments.length - 1];
    const newSegment: TextSegment = {
      id: String(Date.now()),
      startTime: lastSegment. endTime,
      endTime: lastSegment.endTime + 5,
      text: 'Đoạn text mới',
    };
    setSegments([...segments, newSegment]);
  };

  const updateSegment = (id: string, updates: Partial<TextSegment>) => {
    setSegments(
      segments.map((seg) =>
        seg.id === id ? { ...seg, ...updates } : seg
      )
    );
  };

  const deleteSegment = (id: string) => {
    if (segments.length === 1) {
      toast.error('Phải có ít nhất 1 đoạn text');
      return;
    }
    setSegments(segments.filter((seg) => seg.id !== id));
  };

  const duplicateSegment = (id: string) => {
    const original = segments.find((seg) => seg.id === id);
    if (!original) return;

    const duplicate: TextSegment = {
      ... original,
      id: String(Date.now()),
      startTime: original.endTime,
      endTime: original.endTime + (original.endTime - original.startTime),
    };

    setSegments([...segments, duplicate]);
  };

  return (
    <div className="space-y-6">
      {/* Styling Options */}
      <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
        <h3 className="flex items-center gap-2 mb-4 text-lg font-semibold">
          <Type className="w-5 h-5" />
          Cài đặt Phông chữ
        </h3>

        <div className="grid grid-cols-1 grid-cols-2 gap-4 md:">
          {/* Font Size */}
          <div>
            <label className="block mb-2 text-sm font-medium">
              Kích thước phông chữ:  {textStyle. fontSize}px
            </label>
            <input
              type="range"
              min="20"
              max="120"
              value={textStyle.fontSize}
              onChange={(e) =>
                setTextStyle({ fontSize: parseInt(e.target.value) })
              }
              className="w-full"
            />
          </div>

          {/* Font Color */}
          <div>
            <label className="block mb-2 text-sm font-medium">
              Màu chữ
            </label>
            <div className="flex gap-2">
              <input
                type="color"
                value={`#${textStyle.fontColor}`}
                onChange={(e) =>
                  setTextStyle({
                    fontColor: e. target.value. substring(1).toUpperCase(),
                  })
                }
                className="w-20 h-10 border rounded cursor-pointer"
              />
              <input
                type="text"
                value={textStyle.fontColor}
                onChange={(e) =>
                  setTextStyle({ fontColor: e.target.value. toUpperCase() })
                }
                className="flex-1 px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700"
                placeholder="FFFFFF"
              />
            </div>
          </div>

          {/* Background Color */}
          <div>
            <label className="block mb-2 text-sm font-medium">
              Màu nền
            </label>
            <div className="flex gap-2">
              <input
                type="color"
                value={`#${textStyle.bgColor}`}
                onChange={(e) =>
                  setTextStyle({
                    bgColor: e.target.value.substring(1).toUpperCase(),
                  })
                }
                className="w-20 h-10 border rounded cursor-pointer"
              />
              <input
                type="text"
                value={textStyle.bgColor}
                onChange={(e) =>
                  setTextStyle({ bgColor: e. target.value.toUpperCase() })
                }
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded dark:"
                placeholder="000000"
              />
            </div>
          </div>

          {/* Position */}
          <div>
            <label className="block mb-2 text-sm font-medium">
              Vị trí
            </label>
            <select
              value={textStyle.position}
              onChange={(e) =>
                setTextStyle({
                  position: e.target.value as 'top' | 'center' | 'bottom',
                })
              }
              className="w-full px-3 py-2 border rounded dark:bg-gray-800 dark:border-gray-700"
            >
              <option value="top">Trên cùng</option>
              <option value="center">Giữa</option>
              <option value="bottom">Dưới cùng</option>
            </select>
          </div>

          {/* Opacity */}
          <div className="md:col-span-2">
            <label className="block mb-2 text-sm font-medium">
              Độ mờ nền:  {Math.round(textStyle.bgAlpha * 100)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={textStyle.bgAlpha}
              onChange={(e) =>
                setTextStyle({ bgAlpha: parseFloat(e.target.value) })
              }
              className="w-full"
            />
          </div>
        </div>

        {/* Preview */}
        <div
          className="p-6 mt-6 text-2xl font-bold text-center rounded"
          style={{
            color: `#${textStyle.fontColor}`,
            backgroundColor: `rgba(0, 0, 0, ${textStyle.bgAlpha})`,
          }}
        >
          Đây là bản xem trước
        </div>
      </div>

      {/* Text Segments */}
      <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Các Đoạn Text</h3>
          <button
            onClick={addSegment}
            className="flex items-center gap-2 px-4 py-2 text-white transition bg-green-600 rounded hover:bg-green-700"
          >
            <Plus className="w-4 h-4" />
            Thêm đoạn
          </button>
        </div>

        <div className="space-y-4">
          {segments.map((segment, index) => (
            <div
              key={segment.id}
              className="p-4 border rounded-lg dark:border-gray-700 dark:bg-gray-800"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="px-3 py-1 text-sm font-medium bg-gray-200 rounded dark:bg-gray-700">
                  Đoạn {index + 1}
                </span>
                <div className="flex gap-2 ml-auto">
                  <button
                    onClick={() => duplicateSegment(segment.id)}
                    className="p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700"
                    title="Sao chép"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteSegment(segment.id)}
                    className="p-2 text-red-600 bg-red-100 rounded hover: dark:hover:bg-red-900/20"
                    title="Xóa"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 gap-3 mb-3 md:grid-cols-3">
                {/* Start Time */}
                <div>
                  <label className="block mb-1 text-xs font-medium">
                    Thời gian bắt đầu (s)
                  </label>
                  <input
                    type="number"
                    value={segment.startTime}
                    onChange={(e) =>
                      updateSegment(segment.id, {
                        startTime: parseFloat(e.target.value),
                      })
                    }
                    min="0"
                    step="0.1"
                    className="w-full px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                {/* End Time */}
                <div>
                  <label className="block mb-1 text-xs font-medium">
                    Thời gian kết thúc (s)
                  </label>
                  <input
                    type="number"
                    value={segment.endTime}
                    onChange={(e) =>
                      updateSegment(segment.id, {
                        endTime: parseFloat(e.target.value),
                      })
                    }
                    min="0"
                    step="0.1"
                    className="w-full px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>

                {/* Duration */}
                <div>
                  <label className="block mb-1 text-xs font-medium">
                    Thời lượng
                  </label>
                  <div className="px-3 py-2 border rounded bg-gray-50 dark:bg-gray-700 dark:border-gray-600">
                    {(segment.endTime - segment.startTime).toFixed(1)}s
                  </div>
                </div>
              </div>

              {/* Text Content */}
              <div>
                <label className="block mb-1 text-xs font-medium">
                  Nội dung text
                </label>
                <textarea
                  value={segment. text}
                  onChange={(e) =>
                    updateSegment(segment.id, { text: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded dark:"
                  rows={2}
                  placeholder="Nhập text tại đây..."
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}