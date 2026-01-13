'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import {
    MessageCircle,
    X,
    Send,
    Loader,
    Download,
    Sparkles,
    Volume2,
    Trash2,
    Bot,
    Mic,
    Minimize2,
    Maximize2
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/lib/api-client';
import clsx from 'clsx';

interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp?: Date;
    audioUrl?: string;
}

interface CollectedInfo {
    style?: string;
    estimated_duration?: number;
    target_audience?: string;
    voice_gender?: string;
    action?: string;
    story_outline?: string;
    [key: string]: any;
}

export function EOAChatbot() {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [collectedInfo, setCollectedInfo] = useState<CollectedInfo>({});
    const [readyToProcess, setReadyToProcess] = useState(false);
    const [generatedAudio, setGeneratedAudio] = useState<{
        url: string;
        storyText: string;
        duration: number;
    } | null>(null);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    // Focus input when chat opens
    useEffect(() => {
        if (isOpen) {
            inputRef.current?.focus();
        }
    }, [isOpen]);

    // Initial greeting
    useEffect(() => {
        if (isOpen && messages.length === 0) {
            setMessages([{
                role: 'assistant',
                content: `👋 **Xin chào! Tôi là EOA - AI Story Creator**

Tôi sẽ giúp bạn tạo nội dung câu chuyện và chuyển thành audio!

🎯 **Để bắt đầu, hãy cho tôi biết:**
• Chủ đề câu chuyện bạn muốn
• Phong cách (hài hước, kịch tính, cảm động...)
• Độ dài mong muốn

💡 *Tip: Gõ **@EOA xử lý** khi bạn muốn tạo audio*`
            }]);
        }
    }, [isOpen, messages.length]);

    const handleSendMessage = useCallback(async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMessage = inputValue.trim();
        setInputValue('');

        const newMessages: ChatMessage[] = [
            ...messages,
            { role: 'user', content: userMessage, timestamp: new Date() }
        ];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            const history = newMessages.map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await apiClient.eoaChat(
                userMessage,
                history.slice(0, -1),
                sessionId || undefined
            );

            if (response.success) {
                if (!sessionId) {
                    setSessionId(response.collected_info?.session_id || `session_${Date.now()}`);
                }

                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: response.message,
                    timestamp: new Date()
                }]);

                if (response.collected_info) {
                    setCollectedInfo(response.collected_info);
                }

                setReadyToProcess(response.ready_to_process || false);
            } else {
                throw new Error('Failed to get response');
            }
        } catch (error) {
            console.error('Chat error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '❌ Xin lỗi, tôi gặp lỗi kết nối. Vui lòng thử lại!'
            }]);
        } finally {
            setIsLoading(false);
        }
    }, [inputValue, messages, isLoading, sessionId]);

    const handleProcessAudio = async () => {
        if (!sessionId || isProcessing) return;

        setIsProcessing(true);
        setMessages(prev => [...prev, {
            role: 'assistant',
            content: '⏳ **Đang tạo câu chuyện và audio...**\n\nQuá trình này có thể mất 30-60 giây.'
        }]);

        try {
            const history = messages.map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await apiClient.eoaProcess(
                sessionId,
                history,
                collectedInfo,
                undefined,
                1.0,
                true
            );

            if (response.success) {
                setGeneratedAudio({
                    url: response.audio_url,
                    storyText: response.story_text,
                    duration: response.duration
                });

                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: `✅ **Hoàn thành!**

📝 **Nội dung:**
"${response.story_text.substring(0, 200)}${response.story_text.length > 200 ? '...' : ''}"

⏱️ Thời lượng: **${Math.round(response.duration)}s**
📊 Số từ: **${response.word_count}** từ`,
                    audioUrl: response.audio_url
                }]);

                toast.success('Đã tạo audio thành công!');
                setReadyToProcess(false);
            } else {
                throw new Error(response.error || 'Processing failed');
            }
        } catch (error: any) {
            console.error('Process error:', error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: `❌ Lỗi: ${error.message || 'Unknown error'}. Vui lòng thử lại!`
            }]);
            toast.error('Lỗi khi tạo audio');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleDownloadAudio = async () => {
        if (!sessionId) return;

        try {
            const blob = await apiClient.eoaDownloadAudio(sessionId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `eoa_story_${sessionId}.mp3`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            toast.success('Đã tải xuống file audio!');
        } catch (error) {
            console.error('Download error:', error);
            toast.error('Lỗi khi tải file');
        }
    };

    const handleClearChat = async () => {
        if (sessionId) {
            try {
                await apiClient.eoaClearSession(sessionId);
            } catch (e) {
                console.error('Clear session error:', e);
            }
        }
        setMessages([]);
        setSessionId(null);
        setCollectedInfo({});
        setReadyToProcess(false);
        setGeneratedAudio(null);
        toast.success('Đã xóa cuộc trò chuyện');
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    // Get window size based on expanded state
    const windowSize = isExpanded
        ? 'w-[600px] h-[700px]'
        : 'w-[450px] h-[600px]';

    return (
        <>
            {/* Floating Button - Premium Design */}
            <button
                onClick={() => setIsOpen(true)}
                className={clsx(
                    'fixed z-50 group',
                    'bottom-8 right-8',
                    isOpen && 'opacity-0 pointer-events-none'
                )}
            >
                {/* Glow effect */}
                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 blur-xl opacity-60 group-hover:opacity-100 transition-opacity animate-pulse" />

                {/* Button */}
                <div className="relative flex items-center gap-3 px-6 py-4 rounded-full bg-gradient-to-r from-purple-600 via-pink-500 to-orange-500 shadow-2xl transform transition-all duration-300 group-hover:scale-105 group-hover:shadow-purple-500/50">
                    <div className="relative">
                        <Bot className="w-7 h-7 text-white" />
                        <Sparkles className="absolute w-4 h-4 text-yellow-300 -top-2 -right-2 animate-bounce" />
                    </div>
                    <span className="font-bold text-white text-lg">EOA Chat</span>

                    {/* Status dot */}
                    <span className="absolute top-2 right-2 w-3 h-3 bg-green-400 rounded-full animate-ping" />
                    <span className="absolute top-2 right-2 w-3 h-3 bg-green-400 rounded-full" />
                </div>
            </button>

            {/* Chat Window - Premium Glass Design */}
            {isOpen && (
                <div
                    className={clsx(
                        'fixed bottom-8 right-8 z-50 flex flex-col',
                        windowSize,
                        'bg-gradient-to-b from-slate-900/95 via-purple-900/20 to-slate-900/95',
                        'backdrop-blur-2xl rounded-3xl shadow-2xl',
                        'border border-white/10',
                        'transform transition-all duration-300',
                        'animate-slideUp'
                    )}
                    style={{
                        boxShadow: '0 25px 50px -12px rgba(139, 92, 246, 0.25), 0 0 100px -20px rgba(236, 72, 153, 0.2)'
                    }}
                >
                    {/* Gradient Border Effect */}
                    <div className="absolute inset-0 rounded-3xl p-[1px] bg-gradient-to-b from-purple-500/50 via-pink-500/20 to-transparent pointer-events-none" />

                    {/* Header */}
                    <div className="relative flex items-center justify-between px-6 py-4 border-b border-white/10">
                        {/* Left - Bot Info */}
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg">
                                    <Bot className="w-7 h-7 text-white" />
                                </div>
                                <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-slate-900 rounded-full" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                    EOA Assistant
                                    <span className="px-2 py-0.5 text-[10px] font-medium bg-gradient-to-r from-amber-400 to-orange-500 text-white rounded-full">
                                        VIP
                                    </span>
                                </h3>
                                <p className="text-sm text-gray-400">AI Story & Audio Creator</p>
                            </div>
                        </div>

                        {/* Right - Controls */}
                        <div className="flex items-center gap-1">
                            <button
                                onClick={() => setIsExpanded(!isExpanded)}
                                className="p-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
                                title={isExpanded ? 'Thu nhỏ' : 'Phóng to'}
                            >
                                {isExpanded ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
                            </button>
                            <button
                                onClick={handleClearChat}
                                className="p-2.5 text-gray-400 hover:text-white hover:bg-white/10 rounded-xl transition-colors"
                                title="Xóa chat"
                            >
                                <Trash2 className="w-5 h-5" />
                            </button>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2.5 text-gray-400 hover:text-white hover:bg-red-500/20 rounded-xl transition-colors"
                                title="Đóng"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Messages Area */}
                    <div className="flex-1 overflow-y-auto p-5 space-y-4 scrollbar-thin">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={clsx(
                                    'flex gap-3',
                                    msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                                )}
                            >
                                {/* Avatar */}
                                {msg.role === 'assistant' && (
                                    <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                                        <Bot className="w-5 h-5 text-white" />
                                    </div>
                                )}

                                {/* Message Bubble */}
                                <div
                                    className={clsx(
                                        'max-w-[80%] rounded-2xl px-5 py-4',
                                        msg.role === 'user'
                                            ? 'bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-br-md shadow-lg shadow-purple-500/20'
                                            : 'bg-white/5 text-gray-200 rounded-bl-md border border-white/10 backdrop-blur'
                                    )}
                                >
                                    <div
                                        className="text-sm leading-relaxed whitespace-pre-wrap break-words prose prose-invert prose-sm max-w-none"
                                        dangerouslySetInnerHTML={{
                                            __html: msg.content
                                                .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>')
                                                .replace(/\*(.*?)\*/g, '<em class="text-gray-300">$1</em>')
                                                .replace(/\n/g, '<br/>')
                                        }}
                                    />

                                    {/* Audio Download Button */}
                                    {msg.audioUrl && (
                                        <button
                                            onClick={handleDownloadAudio}
                                            className="flex items-center gap-2 px-5 py-3 mt-4 text-sm font-semibold text-white bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl hover:from-green-400 hover:to-emerald-500 transition-all shadow-lg shadow-green-500/25"
                                        >
                                            <Download className="w-5 h-5" />
                                            Tải Audio MP3
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* Loading Indicator */}
                        {isLoading && (
                            <div className="flex gap-3">
                                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center animate-pulse">
                                    <Bot className="w-5 h-5 text-white" />
                                </div>
                                <div className="px-5 py-4 bg-white/5 rounded-2xl rounded-bl-md border border-white/10">
                                    <div className="flex items-center gap-2 text-gray-400">
                                        <Loader className="w-4 h-4 animate-spin" />
                                        <span className="text-sm">EOA đang suy nghĩ...</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Action Buttons */}
                    {readyToProcess && !isProcessing && (
                        <div className="px-5 pb-3">
                            <button
                                onClick={handleProcessAudio}
                                className="flex items-center justify-center w-full gap-3 px-5 py-4 font-bold text-white bg-gradient-to-r from-green-500 via-emerald-500 to-teal-500 rounded-2xl hover:opacity-90 transition-all shadow-xl shadow-green-500/30 animate-pulse hover:animate-none"
                            >
                                <Mic className="w-6 h-6" />
                                <span className="text-lg">Tạo Audio Ngay</span>
                                <Sparkles className="w-5 h-5" />
                            </button>
                        </div>
                    )}

                    {isProcessing && (
                        <div className="px-5 pb-3">
                            <div className="flex items-center justify-center gap-3 px-5 py-4 font-bold text-white bg-gradient-to-r from-orange-500 to-amber-500 rounded-2xl">
                                <Loader className="w-6 h-6 animate-spin" />
                                <span className="text-lg">Đang xử lý...</span>
                            </div>
                        </div>
                    )}

                    {/* Input Area */}
                    <div className="p-5 border-t border-white/10 bg-black/20 rounded-b-3xl">
                        <div className="flex items-end gap-3">
                            <div className="flex-1 relative">
                                <textarea
                                    ref={inputRef}
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onKeyDown={handleKeyDown}
                                    placeholder="Nhập tin nhắn của bạn..."
                                    rows={1}
                                    className="w-full px-5 py-4 pr-12 text-sm text-white bg-white/5 border border-white/10 rounded-2xl placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:bg-white/10 resize-none transition-all"
                                    style={{ minHeight: '56px', maxHeight: '120px' }}
                                    disabled={isLoading || isProcessing}
                                />
                            </div>
                            <button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim() || isLoading || isProcessing}
                                className={clsx(
                                    'flex-shrink-0 p-4 rounded-2xl transition-all duration-200',
                                    inputValue.trim() && !isLoading
                                        ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg shadow-purple-500/30 hover:scale-105 hover:shadow-xl'
                                        : 'bg-white/5 text-gray-600 cursor-not-allowed'
                                )}
                            >
                                <Send className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Hint */}
                        <p className="mt-3 text-xs text-center text-gray-500">
                            💡 Gõ <span className="font-semibold text-purple-400">@EOA xử lý</span> khi sẵn sàng tạo audio
                        </p>
                    </div>
                </div>
            )}

            {/* Custom Styles */}
            <style jsx>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
        </>
    );
}
