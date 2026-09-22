import type { Metadata } from "next";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Agent Forge — Autonomous Multi-Agent Evolution Platform",
  description:
    "Submit tasks and watch Agent Forge dynamically synthesize multi-agent architectures, execute them, evaluate results, reflect, and evolve — improving with every run.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <div className="bg-mesh" />
        <div style={{ position: "relative", zIndex: 1 }}>
          <NavBar />
          <main style={{ minHeight: "calc(100vh - 60px)" }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
