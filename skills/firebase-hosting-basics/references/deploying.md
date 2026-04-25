# Deploying to Firebase Hosting

## Standard Deployment
To deploy your Hosting content and configuration to your live site:

```bash
npx -y firebase-tools@latest deploy --only hosting
```

This deploys to your default sites (`PROJECT_ID.web.app` and `PROJECT_ID.firebaseapp.com`).

## Preview Channels
Preview channels allow you to test changes on a temporary URL before going live.

### Deploy to a Preview Channel
```bash
npx -y firebase-tools@latest hosting:channel:deploy CHANNEL_ID
```
Replace `CHANNEL_ID` with a name (e.g., `feature-beta`).
This returns a preview URL like `PROJECT_ID--CHANNEL_ID-RANDOM_HASH.web.app`.

### Expiration
Channels expire after 7 days by default. To set a different expiration:
```bash
npx -y firebase-tools@latest hosting:channel:deploy CHANNEL_ID --expires 1d
```

## Multiple Sites (Multisite Hosting)

A single Firebase project can host up to 36 separate sites, each with its own `SITE_ID.web.app` URL and independent content. Deploying to one site does not affect the others.

### 1. Create a New Site
```bash
npx -y firebase-tools@latest hosting:sites:create SITE_ID --project PROJECT_ID
```
Site IDs must be globally unique, use only lowercase letters, numbers, and hyphens (no underscores or dots).

### 2. Set Up a Deploy Target
Deploy targets map a short name to a site ID. The mapping is stored in `.firebaserc`.
```bash
npx -y firebase-tools@latest target:apply hosting TARGET_NAME SITE_ID --project PROJECT_ID
```

### 3. Configure `firebase.json`
Reference the deploy target in your hosting config. Use an array for multiple sites:
```json
{
  "hosting": [
    {
      "target": "main",
      "public": "public",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"]
    },
    {
      "target": "blog",
      "public": "blog/dist",
      "ignore": ["firebase.json", "**/.*", "**/node_modules/**"]
    }
  ]
}
```
A single site can also use the `target` field without an array.

### 4. Deploy to a Specific Site
```bash
npx -y firebase-tools@latest deploy --only hosting:TARGET_NAME --project PROJECT_ID
```
Omit the `:TARGET_NAME` to deploy all sites at once.

### 5. List and Delete Sites
```bash
npx -y firebase-tools@latest hosting:sites:list --project PROJECT_ID
npx -y firebase-tools@latest hosting:sites:delete SITE_ID --project PROJECT_ID --force
```
The default site (matching the project ID) cannot be deleted. Deleting a site is permanent and the site ID cannot be reused.

### 6. Emulate a Specific Site Locally
```bash
npx -y firebase-tools@latest emulators:start --only hosting:TARGET_NAME
```

## Cloning to Live
You can promote a version from a preview channel to your live channel without rebuilding.

```bash
npx -y firebase-tools@latest hosting:clone SOURCE_SITE_ID:SOURCE_CHANNEL_ID TARGET_SITE_ID:live
```

**Example:**
Clone the `feature-beta` channel on your default site to live:
```bash
npx -y firebase-tools@latest hosting:clone my-project:feature-beta my-project:live
```
