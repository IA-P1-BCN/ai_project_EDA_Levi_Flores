# 📁 GitHub Projects Setup — EDA Project

This document defines the operational layer of the project: labels, milestones, custom fields and the two
required project views. It is aligned with [`docs/Work_Plan.md`](../Work_Plan.md) and the issue backlog in
[`ISSUE_BACKLOG.md`](ISSUE_BACKLOG.md).

**Project name:** `EDA Project — Customer Messy Data`
**Template:** Board
**Repository:** `IA-P1-BCN/ai_project_EDA_Levi_Flores`

---

## 1. Labels

Create these labels before opening any issue. The issue templates apply `task` and `daily` automatically;
the rest are added when the issue is created or refined.

| Label | Colour | Purpose |
|---|---|---|
| `task` | `#1D76DB` | Development or documentation task. |
| `daily` | `#0E8A16` | Daily progress report. |
| `level:foundation` | `#C5DEF5` | Project setup and planning. |
| `level:essential` | `#0E8A16` | Essential delivery level. |
| `level:medium` | `#FBCA04` | Medium delivery level. |
| `level:advanced` | `#D93F0B` | Advanced delivery level. |
| `level:expert` | `#B60205` | Expert delivery level. |
| `area:setup` | `#BFD4F2` | Repository, environment and planning. |
| `area:data` | `#1D76DB` | Data loading and enrichment. |
| `area:cleaning` | `#5319E7` | Data quality and cleaning. |
| `area:analysis` | `#006B75` | Statistical analysis and feature engineering. |
| `area:visualization` | `#F9D0C4` | Charts and interactive visuals. |
| `area:reporting` | `#D4C5F9` | Executive report, quality report and presentation. |
| `area:engineering` | `#C2E0C6` | Reusable code, pipeline and tests. |
| `area:release` | `#FEF2C0` | Publication and final documentation. |

Optional creation commands:

```bash
gh label create "task" --color "1D76DB" --description "Development or documentation task"
gh label create "daily" --color "0E8A16" --description "Daily progress report"
gh label create "level:foundation" --color "C5DEF5" --description "Project setup and planning"
gh label create "level:essential" --color "0E8A16" --description "Essential delivery level"
gh label create "level:medium" --color "FBCA04" --description "Medium delivery level"
gh label create "level:advanced" --color "D93F0B" --description "Advanced delivery level"
gh label create "level:expert" --color "B60205" --description "Expert delivery level"
gh label create "area:setup" --color "BFD4F2" --description "Repository, environment and planning"
gh label create "area:data" --color "1D76DB" --description "Data loading and enrichment"
gh label create "area:cleaning" --color "5319E7" --description "Data quality and cleaning"
gh label create "area:analysis" --color "006B75" --description "Statistical analysis and feature engineering"
gh label create "area:visualization" --color "F9D0C4" --description "Charts and interactive visuals"
gh label create "area:reporting" --color "D4C5F9" --description "Executive report, quality report and presentation"
gh label create "area:engineering" --color "C2E0C6" --description "Reusable code, pipeline and tests"
gh label create "area:release" --color "FEF2C0" --description "Publication and final documentation"
```

---

## 2. Milestones

| Milestone | Due date | Scope |
|---|---|---|
| Foundation | 2026-11-04 | Repository, environment and work plan. |
| Essential | 2026-11-06 | Tasks E1–E6. |
| Medium | 2026-11-08 | Tasks M1–M7 and executive report. |
| Advanced | 2026-11-09 | Tasks A1–A7. |
| Expert | 2026-11-10 | Tasks X1–X6, quality report and public release. |

---

## 3. Custom fields

Create the fields in this exact order: **the order of the options defines the order of the board columns**.

| Field | Type | Options / notes |
|---|---|---|
| `Status` | Single select | `Backlog`, `Ready`, `In Progress`, `Blocked`, `In Review`, `Done` |
| `Level` | Single select | `Foundation`, `Essential`, `Medium`, `Advanced`, `Expert` |
| `Day` | Single select | `Tue 03 Nov 2026`, `Wed 04 Nov 2026`, `Thu 05 Nov 2026`, `Fri 06 Nov 2026`, `Sat 07 Nov 2026`, `Sun 08 Nov 2026`, `Mon 09 Nov 2026`, `Tue 10 Nov 2026` |
| `Workstream` | Single select | `Setup`, `Data`, `Cleaning`, `Analysis`, `Visualization`, `Reporting`, `Engineering`, `Release`, `Management` |
| `Priority` | Single select | `P0 - Critical`, `P1 - High`, `P2 - Normal` |
| `Estimate` | Single select | `S - Up to 2 hours`, `M - 2 to 4 hours`, `L - 4 to 8 hours` |
| `Task ID` | Text | Values such as `E1`, `M3`, `A2`, `X4`, `D1`. |
| `Branch` | Text | Branch created for the task. Empty for daily logs. |
| `Pull Request` | Text | PR number or URL. |
| `Start date` | Date | Planned start. |
| `Target date` | Date | Planned completion. |

Built-in fields used in the views: `Title`, `Assignees`, `Labels`, `Milestone` and `Linked pull requests`.

---

## 4. Project views

The project has **four views** — two dedicated to development tasks (`Issues Board` and `Issues Table`) and two dedicated to daily tracking (`Daily Log Board` and `Daily Log Table`).

### View 1 — `Issues Board` (Kanban Board for Tasks)

| Setting | Value |
|---|---|
| Layout | Board (`BOARD_LAYOUT`) |
| Filter | `is:issue -label:daily` |
| Group by | `Status` |
| Columns | `Backlog` → `Ready` → `In Progress` → `Blocked` → `In Review` → `Done` |
| Sort | `Priority` (P0 first), then `Target date` (oldest first) |
| Card fields | `Title`, `Status`, `Task ID`, `Level`, `Priority`, `Estimate`, `Target date`, `Branch`, `Pull Request`, `Assignees`, `Milestone`, `Labels` |
| WIP limits | `Ready`: 3, `In Progress`: 1, `In Review`: 1 |

**Column meaning**

| Column | Meaning |
|---|---|
| `Backlog` | Captured but not ready to start. |
| `Ready` | Fully specified, dependencies resolved, next in queue. |
| `In Progress` | Branch open and work actively underway (maximum one task). |
| `Blocked` | Cannot continue; the blocker must be described in the issue. |
| `In Review` | Self-review and CI checks in progress. |
| `Done` | PR squash-merged, issue closed and branch deleted. |

### View 2 — `Issues Table` (Structured Backlog Table for Tasks)

| Setting | Value |
|---|---|
| Layout | Table (`TABLE_LAYOUT`) |
| Filter | `is:issue -label:daily` |
| Group by | `Level` (`Foundation` → `Essential` → `Medium` → `Advanced` → `Expert`) |
| Sort | `Target date` (oldest first), then `Priority` (P0 first) |
| Visible columns | `Title`, `Task ID`, `Status`, `Level`, `Workstream`, `Priority`, `Estimate`, `Day`, `Branch`, `Pull Request`, `Start date`, `Target date`, `Milestone`, `Assignees`, `Labels` |

**Purpose:** provides a full spreadsheet-style overview of all 29 task issues (`F1–F3`, `E1–E6`, `M1–M7`, `A1–A7`, `X1–X6`) to audit metadata, branches, PR links, dates and estimates at a glance.

### View 3 — `Daily Log Board` (Sprint Calendar Board for Dailys)

| Setting | Value |
|---|---|
| Layout | Board (`BOARD_LAYOUT`) |
| Filter | `label:daily` |
| Group by | `Day` |
| Columns | `Tue 03 Nov 2026` → `Wed 04 Nov 2026` → `Thu 05 Nov 2026` → `Fri 06 Nov 2026` → `Sat 07 Nov 2026` → `Sun 08 Nov 2026` → `Mon 09 Nov 2026` → `Tue 10 Nov 2026` |
| Sort | `Target date` (oldest first) |
| Card fields | `Title`, `Day`, `Task ID`, `Status`, `Workstream`, `Start date`, `Target date`, `Assignees`, `Labels` |

**Column meaning:** each column is one working day of the sprint (`D1` to `D8`). The card in a column is the daily log issue for that date. Daily logs record what was done, what is planned, blockers and decisions; they are not development tasks and therefore do not need a branch.

### View 4 — `Daily Log Table` (Chronological Table for Dailys)

| Setting | Value |
|---|---|
| Layout | Table (`TABLE_LAYOUT`) |
| Filter | `label:daily` |
| Sort | `Target date` (oldest first: `2026-11-03` → `2026-11-10`) |
| Visible columns | `Title`, `Task ID`, `Day`, `Status`, `Workstream`, `Estimate`, `Start date`, `Target date`, `Assignees`, `Labels` |

**Purpose:** provides a chronological log table of all 8 working days (`D1–D8`) for quick auditing of sprint progress and completion status.

---

## 5. Recommended workflows

Enable these built-in workflows in **Project → Workflows**:

| Workflow | Action |
|---|---|
| Auto-add to project | Add every issue from this repository to the project. |
| Item added to project | Set `Status` to `Backlog`. |
| Issue closed | Set `Status` to `Done`. |
| Pull request merged | Set `Status` to `Done` for linked issues. |

Status changes during the day are manual so the board reflects reality (one task in `In Progress` at a time).

---

## 6. Setup checklist

1. Create the 15 labels from section 1.
2. Create the five milestones from section 2.
3. Create the project `EDA Project — Customer Messy Data` using the Board template.
4. Add the custom fields from section 3, keeping the option order.
5. Configure **View 1 (`Issues Board`)** and **View 2 (`Issues Table`)** filtered by `is:issue -label:daily`.
6. Configure **View 3 (`Daily Log Board`)** and **View 4 (`Daily Log Table`)** filtered by `label:daily`.
7. Create the task issues from [`ISSUE_BACKLOG.md`](ISSUE_BACKLOG.md) using the **Task** template.
8. Add each issue to the project and fill `Level`, `Day`, `Workstream`, `Priority`, `Estimate`, `Task ID`,
   `Branch`, `Start date` and `Target date`.
9. Enable the workflows from section 5.
10. Create the daily logs (`D1–D8`) with the **Daily Log** template and place each one in its date column.

---

## 7. Daily routine

**Start of day**

1. Create the daily log issue with the **Daily Log** template (`[DAILY] YYYY-MM-DD`).
2. Set `Date`, `Day`, `Task ID`, `Workstream` (`Management`) and `Target date`; add it to the project.
3. Write the plan for the day and link the task IDs that will be worked on.

**During the day**

1. Move the active task issue to `In Progress` and fill its `Branch` field.
2. When the PR is opened, fill `Pull Request` and move the task to `In Review`.
3. Record blockers immediately and link them from the task issue.

**End of day**

1. Complete the daily log: progress, decisions, blockers, branches and PRs, next-day focus.
2. Update the status of every task issue touched during the day.
3. Close the daily log issue only when the report is complete.

---

## 8. Conventions

- **Issue title:** `[ID] Short description` for tasks and `[DAILY] YYYY-MM-DD` for daily logs.
- **One task, one branch, one PR:** use the branch names defined in `docs/Work_Plan.md`.
- **PR linkage:** include `Closes #<issue-number>` in the PR description so the merge closes the issue.
- **Merge policy:** the author self-reviews and squash-merges; the branch is deleted afterwards.
- **Project hygiene:** no task stays in `In Progress` without an open branch and an owner.
