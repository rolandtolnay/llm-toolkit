# Slack App Setup

The app is just a container that Slack requires to issue a token with the right permissions. It won't appear as a bot or do anything on its own — it gives Claude a way to call the Slack API as you. All messages are sent as your Slack user, not as a bot account.

## 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create an App"**
3. Choose **"From scratch"** (simpler — no manifest needed)
4. Give it a name (e.g., "Claude CLI") and pick your workspace

## 2. Configure OAuth Scopes

1. Go to **OAuth & Permissions** in the sidebar
2. Scroll to **User Token Scopes** section
3. Add the following scopes:
   - `chat:write` — post messages
   - `search:read` — search messages
   - `channels:history` — read channel history
   - `channels:read` — read channel list
   - `users:read` — look up users
   - `users.profile:write` — set Slack status
   - `groups:history` — private channel history
   - `groups:read` — private channel access
   - `reactions:write` — add emoji reactions
   - `im:history` — read DM history

## 3. Install the App to Your Workspace

1. Scroll back up to the top of the OAuth & Permissions page
2. Click **"Install to Workspace"**
3. Approve the permission request when prompted
4. Copy the **User OAuth Token** (starts with `xoxp-`) that appears at the top of the page after installation

## 4. Configure Your Project

Add the token to `.claude/settings.local.json` (this file is git-ignored):

```json
{
  "env": {
    "SLACK_USER_TOKEN": "xoxp-your-token-here"
  }
}
```
