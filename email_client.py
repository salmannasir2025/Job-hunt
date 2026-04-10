"""
email_client.py
===============
Gmail API client for the Job Hunt platform.

Features
--------
- OAuth 2.0 authentication with automatic token refresh
- Read emails from inbox, sent, drafts
- Compose and send emails with file attachments
- Search emails using Gmail query syntax
- Manage labels (add/remove, mark read/unread)
- Thread-safe singleton access via get_email_client()

Usage
-----
    from email_client import get_email_client

    client = get_email_client()
    if client.authenticate():
        emails = client.get_inbox(limit=20)
        email  = client.get_email(email_id)
        client.send_email(to, subject, body, attachments=[cv_path])
"""

from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime
import base64
import os
import threading

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.header import Header
from email import encoders

from security_vault import get_key


# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class Email:
    """Represents a single Gmail message."""
    id: str
    thread_id: str
    subject: str
    sender: str
    recipient: str
    date: str
    snippet: str
    body: str = ""
    is_read: bool = True
    labels: List[str] = field(default_factory=list)
    attachments: List[Dict] = field(default_factory=list)


@dataclass
class Attachment:
    """Represents a downloaded email attachment."""
    filename: str
    mime_type: str
    size: int
    data: bytes = None


# ---------------------------------------------------------------------------
# Gmail scopes
# ---------------------------------------------------------------------------

_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]


# ---------------------------------------------------------------------------
# EmailClient
# ---------------------------------------------------------------------------

class EmailClient:
    """
    Full-featured Gmail API client.

    All public methods return sensible defaults (empty lists / False / None)
    when the client is not authenticated so callers don't need to guard every
    call.
    """

    def __init__(self) -> None:
        self.service = None
        self.creds = None
        self._lock = threading.Lock()
        self._profile: Optional[Dict] = None

    # ------------------------------------------------------------------ auth

    def authenticate(self, client_secret_path: str = None) -> bool:
        """
        Authenticate with Gmail API using OAuth 2.0.

        Falls back to the path stored in the security vault when
        *client_secret_path* is not provided explicitly.

        Returns True on success, False on any failure.
        """
        if client_secret_path is None:
            client_secret_path = get_key("client_secret_path")

        if not client_secret_path or not os.path.exists(client_secret_path):
            print("EmailClient: client_secret.json path is missing or invalid.")
            return False

        try:
            from googleapiclient.discovery import build
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request

            token_path = os.path.join(os.getcwd(), "token.json")

            # --- Try existing token first ---
            if os.path.exists(token_path):
                self.creds = Credentials.from_authorized_user_file(token_path, _SCOPES)

                if self.creds and self.creds.valid:
                    self._build_service()
                    return True

                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                    self._build_service()
                    self._save_token(token_path)
                    return True

            # --- Interactive browser flow ---
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, _SCOPES)
            self.creds = flow.run_local_server(port=8080, open_browser=True)
            self._save_token(token_path)
            self._build_service()
            return True

        except Exception as exc:
            print(f"EmailClient: Authentication failed — {exc}")
            return False

    def _build_service(self) -> None:
        """Build the Gmail service object and fetch the user's profile."""
        from googleapiclient.discovery import build
        self.service = build("gmail", "v1", credentials=self.creds)
        try:
            self._profile = self.service.users().getProfile(userId="me").execute()
        except Exception:
            self._profile = {}

    def _save_token(self, token_path: str) -> None:
        """Persist credentials to token.json (thread-safe)."""
        with self._lock:
            with open(token_path, "w") as fh:
                fh.write(self.creds.to_json())

    def is_authenticated(self) -> bool:
        """Return True if the Gmail service is ready."""
        return self.service is not None

    def get_email_address(self) -> str:
        """Return the authenticated user's email address."""
        return (self._profile or {}).get("emailAddress", "")

    # --------------------------------------------------------- reading emails

    def get_inbox(self, limit: int = 20, label: str = None) -> List[Email]:
        """
        Fetch emails from a Gmail label (default: INBOX).

        Args:
            limit: Maximum number of messages to return.
            label: Gmail system label (INBOX, SENT, DRAFTS, SPAM, TRASH …).

        Returns:
            List of :class:`Email` objects (metadata only, no full body).
        """
        if not self.service:
            return []

        try:
            results = self.service.users().messages().list(
                userId="me",
                maxResults=limit,
                q=f"label:{label or 'INBOX'}",
            ).execute()

            emails: List[Email] = []
            for msg in results.get("messages", []):
                email = self._get_email_metadata(msg["id"])
                if email:
                    emails.append(email)
            return emails

        except Exception as exc:
            print(f"EmailClient.get_inbox: {exc}")
            return []

    def get_drafts(self, limit: int = 20) -> List[Email]:
        """Return saved draft messages."""
        if not self.service:
            return []

        try:
            results = self.service.users().drafts().list(
                userId="me", maxResults=limit
            ).execute()

            emails: List[Email] = []
            for draft in results.get("drafts", []):
                msg_id = draft.get("message", {}).get("id", "")
                if not msg_id:
                    continue
                full_msg = self.service.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
                email = self._parse_message(full_msg)
                email.id = f"draft_{msg_id}"  # prefix so callers can tell
                emails.append(email)
            return emails

        except Exception as exc:
            print(f"EmailClient.get_drafts: {exc}")
            return []

    def get_sent(self, limit: int = 20) -> List[Email]:
        """Return sent messages."""
        return self.get_inbox(limit=limit, label="SENT")

    def get_email(self, email_id: str, include_body: bool = True) -> Optional[Email]:
        """
        Fetch a complete email by its ID.

        Accepts the *draft_* prefix used by :meth:`get_drafts`.
        """
        if not self.service:
            return None

        # Handle draft_ prefix
        if email_id.startswith("draft_"):
            actual_id = email_id[6:]
            try:
                draft = self.service.users().drafts().get(
                    userId="me", id=actual_id
                ).execute()
                return self._parse_message(draft.get("message", {}))
            except Exception:
                return None

        try:
            fmt = "full" if include_body else "metadata"
            msg = self.service.users().messages().get(
                userId="me", id=email_id, format=fmt
            ).execute()
            return self._parse_message(msg)

        except Exception as exc:
            print(f"EmailClient.get_email({email_id}): {exc}")
            return None

    def get_unread_count(self) -> int:
        """Return the number of unread messages in the Inbox."""
        if not self.service:
            return 0
        try:
            results = self.service.users().messages().list(
                userId="me", q="is:unread"
            ).execute()
            return len(results.get("messages", []))
        except Exception:
            return 0

    # ----------------------------------------------------- internal parsers

    def _get_email_metadata(self, msg_id: str) -> Optional[Email]:
        """Light-weight fetch — headers + snippet only."""
        try:
            msg = self.service.users().messages().get(
                userId="me", id=msg_id, format="metadata"
            ).execute()
            return self._parse_message(msg)
        except Exception:
            return None

    def _parse_message(self, msg: Dict) -> Email:
        """Convert a raw Gmail API message dict to an :class:`Email` object."""
        headers = msg.get("payload", {}).get("headers", [])

        def hdr(name: str) -> str:
            for h in headers:
                if h["name"].lower() == name.lower():
                    return h["value"]
            return ""

        labels = msg.get("labelIds", [])
        payload = msg.get("payload", {})

        return Email(
            id=msg.get("id", ""),
            thread_id=msg.get("threadId", ""),
            subject=hdr("Subject"),
            sender=hdr("From"),
            recipient=hdr("To"),
            date=hdr("Date"),
            snippet=msg.get("snippet", ""),
            body=self._extract_body(payload),
            is_read="UNREAD" not in labels,
            labels=labels,
            attachments=self._extract_attachments(payload),
        )

    def _extract_body(self, payload: Dict) -> str:
        """Decode the plaintext (or HTML fallback) body from a payload dict."""
        data = payload.get("body", {})
        if data.get("data"):
            return base64.urlsafe_b64decode(data["data"]).decode("utf-8", errors="replace")

        plain = html = ""
        for part in payload.get("parts", []):
            mime = part.get("mimeType", "")
            raw = part.get("body", {}).get("data", "")
            if not raw:
                continue
            decoded = base64.urlsafe_b64decode(raw).decode("utf-8", errors="replace")
            if mime == "text/plain":
                plain = decoded
            elif mime == "text/html" and not html:
                html = decoded

        return plain or html

    def _extract_attachments(self, payload: Dict) -> List[Dict]:
        """Return a list of attachment metadata dicts from a payload."""
        attachments: List[Dict] = []
        for part in payload.get("parts", []):
            if part.get("filename"):
                body = part.get("body", {})
                attachments.append({
                    "filename": part["filename"],
                    "mime_type": part.get("mimeType", "application/octet-stream"),
                    "size": body.get("size", 0),
                    "attachment_id": body.get("attachmentId", ""),
                })
        return attachments

    # -------------------------------------------------------- sending emails

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        attachments: List[str] = None,
        is_html: bool = False,
    ) -> Optional[str]:
        """
        Compose and send an email immediately.

        Args:
            to:          Recipient address.
            subject:     Email subject line.
            body:        Message body (plain text or HTML).
            cc:          Comma-separated CC addresses.
            bcc:         Comma-separated BCC addresses (not visible to recipients).
            attachments: List of *file paths* to attach.
            is_html:     Set True when *body* contains HTML.

        Returns:
            The sent message ID on success, or None on failure.
        """
        if not self.service:
            return None

        try:
            msg = self._build_mime(to, subject, body, cc, bcc, attachments, is_html)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sent = self.service.users().messages().send(
                userId="me", body={"raw": raw}
            ).execute()
            return sent.get("id")

        except Exception as exc:
            print(f"EmailClient.send_email: {exc}")
            return None

    def save_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = None,
        attachments: List[str] = None,
    ) -> Optional[str]:
        """
        Save a composed message as a Gmail draft.

        Returns the draft ID on success, or None on failure.
        """
        if not self.service:
            return None

        try:
            msg = self._build_mime(to, subject, body, cc, attachments=attachments)
            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            draft = self.service.users().drafts().create(
                userId="me", body={"message": {"raw": raw}}
            ).execute()
            return draft.get("id")

        except Exception as exc:
            print(f"EmailClient.save_draft: {exc}")
            return None

    def delete_draft(self, draft_id: str) -> bool:
        """
        Delete a draft by ID.

        Accepts the *draft_* prefix returned by :meth:`get_drafts`.
        """
        if not self.service:
            return False

        try:
            actual_id = draft_id.replace("draft_", "")
            self.service.users().drafts().delete(
                userId="me", id=actual_id
            ).execute()
            return True

        except Exception as exc:
            print(f"EmailClient.delete_draft: {exc}")
            return False

    def _sanitize_header(self, value: str) -> str:
        """Remove newlines and carriage returns to prevent header injection."""
        if not value:
            return ""
        return value.replace("\n", "").replace("\r", "")

    def _build_mime(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        attachments: List[str] = None,
        is_html: bool = False,
    ) -> MIMEMultipart:
        """Build and return a MIME message ready to be base64-encoded."""
        msg = MIMEMultipart("mixed")
        msg["To"] = self._sanitize_header(to)
        msg["Subject"] = Header(subject, "utf-8").encode()
        if cc:
            msg["Cc"] = self._sanitize_header(cc)
        if bcc:
            msg["Bcc"] = self._sanitize_header(bcc)

        subtype = "html" if is_html else "plain"
        msg.attach(MIMEText(body, subtype, "utf-8"))

        for filepath in (attachments or []):
            if not os.path.exists(filepath):
                continue
            with open(filepath, "rb") as fh:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(fh.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{os.path.basename(filepath)}"',
            )
            msg.attach(part)

        return msg

    # ---------------------------------------------------------------- search

    def search(self, query: str, limit: int = 20) -> List[Email]:
        """
        Search emails using Gmail query syntax.

        Example queries::

            "from:hr@company.com subject:application"
            "is:unread after:2024/01/01"
            "has:attachment filename:pdf"

        Returns:
            List of matching :class:`Email` objects (metadata only).
        """
        if not self.service:
            return []

        try:
            results = self.service.users().messages().list(
                userId="me", q=query, maxResults=limit
            ).execute()

            emails: List[Email] = []
            for msg in results.get("messages", []):
                email = self._get_email_metadata(msg["id"])
                if email:
                    emails.append(email)
            return emails

        except Exception as exc:
            print(f"EmailClient.search: {exc}")
            return []

    # ---------------------------------------------------------------- labels

    def get_labels(self) -> List[Dict]:
        """Return all Gmail labels available to the authenticated user."""
        if not self.service:
            return []
        try:
            return self.service.users().labels().list(userId="me").execute().get("labels", [])
        except Exception:
            return []

    def mark_as_read(self, email_id: str) -> bool:
        """Remove the UNREAD label from a message."""
        return self._modify_labels(email_id, remove=["UNREAD"])

    def mark_as_unread(self, email_id: str) -> bool:
        """Add the UNREAD label to a message."""
        return self._modify_labels(email_id, add=["UNREAD"])

    def add_label(self, email_id: str, label: str) -> bool:
        """Add a label to a message."""
        return self._modify_labels(email_id, add=[label])

    def remove_label(self, email_id: str, label: str) -> bool:
        """Remove a label from a message."""
        return self._modify_labels(email_id, remove=[label])

    def _modify_labels(
        self,
        email_id: str,
        add: List[str] = None,
        remove: List[str] = None,
    ) -> bool:
        """Low-level label modification helper."""
        if not self.service:
            return False
        try:
            body: Dict = {}
            if add:
                body["addLabelIds"] = add
            if remove:
                body["removeLabelIds"] = remove
            self.service.users().messages().modify(
                userId="me", id=email_id, body=body
            ).execute()
            return True
        except Exception as exc:
            print(f"EmailClient._modify_labels({email_id}): {exc}")
            return False


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_global_client: Optional[EmailClient] = None


def get_email_client() -> EmailClient:
    """Return (or lazily create) the module-level :class:`EmailClient` singleton."""
    global _global_client
    if _global_client is None:
        _global_client = EmailClient()
    return _global_client


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = get_email_client()
    print("EmailClient smoke-test")
    print(f"  Authenticated : {client.is_authenticated()}")
    print(f"  Email address : {client.get_email_address() or '(not authenticated)'}")
