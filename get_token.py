#!/usr/bin/env python3
"""
OAuth 2.0 helper: exchanges a TeamSnap client ID + secret for an access token
using the out-of-band (OOB) Authorization Code flow. Works in dev containers
and any environment without a local HTTP server.

Usage:
    python get_token.py --client-id YOUR_ID --client-secret YOUR_SECRET

Steps:
  1. Script prints an authorization URL â€” open it in your browser
  2. Log in to TeamSnap and click Authorize
  3. TeamSnap displays an authorization code â€” paste it back here
  4. Script exchanges it for access + refresh tokens
"""

from __future__ import annotations

import argparse
from urllib.parse import urlencode

import requests

TEAMSNAP_AUTH_URL = "https://auth.teamsnap.com/oauth/authorize"
TEAMSNAP_TOKEN_URL = "https://auth.teamsnap.com/oauth/token"
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


def get_tokens(client_id: str, client_secret: str) -> dict:
    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "read",
    }
    auth_url = f"{TEAMSNAP_AUTH_URL}?{urlencode(auth_params)}"

    print("\n1. Open this URL in your browser:\n")
    print(f"   {auth_url}\n")
    print("2. Log in to TeamSnap and click Authorize.")
    print("3. Copy the authorization code shown on screen.\n")

    code = input("Paste the authorization code here: ").strip()

    print("\nExchanging code for tokens...")
    response = requests.post(
        TEAMSNAP_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Get a TeamSnap OAuth access + refresh token.")
    parser.add_argument("--client-id", required=True, help="TeamSnap OAuth client ID")
    parser.add_argument("--client-secret", required=True, help="TeamSnap OAuth client secret")
    args = parser.parse_args()

    token_data = get_tokens(args.client_id, args.client_secret)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", "unknown")

    print("\nâœ… Success!")
    print(f"   Access token  : {access_token}")
    print(f"   Refresh token : {refresh_token}")
    print(f"   Expires in    : {expires_in} seconds")
    print("\nAdd these to your .env file:")
    print(f"   TEAMSNAP_CLIENT_ID={args.client_id}")
    print(f"   TEAMSNAP_CLIENT_SECRET={args.client_secret}")
    print(f"   TEAMSNAP_REFRESH_TOKEN={refresh_token}")
    print("\nFor GitHub Actions, add TEAMSNAP_CLIENT_ID, TEAMSNAP_CLIENT_SECRET,")
    print("and TEAMSNAP_REFRESH_TOKEN as repository secrets.")


if __name__ == "__main__":
    main()

