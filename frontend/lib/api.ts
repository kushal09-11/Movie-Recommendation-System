const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export type Movie = {
  id: number;
  title: string;
  genres: string | null;
};

export type Recommendation = Movie & {
  score: number | null;
};

export type RecommendationResponse = {
  user_id: string;
  count: number;
  source: string;
  recommendations: Recommendation[];
};

export type RatingPayload = {
  user_id: string;
  movie_id: number;
  rating: number;
};

export type MoviesQuery = {
  limit?: number;
  offset?: number;
  search?: string;
  genre?: string;
};

type RequestOptions = RequestInit & {
  accessToken?: string;
};

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function buildUrl(path: string, params?: Record<string, string | number | undefined>) {
  const url = new URL(`${API_BASE_URL}${path}`);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") {
      url.searchParams.set(key, String(value));
    }
  });
  return url.toString();
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("accept", "application/json");

  if (options.body && !headers.has("content-type")) {
    headers.set("content-type", "application/json");
  }

  if (options.accessToken) {
    headers.set("authorization", `Bearer ${options.accessToken.replace(/^Bearer\s+/i, "")}`);
  }

  let response: Response;
  try {
    response = await fetch(path.startsWith("http") ? path : `${API_BASE_URL}${path}`, {
      ...options,
      headers,
      cache: "no-store",
    });
  } catch (error) {
    throw new ApiError(
      error instanceof Error ? error.message : "Unable to reach backend API.",
      0,
    );
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`;
    try {
      const data = (await response.json()) as { detail?: unknown };
      if (typeof data.detail === "string") {
        message = data.detail;
      } else if (Array.isArray(data.detail)) {
        message = data.detail.map((item) => item.msg ?? "Validation error").join(", ");
      }
    } catch {
      message = response.statusText || message;
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export function getMovies(query: MoviesQuery = {}) {
  return request<Movie[]>(
    buildUrl("/movies", {
      limit: query.limit ?? 24,
      offset: query.offset ?? 0,
      search: query.search,
      genre: query.genre,
    }),
  );
}

export function getMovie(movieId: number) {
  return request<Movie>(`/movies/${movieId}`);
}

export function getRecommendations(userId: string, topN = 10, accessToken?: string) {
  return request<RecommendationResponse>(buildUrl(`/recommend/${userId}`, { top_n: topN }), {
    accessToken,
  });
}

export function getDemoRecommendations(userId: string, topN = 10) {
  return request<RecommendationResponse>(
    buildUrl(`/recommend/demo/${userId}`, { top_n: topN }),
  );
}

export function rateMovie(payload: RatingPayload, accessToken?: string) {
  return request<RatingPayload>("/rate", {
    method: "POST",
    body: JSON.stringify(payload),
    accessToken,
  });
}

export { ApiError };
