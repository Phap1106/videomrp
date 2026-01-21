
"use client";

import { PieChart } from "lucide-react";

const dist = [
    { label: "Staking Rewards", pct: 40, color: "bg-[#00F3FF]" },
    { label: "Treasury", pct: 20, color: "bg-[#FF003C]" },
    { label: "Team & Advisors", pct: 15, color: "bg-purple-500" },
    { label: "IDO / Public Sale", pct: 15, color: "bg-yellow-400" },
    { label: "Liquidity", pct: 10, color: "bg-green-400" },
];

export function TokenomicsSection() {
    return (
        <section className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-16">
                Token<span className="text-[#FF003C]">omics</span>
            </h2>

            <div className="flex flex-col md:flex-row items-center justify-center gap-12 md:gap-24">
                {/* CSS Pie Chart (simplified) */}
                <div className="relative w-64 h-64 md:w-80 md:h-80 rounded-full border-4 border-white/10 flex items-center justify-center animate-spin-slow group">
                    <div className="absolute inset-2 rounded-full border border-[#00F3FF]/20" />
                    <div className="absolute inset-4 rounded-full border border-[#FF003C]/20" />

                    <div className="text-center z-10">
                        <div className="text-5xl font-black mb-1">1B</div>
                        <div className="text-sm text-gray-400 uppercase tracking-widest">Total Supply</div>
                    </div>

                    {/* Orbiting particles */}
                    <div className="absolute top-0 left-1/2 w-4 h-4 bg-[#00F3FF] rounded-full blur-[2px] shadow-[0_0_10px_#00F3FF]" />
                    <div className="absolute bottom-0 right-1/2 w-3 h-3 bg-[#FF003C] rounded-full blur-[2px] shadow-[0_0_10px_#FF003C]" />
                </div>

                {/* Legend */}
                <div className="max-w-sm w-full space-y-4">
                    {dist.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between p-4 rounded-xl bg-[#101012] border border-white/5 hover:border-white/20 transition-all cursor-crosshair">
                            <div className="flex items-center gap-3">
                                <div className={`w-3 h-3 rounded-full ${item.color} shadow-[0_0_8px_currentColor]`} />
                                <span className="font-medium text-gray-300">{item.label}</span>
                            </div>
                            <span className="font-mono font-bold text-white">{item.pct}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
}
