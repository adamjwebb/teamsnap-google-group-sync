# TeamSnap → Google Group Sync

Automatically keeps a **Google Group distribution list** in sync with your **TeamSnap organization** member emails.

- ➕ Adds new TeamSnap members to the Google Group
- ➖ Removes members who are no longer in the TeamSnap org
- 🔄 Runs on a daily schedule via GitHub Actions, or manually on demand
- 🧪 `--dry-run` mode shows planned changes without applying them

---

## How It Works

1. Fetches all member email addresses from a TeamSnap organization via the [TeamSnap API v3](https://app.teamsnap.com/api/v3).
2. Fetches the current membership of a Google Group via the [Google Admin Directory API](https://developers.google.com/admin-sdk/directory).
3. Computes the diff and adds/removes members accordingly.

---

## Prerequisites

| Requirement | Details |
|---|---|
| Python 3.11+ | [python.org](https://www.python.org/) |
| TeamSnap account | With access to the org you want to sync |
| Google Workspace | Admin access to manage Group membership |

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/YOUR_USERNAME/teamsnap-google-group-sync.git
cd teamsnap-google-group-sync
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get a TeamSnap API token

1. Log in to TeamSnap and go to **Account → Connected Apps**.
2. Generate a personal access token (OAuth2).
3. Note your **Organization ID** — visible in the org URL: `https://go.teamsnap.com/XXXXXXX/...`

### 3. Create a Google Service Account

1. Open [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **Admin SDK API**: *APIs & Services → Library → Admin SDK API*.
3. Create a **Service Account**: *IAM & Admin → Service Accounts → Create*.
4. Create and download a **JSON key** for the service account.
5. Enable **Domain-Wide Delegation** on the service account.
6. In [Google Workspace Admin Console](https://admin.google.com/):
   - Go to *Security → API Controls → Domain-wide Delegation*.
   - Add the service account client ID with scope:
     ```
     https://www.googleapis.com/auth/admin.directory.group.member
     ```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your real values
```

| Variable | Description |
|---|---|
| `TEAMSNAP_TOKEN` | TeamSnap personal access token |
| `TEAMSNAP_ORG_ID` | TeamSnap organization ID |
| `GOOGLE_GROUP_EMAIL` | Email of the target Google Group |
| `GOOGLE_ADMIN_EMAIL` | Workspace admin email for impersonation |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to the service account JSON key |

> ⚠️ **Never commit `.env` or `service_account.json` to version control.**

### 5. Run the sync

```bash
# Preview changes (no writes)
python main.py --dry-run

# Apply changes
python main.py

# Verbose output
python main.py --verbose
```

---

## GitHub Actions (Scheduled Sync)

The workflow at `.github/workflows/sync.yml` runs daily at **06:00 UTC**. You can also trigger it manually from the *Actions* tab with an optional dry-run toggle.

### Required Secrets

Go to your repo → *Settings → Secrets and variables → Actions* and add:

| Secret | Value |
|---|---|
| `TEAMSNAP_TOKEN` | TeamSnap personal access token |
| `TEAMSNAP_ORG_ID` | TeamSnap organization ID |
| `GOOGLE_GROUP_EMAIL` | Email of the target Google Group |
| `GOOGLE_ADMIN_EMAIL` | Workspace admin email |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | **Full contents** of the service account JSON key file |

---

## Project Structure

```
teamsnap-google-group-sync/
├── src/
│   ├── teamsnap.py        # TeamSnap API client
│   ├── google_groups.py   # Google Admin SDK client
│   └── sync.py            # Core sync logic
├── main.py                # CLI entry point
├── requirements.txt
├── .env.example
└── .github/
    └── workflows/
        └── sync.yml       # Scheduled GitHub Actions workflow
```

---

## License

MIT
