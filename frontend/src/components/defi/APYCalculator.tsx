
"use client";

import { useState } from "react";
import { Slider } from "@/components/ui/slider"; // Assuming standard UI component or simple equivalent

export function APYCalculator() {
    const [balance, setBalance] = useState(1000);
    const [days, setDays] = useState(30);
    const apy = 2.45; // 245%

    const dailyRate = apy / 365;
    const estimatedReturns = balance * dailyRate * days;

    return (
        <section className="grid md:grid-cols-2 gap-12 items-center">
            <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-r from-[#FF003C] to-[#00F3FF] rounded-3xl blur-3xl opacity-20" />
                <div className="relative bg-[#101012] border border-white/10 rounded-3xl p-8 md:p-12">
                    <h2 className="text-3xl font-bold mb-8">ROI <span className="text-[#00F3FF]">Calculator</span></h2>

                    <div className="space-y-8">
                        <div>
                            <div className="flex justify-between mb-4">
                                <label className="text-gray-400 font-medium">Staked Amount</label>
                                <span className="font-mono text-xl text-white">${balance}</span>
                            </div>
                            <input
                                type="range"
                                min="100"
                                max="100000"
                                step="100"
                                value={balance}
                                onChange={(e) => setBalance(Number(e.target.value))}
                                className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-[#00F3FF]"
                            />
                        </div>

                        <div>
                            <div className="flex justify-between mb-4">
                                <label className="text-gray-400 font-medium">Timeframe</label>
                                <span className="font-mono text-xl text-white">{days} Days</span>
                            </div>
                            <input
                                type="range"
                                min="1"
                                max="365"
                                value={days}
                                onChange={(e) => setDays(Number(e.target.value))}
                                className="w-full h-2 bg-gray-800 rounded-lg appearance-none cursor-pointer accent-[#FF003C]"
                            />
                        </div>
                    </div>
                </div>
            </div>

            <div className="space-y-8">
                <div>
                    <h3 className="text-2xl font-bold mb-2">Estimated Returns</h3>
                    <p className="text-gray-400">Based on current APY of 245%.</p>
                </div>

                <div className="grid gap-4">
                    <div className="p-6 rounded-2xl bg-[#101012] border border-white/10 flex justify-between items-center">
                        <span className="text-gray-400">Daily Income</span>
                        <span className="text-xl font-mono font-bold text-[#00F3FF]">
                            ${(balance * dailyRate).toFixed(2)}
                        </span>
                    </div>
                    <div className="p-6 rounded-2xl bg-[#101012] border border-white/10 flex justify-between items-center">
                        <span className="text-gray-400">Total Profit</span>
                        <span className="text-3xl font-mono font-bold text-[#FF003C] text-shadow-neon">
                            ${estimatedReturns.toFixed(2)}
                        </span>
                    </div>
                </div>

                <button className="w-full py-4 bg-white text-black font-bold rounded-xl hover:scale-[1.02] transition-transform shadow-[0_0_20px_rgba(255,255,255,0.3)]">
                    Invest Now
                </button>
            </div>
        </section>
    );
}
