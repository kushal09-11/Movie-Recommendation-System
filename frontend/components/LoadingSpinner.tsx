export function LoadingSpinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 rounded-lg border border-black/10 bg-white/80 p-6 shadow-soft dark:border-white/10 dark:bg-white/10">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-pine border-t-transparent" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
