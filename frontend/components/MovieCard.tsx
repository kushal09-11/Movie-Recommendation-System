"use client";

import { useState } from "react";
import type { Movie } from "@/lib/api";
import { FilmIcon } from "@/components/Icons";
import { Rating } from "@/components/Rating";

type MovieCardProps = {
  movie: Movie;
  score?: number | null;
  ratingDisabled?: boolean;
  onRate?: (movieId: number, rating: number) => Promise<void> | void;
  onViewDetails?: (movieId: number) => void;
};

function splitGenres(genres: string | null) {
  if (!genres || genres === "(no genres listed)") {
    return ["Unlisted"];
  }
  return genres.split("|").slice(0, 3);
}

export function MovieCard({
  movie,
  score,
  ratingDisabled = false,
  onRate,
  onViewDetails,
}: MovieCardProps) {
  const [localRating, setLocalRating] = useState(0);
  const [saving, setSaving] = useState(false);
  const genres = splitGenres(movie.genres);

  async function handleRate(value: number) {
    if (!onRate) {
      return;
    }
    setLocalRating(value);
    setSaving(true);
    try {
      await onRate(movie.id, value);
    } finally {
      setSaving(false);
    }
  }

  return (
    <article className="flex min-h-64 flex-col rounded-lg border border-black/10 bg-white/88 p-5 shadow-soft transition hover:-translate-y-1 hover:border-pine/30 dark:border-white/10 dark:bg-white/10">
      <div className="flex items-start justify-between gap-3">
        <div className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-pine/10 text-pine dark:bg-gold/15 dark:text-gold">
          <FilmIcon />
        </div>
        {typeof score === "number" ? (
          <span className="rounded-md bg-gold/20 px-2 py-1 text-xs font-bold text-ink dark:text-gold">
            {score.toFixed(2)}
          </span>
        ) : null}
      </div>

      <h2 className="mt-4 line-clamp-2 text-lg font-bold leading-6">{movie.title}</h2>

      <div className="mt-3 flex flex-wrap gap-2">
        {genres.map((genre) => (
          <span
            key={`${movie.id}-${genre}`}
            className="rounded-md bg-black/5 px-2 py-1 text-xs font-medium text-ink/75 dark:bg-white/10 dark:text-mist/80"
          >
            {genre}
          </span>
        ))}
      </div>

      <div className="mt-auto pt-5">
        <Rating value={localRating} disabled={ratingDisabled || saving || !onRate} onRate={handleRate} />
        <div className="mt-4 flex items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => onViewDetails?.(movie.id)}
            className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold hover:bg-black/5 dark:border-white/10 dark:hover:bg-white/10"
          >
            View Details
          </button>
          {saving ? <span className="text-xs font-medium text-pine dark:text-gold">Saving...</span> : null}
        </div>
      </div>
    </article>
  );
}
