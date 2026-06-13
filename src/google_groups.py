"""Google Admin SDK client for managing Google Group members."""

from __future__ import annotations

import logging
import time
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/admin.directory.group.member"]

# Google API quota: max 10 requests/second per user
_RATE_LIMIT_DELAY = 0.15


class GoogleGroupsClient:
    def __init__(self, service_account_file: str, impersonated_admin_email: str) -> None:
        """
        Args:
            service_account_file: Path to the service account JSON key file.
            impersonated_admin_email: A Google Workspace admin email to impersonate
                (required for domain-wide delegation).
        """
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        delegated = credentials.with_subject(impersonated_admin_email)
        self._service = build("admin", "directory_v1", credentials=delegated, cache_discovery=False)

    def get_group_member_emails(self, group_email: str) -> set[str]:
        """Return the set of current member emails for the given group."""
        emails: set[str] = set()
        page_token: Optional[str] = None

        while True:
            result = (
                self._service.members()
                .list(groupKey=group_email, pageToken=page_token)
                .execute()
            )
            for member in result.get("members", []):
                if member.get("email"):
                    emails.add(member["email"].strip().lower())
            page_token = result.get("nextPageToken")
            if not page_token:
                break
            time.sleep(_RATE_LIMIT_DELAY)

        logger.info("Group %s currently has %d member(s)", group_email, len(emails))
        return emails

    def add_member(self, group_email: str, member_email: str) -> None:
        try:
            self._service.members().insert(
                groupKey=group_email, body={"email": member_email, "role": "MEMBER"}
            ).execute()
            logger.info("Added %s to %s", member_email, group_email)
        except HttpError as exc:
            if exc.status_code == 409:
                logger.debug("%s is already a member of %s", member_email, group_email)
            else:
                raise
        time.sleep(_RATE_LIMIT_DELAY)

    def remove_member(self, group_email: str, member_email: str) -> None:
        try:
            self._service.members().delete(
                groupKey=group_email, memberKey=member_email
            ).execute()
            logger.info("Removed %s from %s", member_email, group_email)
        except HttpError as exc:
            if exc.status_code == 404:
                logger.debug("%s was not a member of %s", member_email, group_email)
            else:
                raise
        time.sleep(_RATE_LIMIT_DELAY)
