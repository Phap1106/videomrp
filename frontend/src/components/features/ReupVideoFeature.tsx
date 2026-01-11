// //src/components/features/ReupVideoFeature.tsx
// 'use client';

// import { useState } from 'react';
// import { Upload, Settings, Play } from 'lucide-react';
// import toast from 'react-hot-toast';
// import { apiClient } from '@/lib/api-client';
// import { useAppStore } from '@/lib/store';
// import { VoiceSelector } from '../VoiceSelector';
// import { VideoPreview } from '../VideoPreview';
// import { TextEditor } from '../TextEditor';
// import clsx from 'clsx';

// export function ReupVideoFeature() {
//   const [videoUrl, setVideoUrl] = useState('');
//   const [title, setTitle] = useState('');
//   const [description, setDescription] = useState('');
//   const [isProcessing, setIsProcessing] = useState(false);
//   const [currentJobId, setCurrentJobId] = useState<string | null>(null);
//   const [jobStatus, setJobStatus] = useState<any>(null);
//   const [showTextEditor, setShowTextEditor] = useState(false);
//   const [showPreview, setShowPreview] = useState(false);

//   const currentOptions = useAppStore((state) => state.currentOptions);
//   const setCurrentOptions = useAppStore((state) => state.setCurrentOptions);
//   const selectedVoice = useAppStore((state) => state.selectedVoice);

//   const handleProcessVideo = async () => {
//     if (!videoUrl. trim()) {
//       toast.error('Vui lòng nhập URL video');
//       return;
//     }

//     try {
//       setIsProcessing(true);

//       const result = await apiClient.processReupVideo({
//         source_url: videoUrl,
//         title:  title || 'Reup Video',
//         description,
//         target_platform: currentOptions.targetPlatform,
//         video_type: currentOptions.videoType,
//         duration: currentOptions.duration,
//         add_subtitles: currentOptions.addSubtitles,
//         add_ai_narration: currentOptions.addAiNarration,
//         add_text_overlay: currentOptions.addTextOverlay,
//         remove_watermark: currentOptions.removeWatermark,
//         ai_provider: currentOptions.aiProvider,
//         tts_voice: selectedVoice,
//         narration_style: currentOptions.narrationStyle,
//         processing_flow: currentOptions.processingFlow,
//       });

//       if (result.success) {
//         setCurrentJobId(result.job_id);
//         toast.success('Video đã được thêm vào hàng đợi xử lý');
        
//         // Poll job status
//         pollJobStatus(result.job_id);
//       }
//     } catch (error) {
//       toast.error('Lỗi khi xử lý video');
//     } finally {
//       setIsProcessing(false);
//     }
//   };

//   const pollJobStatus = async (jobId: string) => {
//     const pollInterval = setInterval(async () => {
//       try {
//         const status = await apiClient.getJobStatus(jobId);
//         setJobStatus(status);

//         if (status.status === 'completed' || status.status === 'failed') {
//           clearInterval(pollInterval);
//           if (status.status === 'completed') {
//             toast.success('Video đã được xử lý thành công!');
//             setShowPreview(true);
//           } else {
//             toast.error(status.error_message || 'Lỗi khi xử lý video');
//           }
//         }
//       } catch (error) {
//         clearInterval(pollInterval);
//       }
//     }, 2000);
//   };

//   return (
//     <div className="space-y-6">
//       {/* Video Input Section */}
//       <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
//         <h2 className="flex items-center gap-2 mb-6 text-2xl font-bold">
//           <Upload className="w-6 h-6" />
//           Tính năng Reup Video
//         </h2>

//         <div className="space-y-4">
//           {/* URL Input */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               URL Video (YouTube, TikTok, Instagram, v.v.)
//             </label>
//             <input
//               type="url"
//               value={videoUrl}
//               onChange={(e) => setVideoUrl(e.target.value)}
//               placeholder="https://www.youtube.com/watch?v=..."
//               className="w-full px-4 py-3 border rounded-lg dark:bg-gray-800 dark:border-gray-700 focus:ring-2 focus:ring-purple-500"
//             />
//           </div>

//           {/* Title and Description */}
//           <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
//             <div>
//               <label className="block mb-2 text-sm font-medium">
//                 Tiêu đề (tùy chọn)
//               </label>
//               <input
//                 type="text"
//                 value={title}
//                 onChange={(e) => setTitle(e.target.value)}
//                 placeholder="Tiêu đề video"
//                 className="w-full px-4 py-3 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//               />
//             </div>

//             <div>
//               <label className="block mb-2 text-sm font-medium">
//                 Mô tả (tùy chọn)
//               </label>
//               <input
//                 type="text"
//                 value={description}
//                 onChange={(e) => setDescription(e. target.value)}
//                 placeholder="Mô tả video"
//                 className="w-full px-4 py-3 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//               />
//             </div>
//           </div>
//         </div>
//       </div>

//       {/* Processing Options */}
//       <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
//         <h3 className="flex items-center gap-2 mb-6 text-xl font-semibold">
//           <Settings className="w-5 h-5" />
//           Cài đặt Xử lý
//         </h3>

//         <div className="grid grid-cols-1 grid-cols-2 gap-6 md: lg:grid-cols-3">
//           {/* Target Platform */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               Nền tảng đích
//             </label>
//             <select
//               value={currentOptions.targetPlatform}
//               onChange={(e) =>
//                 setCurrentOptions({
//                   targetPlatform: e.target. value as any,
//                 })
//               }
//               className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//             >
//               <option value="tiktok">TikTok</option>
//               <option value="youtube">YouTube</option>
//               <option value="facebook">Facebook</option>
//               <option value="instagram">Instagram</option>
//               <option value="douyin">Douyin</option>
//               <option value="twitter">Twitter/X</option>
//             </select>
//           </div>

//           {/* Video Type */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               Loại video
//             </label>
//             <select
//               value={currentOptions.videoType}
//               onChange={(e) =>
//                 setCurrentOptions({ videoType: e.target.value as any })
//               }
//               className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//             >
//               <option value="short">Short (15-60s)</option>
//               <option value="highlight">Highlight (2-5m)</option>
//               <option value="viral">Viral (30-90s)</option>
//               <option value="meme">Meme (15-30s)</option>
//               <option value="full">Full</option>
//               <option value="reel">Reel (15-90s)</option>
//             </select>
//           </div>

//           {/* Duration */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               Thời lượng (giây): {currentOptions.duration}
//             </label>
//             <input
//               type="range"
//               min="15"
//               max="600"
//               value={currentOptions.duration}
//               onChange={(e) =>
//                 setCurrentOptions({
//                   duration: parseInt(e.target.value),
//                 })
//               }
//               className="w-full"
//             />
//           </div>

//           {/* Processing Flow */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               Quy trình xử lý
//             </label>
//             <select
//               value={currentOptions.processingFlow}
//               onChange={(e) =>
//                 setCurrentOptions({
//                   processingFlow: e.target.value as any,
//                 })
//               }
//               className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//             >
//               <option value="auto">Auto (Khuyến nghị)</option>
//               <option value="fast">Nhanh</option>
//               <option value="ai">AI-Enhanced</option>
//               <option value="full">Đầy đủ</option>
//               <option value="custom">Tùy chỉnh</option>
//             </select>
//           </div>

//           {/* Narration Style */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               Kiểu lời thoại
//             </label>
//             <select
//               value={currentOptions. narrationStyle}
//               onChange={(e) =>
//                 setCurrentOptions({
//                   narrationStyle: e.target.value as any,
//                 })
//               }
//               className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//             >
//               <option value="professional">Chuyên nghiệp</option>
//               <option value="casual">Bình thường</option>
//               <option value="dramatic">Kịch tính</option>
//             </select>
//           </div>

//           {/* AI Provider */}
//           <div>
//             <label className="block mb-2 text-sm font-medium">
//               Nhà cung cấp AI
//             </label>
//             <select
//               value={currentOptions.aiProvider}
//               onChange={(e) =>
//                 setCurrentOptions({
//                   aiProvider: e.target.value as any,
//                 })
//               }
//               className="w-full px-4 py-2 border rounded-lg dark:bg-gray-800 dark:border-gray-700"
//             >
//               <option value="auto">Auto</option>
//               <option value="openai">OpenAI</option>
//               <option value="gemini">Google Gemini</option>
//             </select>
//           </div>
//         </div>

//         {/* Feature Toggles */}
//         <div className="grid grid-cols-1 grid-cols-2 gap-4 mt-6 md:">
//           {[
//             {
//               key: 'addSubtitles',
//               label: 'Thêm phụ đề',
//             },
//             {
//               key:  'addAiNarration',
//               label: 'Thêm lời thoại AI',
//             },
//             {
//               key: 'addTextOverlay',
//               label: 'Thêm chèn chữ',
//             },
//             {
//               key: 'removeWatermark',
//               label: 'Xóa watermark',
//             },
//           ].map((feature) => (
//             <label
//               key={feature.key}
//               className="flex items-center gap-3 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50"
//             >
//               <input
//                 type="checkbox"
//                 checked={(currentOptions as any)[feature.key]}
//                 onChange={(e) =>
//                   setCurrentOptions({
//                     [feature.key]: e.target.checked,
//                   })
//                 }
//                 className="w-5 h-5 rounded cursor-pointer"
//               />
//               <span className="font-medium">{feature.label}</span>
//             </label>
//           ))}
//         </div>
//       </div>

//       {/* Voice Selection */}
//       <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
//         <VoiceSelector
//           aiProvider={currentOptions.aiProvider}
//           onVoiceSelect={(voice) =>
//             console.log('Selected voice:', voice)
//           }
//         />
//       </div>

//       {/* Text Editor */}
//       {currentOptions.addTextOverlay && (
//         <div className="p-6 bg-white bg-gray-900 border border-gray-200 rounded-lg dark: dark:border-gray-700">
//           <TextEditor />
//         </div>
//       )}

//       {/* Action Buttons */}
//       <div className="flex gap-4">
//         <button
//           onClick={handleProcessVideo}
//           disabled={isProcessing || !videoUrl}
//           className={clsx(
//             'flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-semibold transition-colors',
//             isProcessing || !videoUrl
//               ? 'bg-gray-400 text-white cursor-not-allowed'
//               : 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover: from-purple-700 hover: to-blue-700'
//           )}
//         >
//           <Upload className="w-5 h-5" />
//           {isProcessing ? 'Đang xử lý...' : 'Bắt đầu xử lý'}
//         </button>

//         {currentJobId && (
//           <button
//             onClick={() => setShowPreview(true)}
//             className="flex items-center gap-2 px-6 py-3 text-white transition bg-green-600 rounded-lg hover:bg-green-700"
//           >
//             <Play className="w-5 h-5" />
//             Xem trước
//           </button>
//         )}
//       </div>

//       {/* Job Status */}
//       {jobStatus && (
//         <div className="p-4 border border-blue-200 border-blue-700 rounded-lg bg-blue-50 dark:bg-blue-900/20 dark:">
//           <h4 className="mb-2 font-semibold">Trạng thái công việc</h4>
//           <div className="space-y-2 text-sm">
//             <div>
//               <strong>Trạng thái: </strong>{' '}
//               <span
//                 className={clsx(
//                   'px-2 py-1 rounded text-xs font-medium',
//                   {
//                     'bg-yellow-200 text-yellow-800': jobStatus. status === 'pending',
//                     'bg-blue-200 text-blue-800': jobStatus.status === 'processing',
//                     'bg-green-200 text-green-800': jobStatus.status === 'completed',
//                     'bg-red-200 text-red-800': jobStatus.status === 'failed',
//                   }
//                 )}
//               >
//                 {jobStatus.status}
//               </span>
//             </div>
//             <div>
//               <strong>Bước hiện tại:</strong> {jobStatus.current_step}
//             </div>
//             <div>
//               <strong>Tiến độ:</strong> {jobStatus. progress}%
//             </div>
//             {jobStatus.error_message && (
//               <div className="text-red-600">
//                 <strong>Lỗi:</strong> {jobStatus.error_message}
//               </div>
//             )}
//           </div>
//         </div>
//       )}

//       {/* Video Preview Modal */}
//       {showPreview && currentJobId && (
//         <div className="p-6 bg-white border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700">
//           <VideoPreview
//             jobId={currentJobId}
//             onClose={() => setShowPreview(false)}
//           />
//         </div>
//       )}
//     </div>
//   );
// }











// src/components/features/ReupVideoFeature.tsx
"use client";

import { useState } from "react";
import { Upload, Settings, Play } from "lucide-react";
import toast from "react-hot-toast";
import { apiClient } from "@/lib/api-client";
import { useAppStore } from "@/lib/store";
import { VoiceSelector } from "../VoiceSelector";
import { VideoPreview } from "../VideoPreview";
import { TextEditor } from "../TextEditor";
import clsx from "clsx";

export function ReupVideoFeature() {
  const [videoUrl, setVideoUrl] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);

  const currentOptions = useAppStore((s) => s.currentOptions);
  const setCurrentOptions = useAppStore((s) => s.setCurrentOptions);
  const selectedVoice = useAppStore((s) => s.selectedVoice);

  const pollJobStatus = (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiClient.getJobStatus(jobId);
        setJobStatus(status);

        if (status.status === "completed" || status.status === "failed") {
          clearInterval(pollInterval);
          if (status.status === "completed") {
            toast.success("Video đã được xử lý thành công!");
            setShowPreview(true);
          } else {
            toast.error(status.error_message || "Lỗi khi xử lý video");
          }
        }
      } catch {
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const handleProcessVideo = async () => {
    if (!videoUrl.trim()) {
      toast.error("Vui lòng nhập URL video");
      return;
    }

    try {
      setIsProcessing(true);

      const result = await apiClient.processReupVideo({
        source_url: videoUrl.trim(),
        title: title || "Reup Video",
        description,
        target_platform: currentOptions.targetPlatform,
        video_type: currentOptions.videoType,
        duration: currentOptions.duration,
        add_subtitles: currentOptions.addSubtitles,
        add_ai_narration: currentOptions.addAiNarration,
        add_text_overlay: currentOptions.addTextOverlay,
        remove_watermark: currentOptions.removeWatermark,
        ai_provider: currentOptions.aiProvider,
        tts_voice: selectedVoice,
        narration_style: currentOptions.narrationStyle,
        processing_flow: currentOptions.processingFlow,
      });

      if (result?.success) {
        setCurrentJobId(result.job_id);
        toast.success("Video đã được thêm vào hàng đợi xử lý");
        pollJobStatus(result.job_id);
      } else {
        toast.error("Không tạo được job xử lý");
      }
    } catch {
      toast.error("Lỗi khi xử lý video");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Video Input */}
      <section className="p-6 border rounded-xl border-white/10 bg-white/5 backdrop-blur-sm">
        <h2 className="flex items-center gap-2 mb-6 text-2xl font-bold text-white">
          <Upload className="w-6 h-6 text-purple-400" />
          Tính năng Reup Video
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">
              URL Video (YouTube, TikTok, Instagram, v.v.)
            </label>
            <input
              type="url"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="app-control"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Tiêu đề (tùy chọn)</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Tiêu đề video"
                className="app-control"
              />
            </div>

            <div>
              <label className="block mb-2 text-sm font-medium text-gray-200">Mô tả (tùy chọn)</label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Mô tả video"
                className="app-control"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Options */}
      <section className="p-6 border rounded-xl border-white/10 bg-white/5 backdrop-blur-sm">
        <h3 className="flex items-center gap-2 mb-6 text-xl font-semibold text-white">
          <Settings className="w-5 h-5 text-purple-400" />
          Cài đặt Xử lý
        </h3>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Nền tảng đích</label>
            <select
              value={currentOptions.targetPlatform}
              onChange={(e) => setCurrentOptions({ targetPlatform: e.target.value as any })}
              className="app-control"
            >
              <option value="tiktok">TikTok</option>
              <option value="youtube">YouTube</option>
              <option value="facebook">Facebook</option>
              <option value="instagram">Instagram</option>
              <option value="douyin">Douyin</option>
              <option value="twitter">Twitter/X</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Loại video</label>
            <select
              value={currentOptions.videoType}
              onChange={(e) => setCurrentOptions({ videoType: e.target.value as any })}
              className="app-control"
            >
              <option value="short">Short (15-60s)</option>
              <option value="highlight">Highlight (2-5m)</option>
              <option value="viral">Viral (30-90s)</option>
              <option value="meme">Meme (15-30s)</option>
              <option value="full">Full</option>
              <option value="reel">Reel (15-90s)</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">
              Thời lượng (giây): <span className="text-purple-300">{currentOptions.duration}</span>
            </label>
            <input
              type="range"
              min={15}
              max={600}
              value={currentOptions.duration}
              onChange={(e) => setCurrentOptions({ duration: parseInt(e.target.value, 10) })}
              className="w-full"
            />
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Quy trình xử lý</label>
            <select
              value={currentOptions.processingFlow}
              onChange={(e) => setCurrentOptions({ processingFlow: e.target.value as any })}
              className="app-control"
            >
              <option value="auto">Auto (Khuyến nghị)</option>
              <option value="fast">Nhanh</option>
              <option value="ai">AI-Enhanced</option>
              <option value="full">Đầy đủ</option>
              <option value="custom">Tùy chỉnh</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Kiểu lời thoại</label>
            <select
              value={currentOptions.narrationStyle}
              onChange={(e) => setCurrentOptions({ narrationStyle: e.target.value as any })}
              className="app-control"
            >
              <option value="professional">Chuyên nghiệp</option>
              <option value="casual">Bình thường</option>
              <option value="dramatic">Kịch tính</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-200">Nhà cung cấp AI</label>
            <select
              value={currentOptions.aiProvider}
              onChange={(e) => setCurrentOptions({ aiProvider: e.target.value as any })}
              className="app-control"
            >
              <option value="auto">Auto</option>
              <option value="openai">OpenAI</option>
              <option value="gemini">Google Gemini</option>
            </select>
          </div>
        </div>

        {/* Toggles */}
        <div className="grid grid-cols-1 gap-4 mt-6 md:grid-cols-2">
          {[
            { key: "addSubtitles", label: "Thêm phụ đề" },
            { key: "addAiNarration", label: "Thêm lời thoại AI" },
            { key: "addTextOverlay", label: "Thêm chèn chữ" },
            { key: "removeWatermark", label: "Xóa watermark" },
          ].map((feature) => (
            <label
              key={feature.key}
              className="flex items-center gap-3 p-3 border cursor-pointer rounded-xl border-white/10 bg-white/5 hover:bg-white/10"
            >
              <input
                type="checkbox"
                checked={(currentOptions as any)[feature.key]}
                onChange={(e) => setCurrentOptions({ [feature.key]: e.target.checked } as any)}
                className="w-5 h-5"
              />
              <span className="font-medium text-gray-200">{feature.label}</span>
            </label>
          ))}
        </div>
      </section>

      {/* Voice Selection */}
      <section className="p-6 border rounded-xl border-white/10 bg-white/5 backdrop-blur-sm">
        <VoiceSelector aiProvider={currentOptions.aiProvider} onVoiceSelect={() => {}} />
      </section>

      {/* Text Editor */}
      {currentOptions.addTextOverlay && (
        <section className="p-6 border rounded-xl border-white/10 bg-white/5 backdrop-blur-sm">
          <TextEditor />
        </section>
      )}

      {/* Actions */}
      <div className="flex flex-col gap-4 md:flex-row">
        <button
          onClick={handleProcessVideo}
          disabled={isProcessing || !videoUrl.trim()}
          className={clsx(
            "flex flex-1 items-center justify-center gap-2 rounded-xl px-6 py-3 font-semibold transition-colors",
            isProcessing || !videoUrl.trim()
              ? "cursor-not-allowed bg-white/10 text-gray-400"
              : "bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700"
          )}
        >
          <Upload className="w-5 h-5" />
          {isProcessing ? "Đang xử lý..." : "Bắt đầu xử lý"}
        </button>

        {currentJobId && (
          <button
            onClick={() => setShowPreview(true)}
            className="flex items-center justify-center gap-2 px-6 py-3 text-white bg-green-600 rounded-xl hover:bg-green-700"
          >
            <Play className="w-5 h-5" />
            Xem trước
          </button>
        )}
      </div>

      {/* Job Status */}
      {jobStatus && (
        <section className="p-4 border rounded-xl border-white/10 bg-white/5">
          <h4 className="mb-2 font-semibold text-white">Trạng thái công việc</h4>
          <div className="space-y-2 text-sm text-gray-200">
            <div>
              <strong>Trạng thái:</strong>{" "}
              <span
                className={clsx("rounded px-2 py-1 text-xs font-medium", {
                  "bg-yellow-500/20 text-yellow-300": jobStatus.status === "pending",
                  "bg-blue-500/20 text-blue-300": jobStatus.status === "processing",
                  "bg-green-500/20 text-green-300": jobStatus.status === "completed",
                  "bg-red-500/20 text-red-300": jobStatus.status === "failed",
                })}
              >
                {jobStatus.status}
              </span>
            </div>
            <div>
              <strong>Bước hiện tại:</strong> {jobStatus.current_step}
            </div>
            <div>
              <strong>Tiến độ:</strong> {jobStatus.progress}%
            </div>
            {jobStatus.error_message && (
              <div className="text-red-300">
                <strong>Lỗi:</strong> {jobStatus.error_message}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Preview */}
      {showPreview && currentJobId && (
        <section className="p-6 border rounded-xl border-white/10 bg-white/5 backdrop-blur-sm">
          <VideoPreview jobId={currentJobId} onClose={() => setShowPreview(false)} />
        </section>
      )}
    </div>
  );
}
