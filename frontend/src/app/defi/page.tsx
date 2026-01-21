
"use client";

import { Navbar } from "@/components/defi/Navbar";
import { HeroSection } from "@/components/defi/HeroSection";
import { StatsGrid } from "@/components/defi/StatsGrid";
import { PoolsPreview } from "@/components/defi/PoolsPreview";
import { APYCalculator } from "@/components/defi/APYCalculator";
import { TokenomicsSection } from "@/components/defi/TokenomicsSection";

export default function DeFiPage() {
    return (
        <main className="pb-20">
            <Navbar />
            <HeroSection />

            <div className="container mx-auto px-4 space-y-32 relative">
                {/* Glowing orb effect for background ambiance */}
                <div className="absolute top-1/4 -left-64 w-96 h-96 bg-cyan-500/20 rounded-full blur-[128px] pointer-events-none" />
                <div className="absolute bottom-1/4 -right-64 w-96 h-96 bg-pink-500/20 rounded-full blur-[128px] pointer-events-none" />

                <StatsGrid />
                <PoolsPreview />
                <APYCalculator />
                <TokenomicsSection />
            </div>

            <footer className="mt-32 border-t border-white/10 py-12 text-center text-gray-500 text-sm">
                <p>© 2077 CyberDeFi Protocol. All rights reserved.</p>
                <p className="mt-2 text-xs">Built with Antigravity Kit</p>
            </footer>
        </main>
    );
}
