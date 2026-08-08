"""Pull the real contribution numbers from GitHub's GraphQL API into stats.json.

Run by .github/workflows/banner.yml on a daily cron. Needs a token in GH_STATS_TOKEN
with the read:user scope, because restrictedContributionsCount (the private commit
count) is only visible to a token acting as the user. The default Actions
GITHUB_TOKEN is repo-scoped, not user-scoped, and returns 0 there.

If the API call fails, this exits non-zero WITHOUT writing, so the workflow keeps
the last known-good stats.json rather than publishing a banner that claims zero.
"""

import json
import os
import pathlib
import subprocess
import sys

USER = "sarthaknimbalkar"

QUERY = """
query($login:String!){
  user(login:$login){
    createdAt
    contributionsCollection{
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ contributionCount } }
      }
    }
  }
}
"""


def main():
    token = os.environ.get("GH_STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("no GH_STATS_TOKEN in env")

    env = {**os.environ, "GITHUB_TOKEN": token, "GH_TOKEN": token}
    proc = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"login={USER}"],
        capture_output=True, text=True, env=env,
    )
    if proc.returncode != 0:
        sys.exit(f"graphql call failed: {proc.stderr.strip()}")

    user = json.loads(proc.stdout)["data"]["user"]
    cc = user["contributionsCollection"]
    cal = cc["contributionCalendar"]

    total = cal["totalContributions"]
    private = cc["restrictedContributionsCount"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]]

    if total <= 0:
        sys.exit("refusing to write: API returned zero contributions")

    stats = {
        "total": total,
        "private": private,
        "public": total - private,
        "since": user["createdAt"][:4],
        "weeks": weeks,
    }
    out = pathlib.Path(__file__).parent / "stats.json"
    out.write_text(json.dumps(stats, indent=1), encoding="utf-8")
    print(f"total={total} private={private} weeks={len(weeks)}")


if __name__ == "__main__":
    main()
