# TaskFlow

TaskFlow is a task-management application for the Hairdrama Tech assignment.
Users sign in with Google, create tasks, assign them to registered users, and
mark tasks complete. The Gmail integration notifies the assignee on creation
and the creator on completion.

## Deployment status

- Frontend: https://hairdrama-task-manager-red.vercel.app
- Backend health: https://flask-api-production-499c.up.railway.app/health
- Repository: https://github.com/coderK1777/hairdrama-task-manager

The frontend and backend are deployed. Local Google login, the frontend build,
lint, 13 backend/Gmail unit tests, and production HTTP/CORS checks have passed.
Gmail sender authorization and delivery tests are pending. Production login,
the two-user task flow, and application of the second database migration still
need verification.

## Features

- Google OAuth 2.0 login through Supabase Auth
- Automatic account/profile creation on first Google login
- Create a task and assign it to any registered user
- View tasks created by you or assigned to you
- Mark assigned tasks as completed
- Gmail API notification when a task is assigned
- Gmail API notification when a task is completed
- Responsive dashboard UI
- PostgreSQL schema and RLS policies in `/migrations`

## Technology

- **Frontend:** Next.js + TypeScript
- **Backend:** Flask (Python)
- **Database/Auth:** Supabase (PostgreSQL + Auth)
- **OAuth:** Google OAuth 2.0 via Supabase
- **Email:** Gmail API with OAuth 2.0
- **Deployment:** Vercel (frontend), Railway or Render (backend), Supabase (database/auth)

## Architecture

Next.js handles the interface and Supabase session. Google login returns through
Supabase to `/auth/callback`, where the browser exchanges the authorization code
for a session. Each API request includes the user's access token.

Flask verifies the token, checks task permissions, and reads or writes Supabase
using a server-only database key. After a task is saved or completed, Flask calls
Gmail using a separate sender account's OAuth credentials.

## Project Structure

```text
frontend/
  src/app/          Login, callback, and dashboard pages
  src/components/   Task form and task cards
  src/lib/          Supabase client and API helpers
backend/
  app.py            Authentication, validation, and task endpoints
  services/         Gmail integration
  scripts/          Sender authorization helper
  tests/            API and Gmail unit tests
migrations/         Initial schema and follow-up permission migration
scripts/            Read-only database verification
```

## Database

`profiles` stores the application identity linked to each Supabase Auth user.
`tasks` references its creator and assignee, with a title, description, status,
and creation/completion timestamps. Database triggers create profiles and
maintain timestamps.

## API Endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Deployment health check |
| `POST` | `/api/profile/sync` | Sync Google profile into `profiles` |
| `GET` | `/api/profiles` | List users available for assignment |
| `GET` | `/api/tasks` | List tasks related to logged-in user |
| `POST` | `/api/tasks` | Create and assign a task |
| `PATCH` | `/api/tasks/:id/complete` | Mark a related task complete |

All `/api/*` routes require `Authorization: Bearer <supabase_access_token>`.

## Local Setup

Requires Node.js 22 or later and Python 3.14. Before starting, copy
`frontend/.env.example` to `frontend/.env.local` and `backend/.env.example` to
`backend/.env`, then fill in the values. Preserve existing environment files
when updating a checkout.

### 1. Supabase

1. Create a Supabase project.
2. Open the SQL Editor and run the SQL files in `migrations/` in filename order.
   The first migration creates the schema. The second preserves rows and restricts
   writes to the server role, so browser clients cannot bypass Flask validation or
   Gmail notification logic. It also maintains profile update timestamps.
   Then run the read-only `scripts/verify_database.sql` to inspect constraints,
   indexes, triggers, RLS, grants, missing profiles, and task timestamps.
3. Copy your Project URL, anon/publishable key, and service-role secret.
4. Never put the service-role secret in the frontend.

### 2. Google login through Supabase

1. Create a Google Cloud project.
2. Configure the OAuth consent screen / Google Auth Platform audience.
3. Create a **Web application** OAuth client.
4. In Google Cloud, add the Supabase callback URL shown in Supabase's Google provider settings. It normally looks like:
   `https://YOUR_PROJECT_REF.supabase.co/auth/v1/callback`
5. In Supabase → Authentication → Providers → Google, enable Google and enter the web client ID and secret.
6. In Supabase Auth URL configuration, add both development and production frontend callback URLs, for example:
   - `http://localhost:3000/auth/callback`
   - `https://your-vercel-domain.vercel.app/auth/callback`

First Google login creates the Supabase Auth user; the database trigger creates the matching `profiles` row.

### 3. Gmail API sender

The app sends notification email from one application Gmail account. Individual users do not need to authorize inbox access.

1. Enable **Gmail API** in the Google Cloud project.
2. Create a **Desktop application** OAuth client for the notification sender.
3. Put that client ID and secret in `backend/.env`.
4. Add the sender Google account as a test user if your OAuth app is still in testing.
5. Generate a refresh token:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python scripts/generate_gmail_token.py
```

6. The helper saves `GMAIL_REFRESH_TOKEN` directly into the ignored `backend/.env`
   without printing it. Set `GMAIL_SENDER_EMAIL` to the account that granted consent.

The backend requests only the `gmail.send` scope.

### 4. Run the Flask API

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Backend: `http://localhost:5000`

Check: `http://localhost:5000/health`

### 5. Run Next.js

```bash
cd frontend
npm ci
npm run dev
```

Frontend: `http://localhost:3000`

## Environment Variables

### Frontend

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=http://localhost:5000
```

Only values prefixed with `NEXT_PUBLIC_` are exposed to browser code. Do not place secret keys there.

### Backend

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
FRONTEND_URL=http://localhost:3000
GMAIL_OAUTH_CLIENT_ID=
GMAIL_OAUTH_CLIENT_SECRET=
GMAIL_REFRESH_TOKEN=
GMAIL_SENDER_EMAIL=
```

## Deployment

### Frontend — Vercel

1. Push the repository to GitHub.
2. Import it into Vercel.
3. Set the project root directory to `frontend`.
4. Add the three frontend environment variables.
5. Deploy.

After deployment, copy the Vercel URL. You will use it for Supabase redirect configuration and backend CORS.

### Backend — Railway

1. Create a Railway project from the same GitHub repository.
2. Set the service root directory to `backend`.
3. Add all backend environment variables.
4. Set `FRONTEND_URL` to the Vercel production URL.
5. Use the checked-in `backend/railway.toml` start command and `/health` check.
   Gunicorn binds to `0.0.0.0:$PORT`; Railway supplies the port.
6. Generate a Railway public domain.
7. Update Vercel's `NEXT_PUBLIC_API_URL` with that Railway URL and redeploy the frontend.

The currently installed Railway CLI warns that `railway.toml` support ends on
December 1, 2026. Before that date, migrate the working service configuration with
`railway config migrate` and verify the generated infrastructure configuration.

### Final OAuth production setup

Add the final Vercel URL to Supabase Auth URL configuration, including:

```text
https://your-app.vercel.app/auth/callback
```

Then test Google login again in production.

## Authorization Rules

There are two layers:

1. **API authentication** — Flask verifies every Supabase access token using `supabase.auth.get_user(token)`.
2. **Business authorization** — task endpoints check whether the current user is the task creator or assignee before returning/updating data.

The database also has Row Level Security enabled as defense in depth.
After migration `202609250002_api_write_permissions.sql`, authenticated clients
have read access subject to RLS; only the backend service role can write.

## Verification

From `frontend`, run `npm ci`, `npm run lint`, and `npm run build`.
From `backend`, run `python -m unittest discover -s tests -v` after installing
requirements. These regression tests mock external services and do not replace
Google sign-in, database-trigger, or actual Gmail delivery tests.

## Email Flow

### New task

1. Creator sends `POST /api/tasks`.
2. Flask validates the assignee.
3. Flask inserts the task.
4. Flask calls Gmail API using the application sender's OAuth refresh token.
5. Assignee receives the new-task email.

### Completed task

1. Related user calls `PATCH /api/tasks/:id/complete`.
2. Flask verifies authorization.
3. Database updates task status and `completed_at`.
4. Flask sends a completion email to the task creator.

If Gmail temporarily fails, the task operation still succeeds and the API returns `email_sent: false`. This prevents an email outage from losing task data.

## Limitations

Notifications run during the API request; there is no background retry queue.
Task lists are not paginated. Accounts must sign in once before other users can
assign tasks to them.
