import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Toaster } from 'react-hot-toast';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Video Reup AI Factory - AI Video Processing Tool',
  description: 
    'Công cụ tự động xử lý, chỉnh sửa và tái đăng video với AI.  Hỗ trợ TikTok, YouTube, Facebook, Instagram, Douyin',
  keywords: 'video, reup, ai, tiktok, youtube, facebook, instagram, douyin, automation',
  authors: [{ name: 'Video Reup AI Factory' }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi" className="dark" suppressHydrationWarning>
      <body className={`${inter.className} bg-gray-900 text-white antialiased`}>
        {children}
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}