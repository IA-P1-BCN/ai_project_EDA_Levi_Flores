"""
Script to reformat GitHub Issues with Shields.io badges and clean Markdown tables.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile

# Resolve the GitHub CLI from PATH so the script runs on any machine or AI engine.
GH_PATH = shutil.which("gh") or "gh"

LEVEL_CONFIG = {
    "Foundation": {"color": "C5DEF5", "logo_color": "black"},
    "Essential": {"color": "0E8A16", "logo_color": "white"},
    "Medium": {"color": "FBCA04", "logo_color": "black"},
    "Advanced": {"color": "D93F0B", "logo_color": "white"},
    "Expert": {"color": "B60205", "logo_color": "white"},
}

WORKSTREAM_CONFIG = {
    "Setup": "BFD4F2",
    "Data": "1D76DB",
    "Cleaning": "5319E7",
    "Analysis": "006B75",
    "Visualization": "F9D0C4",
    "Reporting": "D4C5F9",
    "Engineering": "C2E0C6",
    "Release": "FEF2C0",
}

PRIORITY_CONFIG = {
    "P0 - Critical": "red",
    "P1 - High": "orange",
    "P2 - Normal": "yellow",
}

def extract_section(text, header):
    pattern = rf"###\s+{re.escape(header)}\s*\n\s*(.*?)(?=\n###|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

def format_task_issue(body):
    task_id = extract_section(body, "Task ID")
    level = extract_section(body, "Level")
    workstream = extract_section(body, "Workstream")
    priority = extract_section(body, "Priority")
    estimate = extract_section(body, "Estimate")
    target_date = extract_section(body, "Target date")
    branch = extract_section(body, "Branch")
    description = extract_section(body, "Description")
    acceptance = extract_section(body, "Acceptance criteria")
    dependencies = extract_section(body, "Dependencies") or "None"
    dod = extract_section(body, "Definition of Done")

    if not task_id and not level:
        # If it doesn't match standard sections or is already formatted, skip
        return None

    # Clean level badge
    lvl_clean = level.replace("🟢", "").replace("🟡", "").replace("🟠", "").replace("🔴", "").replace("🔵", "").strip()
    lvl_cfg = LEVEL_CONFIG.get(lvl_clean, {"color": "0E8A16", "logo_color": "white"})
    level_badge = f"![Level: {lvl_clean}](https://img.shields.io/badge/Level-{lvl_clean}-{lvl_cfg['color']}?style=flat-square)"

    # Clean priority badge
    prio_clean = priority.replace("🔴", "").replace("🟠", "").replace("🟡", "").strip()
    prio_color = PRIORITY_CONFIG.get(prio_clean, "red")
    prio_badge_str = prio_clean.replace(" ", "%20").replace("-", "--")
    priority_badge = f"![Priority: {prio_clean}](https://img.shields.io/badge/Priority-{prio_badge_str}-{prio_color}?style=flat-square)"

    # Clean workstream badge
    ws_clean = workstream.strip()
    ws_color = WORKSTREAM_CONFIG.get(ws_clean, "006B75")
    workstream_badge = f"![Workstream: {ws_clean}](https://img.shields.io/badge/Workstream-{ws_clean}-{ws_color}?style=flat-square)"

    # Clean estimate badge
    est_clean = estimate.strip()
    est_badge_str = est_clean.replace(" ", "%20").replace("-", "--")
    est_color = "5319E7" if "M" in est_clean else ("2ea44f" if "S" in est_clean else "0366d6")
    estimate_badge = f"![Estimate: {est_clean}](https://img.shields.io/badge/Estimate-{est_badge_str}-{est_color}?style=flat-square)"

    # Target date badge
    date_clean = target_date.strip()
    date_badge = f"![Target Date: {date_clean}](https://img.shields.io/badge/Target_Date-{date_clean}-blue?style=flat-square)" if date_clean else "N/A"

    # Branch link
    branch_link = f"[`{branch}`](https://github.com/IA-P1-BCN/ai_project_EDA_Levi_Flores/tree/{branch})" if branch else "N/A"

    new_body = f"""### 🏷️ Metadata & Planning

| Attribute | Details |
| :--- | :--- |
| **Task ID** | `{task_id}` |
| **Level** | {level_badge} |
| **Workstream** | {workstream_badge} |
| **Priority** | {priority_badge} |
| **Estimate** | {estimate_badge} |
| **Target Date** | {date_badge} |
| **Branch** | {branch_link} |
| **Dependencies** | `{dependencies}` |

---

## 🎯 Description
{description}

---

## 📋 Acceptance Criteria
{acceptance}

---

## ✅ Definition of Done
{dod}
"""
    return new_body

def format_daily_issue(body):
    date = extract_section(body, "Date")
    day = extract_section(body, "Day")
    yesterday = extract_section(body, "Progress since the previous log")
    today = extract_section(body, "Plan for today")
    blockers = extract_section(body, "Blockers or questions")
    decisions = extract_section(body, "Decisions made or notes")

    if not day and not yesterday:
        return None

    day_clean = day.strip()
    day_badge_str = day_clean.replace(" ", "%20").replace("-", "--")
    day_badge = f"![Day: {day_clean}](https://img.shields.io/badge/Day-{day_badge_str}-1D76DB?style=flat-square)"
    type_badge = "![Type: Daily Log](https://img.shields.io/badge/Type-Daily_Log-0E8A16?style=flat-square)"

    new_body = f"""### 📅 Daily Standup Report

| Attribute | Details |
| :--- | :--- |
| **Report Type** | {type_badge} |
| **Date** | `{date}` |
| **Day** | {day_badge} |

---

## ⏪ Progress since previous log
{yesterday}

---

## 🎯 Plan for today
{today}

---

## 🚧 Blockers or questions
{blockers if blockers else "None."}

---

## 💡 Decisions made or notes
{decisions if decisions else "None."}
"""
    return new_body

def main():
    print("Fetching issue list from GitHub...")
    out = subprocess.check_output([GH_PATH, "issue", "list", "--state", "all", "--limit", "50", "--json", "number,title,labels,body"])
    issues = json.loads(out)
    print(f"Found {len(issues)} issues total.")

    updated_count = 0
    for issue in sorted(issues, key=lambda x: x["number"]):
        num = issue["number"]
        title = issue["title"]
        body = issue.get("body", "")
        labels = [l["name"] for l in issue.get("labels", [])]

        new_body = None
        if "daily" in labels or "[DAILY]" in title:
            new_body = format_daily_issue(body)
        elif "task" in labels or "[TASK]" in title or re.match(r"^\[[EMAXF]\d+\]", title):
            new_body = format_task_issue(body)

        if new_body and new_body.strip() != body.strip():
            print(f"Updating Issue #{num}: {title}...")
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
                tf.write(new_body)
                temp_path = tf.name

            try:
                subprocess.check_call([GH_PATH, "issue", "edit", str(num), "--body-file", temp_path])
                updated_count += 1
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    print(f"Successfully updated {updated_count} issues with beautiful badges!")

if __name__ == "__main__":
    main()
