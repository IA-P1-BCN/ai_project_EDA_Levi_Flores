"""Keep GitHub Project #54 in sync with the GitHub Flow life cycle.

Two modes:

``pr --number N``
    For every task issue the PR closes (``Closes #12`` in its body), add the issue to the
    project if needed, fill the ``Branch`` and ``Pull Request`` fields and set ``Status``:

    =====================  ===============
    PR state               Issue Status
    =====================  ===============
    draft                  In Progress
    open, ready to review  In Review
    merged into main       Done
    closed, not merged     In Progress
    =====================  ===============

    When the PR is merged, today's ``[DAILY] YYYY-MM-DD`` issue gets a comment that records it.

``daily``
    Roll the daily logs over (run every morning): today's log moves to ``In Progress``; open
    logs from previous days move to ``Done`` and are closed. Future logs are left untouched.

Needs a token with project write access in ``PROJECT_TOKEN`` (GITHUB_TOKEN cannot write
organization projects). ``--dry-run`` prints the changes without applying them.

Usage:
    python .github/scripts/project_sync.py pr --number 50 [--dry-run]
    python .github/scripts/project_sync.py daily [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

OWNER = "IA-P1-BCN"
REPO = "ai_project_EDA_Levi_Flores"
PROJECT_NUMBER = 54
TIMEZONE = "Europe/Madrid"
DAILY_TITLE = re.compile(r"^\[DAILY\]\s+(\d{4}-\d{2}-\d{2})")
API_URL = "https://api.github.com/graphql"


class GitHub:
    """Minimal GraphQL client (standard library only)."""

    def __init__(self, token: str, dry_run: bool) -> None:
        self.token = token
        self.dry_run = dry_run

    def query(self, query: str, **variables: object) -> dict:
        payload = json.dumps({"query": query, "variables": variables}).encode()
        request = urllib.request.Request(
            API_URL,
            data=payload,
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.load(response)
        if body.get("errors"):
            raise RuntimeError(f"GraphQL error: {body['errors']}")
        return body["data"]

    def mutate(self, description: str, query: str, **variables: object) -> dict | None:
        print(f"{'[dry-run] ' if self.dry_run else ''}{description}")
        return None if self.dry_run else self.query(query, **variables)


class Project:
    """Project #54 metadata plus helpers to add items and set fields."""

    def __init__(self, gh: GitHub) -> None:
        self.gh = gh
        data = gh.query(
            """query($owner: String!, $number: Int!) {
              organization(login: $owner) { projectV2(number: $number) {
                id
                fields(first: 50) { nodes {
                  ... on ProjectV2FieldCommon { id name dataType }
                  ... on ProjectV2SingleSelectField { options { id name } }
                } }
              } }
            }""",
            owner=OWNER,
            number=PROJECT_NUMBER,
        )["organization"]["projectV2"]
        self.id = data["id"]
        self.fields = {field["name"]: field for field in data["fields"]["nodes"] if field}

    def item_id(self, issue: dict) -> str | None:
        """Return the issue's item id in this project, adding the issue if it is missing."""
        for item in issue["projectItems"]["nodes"]:
            if item["project"]["id"] == self.id:
                return item["id"]
        result = self.gh.mutate(
            f"#{issue['number']}: add to project #{PROJECT_NUMBER}",
            """mutation($project: ID!, $content: ID!) {
              addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } }
            }""",
            project=self.id,
            content=issue["id"],
        )
        return result["addProjectV2ItemById"]["item"]["id"] if result else None

    def set_value(self, issue: dict, item_id: str | None, field_name: str, value: str) -> None:
        field = self.fields.get(field_name)
        if field is None:
            print(f"::warning::project has no field '{field_name}'; skipped")
            return
        if field.get("options") is not None:
            option = next((o["id"] for o in field["options"] if o["name"] == value), None)
            if option is None:
                raise ValueError(f"'{value}' is not an option of field '{field_name}'")
            field_value = {"singleSelectOptionId": option}
        else:
            field_value = {"text": value}
        if item_id is None and not self.gh.dry_run:
            raise RuntimeError(f"#{issue['number']} has no project item")
        self.gh.mutate(
            f"#{issue['number']}: {field_name} = {value}",
            """mutation($project: ID!, $item: ID!, $field: ID!, $value: ProjectV2FieldValue!) {
              updateProjectV2ItemFieldValue(input: {projectId: $project, itemId: $item, fieldId: $field, value: $value}) {
                projectV2Item { id }
              }
            }""",
            project=self.id,
            item=item_id or "",
            field=field["id"],
            value=field_value,
        )


ISSUE_FIELDS = "id number title state projectItems(first: 20) { nodes { id project { id } } }"


def local_date(moment: datetime | None = None) -> date:
    """Date in the project time zone, for now or for a given aware datetime."""
    try:
        zone = ZoneInfo(TIMEZONE)
    except ZoneInfoNotFoundError:
        print(f"::warning::time zone {TIMEZONE} not available; using UTC")
        return (moment or datetime.now()).date()
    return (moment.astimezone(zone) if moment else datetime.now(zone)).date()


def pr_status(pr: dict) -> str:
    if pr["merged"]:
        return "Done"
    if pr["state"] == "CLOSED" or pr["isDraft"]:
        return "In Progress"
    return "In Review"


def find_daily(gh: GitHub, day: date) -> dict | None:
    for issue in open_dailies(gh):
        match = DAILY_TITLE.match(issue["title"])
        if match and match.group(1) == day.isoformat():
            return issue
    return None


def open_dailies(gh: GitHub) -> list[dict]:
    data = gh.query(
        f"""query($owner: String!, $repo: String!) {{
          repository(owner: $owner, name: $repo) {{
            issues(first: 100, states: OPEN, labels: ["daily"]) {{ nodes {{ {ISSUE_FIELDS} }} }}
          }}
        }}""",
        owner=OWNER,
        repo=REPO,
    )
    return data["repository"]["issues"]["nodes"]


def sync_pr(gh: GitHub, number: int) -> None:
    pr = gh.query(
        f"""query($owner: String!, $repo: String!, $number: Int!) {{
          repository(owner: $owner, name: $repo) {{ pullRequest(number: $number) {{
            number title url state isDraft merged mergedAt headRefName baseRefName
            closingIssuesReferences(first: 25) {{ nodes {{ {ISSUE_FIELDS} }} }}
          }} }}
        }}""",
        owner=OWNER,
        repo=REPO,
        number=number,
    )["repository"]["pullRequest"]

    issues = pr["closingIssuesReferences"]["nodes"]
    status = pr_status(pr)
    print(f"PR #{pr['number']} ({pr['headRefName']} -> {pr['baseRefName']}): status for linked issues = {status}")
    if pr["baseRefName"] != "main":
        print("PR does not target main; GitHub Flow only tracks PRs into main. Nothing to do.")
        return
    if not issues:
        print("::notice::PR has no 'Closes #<issue>' link; no project item to update.")

    project = Project(gh)
    for issue in issues:
        item_id = project.item_id(issue)
        project.set_value(issue, item_id, "Branch", pr["headRefName"])
        project.set_value(issue, item_id, "Pull Request", pr["url"])
        project.set_value(issue, item_id, "Status", status)

    if pr["merged"]:
        merge_day = local_date(datetime.fromisoformat(pr["mergedAt"]))
        daily = find_daily(gh, merge_day)
        if daily is None:
            print(f"::notice::no open [DAILY] {merge_day} issue; merge not logged")
            return
        closed = ", ".join(f"#{i['number']} {i['title']}" for i in issues) or "no linked task"
        gh.mutate(
            f"#{daily['number']}: comment merged PR #{pr['number']}",
            "mutation($subject: ID!, $body: String!) { addComment(input: {subjectId: $subject, body: $body}) { clientMutationId } }",
            subject=daily["id"],
            body=f"✅ Merged {pr['url']} — **{pr['title']}**\n\nCloses: {closed}",
        )
        project.set_value(daily, project.item_id(daily), "Status", "In Progress")


def roll_dailies(gh: GitHub) -> None:
    current = local_date()
    project = Project(gh)
    print(f"Daily rollover for {current} ({TIMEZONE})")
    for issue in open_dailies(gh):
        match = DAILY_TITLE.match(issue["title"])
        if not match:
            print(f"::warning::#{issue['number']} has the daily label but no [DAILY] YYYY-MM-DD title")
            continue
        day = date.fromisoformat(match.group(1))
        if day == current:
            project.set_value(issue, project.item_id(issue), "Status", "In Progress")
        elif day < current:
            project.set_value(issue, project.item_id(issue), "Status", "Done")
            gh.mutate(
                f"#{issue['number']}: close (day {day} is over)",
                "mutation($id: ID!) { closeIssue(input: {issueId: $id, stateReason: COMPLETED}) { clientMutationId } }",
                id=issue["id"],
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--dry-run", action="store_true", help="print changes without applying them")
    sub = parser.add_subparsers(dest="mode", required=True)
    pr_parser = sub.add_parser("pr", parents=[common], help="sync the issues linked to a pull request")
    pr_parser.add_argument("--number", type=int, required=True)
    sub.add_parser("daily", parents=[common], help="roll daily logs over")
    args = parser.parse_args()

    # Strip whitespace: secrets pasted in the web UI often carry a trailing newline.
    token = os.environ.get("PROJECT_TOKEN", "").strip()
    if not token:
        print("::warning::PROJECT_TOKEN is not set; project sync skipped. See README > Project automation.")
        return 0

    gh = GitHub(token, dry_run=args.dry_run)
    if args.mode == "pr":
        sync_pr(gh, args.number)
    else:
        roll_dailies(gh)
    return 0


if __name__ == "__main__":
    sys.exit(main())
