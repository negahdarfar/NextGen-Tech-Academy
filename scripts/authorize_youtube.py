"""Create a YouTube OAuth refresh token for unattended private uploads.

Run this once on a trusted computer with a browser:
    python scripts/authorize_youtube.py --client-secrets credentials.json
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-secrets", default="credentials.json")
    parser.add_argument("--output", default="token.json")
    args = parser.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit('Install cloud dependencies: pip install -e ".[cloud]"') from exc

    secrets = Path(args.client_secrets)
    if not secrets.is_file():
        raise SystemExit(
            f"OAuth client file not found: {secrets}. Download an OAuth Desktop app "
            "client JSON from Google Cloud Console and save it locally."
        )

    flow = InstalledAppFlow.from_client_secrets_file(
        str(secrets),
        scopes=["https://www.googleapis.com/auth/youtube.upload"],
    )
    credentials = flow.run_local_server(
        host="localhost", port=0, access_type="offline", prompt="consent",
        authorization_prompt_message="Open this URL to authorize your YouTube channel: {url}",
        success_message="YouTube authorization complete. You may close this browser tab.",
    )
    output = Path(args.output)
    output.write_text(credentials.to_json(), encoding="utf-8")
    try:
        output.chmod(0o600)
    except OSError:
        pass
    print(f"OAuth token saved to {output}. Do not commit or share this file.")
    print("Copy the full file contents into GitHub Actions Secret: YOUTUBE_TOKEN_JSON.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
