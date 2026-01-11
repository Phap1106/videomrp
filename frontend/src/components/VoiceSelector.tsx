'use client';

import { useEffect, useState } from 'react';
import { Volume2, Play, Pause, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import { useAppStore } from '@/lib/store';
import clsx from 'clsx';

export interface Voice {
  id: string;
  name: string;
  gender: string;
  language: string;
}

interface VoiceSelectorProps {
  onVoiceSelect?:  (voiceId: string) => void;
  aiProvider?: string;
}

export function VoiceSelector({ onVoiceSelect, aiProvider }: VoiceSelectorProps) {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewing, setPreviewing] = useState<string | null>(null);
  const [playingVoice, setPlayingVoice] = useState<string | null>(null);
  const [audioElement, setAudioElement] = useState<HTMLAudioElement | null>(null);

  const selectedVoice = useAppStore((state) => state.selectedVoice);
  const setSelectedVoice = useAppStore((state) => state.setSelectedVoice);

  useEffect(() => {
    const loadVoices = async () => {
      try {
        setLoading(true);
        const voiceList = await apiClient.getAvailableVoices(aiProvider);
        setVoices(Array.isArray(voiceList) ? voiceList : []);
      } catch (error) {
        console.error('Error loading voices:', error);
        toast.error('Failed to load voices');
      } finally {
        setLoading(false);
      }
    };

    loadVoices();
  }, [aiProvider]);

  const handleVoiceSelect = (voiceId: string) => {
    setSelectedVoice(voiceId);
    onVoiceSelect?.(voiceId);
    toast.success('Voice selected');
  };

  const handlePreviewVoice = async (voiceId: string) => {
    try {
      setPreviewing(voiceId);
      const audioBlob = await apiClient.previewVoice(voiceId, undefined, aiProvider);
      const audioUrl = URL.createObjectURL(audioBlob);

      if (audioElement) {
        audioElement.pause();
      }

      const audio = new Audio(audioUrl);
      setAudioElement(audio);
      setPlayingVoice(voiceId);
      
      audio.play().catch((err) => {
        console.error('Error playing audio:', err);
        toast.error('Failed to play preview');
      });

      audio.onended = () => {
        setPlayingVoice(null);
      };
    } catch (error) {
      console.error('Preview error:', error);
      toast.error('Failed to preview voice');
    } finally {
      setPreviewing(null);
    }
  };

  const handleStopPreview = () => {
    if (audioElement) {
      audioElement.pause();
      setPlayingVoice(null);
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-4">
        <Volume2 className="w-5 h-5 text-purple-500" />
        <h3 className="text-lg font-semibold">Chọn Giọng AI</h3>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader className="w-6 h-6 text-purple-500 animate-spin" />
          <span className="ml-2">Đang tải danh sách giọng nói...</span>
        </div>
      ) : voices.length === 0 ? (
        <div className="py-8 text-center text-gray-400">
          <p>Không có giọng nói nào khả dụng</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 grid-cols-2 gap-4 md: lg:grid-cols-3">
          {voices. map((voice) => (
            <div
              key={voice. id}
              className={clsx(
                'p-4 border-2 rounded-lg cursor-pointer transition-all',
                selectedVoice === voice.id
                  ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-purple-300'
              )}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 dark:text-white">{voice.name}</h4>
                  <div className="flex gap-2 mt-1 text-xs text-gray-600 dark:text-gray-400">
                    <span className="px-2 py-1 bg-gray-100 rounded dark:bg-gray-800">
                      {voice.gender}
                    </span>
                    <span className="px-2 py-1 bg-gray-100 bg-gray-800 rounded dark:">
                      {voice.language}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => {
                    if (playingVoice === voice.id) {
                      handleStopPreview();
                    } else {
                      handlePreviewVoice(voice.id);
                    }
                  }}
                  disabled={previewing === voice.id}
                  className={clsx(
                    'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded text-sm font-medium transition-colors',
                    playingVoice === voice.id
                      ? 'bg-purple-600 text-white'
                      : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200'
                  )}
                >
                  {previewing === voice.id ? (
                    <Loader className="w-4 h-4 animate-spin" />
                  ) : playingVoice === voice.id ? (
                    <>
                      <Pause className="w-4 h-4" />
                      Dừng
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Nghe
                    </>
                  )}
                </button>

                <button
                  onClick={() => handleVoiceSelect(voice.id)}
                  className={clsx(
                    'flex-1 px-3 py-2 rounded text-sm font-medium transition-colors',
                    selectedVoice === voice.id
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-600'
                  )}
                >
                  {selectedVoice === voice.id ? '✓ Đã chọn' : 'Chọn'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}