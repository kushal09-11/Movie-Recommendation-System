# Movie Recommendation Frontend

Next.js App Router frontend for the FastAPI Movie Recommendation Mining backend.

## Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

The app expects the backend at:

```text
http://127.0.0.1:8000
```

Override it in `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Pages

- `/` - movie listing, search, pagination, details modal, rating controls
- `/recommend` - recommendations for MovieLens demo users or protected Supabase users

## Backend Auth Notes

When Supabase is enabled on the backend, rating calls require the same Supabase user ID and access token returned by `POST /auth/login`.

For demos, use `/recommend` with "Demo MovieLens mode" enabled and try user `1` or `10`.

## Scripts

```bash
npm run dev
npm run build
npm run typecheck
```
