create table if not exists public.movies (
  id bigint primary key,
  title text not null,
  genres text
);

create table if not exists public.movie_lens_movies (
  id bigint primary key,
  title text not null,
  genres text
);

create table if not exists public.ratings (
  id bigint generated always as identity primary key,
  user_id text not null,
  movie_id bigint not null,
  rating numeric(2,1) not null check (rating >= 0.5 and rating <= 5.0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, movie_id)
);

create index if not exists idx_ratings_user_id on public.ratings(user_id);
create index if not exists idx_ratings_movie_id on public.ratings(movie_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_ratings_updated_at on public.ratings;

create trigger set_ratings_updated_at
before update on public.ratings
for each row
execute function public.set_updated_at();

alter table public.movies enable row level security;
alter table public.movie_lens_movies enable row level security;
alter table public.ratings enable row level security;

drop policy if exists "Movies are readable by everyone" on public.movies;
drop policy if exists "MovieLens movies are readable by everyone" on public.movie_lens_movies;
drop policy if exists "Users can read their own ratings" on public.ratings;
drop policy if exists "Users can insert their own ratings" on public.ratings;
drop policy if exists "Users can update their own ratings" on public.ratings;

create policy "Movies are readable by everyone"
on public.movies
for select
using (true);

create policy "MovieLens movies are readable by everyone"
on public.movie_lens_movies
for select
using (true);

create policy "Users can read their own ratings"
on public.ratings
for select
using (auth.uid()::text = user_id);

create policy "Users can insert their own ratings"
on public.ratings
for insert
with check (auth.uid()::text = user_id);

create policy "Users can update their own ratings"
on public.ratings
for update
using (auth.uid()::text = user_id)
with check (auth.uid()::text = user_id);
