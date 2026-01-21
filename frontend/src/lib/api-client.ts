import axios, { AxiosInstance, AxiosError } from 'axios';
import toast from 'react-hot-toast';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Error interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        const message = (error.response?.data as any)?.detail || error.message || 'An error occurred';
        toast.error(typeof message === 'string' ? message : 'An error occurred');
        return Promise.reject(error);
      }
    );
  }

  // Health & Info
  async getHealth() {
    const { data } = await this.client.get('/health');
    return data;
  }

  async getAvailableVoices(aiProvider?: string) {
    const { data } = await this.client.get('/voices', {
      params: { ai_provider: aiProvider },
    });
    return data;
  }

  async getProcessingFlows() {
    const { data } = await this.client.get('/processing-flows');
    return data;
  }

  // ==================== TTS ====================

  async getTTSProviders() {
    const { data } = await this.client.get('/tts/providers');
    return data;
  }

  async getTTSVoices(provider?: string) {
    const { data } = await this.client.get('/tts/voices', {
      params: provider ? { provider } : undefined,
    });
    return data;
  }

  async generateTTS(
    text: string,
    voice?: string,
    speed?: number,
    aiProvider?: string
  ) {
    const { data } = await this.client.post('/tts/generate', {
      text,
      voice,
      speed,
      ai_provider: aiProvider,
    });
    return data;
  }

  async downloadTTSAudio(audioId: string) {
    const response = await this.client.get(`/tts/download/${audioId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async previewVoice(voiceId: string, sampleText?: string, aiProvider?: string) {
    const response = await this.client.post(
      '/tts/preview-voice',
      {
        voice_id: voiceId,
        sample_text: sampleText,
        ai_provider: aiProvider,
      },
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  // Transcription
  async transcribeVideo(videoUrl: string, language: string = 'vi') {
    const { data } = await this.client.post('/transcription/transcribe', null, {
      params: { video_url: videoUrl, language },
    });
    return data;
  }

  // Story Generation
  async generateStory(prompt: string, maxLength?: number, style?: string, language?: string) {
    const { data } = await this.client.post('/story/generate', null, {
      params: { prompt, max_length: maxLength, style, language },
    });
    return data;
  }

  async rewriteTranscript(originalText: string, style?: string) {
    const { data } = await this.client.post('/story/rewrite-transcript', null, {
      params: { original_text: originalText, style },
    });
    return data;
  }

  async generateNarration(topic: string, duration?: number, tone?: string) {
    const { data } = await this.client.post('/story/narration', null, {
      params: { topic, duration, tone },
    });
    return data;
  }

  // Video Processing
  async processReupVideo(request: any) {
    const { data } = await this.client.post('/videos/process-reup', request);
    return data;
  }

  async processStoryVideo(request: any) {
    const { data } = await this.client.post('/videos/process-story', request);
    return data;
  }

  async createStorySeries(request: any) {
    const { data } = await this.client.post('/story-series/create', request);
    return data;
  }

  async getJobStatus(jobId: string) {
    const { data } = await this.client.get(`/videos/job/${jobId}`);
    return data;
  }

  async downloadVideo(jobId: string) {
    const response = await this.client.get(`/videos/download/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // ==================== EOA CHATBOT ====================

  async eoaChat(
    message: string,
    conversationHistory: Array<{ role: string; content: string }> = [],
    sessionId?: string,
    aiProvider?: string
  ) {
    const { data } = await this.client.post('/eoa/chat', {
      message,
      conversation_history: conversationHistory,
      session_id: sessionId,
      ai_provider: aiProvider,
    });
    return data;
  }

  async eoaProcess(
    sessionId: string,
    conversationHistory: Array<{ role: string; content: string }>,
    storyConfig?: Record<string, any>,
    voice?: string,
    speed: number = 1.0,
    addPauses: boolean = true,
    aiProvider?: string
  ) {
    const { data } = await this.client.post('/eoa/process', {
      session_id: sessionId,
      conversation_history: conversationHistory,
      story_config: storyConfig,
      voice,
      speed,
      add_pauses: addPauses,
      ai_provider: aiProvider,
    });
    return data;
  }

  async eoaDownloadAudio(sessionId: string) {
    const response = await this.client.get(`/eoa/download/${sessionId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async eoaClearSession(sessionId: string) {
    const { data } = await this.client.delete(`/eoa/session/${sessionId}`);
    return data;
  }

  // ==================== SPLIT-SCREEN MERGE ====================

  async mergeSplitScreen(
    video1Url: string,
    video2Url: string,
    layout: string = 'horizontal',
    ratio: string = '1:1',
    outputRatio: string = '9:16',
    audioSource: string = 'both'
  ) {
    const { data } = await this.client.post('/videos/merge-split-screen', null, {
      params: {
        video1_url: video1Url,
        video2_url: video2Url,
        layout,
        ratio,
        output_ratio: outputRatio,
        audio_source: audioSource,
      },
    });
    return data;
  }

  async downloadMergedVideo(jobId: string) {
    const response = await this.client.get(`/videos/merged/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // ==================== ASPECT RATIO CONVERSION ====================

  async convertAspectRatio(
    sourceUrl: string,
    targetRatio: string = '9:16',
    method: string = 'pad',
    bgColor: string = '000000'
  ) {
    const { data } = await this.client.post('/videos/convert-aspect-ratio', null, {
      params: {
        source_url: sourceUrl,
        target_ratio: targetRatio,
        method,
        bg_color: bgColor,
      },
    });
    return data;
  }

  async convertForPlatform(
    sourceUrl: string,
    platform: string,
    method: string = 'pad'
  ) {
    const { data } = await this.client.post('/videos/convert-for-platform', null, {
      params: {
        source_url: sourceUrl,
        platform,
        method,
      },
    });
    return data;
  }

  async getAspectRatios() {
    const { data } = await this.client.get('/aspect-ratios');
    return data;
  }

  async downloadConvertedVideo(jobId: string) {
    const response = await this.client.get(`/videos/converted/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // ==================== HIGHLIGHT EXTRACTION ====================

  async extractHighlights(
    sourceUrl: string,
    targetDuration: number = 60,
    numHighlights: number = 5,
    style: string = 'engaging',
    aiProvider: string = 'auto'
  ) {
    const { data } = await this.client.post('/videos/extract-highlights', null, {
      params: {
        source_url: sourceUrl,
        target_duration: targetDuration,
        num_highlights: numHighlights,
        style,
        ai_provider: aiProvider,
      },
    });
    return data;
  }

  async downloadHighlightsVideo(jobId: string) {
    const response = await this.client.get(`/videos/highlights/${jobId}`, {
      responseType: 'blob',
    });
    return response.data;
  }
}

export const apiClient = new APIClient();