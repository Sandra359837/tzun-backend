# title_bucketer.py

import os
import json
from github import Github

# ─── Config ────────────────────────────────────────
BUCKETS_FILE = "buckets.json"
REPO_NAME    = "Sandra359837/tzun-backend"  # <— your GitHub repo
BRANCH       = "main"                       # <— the branch to commit to

# ─── Helpers ───────────────────────────────────────
def load_buckets():
    """Read the existing JSON array of buckets, or return [] if missing."""
    try:
        with open(BUCKETS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_buckets_and_commit(buckets: list):
    """
    1) Overwrite the local buckets.json
    2) Commit that change back to GitHub via the PyGithub API.
    """
    # 1) Write locally
    with open(BUCKETS_FILE, "w") as f:
        json.dump(buckets, f, indent=2)

    # 2) Push up to GitHub
    gh   = Github(os.environ["GITHUB_TOKEN"])
    repo = gh.get_repo(REPO_NAME)

    # We need the current file SHA to update it
    source_file = repo.get_contents(BUCKETS_FILE, ref=BRANCH)

    repo.update_file(
        path    = BUCKETS_FILE,
        message = "chore: update dynamic buckets",
        content = json.dumps(buckets, indent=2),
        sha     = source_file.sha,
        branch  = BRANCH
    )

# ─── Main API ───────────────────────────────────────
def classify_title(title: str):
    """
    Normalize the incoming persona_context (title).  
    If it’s new, append & commit it.
    Returns a (bucket, confidence) pair.
    """
    normalized = title.strip().lower()
    buckets    = load_buckets()

    if normalized not in buckets:
        buckets.append(normalized)
        save_buckets_and_commit(buckets)

    # You can replace this 1.0 with a real confidence score if desired
    return normalized, 1.0
