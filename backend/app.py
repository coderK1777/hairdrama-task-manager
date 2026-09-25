import logging
import os
from functools import wraps
from pathlib import Path
from typing import Any, Callable
from uuid import UUID

from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from supabase import Client, create_client
from werkzeug.exceptions import HTTPException

from services.gmail_service import send_email

load_dotenv(Path(__file__).with_name(".env"))
logging.basicConfig(level=logging.INFO)
# Auth URLs and upstream exception bodies do not belong in application logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
frontend_urls = [
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_URL", "http://localhost:3000").split(",")
    if origin.strip()
]
CORS(app, origins=frontend_urls, supports_credentials=False)


def error_response(message: str, status: int = 400):
    return jsonify({"error": message}), status


def get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.removeprefix("Bearer ").strip()


def require_auth(view: Callable[..., Any]):
    @wraps(view)
    def wrapped(*args, **kwargs):
        token = get_bearer_token()
        if not token:
            return error_response("Missing access token", 401)

        try:
            user_response = supabase.auth.get_user(token)
            user = user_response.user
            if not user:
                return error_response("Invalid access token", 401)

        except Exception:
            return error_response("Invalid or expired access token", 401)

        g.user = user
        return view(*args, **kwargs)

    return wrapped


def profile_payload(user) -> dict[str, Any]:
    metadata = user.user_metadata or {}
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": metadata.get("full_name") or metadata.get("name"),
        "avatar_url": metadata.get("avatar_url") or metadata.get("picture"),
    }


def get_profile(user_id: str) -> dict[str, Any] | None:
    result = (
        supabase.table("profiles")
        .select("id,email,full_name,avatar_url")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def decorate_task(task: dict[str, Any]) -> dict[str, Any]:
    task = dict(task)
    task["creator"] = get_profile(task["creator_id"])
    task["assignee"] = get_profile(task["assignee_id"])
    return task


def safe_send_email(to_email: str, subject: str, body: str) -> bool:
    try:
        send_email(to_email, subject, body)
        return True
    except Exception as exc:
        logger.warning("Email notification failed (%s)", type(exc).__name__)
        return False


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/profile/sync")
@require_auth
def sync_profile():
    payload = profile_payload(g.user)
    result = (
        supabase.table("profiles")
        .upsert(payload, on_conflict="id")
        .execute()
    )
    profile = result.data[0] if result.data else payload
    return jsonify({"profile": profile})


@app.get("/api/profiles")
@require_auth
def list_profiles():
    result = (
        supabase.table("profiles")
        .select("id,email,full_name,avatar_url")
        .order("full_name")
        .execute()
    )
    return jsonify({"profiles": result.data or []})


@app.get("/api/tasks")
@require_auth
def list_tasks():
    user_id = str(g.user.id)

    created = (
        supabase.table("tasks")
        .select("*")
        .eq("creator_id", user_id)
        .execute()
    ).data or []

    assigned = (
        supabase.table("tasks")
        .select("*")
        .eq("assignee_id", user_id)
        .execute()
    ).data or []

    unique_tasks = {task["id"]: task for task in created + assigned}
    ordered_tasks = sorted(
        unique_tasks.values(),
        key=lambda item: item["created_at"],
        reverse=True,
    )

    return jsonify({"tasks": [decorate_task(task) for task in ordered_tasks]})


@app.post("/api/tasks")
@require_auth
def create_task():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error_response("Request body must be a JSON object")
    if any(not isinstance(body.get(field, ""), str) for field in ("title", "description", "assignee_id")):
        return error_response("Title, description, and assignee must be text")
    title = body.get("title", "").strip()
    description = body.get("description", "").strip()
    assignee_id = body.get("assignee_id", "").strip()

    if not title:
        return error_response("Task title is required")
    if len(title) > 120:
        return error_response("Task title must be 120 characters or less")
    if "\r" in title or "\n" in title:
        return error_response("Task title must be a single line")
    if len(description) > 1000:
        return error_response("Description must be 1000 characters or less")
    if not assignee_id:
        return error_response("Assignee is required")
    try:
        assignee_id = str(UUID(assignee_id))
    except ValueError:
        return error_response("Assignee must be a valid user ID")

    assignee = get_profile(assignee_id)
    if not assignee:
        return error_response("Selected assignee does not exist", 404)

    creator = get_profile(str(g.user.id))
    if not creator:
        creator = profile_payload(g.user)
        supabase.table("profiles").upsert(creator, on_conflict="id").execute()

    task_data = {
        "title": title,
        "description": description or None,
        "creator_id": str(g.user.id),
        "assignee_id": assignee_id,
        "status": "pending",
    }

    result = supabase.table("tasks").insert(task_data).execute()
    if not result.data:
        return error_response("Could not create task", 500)

    task = decorate_task(result.data[0])
    creator_name = creator.get("full_name") or creator.get("email")

    email_body = (
        f"Hi {assignee.get('full_name') or assignee['email']},\n\n"
        f"{creator_name} assigned you a new task.\n\n"
        f"Task: {title}\n"
        "Status: Pending\n"
        f"Description: {description or 'No description provided'}\n\n"
        "Open TaskFlow to review the task."
    )
    email_sent = safe_send_email(
        assignee["email"],
        f"New task assigned: {title}",
        email_body,
    )

    return jsonify({"task": task, "email_sent": email_sent}), 201


@app.patch("/api/tasks/<task_id>/complete")
@require_auth
def complete_task(task_id: str):
    try:
        task_id = str(UUID(task_id))
    except ValueError:
        return error_response("Task ID must be a valid UUID")
    result = (
        supabase.table("tasks")
        .select("*")
        .eq("id", task_id)
        .limit(1)
        .execute()
    )
    if not result.data:
        return error_response("Task not found", 404)

    task = result.data[0]
    user_id = str(g.user.id)

    if user_id not in {task["creator_id"], task["assignee_id"]}:
        return error_response("You are not allowed to update this task", 403)

    if task["status"] == "completed":
        return jsonify({"task": decorate_task(task), "email_sent": False, "already_completed": True})

    update_result = (
        supabase.table("tasks")
        .update({"status": "completed"})
        .eq("id", task_id)
        .eq("status", "pending")
        .execute()
    )
    if not update_result.data:
        return error_response("Task changed while completing it. Refresh and try again.", 409)

    completed_task = decorate_task(update_result.data[0])
    creator = completed_task.get("creator")
    assignee = completed_task.get("assignee")

    email_sent = False
    if creator and creator.get("email"):
        actor = profile_payload(g.user)
        actor_name = actor.get("full_name") or actor.get("email") or "A task participant"
        assignee_name = (assignee or {}).get("full_name") or (assignee or {}).get("email") or "Unknown"
        email_body = (
            f"Hi {creator.get('full_name') or creator['email']},\n\n"
            f"{actor_name} completed the task below.\n\n"
            f"Task: {completed_task['title']}\n"
            f"Assigned to: {assignee_name}\n"
            "Status: Completed\n"
            f"Completed at: {completed_task.get('completed_at')}\n\n"
            "Open TaskFlow to view the latest status."
        )
        email_sent = safe_send_email(
            creator["email"],
            f"Task completed: {completed_task['title']}",
            email_body,
        )

    return jsonify({"task": completed_task, "email_sent": email_sent})


@app.errorhandler(404)
def not_found(_error):
    return error_response("Route not found", 404)


@app.errorhandler(Exception)
def server_error(error):
    if isinstance(error, HTTPException):
        return error_response(error.name, error.code or 500)
    logger.error("Request failed (%s)", type(error).__name__)
    return error_response("Internal server error", 500)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
