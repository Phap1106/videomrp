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
      (error:  AxiosError) => {
        const message = (error.response?.data as any)?.detail || error.message || 'An error occurred';
        toast.error(typeof message === 'string' ? message : 'An error occurred');
        return Promise. reject(error);
      }
    );
  }

  // Health & Info
  async getHealth() {
    const { data } = await this.client. get('/health');
    return data;
  }

  async getAvailableVoices(aiProvider?:  string) {
    const { data } = await this.client.get('/voices', {
      params: { ai_provider: aiProvider },
    });
    return data;
  }

  async getProcessingFlows() {
    const { data } = await this.client.get('/processing-flows');
    return data;
  }

  // TTS
  async generateTTS(
    text: string,
    voice?:  string,
    speed?:  number,
    pitch?: number,
    aiProvider?: string
  ) {
    const { data } = await this.client.post('/tts/generate', {
      text,
      voice,
      speed,
      pitch,
      ai_provider: aiProvider,
    });
    return data;
  }

  async previewVoice(voiceId: string, sampleText?:  string, aiProvider?: string) {
    const response = await this.client.post(
      '/tts/preview-voice',
      {
        voice_id: voiceId,
        sample_text:  sampleText,
        ai_provider: aiProvider,
      },
      {
        responseType: 'blob',
      }
    );
    return response.data;
  }

  // Transcription
  async transcribeVideo(videoUrl: string, language:  string = 'vi') {
    const { data } = await this.client. post('/transcription/transcribe', null, {
      params: { video_url: videoUrl, language },
    });
    return data;
  }

  // Story Generation
  async generateStory(prompt: string, maxLength?:  number, style?: string, language?: string) {
    const { data } = await this.client. post('/story/generate', null, {
      params: { prompt, max_length: maxLength, style, language },
    });
    return data;
  }

  async rewriteTranscript(originalText: string, style?:  string) {
    const { data } = await this.client.post('/story/rewrite-transcript', null, {
      params: { original_text: originalText, style },
    });
    return data;
  }

  async generateNarration(topic: string, duration?:  number, tone?: string) {
    const { data } = await this.client. post('/story/narration', null, {
      params:  { topic, duration, tone },
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
}

export const apiClient = new APIClient();