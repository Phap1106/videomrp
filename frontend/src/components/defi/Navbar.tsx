
"use client";

import { Wallet, Menu } from "lucide-react";

export function Navbar() {
    return (
        <nav className="fixed top-0 left-0 right-0 z-50 px-4 py-4">
            <div className="max-w-7xl mx-auto">
                <div className="flex items-center justify-between px-6 py-3 rounded-2xl bg-[#101012]/70 backdrop-blur-xl border border-white/10 shadow-[0_0_20px_rgba(0,0,0,0.5)]">

                    {/* Logo */}
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded bg-gradient-to-br from-[#00F3FF] to-[#FF003C] animate-pulse" />
                        <span className="text-xl font-bold tracking-widest text-white uppercase font-mono">
                            Cyber<span className="text-[#00F3FF]">DeFi</span>
                        </span>
                    </div>

                    {/* Desktop Links */}
                    <div className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-400">
                        <a href="#" className="hover:text-white hover:text-shadow-neon transition-all">Farms</a>
                        <a href="#" className="hover:text-white hover:text-shadow-neon transition-all">Pools</a>
                        <a href="#" className="hover:text-white hover:text-shadow-neon transition-all">Stake</a>
                        <a href="#" className="hover:text-white hover:text-shadow-neon transition-all">Gov</a>
                    </div>

                    {/* Connect Button */}
                    <button className="flex items-center gap-2 px-5 py-2 bg-[#00F3FF]/10 hover:bg-[#00F3FF]/20 border border-[#00F3FF]/50 text-[#00F3FF] rounded-lg font-mono text-sm font-bold transition-all shadow-[0_0_15px_rgba(0,243,255,0.2)] hover:shadow-[0_0_25px_rgba(0,243,255,0.5)] active:scale-95 group">
                        <Wallet className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                        CONNECT_WALLET
                    </button>
                </div>
            </div>
        </nav>
    );
}
