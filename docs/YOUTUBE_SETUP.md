# YouTube OAuth setup

This setup is required only once on a trusted computer. After the refresh token is saved as a GitHub Actions Secret, scheduled cloud uploads can run while the computer is off.

## 1. Enable YouTube Data API

1. Open Google Cloud Console and create or select a project.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen and add the Google account that owns/manages the target YouTube channel as a test user if the app is in Testing.
4. Create an OAuth Client ID of type **Desktop app** and download its JSON file as `credentials.json`.

Do not upload the OAuth client file or token file to the repository. Both are ignored by Git.

## 2. Create the refresh token

On a trusted computer with Python and a browser:

```bash
python -m pip install -e ".[cloud]"
python scripts/authorize_youtube.py --client-secrets credentials.json
```

A browser window opens. Sign in to the Google account that owns the intended channel and grant the YouTube upload permission. The script writes `token.json` locally and does not print the token.

If Google does not return a refresh token, revoke the previous app grant in the Google Account security settings and run the script again.

## 3. Store the token securely in GitHub

Open the repository's **Settings → Secrets and variables → Actions → New repository secret**.

- Name: `YOUTUBE_TOKEN_JSON`
- Value: the entire content of local `token.json`

Never paste the token into a chat, issue, pull request, source file, or workflow log.

Also add these repository secrets:

- `VIDOGRID_API_KEY`
- At least one cloud text model key: `GEMINI_API_KEY` or `GROQ_API_KEY`. OpenRouter is optional and only uses models marked `:free` unless paid usage is explicitly enabled.

## 4. Configure safe VidoGrid model rotation

In **Settings → Secrets and variables → Actions → Variables**, configure:

- `VIDOGRID_MODEL_ROTATION`: a comma-separated list of enabled VidoGrid model names.
- `VIDOGRID_MODEL_CREDIT_COSTS`: JSON object mapping each selected model to the current cost in VidoGrid credits per 15-second clip.
- `VIDOGRID_TOTAL_BALANCE_IS_FREE`: leave `false` unless you have confirmed that the entire account balance reported by `GET /account` consists only of free credits.

If the API reports a separate free/trial credit field, the automation uses that. If it reports only a total balance, the workflow stops unless you explicitly confirm the entire balance is free. Never guess costs or enable this flag if paid credits may be present.

## 5. First upload

Keep YouTube visibility as `private`. Run the workflow manually on the feature branch only after all secrets and variables are configured. Review the uploaded private video in YouTube Studio before considering any public publishing.

The scheduled workflow runs only after the workflow file is present on the repository's default branch. Merging the current draft PR is a separate decision and is not performed automatically.
