"use client";

type RatingProps = {
  value?: number;
  disabled?: boolean;
  onRate: (rating: number) => void;
};

export function Rating({ value = 0, disabled = false, onRate }: RatingProps) {
  return (
    <div className="flex items-center gap-1" aria-label="Rate movie">
      {Array.from({ length: 5 }, (_, index) => {
        const rating = index + 1;
        const active = rating <= value;
        return (
          <button
            key={rating}
            type="button"
            disabled={disabled}
            onClick={() => onRate(rating)}
            className={[
              "grid h-8 w-8 place-items-center rounded-md transition",
              active ? "text-gold" : "text-black/30 dark:text-white/35",
              disabled ? "cursor-not-allowed opacity-45" : "hover:bg-gold/15 hover:text-gold",
            ].join(" ")}
            title={disabled ? "Enter a user ID first" : `Rate ${rating} out of 5`}
            aria-label={`Rate ${rating} out of 5`}
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M10 1.7 12.4 7l5.8.6-4.4 3.9 1.3 5.7L10 14.2l-5.1 3 1.3-5.7-4.4-3.9L7.6 7 10 1.7Z" />
            </svg>
          </button>
        );
      })}
    </div>
  );
}
