"""Refreshes stats.json — the GitHub Stats block in the profile card.

Usage: python stats.py            (needs GITHUB_TOKEN, or falls back to `gh auth token`)

Queries the API for repo/star/commit counts and total lines of code, caches the
result to JSON, and lets build.py render it.

Commits and lines of code both come from /repos/{o}/{r}/stats/contributors
rather than GraphQL's contributionsCollection. That field reports private work
via restrictedContributionsCount, which is only populated for tokens holding
the classic `read:user` scope AND profiles that opt into showing private
contributions — otherwise private commits silently vanish from the total. The
stats endpoint has no such caveat and needs only `Metadata: Read`, so this
works with a read-only fine-grained token.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

API = "https://api.github.com"


def token():
    tok = os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    return subprocess.run(["gh", "auth", "token"], capture_output=True,
                          text=True, check=True).stdout.strip()


TOK = token()


def call(url, data=None, retries=6):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"bearer {TOK}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "profile-card",
    })
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as r:
                # /stats/ endpoints answer 202 while GitHub computes them
                if r.status == 202:
                    time.sleep(2 * (attempt + 1))
                    continue
                return json.loads(r.read() or "null")
        except urllib.error.HTTPError as e:
            if e.code in (403, 502) and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    return None


def graphql(query, **variables):
    out = call(f"{API}/graphql", {"query": query, "variables": variables})
    if "errors" in out:
        sys.exit(f"GraphQL error: {out['errors']}")
    return out["data"]


profile = graphql("""
query {
  viewer {
    login
    repositoriesContributedTo(
      first: 1
      contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]
    ) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes { name stargazerCount }
    }
  }
}""")["viewer"]

login = profile["login"]
repos = profile["repositories"]["nodes"]

# one pass over the repos covers both commits and lines of code
commits = added = deleted = 0
for repo in repos:
    contributors = call(f"{API}/repos/{login}/{repo['name']}/stats/contributors")
    for entry in contributors or []:
        if entry["author"] and entry["author"]["login"] == login:
            commits += entry["total"]
            added += sum(w["a"] for w in entry["weeks"])
            deleted += sum(w["d"] for w in entry["weeks"])

stats = {
    "repos": profile["repositories"]["totalCount"],
    "contributed": profile["repositoriesContributedTo"]["totalCount"],
    "stars": sum(r["stargazerCount"] for r in repos),
    "commits": commits,
    "loc_added": added,
    "loc_deleted": deleted,
}
with open("stats.json", "w", encoding="utf-8") as fh:
    json.dump(stats, fh, indent=2)
print(json.dumps(stats, indent=2))
