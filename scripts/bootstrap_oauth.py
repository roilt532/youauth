#!/usr/bin/env python3
"""One-time OAuth 2.0 flow to obtain a YouTube refresh token.

Usage:
    python scripts/bootstrap_oauth.py

Prerequisites:
    - YT_CLIENT_ID and YT_CLIENT_SECRET set in environment (or .env)
    - A redirect URI http://localhost:8080/ configured in Google Cloud Console

After running, copy the printed YT_REFRESH_TOKEN value into GitHub Secrets
(Settings -> Secrets -> Actions -> New repository secret).
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow  # type: ignore[import-untyped]

load_dotenv()

_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
_TOKEN_PATH = Path.home() / ".alvaro_oauth_token.json"

_CLIENT_CONFIG = {
    "installed": {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080/"],
    }
}


def main() -> None:
    flow = InstalledAppFlow.from_client_config(_CLIENT_CONFIG, scopes=_SCOPES)
    creds = flow.run_local_server(port=8080)

    token_data = {
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }

    _TOKEN_PATH.write_text(json.dumps(token_data, indent=2))
    _TOKEN_PATH.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600

    print(f"Token saved to {_TOKEN_PATH} (permissions 600)")  # noqa: T201
    print()  # noqa: T201
    print("Add the following to GitHub Secrets (Settings -> Secrets -> Actions):")  # noqa: T201
    print(f"  YT_REFRESH_TOKEN = {creds.refresh_token}")  # noqa: T201
    print()  # noqa: T201
    print("Also ensure YT_CLIENT_ID and YT_CLIENT_SECRET are set as secrets.")  # noqa: T201


if __name__ == "__main__":
    main()
