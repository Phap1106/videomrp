'use client';

import { useState, useEffect } from 'react';
import { Volume2, Settings, Play, Loader, Check, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import clsx from 'clsx';

interface TTSProvider {
    id: string;
    name: string;
    requires_api_key: boolean;
    supports_vietnamese: boolean;
    is_free: boolean;
    configured: boolean;
}

interface Voice {
    id: string;
    name: string;
    gender: string;
    language: string;
    provider: string;
}

interface TTSSettingsProps {
    onProviderChange?: (provider: string) => void;
    onVoiceChange?: (voice: string) => void;
    selectedProvider?: string;
    selectedVoice?: string;
}

export function TTSSettings({
    onProviderChange,
    onVoiceChange,
    selectedProvider = '',
    selectedVoice = '',
}: TTSSettingsProps) {
    const [providers, setProviders] = useState<TTSProvider[]>([]);
    const [voices, setVoices] = useState<Voice[]>([]);
    const [currentProvider, setCurrentProvider] = useState(selectedProvider);
    const [currentVoice, setCurrentVoice] = useState(selectedVoice);
    const [previewText, setPreviewText] = useState('Xin chào! Đây là bản demo giọng nói.');
    const [isLoadingProviders, setIsLoadingProviders] = useState(true);
    const [isLoadingVoices, setIsLoadingVoices] = useState(false);
    const [isPreviewing, setIsPreviewing] = useState(false);
    const [previewAudio, setPreviewAudio] = useState<HTMLAudioElement | null>(null);

    // Fetch providers on mount
    useEffect(() => {
        fetchProviders();
    }, []);

    // Fetch voices when provider changes
    useEffect(() => {
        if (currentProvider) {
            fetchVoices(currentProvider);
        }
    }, [currentProvider]);

    const fetchProviders = async () => {
        try {
            setIsLoadingProviders(true);
            const response = await fetch('/api/tts/providers');
            const data = await response.json();

            if (data.success) {
                setProviders(data.providers);
                if (!currentProvider && data.default_provider) {
                    setCurrentProvider(data.default_provider);
                }
            }
        } catch (error) {
            console.error('Error fetching providers:', error);
            toast.error('Không thể tải danh sách TTS providers');
        } finally {
            setIsLoadingProviders(false);
        }
    };

    const fetchVoices = async (provider: string) => {
        try {
            setIsLoadingVoices(true);
            const response = await fetch(`/api/tts/voices?provider=${provider}`);
            const data = await response.json();

            if (data.success) {
                setVoices(data.voices);
                // Auto-select first voice
                if (data.voices.length > 0 && !currentVoice) {
                    setCurrentVoice(data.voices[0].id);
                    onVoiceChange?.(data.voices[0].id);
                }
            }
        } catch (error) {
            console.error('Error fetching voices:', error);
        } finally {
            setIsLoadingVoices(false);
        }
    };

    const handleProviderChange = (providerId: string) => {
        setCurrentProvider(providerId);
        setCurrentVoice(''); // Reset voice when provider changes
        onProviderChange?.(providerId);
    };

    const handleVoiceChange = (voiceId: string) => {
        setCurrentVoice(voiceId);
        onVoiceChange?.(voiceId);
    };

    const handlePreview = async () => {
        if (!currentVoice || !previewText.trim()) {
            toast.error('Vui lòng chọn giọng và nhập văn bản');
            return;
        }

        try {
            setIsPreviewing(true);

            // Stop any playing audio
            if (previewAudio) {
                previewAudio.pause();
                previewAudio.currentTime = 0;
            }

            const response = await fetch('/api/tts/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: previewText,
                    voice: currentVoice,
                    ai_provider: currentProvider,
                    speed: 1.0,
                }),
            });

            const data = await response.json();

            if (data.success && data.audio_url) {
                const audio = new Audio(data.audio_url);
                setPreviewAudio(audio);
                audio.play();
                audio.onended = () => setIsPreviewing(false);
                toast.success('Đang phát thử giọng nói');
            } else {
                throw new Error(data.detail || 'Preview failed');
            }
        } catch (error: any) {
            console.error('Preview error:', error);
            toast.error(error.message || 'Lỗi khi phát thử');
        } finally {
            setIsPreviewing(false);
        }
    };

    const getProviderBadge = (provider: TTSProvider) => {
        if (provider.is_free) {
            return (
                <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400">
                    MIỄN PHÍ
                </span>
            );
        }
        if (!provider.configured) {
            return (
                <span className="px-2 py-0.5 text-xs rounded-full bg-yellow-500/20 text-yellow-400">
                    Cần API Key
                </span>
            );
        }
        return null;
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-2">
                <Volume2 className="w-5 h-5 text-purple-400" />
                <h3 className="text-lg font-semibold text-white">Cài đặt TTS</h3>
            </div>

            {/* Provider Selection */}
            <div className="space-y-3">
                <label className="text-sm font-medium text-gray-300">Nhà cung cấp</label>

                {isLoadingProviders ? (
                    <div className="flex items-center gap-2 text-gray-400">
                        <Loader className="w-4 h-4 animate-spin" />
                        <span>Đang tải...</span>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 gap-2">
                        {providers.map((provider) => (
                            <button
                                key={provider.id}
                                onClick={() => handleProviderChange(provider.id)}
                                disabled={provider.requires_api_key && !provider.configured}
                                className={clsx(
                                    'relative flex flex-col items-start p-3 rounded-xl transition-all text-left',
                                    currentProvider === provider.id
                                        ? 'bg-purple-500/20 border-2 border-purple-500'
                                        : provider.requires_api_key && !provider.configured
                                            ? 'bg-white/5 border border-white/10 opacity-50 cursor-not-allowed'
                                            : 'bg-white/5 border border-white/10 hover:bg-white/10'
                                )}
                            >
                                <div className="flex items-center gap-2 w-full">
                                    <span className="font-medium text-sm truncate flex-1">{provider.name}</span>
                                    {currentProvider === provider.id && (
                                        <Check className="w-4 h-4 text-purple-400 flex-shrink-0" />
                                    )}
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                    {getProviderBadge(provider)}
                                    {provider.supports_vietnamese && (
                                        <span className="text-xs text-gray-500">🇻🇳 VI</span>
                                    )}
                                </div>
                            </button>
                        ))}
                    </div>
                )}
            </div>

            {/* Voice Selection */}
            <div className="space-y-3">
                <label className="text-sm font-medium text-gray-300">Giọng nói</label>

                {isLoadingVoices ? (
                    <div className="flex items-center gap-2 text-gray-400">
                        <Loader className="w-4 h-4 animate-spin" />
                        <span>Đang tải giọng...</span>
                    </div>
                ) : voices.length > 0 ? (
                    <div className="max-h-48 overflow-y-auto space-y-1 pr-2 scrollbar-thin">
                        {voices.map((voice) => (
                            <button
                                key={voice.id}
                                onClick={() => handleVoiceChange(voice.id)}
                                className={clsx(
                                    'w-full flex items-center justify-between p-3 rounded-lg transition-all text-left',
                                    currentVoice === voice.id
                                        ? 'bg-purple-500/20 border border-purple-500'
                                        : 'bg-white/5 border border-transparent hover:bg-white/10'
                                )}
                            >
                                <div>
                                    <div className="font-medium text-sm text-white">{voice.name}</div>
                                    <div className="text-xs text-gray-500">
                                        {voice.gender === 'female' ? '👩' : voice.gender === 'male' ? '👨' : '🧑'}
                                        {' '}{voice.language}
                                    </div>
                                </div>
                                {currentVoice === voice.id && (
                                    <Check className="w-4 h-4 text-purple-400" />
                                )}
                            </button>
                        ))}
                    </div>
                ) : (
                    <div className="flex items-center gap-2 p-4 rounded-lg bg-white/5 text-gray-400">
                        <AlertCircle className="w-4 h-4" />
                        <span className="text-sm">Chọn nhà cung cấp để xem danh sách giọng</span>
                    </div>
                )}
            </div>

            {/* Preview */}
            <div className="space-y-3">
                <label className="text-sm font-medium text-gray-300">Nghe thử</label>
                <input
                    type="text"
                    value={previewText}
                    onChange={(e) => setPreviewText(e.target.value)}
                    placeholder="Nhập văn bản để nghe thử..."
                    className="app-control"
                />
                <button
                    onClick={handlePreview}
                    disabled={isPreviewing || !currentVoice}
                    className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition"
                >
                    {isPreviewing ? (
                        <>
                            <Loader className="w-5 h-5 animate-spin" />
                            Đang phát...
                        </>
                    ) : (
                        <>
                            <Play className="w-5 h-5" />
                            Nghe thử giọng nói
                        </>
                    )}
                </button>
            </div>

            {/* Current Selection Info */}
            {currentProvider && currentVoice && (
                <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30">
                    <p className="text-xs text-purple-300">
                        <strong>Đã chọn:</strong> {providers.find(p => p.id === currentProvider)?.name} - {voices.find(v => v.id === currentVoice)?.name}
                    </p>
                </div>
            )}
        </div>
    );
}
