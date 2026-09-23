import type { Metadata } from "next";
import "./globals.css";
import SideBar from "@/components/SideBar";
import TopHeader from "@/components/TopHeader";

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
        <div className="app-shell" style={{ position: "relative", zIndex: 1 }}>
          <SideBar />
          <div className="app-content">
            <TopHeader />
            <main className="main-content">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
