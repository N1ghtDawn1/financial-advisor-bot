import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const sans = Geist({ variable: "--font-sans", subsets: ["latin"] });
const mono = Geist_Mono({ variable: "--font-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Financial Advisor Bot | Transparent Simulation Lab",
  description: "A reproducible reinforcement-learning trading simulation with faithful explanations and risk-aware evaluation.",
  icons: { icon: "/favicon.svg" },
  openGraph: { title: "Financial Advisor Bot", description: "See the evidence behind every simulated action.", images: ["/og.png"] },
  twitter: { card: "summary_large_image", title: "Financial Advisor Bot", description: "Transparent simulated trading, from policy to evidence.", images: ["/og.png"] },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body className={`${sans.variable} ${mono.variable}`}>{children}</body></html>;
}
