import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Nav } from "@/components/nav";
import { ThemeBoot } from "@/components/theme-boot";

export const metadata: Metadata = {
  title: "AI 투자 일일 리포트",
  description:
    "철도 = AI 사이클 가설로 추적하는 미국·한국 주식 + 크립토 50종목+ 일일 분석.",
};

export const viewport: Viewport = {
  themeColor: "#0b0d12",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className="dark">
      <head>
        <ThemeBoot />
      </head>
      <body className="font-sans min-h-screen flex flex-col">
        <Nav />
        <main className="max-w-6xl mx-auto px-4 py-6 w-full flex-1">
          {children}
        </main>
        <footer className="border-t border-slate-800 mt-12">
          <div className="max-w-6xl mx-auto px-4 py-6 text-xs text-slate-500 flex flex-wrap items-center justify-between gap-2">
            <span>ai-stock · 의사결정 보조 도구 · 매수 추천 아님</span>
            <a
              href="https://github.com/homiepark/ai-stock"
              className="hover:text-slate-300"
              target="_blank"
              rel="noopener"
            >
              GitHub
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
