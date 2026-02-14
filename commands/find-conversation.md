---
description: Find a previous Claude Code conversation by describing what it was about
argument-hint: <description of the conversation>
allowed-tools: [Bash, Read, Grep, Glob, AskUserQuestion]
---

<objective>
Find a previous Claude Code conversation in the current project by searching session JSONL files for content matching the user's natural language description.

Return the session ID so the user can resume it with `claude --resume <id>`.
</objective>

<context>
User is looking for: $ARGUMENTS

Current project path: !`pwd`
</context>

<process>
1. **Encode the project path** to find the conversation storage directory.
   Claude Code stores conversations at `~/.claude/projects/[encoded-path]/`.
   Path encoding: replace `/` with `-`, prefix with `-`.
   Example: `/Users/name/project` becomes `-Users-name-project`.
   Run `ls` on the encoded directory to confirm it exists.

2. **Extract 3-5 distinctive keywords** from the user's description.
   Pick terms that are specific enough to narrow results — proper nouns, technical terms, ticket IDs, feature names.
   Avoid generic words like "the", "code", "work", "changes".

3. **Search today's sessions first, then expand if needed.**
   List JSONL files sorted by modification time (`ls -lt`).
   Focus on files from the relevant timeframe. If the user mentions "today", "yesterday", or a date, filter accordingly.
   For each candidate file, count keyword matches:
   ```
   grep -c "keyword1\|keyword2\|keyword3" <file>
   ```
   Rank files by hit count. The file with the most combined hits is the strongest candidate.

4. **Verify the top candidate.**
   For the top 1-2 candidates, extract matching lines to confirm relevance:
   ```
   grep -o "keyword1\|keyword2\|specific-phrase" <file> | sort | uniq -c | sort -rn | head -20
   ```
   Check that the content matches what the user described — not just keyword presence but contextual fit.

5. **If results are ambiguous, ask the user.**
   When multiple sessions have similar hit counts, or the top candidate doesn't clearly match, use AskUserQuestion with options showing:
   - Session ID (shortened)
   - Date/time from filename modification
   - Key content snippets found
   Let the user pick the right one.

6. **Return the session ID.**
   Present the result clearly with the resume command:
   ```
   claude --resume <session-id>
   ```
</process>

<success_criteria>
- Correct session ID identified and returned
- User can immediately copy-paste the resume command
- If ambiguous, user was presented with clear options to choose from
- No false positives — verified the session content matches the description
</success_criteria>
