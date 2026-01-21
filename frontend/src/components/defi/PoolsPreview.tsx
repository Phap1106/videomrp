
"use client";

import { ArrowRight } from "lucide-react";

const pools = [
    { name: "Cyber-BTC / ETH", apy: "340%", tvl: "$450M", risk: "Low", color: "from-orange-500 to-yellow-500" },
    { name: "Neon-SOL / USDC", apy: "890%", tvl: "$120M", risk: "Medium", color: "from-[#00F3FF] to-blue-600" },
    { name: "Plasma-DOT / USDT", apy: "1250%", tvl: "$80M", risk: "High", color: "from-[#FF003C] to-pink-600" },
];

export function PoolsPreview() {
    return (
        <section>
            <div className="flex items-end justify-between mb-10">
                <div>
                    <h2 className="text-3xl md:text-4xl font-bold mb-2">
                        Top Performing <span className="text-[#00F3FF]">Pools</span>
                    </h2>
                    <p className="text-gray-400">High yield opportunities updated in real-time.</p>
                </div>
                <button className="hidden md:flex items-center gap-2 text-[#00F3FF] hover:text-white transition-colors">
                    View All Pools <ArrowRight className="w-4 h-4" />
                </button>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
                {pools.map((pool, idx) => (
                    <div
                        key={idx}
                        className="group relative p-1 rounded-3xl bg-gradient-to-b from-white/10 to-transparent hover:from-[#00F3FF]/50 transition-all duration-300"
                    >
                        <div className="relative h-full bg-[#101012] rounded-[22px] p-8 overflow-hidden">
                            {/* Glow Effect */}
                            <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${pool.color} opacity-10 blur-2xl group-hover:opacity-20 transition-opacity`} />

                            <div className="flex justify-between items-start mb-8">
                                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-gray-700 to-gray-900 border border-white/10" />
                                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${pool.risk === 'Low' ? 'border-green-500/30 text-green-400 bg-green-500/10' :
                                        pool.risk === 'Medium' ? 'border-yellow-500/30 text-yellow-400 bg-yellow-500/10' :
                                            'border-red-500/30 text-red-400 bg-red-500/10'
                                    }`}>
                                    {pool.risk} Risk
                                </span>
                            </div>

                            <h3 className="text-xl font-bold mb-1">{pool.name}</h3>
                            <p className="text-sm text-gray-500 mb-6">Auto-Compounding</p>

                            <div className="flex justify-between items-end">
                                <div>
                                    <div className="text-sm text-gray-500 mb-1">Total APY</div>
                                    <div className={`text-3xl font-mono font-bold bg-clip-text text-transparent bg-gradient-to-r ${pool.color}`}>
                                        {pool.apy}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm text-gray-500 mb-1">TVL</div>
                                    <div className="text-lg font-mono text-white">{pool.tvl}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}
