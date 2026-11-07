# 🧠 Canonical Skills (`.agents/skills/`)

This directory is the **single source of truth** for the five project skills. Every engine reads
these files; `.claude/skills/` only contains pointers for Claude Code.

| Skill | Persona | Tasks |
|---|---|---|
| `data-cleaning` | `DataCleanerAgent` | E1–E3, M1, A3, A7, X1, X4 |
| `statistical-analysis` | `StatisticalAnalystAgent` | E4–E6, M2–M6, A1, A2, A4 |
| `eda-visualization` | `DataVizAgent` | E4–E5, M2, M5–M6, A4–A6, X2 |
| `executive-reporting` | `ExecutiveReporterAgent` | E6, M7, X5, X6 |
| `pr-self-review` | `QualityReviewerAgent` | X3 + every PR |

## Discovery

| Engine | Source |
|---|---|
| OpenCode | `.agents/skills/` (canonical) + `.claude/skills/` (pointers) |
| Claude Code | `.claude/skills/` (pointers) |
| Antigravity / Gemini Argon | `.agents/skills/` |

In OpenCode, `.agents/skills/` has higher precedence than `.claude/skills/` for the same skill ID,
so the canonical protocol always wins.

## Rules

1. **Never edit `.claude/skills/`.** Those files only point to this directory.
2. A skill is a directory with a `SKILL.md`; the ID is the directory name (lowercase kebab-case).
3. The frontmatter must include a clear `description` with the task IDs that activate the skill.
4. Supporting scripts and references live beside `SKILL.md`; paths inside a skill are relative to
   its directory.
5. Add or change a skill only when the spec (`specs/ontology.md`) or the governance (`AGENTS.md`)
   requires it.
