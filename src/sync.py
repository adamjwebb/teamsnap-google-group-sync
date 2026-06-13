"""Core sync logic: compares TeamSnap emails with Google Group membership and reconciles."""

from __future__ import annotations

import logging

from src.google_groups import GoogleGroupsClient
from src.teamsnap import TeamsnapClient

logger = logging.getLogger(__name__)


class SyncResult:
    def __init__(self) -> None:
        self.added: list[str] = []
        self.removed: list[str] = []
        self.unchanged: int = 0

    def __str__(self) -> str:
        return (
            f"Added: {len(self.added)}, "
            f"Removed: {len(self.removed)}, "
            f"Unchanged: {self.unchanged}"
        )


def sync(
    teamsnap_client: TeamsnapClient,
    google_client: GoogleGroupsClient,
    teamsnap_org_id: str,
    google_group_email: str,
    dry_run: bool = False,
) -> SyncResult:
    """
    Synchronize Google Group membership to match TeamSnap org member emails.

    Args:
        teamsnap_client: Authenticated TeamsnapClient instance.
        google_client: Authenticated GoogleGroupsClient instance.
        teamsnap_org_id: TeamSnap organization ID.
        google_group_email: Email address of the target Google Group.
        dry_run: If True, log planned changes without applying them.

    Returns:
        SyncResult with counts of added, removed, and unchanged members.
    """
    result = SyncResult()

    logger.info("Fetching TeamSnap members for org %s…", teamsnap_org_id)
    source_emails = teamsnap_client.get_organization_member_emails(teamsnap_org_id)

    logger.info("Fetching current members of Google Group %s…", google_group_email)
    current_emails = google_client.get_group_member_emails(google_group_email)

    to_add = source_emails - current_emails
    to_remove = current_emails - source_emails
    result.unchanged = len(source_emails & current_emails)

    if dry_run:
        logger.info("[DRY RUN] Would add: %s", sorted(to_add))
        logger.info("[DRY RUN] Would remove: %s", sorted(to_remove))
        result.added = sorted(to_add)
        result.removed = sorted(to_remove)
        return result

    for email in sorted(to_add):
        google_client.add_member(google_group_email, email)
        result.added.append(email)

    for email in sorted(to_remove):
        google_client.remove_member(google_group_email, email)
        result.removed.append(email)

    return result
