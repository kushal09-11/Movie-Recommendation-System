"use client";

import { useEffect, useState } from "react";

type SessionPanelProps = {
  userId: string;
  accessToken: string;
  onUserIdChange: (value: string) => void;
  onAccessTokenChange: (value: string) => void;
};

export function SessionPanel({
  userId,
  accessToken,
  onUserIdChange,
  onAccessTokenChange,
}: SessionPanelProps) {
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const storedUserId = localStorage.getItem("movie-user-id") ?? "";
    const storedToken = localStorage.getItem("movie-access-token") ?? "";
    if (storedUserId) {
      onUserIdChange(storedUserId);
    }
    if (storedToken) {
      onAccessTokenChange(storedToken);
    }
  }, [onAccessTokenChange, onUserIdChange]);

  function updateUserId(value: string) {
    onUserIdChange(value);
    localStorage.setItem("movie-user-id", value);
  }

  function updateToken(value: string) {
    onAccessTokenChange(value);
    localStorage.setItem("movie-access-token", value);
  }

  return (
    <section className="rounded-lg border border-black/10 bg-white/86 p-4 shadow-soft dark:border-white/10 dark:bg-white/10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-pine dark:text-gold">Backend session</p>
          <p className="text-sm text-ink/65 dark:text-mist/70">
            Use the Supabase user ID and access token from your FastAPI login response.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="rounded-lg border border-black/10 px-3 py-2 text-sm font-semibold hover:bg-black/5 dark:border-white/10 dark:hover:bg-white/10"
        >
          {expanded ? "Hide" : "Edit"}
        </button>
      </div>

      {expanded ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-2">
          <label className="block">
            <span className="text-sm font-semibold">User ID</span>
            <input
              value={userId}
              onChange={(event) => updateUserId(event.target.value)}
              placeholder="Supabase UUID or MovieLens demo user"
              className="mt-2 w-full rounded-lg border border-black/10 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-ink"
            />
          </label>
          <label className="block">
            <span className="text-sm font-semibold">Access token</span>
            <input
              value={accessToken}
              onChange={(event) => updateToken(event.target.value)}
              placeholder="Paste JWT for protected rate/recommend calls"
              className="mt-2 w-full rounded-lg border border-black/10 bg-white px-3 py-2 text-sm dark:border-white/10 dark:bg-ink"
            />
          </label>
        </div>
      ) : null}
    </section>
  );
}
