
"use client";

import { ArrowRight, Zap } from "lucide-react";

export function HeroSection() {
    return (
        <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden pt-20">

            {/* Background Grid */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_at_center,black_40%,transparent_100%)] pointer-events-none" />

            <div className="container mx-auto px-4 text-center relative z-10">

                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#FF003C]/10 border border-[#FF003C]/30 text-[#FF003C] text-xs font-mono mb-8 animate-fade-in-up">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FF003C] opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#FF003C]"></span>
                    </span>
                    YIELD FARMING 2077 IS LIVE
                </div>

                {/* Glitch Headline */}
                <h1 className="text-6xl md:text-8xl font-black mb-6 tracking-tight leading-none text-transparent bg-clip-text bg-gradient-to-b from-white to-gray-500 drop-shadow-2xl">
                    EARN <span className="text-[#00F3FF] glitch-text" data-text="PASSIVE">PASSIVE</span> <br />
                    INCOME <span className="text-outline-neon">FOREVER</span>
                </h1>

                <p className="max-w-2xl mx-auto text-lg md:text-xl text-gray-400 mb-10 leading-relaxed">
                    The most advanced yield aggregator on the network.
                    Maximize your crypto APY with automated strategy optimization and
                    <span className="text-[#00F3FF]"> AI-driven rebalancing.</span>
                </p>

                {/* CTA Group */}
                <div className="flex flex-wrap items-center justify-center gap-4">
                    <button className="px-8 py-4 bg-[#FF003C] hover:bg-[#FF003C]/90 text-black font-bold text-lg rounded-xl skew-x-[-10deg] hover:skew-x-[-5deg] transition-all duration-300 shadow-[0_0_30px_rgba(255,0,60,0.4)] flex items-center gap-2 group">
                        <div className="skew-x-[10deg] flex items-center gap-2">
                            START FARMING <Zap className="w-5 h-5 fill-black group-hover:scale-110 transition-transform" />
                        </div>
                    </button>

                    <button className="px-8 py-4 bg-transparent border border-white/20 hover:border-white/50 text-white font-bold text-lg rounded-xl skew-x-[-10deg] transition-all hover:shadow-[0_0_20px_rgba(255,255,255,0.1)] group">
                        <div className="skew-x-[10deg] flex items-center gap-2">
                            EXPLORE POOLS <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </button>
                </div>

                {/* Stats Strip */}
                <div className="mt-20 flex justify-center gap-12 md:gap-20 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
                    <img src="https://img.shields.io/badge/AUDITED_BY-CERTIK-white?style=for-the-badge&logo=certik&color=black" className="h-8 md:h-10 opacity-70" alt="Audit" />
                    <img src="https://img.shields.io/badge/BUILT_ON-SOLANA-white?style=for-the-badge&logo=solana&color=black" className="h-8 md:h-10 opacity-70" alt="Solana" />
                </div>
            </div>
        </section>
    );
}
