
# Movie-Recommendation-System

# Movie Recommendation Mining Backend

FastAPI backend for a Movie Recommendation Mining System with Supabase auth/storage and an item-based collaborative filtering recommender.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Fill in `.env` with your Supabase values. For admin dataset syncs, `SUPABASE_KEY` should be a server-side service-role key because the sync endpoint inserts rows into Supabase. Do not expose that key to the frontend. Set `ADMIN_API_TOKEN` to a long random string before using `/admin/*` endpoints.

## Dataset

The app looks for MovieLens CSV files in this order:

1. `MOVIELENS_DATA_DIR`
2. `./data`
3. `~/Downloads/archive (1)`
4. `~/Downloads/ml-latest-small`

It accepts either `movies.csv` / `ratings.csv` or `movie.csv` / `rating.csv`. If no files are found and `RECOMMENDER_AUTO_DOWNLOAD=true`, it downloads MovieLens small into `./data`.

Large MovieLens exports are supported, but first-run training can be expensive. By default, `RECOMMENDER_MAX_RATINGS=1000000` caps the initial ratings loaded for model training. Set it to `0` to train on the full ratings file.

## Run

```bash
uvicorn app.main:app --reload
```

API docs are available at:

```text
http://127.0.0.1:8000/docs
```

Core endpoints:

- `POST /auth/signup`
- `POST /auth/login`
- `GET /movies`
- `GET /movies/{id}`
- `POST /rate`
- `GET /ratings/{user_id}`
- `GET /recommend/{user_id}?top_n=10`
- `GET /recommend/demo/{movielens_user_id}?top_n=10`
- `GET /admin/model-status`
- `POST /admin/retrain`
- `POST /admin/sync-dataset`

When Supabase is configured, `POST /rate`, `GET /ratings/{user_id}`, and `GET /recommend/{user_id}` require `Authorization: Bearer <access_token>` for that same user. Without Supabase credentials, ratings fall back to `LOCAL_RATING_STORE` for local development and tests.

The demo endpoint uses numeric MovieLens users from the dataset and does not require login:

```text
GET /recommend/demo/1?top_n=10
```

Admin endpoints require this header:

```text
x-admin-token: <ADMIN_API_TOKEN>
```

`POST /admin/sync-dataset` syncs movies into `public.movie_lens_movies` by default. It does not sync all ratings unless `include_ratings=true`, because large MovieLens rating exports can be slow and heavy.

## Test

```bash
pytest
```

## Supabase Schema

Run `supabase/schema.sql` in your Supabase SQL editor before syncing data.

To sync the dataset:

```bash
python scripts/sync_dataset.py
```

## Frontend

The Next.js frontend lives in `frontend/`.

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Open:

```text
http://localhost:3000
```
 283289c (Initial commit)
