"""
conftest.py — shared pytest fixtures for Elite Job Agent test suite.
"""
import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Vault fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_vault(tmp_path, monkeypatch):
    """Redirect vault.dat to a fresh temp file for isolation."""
    vault_path = str(tmp_path / "vault.dat")
    monkeypatch.setattr("security_vault.VAULT_FILE", vault_path)
    return vault_path


# ---------------------------------------------------------------------------
# Mock Gmail service
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_gmail_service():
    """Return a fully mocked Gmail API service object."""
    svc = MagicMock()

    # users().messages().list()
    svc.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "msg001"}, {"id": "msg002"}]
    }

    # users().messages().get()
    svc.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "msg001",
        "threadId": "thread001",
        "labelIds": ["INBOX"],
        "snippet": "Test email snippet",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Test Subject"},
                {"name": "From",    "value": "sender@example.com"},
                {"name": "To",      "value": "recipient@example.com"},
                {"name": "Date",    "value": "Thu, 10 Apr 2026 01:00:00 +0000"},
            ],
            "body": {"data": "SGVsbG8gV29ybGQ="},  # "Hello World" b64
        }
    }

    # users().messages().send()
    svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "sent001"
    }

    # users().drafts().create()
    svc.users.return_value.drafts.return_value.create.return_value.execute.return_value = {
        "id": "draft_d001"
    }

    # users().drafts().list()
    svc.users.return_value.drafts.return_value.list.return_value.execute.return_value = {
        "drafts": [{"id": "d001", "message": {"id": "msg001"}}]
    }

    # users().getProfile()
    svc.users.return_value.getProfile.return_value.execute.return_value = {
        "emailAddress": "test@example.com"
    }

    # users().labels().list()
    svc.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [{"id": "INBOX", "name": "INBOX"}]
    }

    # users().messages().modify()
    svc.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}

    return svc


@pytest.fixture
def authenticated_email_client(mock_gmail_service):
    """Return an EmailClient pre-loaded with a mock Gmail service."""
    from email_client import EmailClient
    client = EmailClient()
    client.service = mock_gmail_service
    client._profile = {"emailAddress": "test@example.com"}
    return client
