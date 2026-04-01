-- Run this in Supabase SQL Editor to set up tables

-- Users table (extends Supabase auth.users)
create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  plan text not null default 'free' check (plan in ('free', 'pro')),
  stripe_customer_id text,
  created_at timestamptz not null default now()
);

-- Usage tracking table
create table public.usage (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.users(id) on delete cascade,
  date date not null default current_date,
  generation_count int not null default 0,
  unique (user_id, date)
);

-- Enable RLS
alter table public.users enable row level security;
alter table public.usage enable row level security;

-- Service role can do everything (backend uses service key)
-- No user-facing RLS policies needed since all access goes through the API
