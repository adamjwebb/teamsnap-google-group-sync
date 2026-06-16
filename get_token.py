#!/usr/bin/env python3
"""
OAuth 2.0 helper: exchanges a TeamSnap client ID + secret for an access token
using the Authorization Code flow, then prints the token for use in .env.

Usage:
    python get_token.py --client-id YOUR_ID --client-secret YOUR_SECRET

A temporary local HTTP server catches the OAuth redirect automatically.
"""

from __future__ import annotations

import argparse
import http.server
import threading
import urllib.parse
import webbrowser
from urllib.parse import urlencode

import requests

TEAMSNAP_AUTH_URL = "https://auth.teamsnap.com/oauth/authorize"
TEAMSNAP_TOKEN_URL = "https://auth.teamsnap.com/oauth/token"
REDIRECT_URI = "http://localhost:9999/callback"

# Shared state between the HTTP handler and main thread
_auth_code: str | None = None
_server_ready = threading.Event()


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "code" in params:
            _auth_code = params["code"][0]
            body = b"<h2>Authorization successful! You can close this tab.</h2>"
            self.send_response(200)
        else:
            error = params.get("error", ["unknown"])[0]
            body = f"<h2>Authorization failed: {error}</h2>".encode()
            self.send_response(400)

        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # suppress request logs


def _run_server(server: http.server.HTTPServer):
    _server_ready.set()
    server.handle_request()  # handle exactly one request then stop


def get_access_token(client_id: str, client_secret: str) -> dict:
    # Start local callback server
    server = http.server.HTTPServer(("localhost", 9999), _CallbackHandler)
    thread = threading.Thread(target=_run_server, args=(server,), daemon=True)
    thread.start()
    _server_ready.wait()

    # Build authorization URL and open browser
    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "read",
    }
    auth_url = f"{TEAMSNAP_AUTH_URL}?{urlencode(auth_params)}"
    print(f"\nOpening browser for TeamSnap authorization...")
    print(f"If it doesn't open automatically, visit:\n  {auth_url}\n")
    webbrowser.open(auth_url)

    # Wait for the redirect callback
    thread.join(timeout=120)
    server.server_close()

    if not _auth_code:
        raise RuntimeError("Did not receive an authorization code within 2 minutes.")

    # Exchange code for token
    print("Exchanging authorization code for access token...")
    response = requests.post(
        TEAMSNAP_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Get a TeamSnap OAuth access token.")
    parser.add_argument("--client-id", required=True, help="TeamSnap OAuth client ID")
    parser.add_argument("--client-secret", required=True, help="TeamSnap OAuth client secret")
    args = parser.parse_args()

    token_data = get_access_token(args.client_id, args.client_secret)

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", "unknown")

    print("\n✅ Success!")
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
