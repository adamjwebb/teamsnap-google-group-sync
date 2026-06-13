"""TeamSnap API client for fetching organization member email addresses."""

from __future__ import annotations

import logging
from typing import Generator

import requests

logger = logging.getLogger(__name__)

TEAMSNAP_API_BASE = "https://api.teamsnap.com/v3"


class TeamsnapClient:
    def __init__(self, token: str) -> None:
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def _get(self, path: str, **params) -> dict:
        url = f"{TEAMSNAP_API_BASE}{path}"
        response = self._session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_organization_member_emails(self, org_id: str) -> set[str]:
        """Return the set of all active member email addresses in the organization."""
        emails: set[str] = set()

        members = self._paginate_collection(f"/organizations/{org_id}/members")
        member_ids = {
            self._item_field(m, "id")
            for m in members
            if self._item_field(m, "is_non_player") is False
            or self._item_field(m, "is_non_player") is None
        }

        logger.info("Found %d members in org %s", len(member_ids), org_id)

        contact_email_addresses = self._paginate_collection(
            f"/organizations/{org_id}/member_email_addresses"
        )

        for item in contact_email_addresses:
            member_id = str(self._item_field(item, "member_id"))
            email = self._item_field(item, "email")
            if member_id in {str(mid) for mid in member_ids} and email:
                emails.add(email.strip().lower())

        logger.info("Collected %d unique email(s) from org %s", len(emails), org_id)
        return emails

    def _paginate_collection(self, path: str) -> list[dict]:
        """Fetch all items from a TeamSnap collection resource."""
        response = self._get(path)
        collection = response.get("collection", {})
        items = collection.get("items", [])
        return items

    @staticmethod
    def _item_field(item: dict, field: str):
        """Extract a named field value from a TeamSnap collection item."""
        for entry in item.get("data", []):
            if entry.get("name") == field:
                return entry.get("value")
        return None
