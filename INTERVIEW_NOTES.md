# TaskFlow Interview Notes

Use this as a study sheet. Do not memorize sentences; understand the request flow and explain it in your own words.

## 1. Login flow

**Files:** `frontend/src/lib/supabase.ts`, `frontend/src/app/login/page.tsx`, `frontend/src/app/auth/callback/page.tsx`

1. `supabase.ts` creates one browser Supabase client using the public project URL and anon/publishable key.
2. Clicking **Continue with Google** calls `supabase.auth.signInWithOAuth({ provider: "google" })`.
3. Google authenticates the user and returns through Supabase to `/auth/callback`.
4. The callback exchanges the authorization code for a Supabase session.
5. The session contains an access token. That token represents the logged-in user.
6. We call `/api/profile/sync` so the backend has an up-to-date profile.

**Important:** the anon/publishable key is allowed in browser code. The service-role key is not.

## 2. How frontend calls Flask

**File:** `frontend/src/lib/api.ts`

Every API call adds:

```text
Authorization: Bearer <supabase access token>
```

The API helper also has one place for JSON parsing and error handling so components remain simple.

## 3. How Flask authenticates the user

**File:** `backend/app.py`

`require_auth` is a custom decorator.

1. Read the `Authorization` header.
2. Extract the bearer token.
3. Call `supabase.auth.get_user(token)`.
4. If Supabase confirms the token, save that user on Flask's request-local `g` object.
5. If verification fails, return HTTP `401`.

This means the API never trusts a user ID sent by the browser.

## 4. Profiles

Google/Supabase authentication data lives in `auth.users`. Our application also needs a simple table that can be queried when assigning tasks.

The migration creates `public.profiles` with:

- `id`
- `email`
- `full_name`
- `avatar_url`

A database trigger automatically creates the profile after a new Auth user is inserted. `/api/profile/sync` updates it on later logins in case the user's Google name/avatar changes.

## 5. Creating a task

**Frontend:** `CreateTaskForm.tsx` → `createTask()` in `api.ts`

**Backend:** `POST /api/tasks`

Backend sequence:

1. Verify login token.
2. Validate title, description, and assignee ID.
3. Confirm the assignee exists.
4. Create the task with the logged-in user's ID as `creator_id`.
5. Read the inserted row.
6. Send a Gmail notification to the assignee.
7. Return the task plus `email_sent`.

The frontend never sends `creator_id`. Flask gets it from the verified token. This prevents a user from pretending another person created a task.

## 6. Viewing tasks

**Backend:** `GET /api/tasks`

We return only tasks where the current user is either:

- `creator_id`, or
- `assignee_id`

We merge those two query results by task UUID so a self-assigned task is not duplicated.

## 7. Completing a task

**Backend:** `PATCH /api/tasks/<task_id>/complete`

1. Load the task.
2. Check that the logged-in user is its creator or assignee.
3. Update status to `completed`.
4. A database trigger sets `completed_at`.
5. Send a completion email to the task creator.

The UI only shows **Mark complete** on tasks assigned to the current user, although the API still checks authorization because UI restrictions are not security.

## 8. Gmail integration

**File:** `backend/services/gmail_service.py`

The backend uses one Gmail sender account.

We store these only on the server:

- OAuth client ID
- OAuth client secret
- refresh token
- sender Gmail address

The refresh token lets Google's library obtain short-lived access tokens without making the sender log in for every email.

The scope is only:

```text
https://www.googleapis.com/auth/gmail.send
```

That is better than requesting full inbox access because the application only needs to send notifications.

The email is built as an `EmailMessage`, converted to base64 URL-safe content, then sent through Gmail API `users.messages.send`.

## 9. Why email errors do not undo task changes

`safe_send_email()` catches Gmail failures.

Example: the database successfully creates a task but Gmail is temporarily unavailable. It is better to keep the valid task and tell the frontend `email_sent: false` than to lose the task completely.

In a larger production system, a queue/retry worker would be a good improvement.

## 10. Database security

**File:** `migrations/202609250001_initial_schema.sql`

Important parts:

- primary keys identify rows uniquely
- foreign keys guarantee creators/assignees reference real profiles
- check constraint limits status values
- indexes make creator/assignee/status lookup faster
- triggers control profile creation and completion timestamps
- Row Level Security policies protect data if the database is called directly in the future

The current Flask API uses the Supabase service role, which bypasses RLS. That is why Flask must perform its own authorization checks. The service key is kept only in backend environment variables.

The second migration, `202609250002_api_write_permissions.sql`, removes direct
browser write privileges. It keeps authenticated reads governed by RLS and adds
an update-time trigger for profiles. This prevents a direct database write from
skipping Flask validation or notification sending.

## 11. Why Flask instead of Next.js API routes?

The assignment specifically requires Flask. Keeping all business logic in Flask also gives one clear backend boundary for authentication, database access, validation, and Gmail integration.

## 12. Why Vercel + Railway?

- Vercel is optimized for Next.js deployment.
- Railway can run the Flask app behind Gunicorn.
- Supabase hosts Postgres and Auth.

The frontend's production environment variable points to the Railway backend URL, while Railway's CORS setting allows only the Vercel frontend origin.

## 13. Terms to understand

### OAuth 2.0
A protocol that lets an application obtain limited authorization without handling the user's Google password.

### Access token
Short-lived credential used to prove the current authenticated session.

### Refresh token
Longer-lived credential used by a trusted server to obtain new access tokens.

### HTTP 401 vs 403
- `401`: not authenticated / bad token.
- `403`: authenticated, but not allowed to perform that action.

### CORS
Browser security rule controlling which website origins are allowed to call the backend.

### RLS
Postgres/Supabase row-level policies that control which rows a user can access.

### Gunicorn
Production WSGI server used to run Flask. Flask's built-in development server should not be used for production traffic.

## 14. Demo preparation

Before recording Loom, create two Google test accounts/users:

1. Log in as User A once.
2. Log out.
3. Log in as User B once.
4. Log out and return as User A.
5. User A assigns a task to User B.
6. Show User B received the new-task email.
7. Log in as User B and complete it.
8. Show User A received the completion email.

This demonstrates every required assignment feature in one clean flow.

## 15. File-by-file interview map

| File | Purpose and data flow | Question to practice |
| --- | --- | --- |
| `frontend/src/app/page.tsx` | Redirects the home URL to login; the login page checks for an existing session. | Why redirect instead of duplicating the login UI? |
| `frontend/src/app/layout.tsx` | Supplies common page markup, metadata, and global CSS. | What belongs in an App Router layout? |
| `frontend/src/app/globals.css` | Styles forms, cards, and responsive layouts. Media queries collapse the desktop sidebar and task grid. | How does the dashboard adapt to mobile widths? |
| `frontend/src/lib/supabase.ts` | Creates the shared browser client with public credentials, PKCE, and persistent sessions. Automatic URL exchange is disabled because the callback owns it. | Why must only one place exchange the OAuth code? |
| `frontend/src/app/login/page.tsx` | `handleGoogleLogin` starts Google OAuth and supplies the current origin's callback; an existing session redirects to the dashboard. | Why does the redirect use `window.location.origin`? |
| `frontend/src/app/auth/callback/page.tsx` | `finishLogin` exchanges the code, checks the session, syncs the profile, and routes to the dashboard. A ref prevents duplicate effect execution. | Why might React development mode run an effect twice? |
| `frontend/src/app/dashboard/page.tsx` | `loadData` syncs the profile then loads users and tasks; create/complete handlers update local state. The auth subscription tracks refreshed tokens. | What happens when an access token expires while the page remains open? |
| `frontend/src/components/CreateTaskForm.tsx` | Owns title, description, and assignee form state; `handleSubmit` sends trimmed input to its parent. | Why validate again on the backend? |
| `frontend/src/components/TaskCard.tsx` | Renders task status and participants; offers completion for the current assignee. | Does hiding a button enforce authorization? |
| `frontend/src/lib/api.ts` | `apiRequest` attaches the bearer token, parses JSON, and converts API errors into UI errors. Typed endpoint helpers describe expected results. | Does a TypeScript type validate the actual server response? |
| `frontend/package.json`, `package-lock.json` | Define scripts and dependencies; the lockfile pins the resolved dependency tree for reproducible installs. | Why use `npm ci` for a clean build? |
| `frontend/tsconfig.json`, `next.config.ts`, `eslint.config.mjs` | Configure TypeScript, Next.js strict mode, and lint checks. | What does each check catch that the others may miss? |
| `backend/app.py` | `require_auth` verifies identity; profile and task routes apply validation and authorization; `safe_send_email` isolates notification failure. | Why must a database error return 500 rather than 401? |
| `backend/services/gmail_service.py` | Builds a plain-text MIME message, base64url-encodes it, and calls Gmail `users.messages.send` using refreshed sender credentials. | Why request `gmail.send` instead of inbox access? |
| `backend/scripts/generate_gmail_token.py` | Runs one-time sender consent on a localhost callback and saves the refresh token into ignored `.env` without printing it. | How do Google login credentials differ from the app sender's credentials? |
| `backend/tests/test_api.py` | Tests invalid input, ownership checks, safe errors, CORS, and completion races with external services mocked. | Which failures still need integration tests? |
| `backend/tests/test_gmail.py` | Verifies the recipient, sender, MIME content, and scope without sending real mail. | Why isn't a mocked Gmail test proof of delivery? |
| `backend/requirements.txt`, `.python-version` | Specify Python dependencies and the deployed interpreter version. | Why pin the runtime and application dependencies? |
| `backend/Procfile`, `railway.toml` | Start Gunicorn on the platform port and configure health checks/restarts. | Why isn't Flask's development server used in production? |
| `migrations/202609250001_initial_schema.sql` | Creates profiles/tasks, foreign keys, indexes, RLS, and triggers for profile creation and completion time. | What guarantees should live in PostgreSQL instead of frontend code? |
| `migrations/202609250002_api_write_permissions.sql` | Preserves data while restricting writes to the backend role and maintaining profile update time. | Why can RLS alone not protect a service-role request? |
| `.env.example`, component `.env.example` files | Document variable names with placeholders; actual values live only in ignored files and hosting settings. | Which variables are bundled into browser JavaScript? |
| `.gitignore`, `.vercelignore`, `.railwayignore` | Keep credentials, dependencies, caches, and local tooling out of repository or deployment uploads. | Why scan tracked files even when ignore rules exist? |
| `README.md`, `DEPLOYMENT_STATUS.md`, `LOOM_WALKTHROUGH.md` | Explain setup/architecture, record evidence and unfinished checks, and organize the demo. | What is deployed versus actually verified end to end? |

## 16. Tradeoffs to explain

- Completion is allowed to the creator or assignee in the API; the normal UI offers it to the assignee.
- A conditional update from pending prevents two simultaneous completions from sending duplicate emails.
- Email delivery runs during the request. There is no durable outbox or automatic retry, so a failed notification needs manual follow-up.
- The first migration is an idempotent schema setup, not a schema drift repair tool. Later changes use new migration files.
- RLS is defense in depth for direct reads. The backend bypasses RLS and must check every protected operation.
- The dashboard currently loads all related tasks; pagination and batching profile reads would be the next scaling improvements.
- Build and mocked tests pass independently of OAuth and Gmail account configuration. Only a real browser login and inbox check prove those flows.
