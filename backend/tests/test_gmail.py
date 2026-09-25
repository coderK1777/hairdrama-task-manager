"""Verify Gmail MIME construction without contacting Google or sending email."""

import base64
import os
import unittest
from email import policy
from email.parser import BytesParser
from unittest.mock import patch

from services import gmail_service


class GmailTests(unittest.TestCase):
    @patch.dict(os.environ, {
        "GMAIL_SENDER_EMAIL": "sender@example.com",
        "GMAIL_OAUTH_CLIENT_ID": "example-client",
        "GMAIL_OAUTH_CLIENT_SECRET": "test-only-secret",
        "GMAIL_REFRESH_TOKEN": "test-only-refresh-token",
    }, clear=True)
    @patch.object(gmail_service, "build")
    def test_message_uses_send_scope_and_expected_recipient(self, build):
        gmail_service.send_email("assignee@example.com", "Task: Review", "Review the page.\nStatus: Pending")
        args, kwargs = build.call_args
        self.assertEqual(args, ("gmail", "v1"))
        self.assertEqual(kwargs["credentials"].scopes, [gmail_service.GMAIL_SCOPE])
        send = build.return_value.users.return_value.messages.return_value.send
        self.assertEqual(send.call_args.kwargs["userId"], "me")
        raw = base64.urlsafe_b64decode(send.call_args.kwargs["body"]["raw"])
        message = BytesParser(policy=policy.default).parsebytes(raw)
        self.assertEqual(message["To"], "assignee@example.com")
        self.assertEqual(message["From"], "sender@example.com")
        self.assertEqual(message["Subject"], "Task: Review")
        self.assertIn("Status: Pending", message.get_content())
        send.return_value.execute.assert_called_once_with()

    @patch.dict(os.environ, {}, clear=True)
    @patch.object(gmail_service, "build")
    def test_unconfigured_sender_fails_before_network_request(self, build):
        with self.assertRaisesRegex(RuntimeError, "GMAIL_SENDER_EMAIL"):
            gmail_service.send_email("assignee@example.com", "Task", "Details")
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
