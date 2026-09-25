# Deployment progress

This is a work-in-progress record, not a production completion report.

## Verified locally

- Supabase project: `qweubbwocnjilqjxlnqz`.
- User reported successful execution of `202609250001_initial_schema.sql`.
- Both tables and all expected columns are accessible through Supabase REST.
- Both tables were empty at the time of verification.
- Local environment files created; excluded by `.gitignore`.
- Frontend production build and TypeScript checks pass.
- ESLint passes; npm install audit reported no vulnerabilities.
- Backend dependencies installed; `pip check` passes.
- Thirteen mocked backend/Gmail regression tests pass. Run from `backend` with
  `.venv\Scripts\python.exe -m unittest discover -s tests -v` on Windows.
- Running frontend serves the login page at `http://localhost:3000`.
- Running backend returns HTTP 200 at `/health` and HTTP 401 for unauthenticated task requests.
- Google provider enabled, verified through Supabase Auth settings.
- User confirmed the dashboard opened after Google login in a fresh browser session.
- An earlier Google-hosted HTTP 500 after account selection did not recur in the fresh session; its cause is unconfirmed.

## Changes made

- Callback exclusively handles PKCE exchange and avoids duplicate effect execution.
- Dashboard tracks refreshed session tokens and handles logout failures.
- Profile sync finishes before loading assignment choices.
- Backend validates JSON types, lengths, single-line titles, and UUIDs.
- Backend errors no longer masquerade as authentication errors or expose exception text.
- Completion update checks pending status to avoid duplicate notifications from concurrent requests.
- Repeated completion no longer claims that an email was sent.
- Completion email identifies the actual actor and includes completion time.
- Gunicorn binds to Railway's injected `PORT`.
- Added ESLint configuration, npm lockfile, and broader credential-file exclusions.

## Still required

- Verify session persistence, logout, and a second Google account locally.
- Production OAuth redirect configuration.
- Gmail sender consent, API enablement, credentials, and real delivery tests.
- Apply the prepared second migration to restrict direct database writes so clients cannot bypass Flask rules and notifications.
- Verify foreign keys, indexes, RLS, profile trigger, and timestamps against the live database.
- Browser-based, two-account end-to-end testing; current session has no browser-control tool.
- Complete GitHub push and confirm repository access for company reviewers.
- Update this record as the remaining integration checks are completed.

Frontend: https://hairdrama-task-manager-red.vercel.app

Backend: https://flask-api-production-499c.up.railway.app

Repository: https://github.com/coderK1777/hairdrama-task-manager

Created as private while repository visibility preference is pending. Company
reviewers need invitations unless the repository is changed to public.

## Hosting setup

- Vercel CLI authenticated; team `task-flow-demo` (TaskFlow Demo, Hobby).
- Created and linked Vercel project `hairdrama-task-manager` using the `frontend` directory.
- Configured production variables `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
- Configured and verified all three production frontend variables, including `NEXT_PUBLIC_API_URL`.
- Added frontend upload exclusions and Railway build/start/healthcheck configuration.
- Railway CLI authenticated; project `fdb184f9-889a-428d-9d1d-53d85c25589b`.
- Railway service `flask-api` (`f2f075b9-dff9-4ece-83c2-22531b0cda9f`) deployed with Gunicorn.
- Backend public `/health` returns 200; unauthenticated task/profile endpoints return 401.
- Vercel production deployment `dpl_KMrcKCYv6KRANea1spuHqfE1KXKq` is READY.
- Vercel public home redirects to `/login` and serves the Google login button with HTTP 200.
- Set Railway `FRONTEND_URL` to the canonical Vercel origin; verified production CORS permits it and rejects an unrelated origin.
- User action pending: add production callback and Site URL in Supabase Auth URL configuration.
- Added `202609250002_api_write_permissions.sql`; not applied to Supabase yet.
- Gmail environment variables are not configured; notification delivery is not yet available.
- Gmail token helper now saves refresh tokens to the ignored local environment file without printing them.
- Git installed locally from the official MinGit release; SHA256 verified.
- GitHub CLI authenticated as `coderK1777`.
- Added the eight-minute Loom plan and a file-by-file interview guide.
