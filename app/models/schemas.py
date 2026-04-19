from pydantic import BaseModel, EmailStr, Field


class AuthRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class AuthResponse(BaseModel):
    user_id: str | None
    email: str | None
    access_token: str | None = None
    refresh_token: str | None = None
    message: str


class MovieOut(BaseModel):
    id: int
    title: str
    genres: str | None = None


class RatingCreate(BaseModel):
    user_id: str = Field(min_length=1)
    movie_id: int = Field(gt=0)
    rating: float = Field(ge=0.5, le=5.0)


class RatingOut(BaseModel):
    user_id: str
    movie_id: int
    rating: float


class RecommendationOut(MovieOut):
    score: float | None = None


class RecommendationResponse(BaseModel):
    user_id: str
    count: int
    source: str
    recommendations: list[RecommendationOut]


class ModelStatusResponse(BaseModel):
    model_ready: bool
    movie_count: int
    ratings_count: int
    model_dir: str
    artifacts_cached: bool
    similarity_cached: bool
    min_similarity: float
    top_k_similar: int


class AdminActionResponse(BaseModel):
    message: str
    details: dict[str, int | str | bool | None] = {}
