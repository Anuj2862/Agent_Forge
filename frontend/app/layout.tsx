import type { Metadata } from "next";
import Script from "next/script";
import "./globals.css";
import SideBar from "@/components/SideBar";
import TopHeader from "@/components/TopHeader";
import GlobalNetworkBackground from "@/components/GlobalNetworkBackground";

export const metadata: Metadata = {
  title: "Agent Forge — Autonomous Multi-Agent Evolution Platform",
  description:
    "Submit tasks and watch Agent Forge dynamically synthesize multi-agent architectures, execute them, evaluate results, reflect, and evolve — improving with every run.",
  icons: {
    icon: "/logo.png",
    shortcut: "/logo.png",
    apple: "/logo.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <Script
          id="theme-initializer"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var t = localStorage.getItem('agentforge_theme') || 'dark';
                document.documentElement.setAttribute('data-theme', t);
                if (t === 'light') {
                  document.documentElement.classList.add('light');
                  document.documentElement.classList.remove('dark');
                } else {
                  document.documentElement.classList.add('dark');
                  document.documentElement.classList.remove('light');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body>
        <div className="bg-mesh" />
        <GlobalNetworkBackground />
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
