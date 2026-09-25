-- All writes must pass through Flask authorization and Gmail notification logic.
-- Preserves existing rows and authenticated read policies.
begin;

revoke all privileges on table public.profiles, public.tasks from anon, authenticated;
grant select on table public.profiles, public.tasks to authenticated;
grant all privileges on table public.profiles, public.tasks to service_role;

-- Keep profile timestamps accurate when Flask syncs Google account metadata.
create or replace function public.set_profile_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists set_profile_updated_at_trigger on public.profiles;
create trigger set_profile_updated_at_trigger
before update on public.profiles
for each row execute function public.set_profile_updated_at();

commit;
