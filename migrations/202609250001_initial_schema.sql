-- TaskFlow initial schema
-- Run this in Supabase SQL Editor or through your preferred migration workflow.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  full_name text,
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.tasks (
  id uuid primary key default gen_random_uuid(),
  title varchar(120) not null,
  description varchar(1000),
  status text not null default 'pending' check (status in ('pending', 'completed')),
  creator_id uuid not null references public.profiles(id) on delete cascade,
  assignee_id uuid not null references public.profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists tasks_creator_id_idx on public.tasks(creator_id);
create index if not exists tasks_assignee_id_idx on public.tasks(assignee_id);
create index if not exists tasks_status_idx on public.tasks(status);

-- Automatically create a profile when a user signs in for the first time.
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name, avatar_url)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
    coalesce(new.raw_user_meta_data ->> 'avatar_url', new.raw_user_meta_data ->> 'picture')
  )
  on conflict (id) do update set
    email = excluded.email,
    full_name = excluded.full_name,
    avatar_url = excluded.avatar_url,
    updated_at = now();

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_user();

-- Keep timestamps consistent in the database instead of trusting the client.
create or replace function public.set_task_timestamps()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();

  if new.status = 'completed' and old.status <> 'completed' then
    new.completed_at = now();
  elsif new.status = 'pending' then
    new.completed_at = null;
  end if;

  return new;
end;
$$;

drop trigger if exists set_task_timestamps_trigger on public.tasks;
create trigger set_task_timestamps_trigger
before update on public.tasks
for each row execute procedure public.set_task_timestamps();

alter table public.profiles enable row level security;
alter table public.tasks enable row level security;

-- These policies are useful even though the Flask API uses the service role.
-- They protect the tables if the frontend later starts calling Supabase directly.
drop policy if exists "Authenticated users can view profiles" on public.profiles;
create policy "Authenticated users can view profiles"
on public.profiles for select
to authenticated
using (true);

drop policy if exists "Users can update their own profile" on public.profiles;
create policy "Users can update their own profile"
on public.profiles for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "Users can view related tasks" on public.tasks;
create policy "Users can view related tasks"
on public.tasks for select
to authenticated
using (auth.uid() = creator_id or auth.uid() = assignee_id);

drop policy if exists "Users can create tasks" on public.tasks;
create policy "Users can create tasks"
on public.tasks for insert
to authenticated
with check (auth.uid() = creator_id);

drop policy if exists "Related users can update tasks" on public.tasks;
create policy "Related users can update tasks"
on public.tasks for update
to authenticated
using (auth.uid() = creator_id or auth.uid() = assignee_id)
with check (auth.uid() = creator_id or auth.uid() = assignee_id);
