
"use client";

import { TrendingUp, Users, Lock, Activity } from "lucide-react";

const stats = [
    { label: "Total Value Locked", value: "$4.2B", icon: Lock, color: "text-[#00F3FF]" },
    { label: "Total Users", value: "842K+", icon: Users, color: "text-[#FF003C]" },
    { label: "Average APY", value: "245%", icon: TrendingUp, color: "text-green-400" },
    { label: "Daily Volume", value: "$128M", icon: Activity, color: "text-purple-400" },
];

export function StatsGrid() {
    return (
        <section className="grid grid-cols-2 md:grid-cols-4 gap-6 relative z-10">
            {stats.map((stat, idx) => (
                <div
                    key={idx}
                    className="p-6 rounded-2xl bg-[#101012]/40 backdrop-blur-md border border-white/5 hover:border-white/20 transition-all hover:-translate-y-1 group"
                >
                    <div className={`mb-4 p-3 rounded-lg bg-white/5 w-fit ${stat.color} group-hover:bg-white/10 transition-colors`}>
                        <stat.icon className="w-6 h-6" />
                    </div>
                    <div className="text-3xl font-mono font-bold text-white mb-1 group-hover:text-shadow-neon transition-all">
                        {stat.value}
                    </div>
                    <div className="text-sm text-gray-500 uppercase tracking-wider font-medium">
                        {stat.label}
                    </div>
                </div>
            ))}
        </section>
    );
}
