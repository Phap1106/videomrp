import { create } from 'zustand';

interface ProcessingJob {
  id: string;
  title: string;
  status: 'pending' | 'downloading' | 'analyzing' | 'processing' | 'completed' | 'failed';
  progress: number;
  currentStep: string;
  outputPath?: string;
  errorMessage?: string;
  createdAt: Date;
}

interface VideoProcessingOptions {
  targetPlatform: 'tiktok' | 'youtube' | 'facebook' | 'instagram' | 'douyin' | 'twitter';
  videoType: 'short' | 'highlight' | 'viral' | 'meme' | 'full' | 'reel';
  duration: number;
  addSubtitles: boolean;
  addAiNarration: boolean;
  addTextOverlay: boolean;
  addBackgroundMusic: boolean;
  bgmStyle: string;
  normalizeAudio: boolean;
  removeWatermark: boolean;
  aiProvider: 'openai' | 'gemini' | 'groq' | 'custom' | 'auto';
  ttsVoice?: string;
  narrationStyle: 'viral' | 'review' | 'storytelling' | 'professional' | 'hài hước' | 'dramatic' | 'casual';
  rewriteFromOriginal: boolean;
  processingFlow: 'auto' | 'fast' | 'ai' | 'full' | 'custom';
}

interface TextOverlayStyle {
  fontFamily: string;
  fontSize: number;
  fontColor: string;
  bold: boolean;
  italic: boolean;
  bgColor: string;
  bgAlpha: number;
  position: 'top' | 'center' | 'bottom';
  borderWidth: number;
  borderColor: string;
  shadow: boolean;
}

interface AppStore {
  // Jobs
  jobs: ProcessingJob[];
  addJob: (job: ProcessingJob) => void;
  updateJob: (id: string, updates: Partial<ProcessingJob>) => void;
  removeJob: (id: string) => void;
  clearJobs: () => void;

  // Current video processing
  currentVideoUrl: string;
  setCurrentVideoUrl: (url: string) => void;

  currentOptions: VideoProcessingOptions;
  setCurrentOptions: (options: Partial<VideoProcessingOptions>) => void;

  currentTextOverlayStyle: TextOverlayStyle;
  setCurrentTextOverlayStyle: (style: Partial<TextOverlayStyle>) => void;

  // UI state
  selectedTab: string;
  setSelectedTab: (tab: string) => void;

  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;

  selectedVoice: string | null;
  setSelectedVoice: (voice: string | null) => void;

  // Modals
  showVoicePreview: boolean;
  setShowVoicePreview: (show: boolean) => void;

  showTextEditor: boolean;
  setShowTextEditor: (show: boolean) => void;

  showVideoPreview: boolean;
  setShowVideoPreview: (show: boolean) => void;

  // Current job tracking
  currentJobId: string | null;
  setCurrentJobId: (id: string | null) => void;

  // Output video URL for preview
  outputVideoUrl: string | null;
  setOutputVideoUrl: (url: string | null) => void;

  // EOA Chatbot session
  eoaSessionId: string | null;
  setEoaSessionId: (id: string | null) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  jobs: [],
  addJob: (job) => set((state) => ({ jobs: [...state.jobs, job] })),
  updateJob: (id, updates) =>
    set((state) => ({
      jobs: state.jobs.map((j) => (j.id === id ? { ...j, ...updates } : j)),
    })),
  removeJob: (id) =>
    set((state) => ({
      jobs: state.jobs.filter((j) => j.id !== id),
    })),
  clearJobs: () => set({ jobs: [] }),

  currentVideoUrl: '',
  setCurrentVideoUrl: (url) => set({ currentVideoUrl: url }),

  currentOptions: {
    targetPlatform: 'tiktok',
    videoType: 'short',
    duration: 60,
    addSubtitles: true,
    addAiNarration: true,
    addTextOverlay: false,
    addBackgroundMusic: false,
    bgmStyle: 'cheerful',
    normalizeAudio: true,
    removeWatermark: true,
    aiProvider: 'auto',
    narrationStyle: 'viral',
    rewriteFromOriginal: true,
    processingFlow: 'auto',
  },
  setCurrentOptions: (options) =>
    set((state) => ({
      currentOptions: { ...state.currentOptions, ...options },
    })),

  currentTextOverlayStyle: {
    fontFamily: 'Arial',
    fontSize: 60,
    fontColor: 'FFFFFF',
    bold: false,
    italic: false,
    bgColor: '000000',
    bgAlpha: 0.7,
    position: 'bottom',
    borderWidth: 2,
    borderColor: '000000',
    shadow: false,
  },
  setCurrentTextOverlayStyle: (style) =>
    set((state) => ({
      currentTextOverlayStyle: { ...state.currentTextOverlayStyle, ...style },
    })),

  selectedTab: 'reup',
  setSelectedTab: (tab) => set({ selectedTab: tab }),

  isProcessing: false,
  setIsProcessing: (processing) => set({ isProcessing: processing }),

  selectedVoice: null,
  setSelectedVoice: (voice) => set({ selectedVoice: voice }),

  showVoicePreview: false,
  setShowVoicePreview: (show) => set({ showVoicePreview: show }),

  showTextEditor: false,
  setShowTextEditor: (show) => set({ showTextEditor: show }),

  showVideoPreview: false,
  setShowVideoPreview: (show) => set({ showVideoPreview: show }),

  // Current job tracking
  currentJobId: null,
  setCurrentJobId: (id) => set({ currentJobId: id }),

  // Output video URL for preview
  outputVideoUrl: null,
  setOutputVideoUrl: (url) => set({ outputVideoUrl: url }),

  // EOA Chatbot
  eoaSessionId: null,
  setEoaSessionId: (id) => set({ eoaSessionId: id }),
}));