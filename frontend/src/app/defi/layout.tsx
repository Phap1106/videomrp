
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google"; // Import Google Fonts
import clsx from "clsx";

const inter = Inter({ subsets: ["latin"], weight: ["400", "500", "600", "700", "800", "900"] });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
    title: "CyberDeFi | Yield Farming 2077",
    description: "Next-gen Yield Farming Platform with High APY and Cyberpunk Aesthetics.",
};

export default function DeFiLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className={clsx(inter.className, jetbrains.variable, "min-h-screen bg-[#050505] text-white selection:bg-cyan-500/30")}>
            <div className="fixed inset-0 z-0 pointer-events-none opacity-20" style={{
                backgroundImage: "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))",
                backgroundSize: "100% 2px, 2px 100%"
            }} />
            <div className="relative z-10">
                {children}
            </div>
        </div>
    );
}
