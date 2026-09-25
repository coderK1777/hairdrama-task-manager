# Eight-minute TaskFlow walkthrough

Record after completing the checklist in `DEPLOYMENT_STATUS.md`. Use two Google
test accounts and keep inboxes restricted to the notification being demonstrated.
Do not show environment files, OAuth credentials, or browser session storage.

| Time | Show | Explain in your own words |
| --- | --- | --- |
| 0:00–0:30 | Public Vercel login page | This Hairdrama Tech assignment lets Google users create, assign, and complete tasks. |
| 0:30–1:10 | README architecture and folder tree | Next.js presents the UI; Flask owns task rules; Supabase hosts Auth and PostgreSQL; Gmail sends notifications. Vercel and Railway host the two application services. |
| 1:10–2:00 | Google login, callback, dashboard | Google authenticates the user through Supabase. The callback exchanges a one-use code using PKCE, stores the session, and syncs the profile through Flask. Refresh the page to demonstrate persistence. |
| 2:00–2:45 | SQL migration and Supabase tables | Profiles share IDs with Auth users. Tasks reference creator and assignee profiles. Database triggers create profiles and maintain completion timestamps. Show table structure without exposing credentials. |
| 2:45–3:30 | `backend/app.py`, `require_auth`, create route | The browser sends a bearer token. Flask verifies it with Supabase, gets the creator from that verified identity, validates the request, and saves the task. The server key bypasses RLS, so API authorization is essential. |
| 3:30–4:30 | Account A creates a task assigned to Account B | Explain the title, description, and registered-user dropdown. Show the saved row and the assignment email received by B. |
| 4:30–5:30 | Account B signs in and completes the task | B sees the assigned task. Completion updates its status and timestamp, and notifies A. Show A's received completion email. |
| 5:30–6:15 | `gmail_service.py` and the token helper | One app sender grants only Gmail send access. Its refresh token obtains short-lived access tokens. A mail failure leaves the task saved and reports a notification failure. |
| 6:15–7:00 | `.env.example`, `.gitignore`, permission migration | Only the public Supabase key reaches the browser. Private credentials are deployment environment variables. Direct database writes are restricted to Flask. Explain 401 versus 403. |
| 7:00–7:40 | Live URLs, deployment dashboards, test results | Show the Vercel site and Railway health endpoint, then mention build, lint, authorization tests, and CORS checks. Show the GitHub repository's real commit history. |
| 7:40–8:00 | Sign out and return to login | Mention remaining limitations honestly: synchronous mail, no retry queue, and no pagination. |

## Rehearsal checklist

- Both Google accounts have signed in once so both profiles exist.
- Supabase permits the exact production callback URL.
- Gmail is configured and both notification types arrive.
- Both database migrations are applied and verified.
- The two account sessions use separate browser profiles or one is signed out before the other signs in.
- The company can open the repository and has any required Google test-user access.
- Use a fresh demo task title that is easy to recognize in the app and inbox.

If Gmail or production login is still pending, describe it as pending rather than
presenting a successful demonstration that has not occurred.
