"""API regression tests. External auth, database, and Gmail calls are mocked."""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# These tests never use a real project's credentials.
os.environ["SUPABASE_URL"] = "https://example.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-only-key"

import app as api

CREATOR = "11111111-1111-4111-8111-111111111111"
ASSIGNEE = "22222222-2222-4222-8222-222222222222"
OTHER = "33333333-3333-4333-8333-333333333333"
TASK_ID = "44444444-4444-4444-8444-444444444444"
HEADERS = {"Authorization": "Bearer test-user-token"}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = api.app.test_client()
        self.db_patch = patch.object(api, "supabase")
        self.db = self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.db.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(
            id=CREATOR, email="creator@example.com", user_metadata={"name": "Creator"}
        ))
        self.query = MagicMock()
        for method in ("select", "eq", "limit", "order", "insert", "update", "upsert"):
            getattr(self.query, method).return_value = self.query
        self.db.table.return_value = self.query
        self.task = {
            "id": TASK_ID, "title": "Review", "description": None,
            "creator_id": CREATOR, "assignee_id": ASSIGNEE,
            "status": "pending", "created_at": "2026-09-25T00:00:00Z",
            "completed_at": None,
        }

    def test_protected_routes_require_token(self):
        for method, path in [("get", "/api/profiles"), ("get", "/api/tasks"),
                             ("post", "/api/tasks"), ("post", "/api/profile/sync"),
                             ("patch", f"/api/tasks/{TASK_ID}/complete")]:
            with self.subTest(path=path):
                self.assertEqual(getattr(self.client, method)(path).status_code, 401)
        self.db.table.assert_not_called()

    def test_invalid_token_does_not_leak_upstream_error(self):
        self.db.auth.get_user.side_effect = RuntimeError("private-auth-detail")
        response = self.client.get("/api/tasks", headers=HEADERS)
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("private-auth-detail", response.get_data(as_text=True))

    def test_database_failure_is_500_not_auth_failure(self):
        self.query.execute.side_effect = RuntimeError("private-database-detail")
        response = self.client.get("/api/profiles", headers=HEADERS)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json, {"error": "Internal server error"})

    def test_invalid_task_inputs_never_reach_database(self):
        for payload in [[], None, {"title": None}, {"title": 23},
                        {"title": " "}, {"title": "x" * 121},
                        {"title": "injected\nsubject"},
                        {"title": "Test", "assignee_id": "bad-id"},
                        {"title": "Test", "description": "x" * 1001}]:
            with self.subTest(payload=payload):
                response = self.client.post("/api/tasks", json=payload, headers=HEADERS)
                self.assertEqual(response.status_code, 400)
        self.db.table.assert_not_called()

    def test_invalid_task_id_is_400(self):
        response = self.client.patch("/api/tasks/not-a-uuid/complete", headers=HEADERS)
        self.assertEqual(response.status_code, 400)
        self.db.table.assert_not_called()

    def test_unrelated_user_cannot_complete(self):
        self.db.auth.get_user.return_value.user.id = OTHER
        self.query.execute.return_value.data = [self.task]
        response = self.client.patch(f"/api/tasks/{TASK_ID}/complete", headers=HEADERS)
        self.assertEqual(response.status_code, 403)
        self.query.update.assert_not_called()

    @patch.object(api, "send_email")
    @patch.object(api, "decorate_task", side_effect=lambda task: task)
    def test_repeat_completion_does_not_claim_or_send_email(self, _decorate, send):
        self.task["status"] = "completed"
        self.query.execute.return_value.data = [self.task]
        response = self.client.patch(f"/api/tasks/{TASK_ID}/complete", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json["already_completed"])
        self.assertFalse(response.json["email_sent"])
        self.query.update.assert_not_called()
        send.assert_not_called()

    @patch.object(api, "send_email")
    def test_concurrent_completion_does_not_send_duplicate_email(self, send):
        self.query.execute.side_effect = [SimpleNamespace(data=[self.task]), SimpleNamespace(data=[])]
        response = self.client.patch(f"/api/tasks/{TASK_ID}/complete", headers=HEADERS)
        self.assertEqual(response.status_code, 409)
        self.query.eq.assert_any_call("status", "pending")
        send.assert_not_called()

    @patch.object(api, "send_email", side_effect=RuntimeError("private-email-detail"))
    @patch.object(api, "decorate_task", side_effect=lambda task: task)
    @patch.object(api, "get_profile")
    def test_task_survives_email_failure_and_creator_cannot_be_forged(self, profile, _decorate, _send):
        profile.side_effect = [
            {"id": ASSIGNEE, "email": "assignee@example.com"},
            {"id": CREATOR, "email": "creator@example.com"},
        ]
        self.query.execute.return_value.data = [self.task]
        response = self.client.post("/api/tasks", headers=HEADERS, json={
            "title": "Review", "assignee_id": ASSIGNEE, "creator_id": OTHER,
        })
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json["email_sent"])
        self.assertEqual(self.query.insert.call_args.args[0]["creator_id"], CREATOR)
        self.assertNotIn("private-email-detail", response.get_data(as_text=True))

    def test_cors_allows_only_configured_origin(self):
        for origin, expected in [("http://localhost:3000", "http://localhost:3000"),
                                 ("https://unrelated.example", None)]:
            response = self.client.options("/api/tasks", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization,content-type",
            })
            self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), expected)

    def test_oversized_body_returns_json_error(self):
        response = self.client.post("/api/tasks", headers=HEADERS,
                                    data="x" * 20000, content_type="application/json")
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json, {"error": "Request Entity Too Large"})


if __name__ == "__main__":
    unittest.main()
