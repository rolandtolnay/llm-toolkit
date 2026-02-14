---
description: Generate a work report from git commit timestamps for a specified time period
argument-hint: <period> [buffer]
---

<objective>
Generate a comprehensive work report based on git commit timestamps for the specified time period.

This helps track work hours by analyzing first/last commit times per day, adding configurable buffers, counting commits, and summarizing accomplishments. The report displays in chat first, then offers optional markdown export.
</objective>

<context>
Verify git repository: ! `git rev-parse --is-inside-work-tree 2>/dev/null || echo "NOT_A_GIT_REPO"`
Current git user: ! `git config user.name`
Current date: ! `date +%Y-%m-%d`
</context>

<process>
1. **Validate environment**
   - If not in a git repository, display a helpful error message and stop
   - Confirm the git user name for filtering commits

2. **Parse the time period from ``**
   - Interpret flexible period formats:
     - Month names: "january", "jan", "January 2026"
     - ISO format: "2026-01", "2026-01-15"
     - Relative: "this week", "last week", "today", "yesterday", "this month", "last month"
   - Determine the start and end dates for the git log query
   - If period is ambiguous, ask user for clarification

3. **Parse buffer time (default: 30 minutes)**
   - Check if `` includes a buffer override (e.g., "january 45min", "this week 1hour")
   - Supported formats: "30min", "45min", "1hour", "1h", "60min"
   - Default to 30 minutes before first commit and 30 minutes after last commit

4. **Fetch git commit data**
   - Run: `git log --format="%H|%ad|%s" --date=format:"%Y-%m-%d %H:%M:%S" --after="[start]" --before="[end]" --author="[git user]"`
   - Group commits by day
   - For each day, extract:
     - All commit timestamps (ordered chronologically)
     - Total commit count
     - All commit messages

5. **Detect work sessions using gap threshold (default: 120 minutes)**
   - For each day, analyze gaps between consecutive commits
   - If gap ≥ 120 minutes (2 hours), treat as a break between sessions
   - Split the day's commits into separate work sessions
   - Example: commits at 10:00, 11:00, 13:00, 18:00, 19:00 → Session 1 (10-13), Session 2 (18-19)

6. **Calculate work hours per session**
   - For each session:
     - Span = last commit time - first commit time
     - Session hours = span + buffer before (30min) + buffer after (30min)
   - For single-commit sessions: use 1 hour (buffer before + buffer after)
   - Daily total = sum of all session hours
   - Calculate two values:
     - **Est. Hours**: Raw calculation rounded to 1 decimal place (e.g., 8.4)
     - **Rounded**: Round to nearest 0.5 hour for cleaner reporting (e.g., 8.4 → 8.5, 12.2 → 12.0)
   - Use the "Rounded" values for all totals and summary statistics

7. **Generate daily summaries**
   - For each day, analyze all commit messages
   - Create a 1-2 sentence summary of accomplishments
   - Focus on features, fixes, and major changes
   - Use action verbs and be concise

8. **Build the report with these sections**

   **Daily Breakdown Table:**
   | Date | Sessions | First | Last | Commits | Est. Hours | Rounded | Summary |

   Notes:
   - "Sessions" shows count if multiple sessions detected (e.g., "2 sessions")
   - "Est. Hours" is raw calculation (1 decimal)
   - "Rounded" is nearest 0.5 hour for cleaner totals

   **Summary Statistics** (use Rounded values for all totals):
   - Total days worked
   - Total commits
   - Total hours (sum of Rounded column)
   - Average hours/day worked
   - Average commits/day
   - Most productive day (hours)
   - Highest commit day

   **Weekly Breakdown** (if period spans multiple weeks, use Rounded values):
   | Week | Days Worked | Hours | Commits |

   **Key Accomplishments:**
   - Group work into logical categories (features, infrastructure, fixes, etc.)
   - List major achievements with brief descriptions

9. **Display the report in chat**
   - Present the full formatted report using markdown tables
   - Include a note about estimation methodology (session detection with 2hr gap threshold)

10. **Offer export option**
   - Ask user: "Would you like to export this report to a markdown file?"
   - If yes, ask for the file path
   - Write the report to the specified location
   - Confirm successful export
</process>

<success_criteria>
- Git repository validated before processing
- Time period correctly interpreted from user input
- All commits within period captured and grouped by day
- Work sessions detected using 2-hour gap threshold
- Work hours calculated per session with appropriate buffers
- Daily summaries accurately reflect commit activity
- Report displays cleanly in chat with proper markdown formatting
- Export works correctly if requested
- Handles edge cases: no commits in period, single-day period, single commit days, single-commit sessions
</success_criteria>

<examples>
**Basic month report:**
`/work-report january`
→ Generates report for January of the current/most recent year

**Specific month with year:**
`/work-report 2026-01`
→ Generates report for January 2026

**Custom buffer:**
`/work-report january 45min`
→ Uses 45-minute buffers instead of default 30

**Relative periods:**
`/work-report this week`
→ Report for current week (Monday to today)

`/work-report last month`
→ Report for the previous calendar month

`/work-report today`
→ Single-day report for today's commits
</examples>
