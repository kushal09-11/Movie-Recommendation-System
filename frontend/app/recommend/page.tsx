"use client";

import { FormEvent, useEffect, useState } from "react";
import { Alert } from "@/components/Alert";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { MovieCard } from "@/components/MovieCard";
import { SparkIcon } from "@/components/Icons";
import { getDemoRecommendations, getRecommendations, Recommendation } from "@/lib/api";

export default function RecommendationPage() {
  const [userId, setUserId] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [demoMode, setDemoMode] = useState(true);
  const [topN, setTopN] = useState(10);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setUserId(localStorage.getItem("movie-user-id") ?? "1");
    setAccessToken(localStorage.getItem("movie-access-token") ?? "");
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedUserId = userId.trim();
    if (!trimmedUserId) {
      setError("Enter a user ID before requesting recommendations.");
      return;
    }

    setLoading(true);
    setError("");
    setRecommendations([]);
    localStorage.setItem("movie-user-id", trimmedUserId);
    localStorage.setItem("movie-access-token", accessToken.trim());

    try {
      const response = demoMode
        ? await getDemoRecommendations(trimmedUserId, topN)
        : await getRecommendations(trimmedUserId, topN, accessToken.trim() || undefined);
      setRecommendations(response.recommendations);
      setSource(response.source);
      if (response.recommendations.length === 0) {
        setError("No recommendations were returned for this user.");
      }
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Unable to fetch recommendations.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-black/10 bg-white/86 p-5 shadow-soft dark:border-white/10 dark:bg-white/10">
        <p className="text-sm font-semibold uppercase tracking-wide text-pine dark:text-gold">
          Recommendation engine
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
          Generate movie recommendations
        </h1>

        <form onSubmit={handleSubmit} className="mt-6 grid gap-4 lg:grid-cols-[1fr_1fr_auto] lg:items-end">
          <label className="block">
            <span className="text-sm font-semibold">User ID</span>
            <input
              value={userId}
              onChange={(event) => setUserId(event.target.value)}
              placeholder={demoMode ? "Try MovieLens user 1 or 10" : "Supabase user UUID"}
              className="mt-2 w-full rounded-lg border border-black/10 bg-white px-3 py-3 text-sm dark:border-white/10 dark:bg-ink"
            />
          </label>

          <label className="block">
            <span className="text-sm font-semibold">Access token</span>
            <input
              value={accessToken}
              onChange={(event) => setAccessToken(event.target.value)}
              disabled={demoMode}
              placeholder="Required for protected backend users"
              className="mt-2 w-full rounded-lg border border-black/10 bg-white px-3 py-3 text-sm disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:bg-ink"
            />
          </label>

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-coral px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-coral/90 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <SparkIcon className="h-4 w-4" />
            Get Recommendations
          </button>

          <div className="flex flex-wrap items-center gap-4 lg:col-span-3">
            <label className="inline-flex items-center gap-2 text-sm font-semibold">
              <input
                type="checkbox"
                checked={demoMode}
                onChange={(event) => setDemoMode(event.target.checked)}
                className="h-4 w-4 accent-pine"
              />
              Demo MovieLens mode
            </label>
            <label className="inline-flex items-center gap-2 text-sm font-semibold">
              Top N
              <input
                type="number"
                min={5}
                max={50}
                value={topN}
                onChange={(event) => setTopN(Number(event.target.value))}
                className="w-20 rounded-lg border border-black/10 bg-white px-3 py-2 dark:border-white/10 dark:bg-ink"
              />
            </label>
          </div>
        </form>
      </section>

      {error ? <Alert title="Recommendation issue" message={error} /> : null}
      {loading ? <LoadingSpinner label="Mining recommendations" /> : null}

      {!loading && recommendations.length > 0 ? (
        <section className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-2xl font-bold">Recommended movies</h2>
              <p className="text-sm text-ink/65 dark:text-mist/70">Source: {source}</p>
            </div>
            <span className="rounded-lg bg-pine/10 px-3 py-2 text-sm font-bold text-pine dark:bg-gold/15 dark:text-gold">
              {recommendations.length} results
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {recommendations.map((movie) => (
              <MovieCard key={movie.id} movie={movie} score={movie.score} ratingDisabled />
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}
