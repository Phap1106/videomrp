// 'use client';

// import { useEffect, useState } from 'react';
// import { Video, Settings, AlertCircle, Loader } from 'lucide-react';
// import toast from 'react-hot-toast';
// import { apiClient } from '@/lib/api-client';
// import { useAppStore } from '@/lib/store';
// import { ReupVideoFeature } from '@/components/features/ReupVideoFeature';
// import { StoryVideoFeature } from '@/components/features/StoryVideoFeature';
// import clsx from 'clsx';

// export default function HomePage() {
//   const [selectedTab, setSelectedTab] = useState<'reup' | 'story'>('reup');
//   const [healthStatus, setHealthStatus] = useState<any>(null);
//   const [isLoading, setIsLoading] = useState(true);
//   const [hasError, setHasError] = useState(false);

//   useEffect(() => {
//     const checkHealth = async () => {
//       try {
//         setIsLoading(true);
//         const health = await apiClient.getHealth();
//         setHealthStatus(health);
//         setHasError(! health.api);
//       } catch (error) {
//         toast.error('Không thể kết nối đến backend');
//         setHasError(true);
//       } finally {
//         setIsLoading(false);
//       }
//     };

//     checkHealth();
//     const interval = setInterval(checkHealth, 10000);
//     return () => clearInterval(interval);
//   }, []);

//   if (isLoading) {
//     return (
//       <div className="flex items-center justify-center min-h-screen">
//         <div className="text-center">
//           <Loader className="w-12 h-12 mx-auto mb-4 text-purple-600 animate-spin" />
//           <p className="text-lg font-semibold">Đang tải...</p>
//         </div>
//       </div>
//     );
//   }

//   return (
//     <main className="min-h-screen px-4 py-8 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
//       <div className="mx-auto max-w-7xl">
//         {/* Header */}
//         <div className="mb-8">
//           <div className="flex items-center gap-3 mb-4">
//             <Video className="w-8 h-8 text-purple-600" />
//             <h1 className="text-4xl font-bold text-white">Video Reup AI Factory</h1>
//           </div>
//           <p className="text-lg text-gray-400">
//             Công cụ tự động xử lý, chỉnh sửa và tái đăng video với AI
//           </p>
//         </div>

//         {/* Health Status */}
//         {hasError && (
//           <div className="flex items-start gap-3 p-4 mb-6 border rounded-lg bg-red-500/10 border-red-500/50">
//             <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
//             <div>
//               <h3 className="mb-1 font-semibold text-red-600">Lỗi Kết Nối</h3>
//               <p className="text-sm text-red-600">
//                 Không thể kết nối đến backend. Vui lòng kiểm tra xem server có đang chạy không.
//               </p>
//             </div>
//           </div>
//         )}

//         {healthStatus && ! hasError && (
//           <div className="p-4 mb-6 border rounded-lg bg-green-500/10 border-green-500/50">
//             <div className="flex items-center justify-between">
//               <div>
//                 <h3 className="mb-2 font-semibold text-green-600">Hệ Thống Khỏe Mạnh</h3>
//                 <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
//                   <div>
//                     <span className="text-gray-400">API:</span>{' '}
//                     <span className={healthStatus.api ? 'text-green-600' : 'text-red-600'}>
//                       {healthStatus.api ? '✓ OK' : '✗ Error'}
//                     </span>
//                   </div>
//                   <div>
//                     <span className="text-gray-400">Database:</span>{' '}
//                     <span className={healthStatus. database ? 'text-green-600' : 'text-red-600'}>
//                       {healthStatus.database ? '✓ OK' : '✗ Error'}
//                     </span>
//                   </div>
//                   <div>
//                     <span className="text-gray-400">Redis:</span>{' '}
//                     <span className={healthStatus. redis ? 'text-green-600' : 'text-red-600'}>
//                       {healthStatus.redis ? '✓ OK' : '✗ Error'}
//                     </span>
//                   </div>
//                   <div>
//                     <span className="text-gray-400">Storage:</span>{' '}
//                     <span className={healthStatus. storage ? 'text-green-600' : 'text-red-600'}>
//                       {healthStatus.storage ? '✓ OK' : '✗ Error'}
//                     </span>
//                   </div>
//                 </div>
//               </div>
//               <Settings className="w-8 h-8 text-green-600" />
//             </div>
//           </div>
//         )}

//         {/* Tab Navigation */}
//         <div className="flex gap-2 mb-8 border-b border-gray-700">
//           <button
//             onClick={() => setSelectedTab('reup')}
//             className={clsx(
//               'px-6 py-3 font-semibold border-b-2 transition-colors',
//               selectedTab === 'reup'
//                 ? 'border-purple-600 text-purple-600'
//                 : 'border-transparent text-gray-400 hover:text-gray-300'
//             )}
//           >
//             📤 Reup Video
//           </button>
//           <button
//             onClick={() => setSelectedTab('story')}
//             className={clsx(
//               'px-6 py-3 font-semibold border-b-2 transition-colors',
//               selectedTab === 'story'
//                 ? 'border-purple-600 text-purple-600'
//                 :  'border-transparent text-gray-400 hover:text-gray-300'
//             )}
//           >
//             📖 Tạo Video Câu Chuyện
//           </button>
//         </div>

//         {/* Content */}
//         <div className="p-8 border rounded-lg bg-white/5 backdrop-blur-sm border-white/10">
//           {selectedTab === 'reup' && <ReupVideoFeature />}
//           {selectedTab === 'story' && <StoryVideoFeature />}
//         </div>

//         {/* Footer */}
//         <div className="mt-8 text-sm text-center text-gray-400">
//           <p>Video Reup AI Factory v3.0.0 © 2024 - Powered by OpenAI, Google Gemini & FFmpeg</p>
//         </div>
//       </div>
//     </main>
//   );
// }











"use client";

import { useEffect, useState } from "react";
import { Video, Settings, AlertCircle, Loader } from "lucide-react";
import toast from "react-hot-toast";
import { apiClient } from "@/lib/api-client";
import { ReupVideoFeature } from "@/components/features/ReupVideoFeature";
import { StoryVideoFeature } from "@/components/features/StoryVideoFeature";
import clsx from "clsx";

type TabKey = "reup" | "story";

type HealthStatus = {
  api?: boolean;
  database?: boolean;
  redis?: boolean;
  storage?: boolean;
  [k: string]: any;
};

export default function HomePage() {
  const [selectedTab, setSelectedTab] = useState<TabKey>("reup");
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    let mounted = true;

    const checkHealth = async () => {
      try {
        setIsLoading(true);
        const health = (await apiClient.getHealth()) as HealthStatus;

        if (!mounted) return;

        setHealthStatus(health);
        setHasError(!Boolean(health?.api));
      } catch (error) {
        if (!mounted) return;
        toast.error("Không thể kết nối đến backend");
        setHasError(true);
        setHealthStatus(null);
      } finally {
        if (mounted) setIsLoading(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Loader className="w-12 h-12 mx-auto mb-4 text-purple-600 animate-spin" />
          <p className="text-lg font-semibold">Đang tải...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Video className="w-8 h-8 text-purple-600" />
            <h1 className="text-4xl font-bold text-white">Video Reup AI Factory</h1>
          </div>
          <p className="text-lg text-gray-400">Công cụ tự động xử lý, chỉnh sửa và tái đăng video với AI</p>
        </div>

        {/* Health Status */}
        {hasError && (
          <div className="flex items-start gap-3 p-4 mb-6 border rounded-lg border-red-500/50 bg-red-500/10">
            <AlertCircle className="mt-0.5 h-6 w-6 flex-shrink-0 text-red-500" />
            <div>
              <h3 className="mb-1 font-semibold text-red-600">Lỗi Kết Nối</h3>
              <p className="text-sm text-red-600">
                Không thể kết nối đến backend. Vui lòng kiểm tra xem server có đang chạy không.
              </p>
            </div>
          </div>
        )}

        {healthStatus && !hasError && (
          <div className="p-4 mb-6 border rounded-lg border-green-500/50 bg-green-500/10">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="mb-2 font-semibold text-green-600">Hệ Thống Khỏe Mạnh</h3>
                <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                  <div>
                    <span className="text-gray-400">API:</span>{" "}
                    <span className={healthStatus.api ? "text-green-600" : "text-red-600"}>
                      {healthStatus.api ? "✓ OK" : "✗ Error"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Database:</span>{" "}
                    <span className={healthStatus.database ? "text-green-600" : "text-red-600"}>
                      {healthStatus.database ? "✓ OK" : "✗ Error"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Redis:</span>{" "}
                    <span className={healthStatus.redis ? "text-green-600" : "text-red-600"}>
                      {healthStatus.redis ? "✓ OK" : "✗ Error"}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Storage:</span>{" "}
                    <span className={healthStatus.storage ? "text-green-600" : "text-red-600"}>
                      {healthStatus.storage ? "✓ OK" : "✗ Error"}
                    </span>
                  </div>
                </div>
              </div>
              <Settings className="w-8 h-8 text-green-600" />
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 border-b border-gray-700">
          <button
            onClick={() => setSelectedTab("reup")}
            className={clsx(
              "border-b-2 px-6 py-3 font-semibold transition-colors",
              selectedTab === "reup"
                ? "border-purple-600 text-purple-600"
                : "border-transparent text-gray-400 hover:text-gray-300"
            )}
          >
            📤 Reup Video
          </button>

          <button
            onClick={() => setSelectedTab("story")}
            className={clsx(
              "border-b-2 px-6 py-3 font-semibold transition-colors",
              selectedTab === "story"
                ? "border-purple-600 text-purple-600"
                : "border-transparent text-gray-400 hover:text-gray-300"
            )}
          >
            📖 Tạo Video Câu Chuyện
          </button>
        </div>

        {/* Content */}
        <div className="p-8 border rounded-lg border-white/10 bg-white/5 backdrop-blur-sm">
          {selectedTab === "reup" && <ReupVideoFeature />}
          {selectedTab === "story" && <StoryVideoFeature />}
        </div>

        {/* Footer */}
        <div className="mt-8 text-sm text-center text-gray-400">
          <p>Video Reup AI Factory v3.0.0 © 2024 - Powered by OpenAI, Google Gemini & FFmpeg</p>
        </div>
      </div>
    </main>
  );
}
