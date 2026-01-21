import type { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'YouTube Video Analyzer | AI-Powered Content Analysis',
    description: 'Analyze YouTube videos with AI. Get viral potential scores, policy compliance checks, and content quality ratings.',
};

export default function AnalyzerLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return children;
}
