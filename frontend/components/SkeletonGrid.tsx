export function SkeletonGrid() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, index) => (
        <div
          key={index}
          className="h-64 animate-pulse rounded-lg border border-black/10 bg-white/70 p-5 shadow-soft dark:border-white/10 dark:bg-white/10"
        >
          <div className="h-5 w-3/4 rounded bg-black/10 dark:bg-white/10" />
          <div className="mt-4 h-4 w-1/2 rounded bg-black/10 dark:bg-white/10" />
          <div className="mt-20 h-10 rounded bg-black/10 dark:bg-white/10" />
        </div>
      ))}
    </div>
  );
}
