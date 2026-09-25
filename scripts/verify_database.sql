-- Read-only verification. Run in Supabase SQL Editor after both migrations.
-- Returns structure and counts, never account emails or credentials.

select c.relname as table_name, c.relrowsecurity as rls_enabled
from pg_class c join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public' and c.relname in ('profiles', 'tasks');

select conrelid::regclass as table_name, conname, pg_get_constraintdef(oid) as definition
from pg_constraint
where conrelid in ('public.profiles'::regclass, 'public.tasks'::regclass)
order by conrelid::regclass::text, conname;

select tablename, indexname, indexdef
from pg_indexes
where schemaname = 'public' and tablename in ('profiles', 'tasks')
order by tablename, indexname;

select tgrelid::regclass as table_name, tgname, tgenabled,
       pg_get_triggerdef(oid) as definition
from pg_trigger
where not tgisinternal
  and tgrelid in ('auth.users'::regclass, 'public.profiles'::regclass, 'public.tasks'::regclass);

select tablename, policyname, roles, cmd, qual, with_check
from pg_policies
where schemaname = 'public' and tablename in ('profiles', 'tasks');

-- Expected: authenticated SELECT true; authenticated writes false; anon all false.
-- Service role must be able to read and write both tables.
select role_name, table_name, privilege,
       has_table_privilege(role_name, table_name, privilege) as allowed
from unnest(array['anon', 'authenticated', 'service_role']) as role_name
cross join unnest(array['public.profiles', 'public.tasks']) as table_name
cross join unnest(array['SELECT', 'INSERT', 'UPDATE', 'DELETE']) as privilege;

select count(*) as auth_users_missing_profiles
from auth.users u left join public.profiles p on p.id = u.id
where p.id is null;

select count(*) as inconsistent_task_timestamps
from public.tasks
where (status = 'completed' and completed_at is null)
   or (status = 'pending' and completed_at is not null)
   or updated_at < created_at;
