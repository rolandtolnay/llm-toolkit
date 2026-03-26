# Investigation Guide

How to verify comments marked INVESTIGATE.

## With agent-browser

**Check if agent-browser is available** (run `which agent-browser` or check if the skill is listed).

If available, spawn a **general-purpose Agent** with a prompt that:
1. Invokes the `agent-browser` skill to load browser automation instructions
2. Navigates to the relevant page/flow in the running app
3. Performs the specific action described in the comment
4. Reports whether the issue reproduces, with screenshot evidence

## Without agent-browser

Present the investigation need to the user via AskUserQuestion:
- Describe what specific behavior needs verification
- Ask the user to check manually and report back
- Include concrete steps: "Open page X, click Y, observe whether Z happens"
