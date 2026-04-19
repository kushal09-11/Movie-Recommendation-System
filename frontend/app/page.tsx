"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { Alert } from "@/components/Alert";
import { MovieCard } from "@/components/MovieCard";
import { SearchIcon } from "@/components/Icons";
import { SessionPanel } from "@/components/SessionPanel";
import { SkeletonGrid } from "@/components/SkeletonGrid";
import { getMovie, getMovies, Movie, rateMovie } from "@/lib/api";

const PAGE_SIZE = 24;

export default function HomePage() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [search, setSearch] = useState("");
  const [genre, setGenre] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [userId, setUserId] = useState("");
  const [accessToken, setAccessToken] = useState("");

  const canGoBack = offset > 0;
  const canGoForward = movies.length === PAGE_SIZE;

  const loadMovies = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await getMovies({
        limit: PAGE_SIZE,
        offset,
        search: search.trim(),
        genre: genre.trim(),
      });
      setMovies(result);
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Unable to load movies.");
    } finally {
      setLoading(false);
    }
  }, [genre, offset, search]);

  useEffect(() => {
    void loadMovies();
  }, [loadMovies]);

  const genres = useMemo(() => {
    const allGenres = movies.flatMap((movie) => movie.genres?.split("|") ?? []);
    return Array.from(new Set(allGenres.filter(Boolean))).sort().slice(0, 12);
  }, [movies]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setOffset(0);
    void loadMovies();
  }

  async function handleViewDetails(movieId: number) {
    setError("");
    try {
      const movie = await getMovie(movieId);
      setSelectedMovie(movie);
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Unable to load movie details.");
    }
  }

  async function handleRate(movieId: number, rating: number) {
    if (!userId.trim()) {
      setError("Enter your Supabase user ID before rating a movie.");
      return;
    }
    setError("");
    setNotice("");
    try {
      await rateMovie(
        {
          user_id: userId.trim(),
          movie_id: movieId,
          rating,
        },
        accessToken.trim() || undefined,
      );
      setNotice(`Saved ${rating} star rating.`);
    } catch (apiError) {
      setError(apiError instanceof Error ? apiError.message : "Unable to save rating.");
    }
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-5 rounded-lg border border-black/10 bg-white/86 p-5 shadow-soft dark:border-white/10 dark:bg-white/10 lg:flex-row lg:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-pine dark:text-gold">
            Movie catalog
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">
            Search, inspect, and rate movies
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70 dark:text-mist/70">
            Results come directly from your FastAPI backend at `127.0.0.1:8000`.
          </p>
        </div>

        <form onSubmit={handleSearch} className="grid w-full gap-3 lg:max-w-xl lg:grid-cols-[1fr_auto]">
          <label className="relative block">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-ink/45 dark:text-mist/45" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search movies"
              className="w-full rounded-lg border border-black/10 bg-white py-3 pl-10 pr-3 text-sm dark:border-white/10 dark:bg-ink"
            />
          </label>
          <button
            type="submit"
            className="rounded-lg bg-pine px-5 py-3 text-sm font-bold text-white shadow-soft hover:bg-pine/90"
          >
            Search
          </button>
        </form>
      </section>

      <SessionPanel
        userId={userId}
        accessToken={accessToken}
        onUserIdChange={setUserId}
        onAccessTokenChange={setAccessToken}
      />

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => {
            setGenre("");
            setOffset(0);
          }}
          className={`rounded-lg px-3 py-2 text-sm font-semibold ${
            !genre
              ? "bg-pine text-white"
              : "border border-black/10 bg-white/70 hover:bg-white dark:border-white/10 dark:bg-white/10"
          }`}
        >
          All
        </button>
        {genres.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => {
              setGenre(item);
              setOffset(0);
            }}
            className={`rounded-lg px-3 py-2 text-sm font-semibold ${
              genre === item
                ? "bg-pine text-white"
                : "border border-black/10 bg-white/70 hover:bg-white dark:border-white/10 dark:bg-white/10"
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {error ? <Alert title="API error" message={error} /> : null}
      {notice ? (
        <div className="rounded-lg border border-pine/25 bg-pine/10 p-4 text-sm font-semibold text-pine dark:text-gold">
          {notice}
        </div>
      ) : null}

      {loading ? (
        <SkeletonGrid />
      ) : movies.length === 0 ? (
        <div className="rounded-lg border border-black/10 bg-white/80 p-8 text-center shadow-soft dark:border-white/10 dark:bg-white/10">
          <p className="text-lg font-bold">No movies found</p>
          <p className="mt-2 text-sm text-ink/65 dark:text-mist/70">
            Try another search term or clear the genre filter.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {movies.map((movie) => (
            <MovieCard
              key={movie.id}
              movie={movie}
              ratingDisabled={!userId.trim()}
              onRate={handleRate}
              onViewDetails={handleViewDetails}
            />
          ))}
        </div>
      )}

      <div className="flex items-center justify-between rounded-lg border border-black/10 bg-white/75 p-3 shadow-soft dark:border-white/10 dark:bg-white/10">
        <button
          type="button"
          disabled={!canGoBack}
          onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
          className="rounded-lg border border-black/10 px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/10"
        >
          Previous
        </button>
        <span className="text-sm font-semibold">Page {Math.floor(offset / PAGE_SIZE) + 1}</span>
        <button
          type="button"
          disabled={!canGoForward}
          onClick={() => setOffset((value) => value + PAGE_SIZE)}
          className="rounded-lg border border-black/10 px-4 py-2 text-sm font-semibold disabled:cursor-not-allowed disabled:opacity-40 dark:border-white/10"
        >
          Next
        </button>
      </div>

      {selectedMovie ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/55 p-4 backdrop-blur-sm">
          <section className="w-full max-w-lg rounded-lg bg-white p-6 shadow-soft dark:bg-ink">
            <p className="text-sm font-semibold text-pine dark:text-gold">Movie details</p>
            <h2 className="mt-2 text-2xl font-bold">{selectedMovie.title}</h2>
            <p className="mt-3 text-sm leading-6 text-ink/70 dark:text-mist/70">
              {selectedMovie.genres ?? "Genres unavailable"}
            </p>
            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={() => setSelectedMovie(null)}
                className="rounded-lg bg-pine px-4 py-2 text-sm font-bold text-white"
              >
                Close
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </div>
  );
}
