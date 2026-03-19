# GitHub API Reference for PR Comment Triage

Commands for fetching, replying to, and resolving PR review comments.

## Finding the PR

```bash
gh pr list --head $(git branch --show-current) --json number,title,url,baseRefName --limit 1
```

## Repo Identity

```bash
gh repo view --json nameWithOwner -q .nameWithOwner
```

Returns `owner/repo` format. Split on `/` for API calls.

## Fetching Comments

### Review comments (inline on code)

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate
```

Key fields: `path`, `line`, `original_line`, `body`, `user.login`, `id`, `in_reply_to_id`

### Issue-level comments (top-level on the PR)

```bash
gh api repos/{owner}/{repo}/issues/{number}/comments --paginate
```

Key fields: `body`, `user.login`, `id`

### Parsing with jq

```bash
# Top-level review comments only (filter out replies)
gh api repos/{owner}/{repo}/pulls/{number}/comments --paginate | \
  jq -r '.[] | select(.in_reply_to_id == null) | "---\n**\(.path):\(.line // .original_line)** by @\(.user.login) (id:\(.id))\n\(.body)\n"'

# Issue-level comments (filter by non-bot authors for human comments)
gh api repos/{owner}/{repo}/issues/{number}/comments --paginate | \
  jq -r '.[] | "---\n**Issue comment by @\(.user.login)** (id:\(.id))\n\(.body)\n"'
```

## Replying to Comments

```bash
gh api repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies \
  -f body="Reply text here"
```

## Editing Comments

```bash
gh api repos/{owner}/{repo}/pulls/comments/{comment_id} -X PATCH \
  -f body="Updated text here"
```

Note: NO PR number in the path. This differs from the reply endpoint.

## Resolving Threads

### Step 1: Get thread IDs

```bash
gh api graphql -f query='{
  repository(owner: "{owner}", name: "{repo}") {
    pullRequest(number: {number}) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) {
            nodes { databaseId }
          }
        }
      }
    }
  }
}'
```

Map `databaseId` (REST API comment ID) to the thread `id` (GraphQL node ID).

### Step 2: Resolve a thread

```bash
gh api graphql -f query='mutation {
  resolveReviewThread(input: {threadId: "{thread_node_id}"}) {
    thread { isResolved }
  }
}'
```

## Gotchas

- **GitHub GraphQL `body` field takes no arguments.** Do NOT use `body(truncate: N)` — it will error with `argumentNotAccepted`. To limit output size, fetch the full `body` and truncate client-side with jq: `--jq '... | .body | .[0:120]'`.

- **Editing a review comment uses a different endpoint than replying.** To PATCH (update) a review comment, use `repos/{owner}/{repo}/pulls/comments/{comment_id}` — note there is NO PR number in the path. The reply endpoint `repos/{owner}/{repo}/pulls/{number}/comments/{comment_id}/replies` nests under the PR number, but the edit endpoint does not. Using `pulls/{number}/comments/{id}` for PATCH will 404.

## Efficiency Notes

- Always use `--paginate` when fetching comments
- Reply to multiple comments in parallel (independent API calls)
- Fetch thread IDs once, then resolve in parallel
- Filter out bot summary comments (walkthrough, poem, checkboxes) — focus on actionable review comments
- Filter out `in_reply_to_id != null` to skip reply comments and get only thread starters
