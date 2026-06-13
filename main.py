#!/usr/bin/env python3
"""Entry point for the TeamSnap → Google Group sync tool."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from src.google_groups import GoogleGroupsClient
from src.sync import sync
from src.teamsnap import TeamsnapClient


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
        stream=sys.stdout,
    )


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        print(f"ERROR: Required environment variable '{name}' is not set.", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Sync TeamSnap organization members to a Google Group distribution list."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned changes without applying them.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug-level logging."
    )
    args = parser.parse_args()

    _configure_logging(args.verbose)
    logger = logging.getLogger(__name__)

    teamsnap_token = _require_env("TEAMSNAP_TOKEN")
    teamsnap_org_id = _require_env("TEAMSNAP_ORG_ID")
    google_group_email = _require_env("GOOGLE_GROUP_EMAIL")
    google_admin_email = _require_env("GOOGLE_ADMIN_EMAIL")
    google_sa_file = _require_env("GOOGLE_SERVICE_ACCOUNT_FILE")

    teamsnap_client = TeamsnapClient(token=teamsnap_token)
    google_client = GoogleGroupsClient(
        service_account_file=google_sa_file,
        impersonated_admin_email=google_admin_email,
    )

    if args.dry_run:
        logger.info("Running in DRY RUN mode — no changes will be made.")

    result = sync(
        teamsnap_client=teamsnap_client,
        google_client=google_client,
        teamsnap_org_id=teamsnap_org_id,
        google_group_email=google_group_email,
        dry_run=args.dry_run,
    )

    logger.info("Sync complete — %s", result)


if __name__ == "__main__":
    main()
