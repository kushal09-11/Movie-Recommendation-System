from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import get_recommender
from app.routes import admin, auth, movies, ratings, recommendations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _recommender_from_app(app: FastAPI):
    recommender_provider = app.dependency_overrides.get(get_recommender, get_recommender)
    return recommender_provider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    recommender = _recommender_from_app(app)
    try:
        recommender.load_or_train()
        logger.info("Recommendation model is ready.")
    except Exception:
        logger.exception("Recommendation model could not be loaded at startup.")
    yield


app = FastAPI(
    title="Movie Recommendation Mining System",
    description="FastAPI, Supabase, and item-based collaborative filtering backend.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(movies.router)
app.include_router(ratings.router)
app.include_router(recommendations.router)
app.include_router(admin.router)


@app.get("/health", tags=["Health"])
def health_check():
    recommender = _recommender_from_app(app)
    return {
        "status": "ok",
        "model_ready": recommender.is_ready,
        "movies_loaded": recommender.movie_count,
    }
