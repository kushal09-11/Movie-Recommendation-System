"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FilmIcon, MoonIcon, SparkIcon, SunIcon } from "@/components/Icons";

export function Navbar() {
  const [darkMode, setDarkMode] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("movie-ui-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const enabled = saved ? saved === "dark" : prefersDark;
    setDarkMode(enabled);
    document.documentElement.classList.toggle("dark", enabled);
  }, []);

  function toggleTheme() {
    const next = !darkMode;
    setDarkMode(next);
    localStorage.setItem("movie-ui-theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-black/10 bg-white/82 backdrop-blur-xl dark:border-white/10 dark:bg-ink/82">
      <nav className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-pine text-white shadow-soft">
            <FilmIcon />
          </span>
          <span>
            <span className="block text-sm font-semibold uppercase tracking-wide text-pine dark:text-gold">
              Mining System
            </span>
            <span className="block text-lg font-bold">Movie Recommendations</span>
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-sm font-semibold hover:bg-black/5 dark:hover:bg-white/10"
          >
            Movies
          </Link>
          <Link
            href="/recommend"
            className="inline-flex items-center gap-2 rounded-lg bg-coral px-3 py-2 text-sm font-semibold text-white shadow-soft hover:bg-coral/90"
          >
            <SparkIcon className="h-4 w-4" />
            Recommend
          </Link>
          <button
            type="button"
            onClick={toggleTheme}
            className="grid h-10 w-10 place-items-center rounded-lg border border-black/10 bg-white text-ink hover:bg-mist dark:border-white/10 dark:bg-white/10 dark:text-mist"
            title={darkMode ? "Use light mode" : "Use dark mode"}
            aria-label={darkMode ? "Use light mode" : "Use dark mode"}
          >
            {darkMode ? <SunIcon /> : <MoonIcon />}
          </button>
        </div>
      </nav>
    </header>
  );
}
