"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Moon, Sun, Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function Nav() {
  const pathname = usePathname();
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setTheme(document.documentElement.classList.contains("dark") ? "dark" : "light");
  }, []);

  function toggleTheme() {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    const root = document.documentElement;
    if (next === "dark") {
      root.classList.add("dark");
      root.classList.remove("light");
    } else {
      root.classList.remove("dark");
      root.classList.add("light");
    }
    localStorage.setItem("theme", next);
  }

  function openSearch() {
    window.dispatchEvent(new CustomEvent("ai-stock:open-search"));
  }

  const tabs: { href: string; label: string; emoji: string; active: boolean }[] = [
    {
      href: "/",
      label: "주식",
      emoji: "📈",
      active: pathname === "/" || pathname?.startsWith("/stock"),
    },
    {
      href: "/coins",
      label: "코인",
      emoji: "🪙",
      active: pathname?.startsWith("/coins") || pathname?.startsWith("/coin/") || false,
    },
    {
      href: "/archive",
      label: "기록",
      emoji: "📚",
      active: pathname?.startsWith("/archive") || false,
    },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur sticky top-0 z-30">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 flex-shrink-0">
          <span className="font-bold text-lg text-lime-400">AI</span>
          <span className="text-slate-400 hidden sm:inline">투자 일일 리포트</span>
        </Link>
        <nav className="flex items-center gap-1 sm:gap-2 text-sm">
          {tabs.map((t) => (
            <Link
              key={t.href}
              href={t.href}
              className={cn(
                "px-2.5 py-1.5 rounded transition-colors",
                t.active
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:text-white hover:bg-slate-900",
              )}
            >
              <span className="mr-1">{t.emoji}</span>
              {t.label}
            </Link>
          ))}
          <button
            onClick={openSearch}
            className="px-2 py-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-900"
            aria-label="검색"
            title="검색 (⌘K)"
          >
            <Search className="size-4" />
          </button>
          <button
            onClick={toggleTheme}
            className="px-2 py-1.5 rounded text-slate-400 hover:text-white hover:bg-slate-900"
            aria-label="테마 변경"
          >
            {mounted && theme === "dark" ? (
              <Sun className="size-4" />
            ) : (
              <Moon className="size-4" />
            )}
          </button>
        </nav>
      </div>
    </header>
  );
}
