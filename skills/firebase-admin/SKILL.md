---
name: firebase-admin
description: Inspect and repair Firestore data, Auth users and Storage objects in a Firebase project, or run Admin SDK JavaScript against it. Use for Firebase data investigation and requested data or account repairs, not deployment, emulator lifecycle or infrastructure.
---

# Firebase Admin Agent CLI

A JSON CLI for Firebase data work. It exists so an agent can investigate and repair Firestore, Auth and Storage without ad hoc scripts, and so every result names the project, database, bucket and identity it ran against. Commands run with the selected identity's real IAM permissions. Reads and emulator-routed writes are routine; confirm a live write unless the user's request already names that change.

## Entry point

One-time setup (Node 22+), then run from the consumer project directory:

```sh
cd ~/.agents/skills/firebase-admin && npm ci && npm run build
CLI=~/.agents/skills/firebase-admin/bin/firebase-admin-agent.mjs
node "$CLI" context
node "$CLI" --help    # every command and its allowed flags
```

Examples below use `node "$CLI"`. Each command prints one JSON envelope on stdout: `{success, command, result}` or `{success:false, command, error:{code, message, suggestions?}}` with exit status 1. Branch on `code`; the message includes the service's own explanation, such as the link that creates a missing index, with tokens masked. Diagnostics, including script `console.log`, go to stderr. Large inputs go in files: `--file input.json` instead of `--data '...'`.

## Targeting

`context` reports the resolved project, database, bucket, identity source and emulator endpoints. It proves resolution, not IAM access. Run it in a repository you have not used this session or after switching accounts, and pass `--project` whenever the report differs from the intended target: a project saved by `firebase use` in an ancestor directory overrides the repository's `.firebaserc`.

- Project: `--project ID-or-alias`, then the Firebase CLI active project inherited up the directory tree, then legacy `firebase.json` defaults, then a single `.firebaserc` alias or its `default`. Missing or ambiguous selection fails rather than guessing. The Firebase root is the nearest ancestor containing `firebase.json`.
- Identity: one of `--account exact-email`, `--credential service-account.json`, `--adc`; then an explicitly set `GOOGLE_APPLICATION_CREDENTIALS`; then the Firebase login selected for this root or the global default login; ADC only when no Firebase login exists. A selected identity that is missing, expired or denied fails; nothing falls back to another identity.
- Resources: `--database NAME` and `--bucket NAME`, or a `.firebase-admin.json` in the root keyed by project ID: `{"PROJECT_ID":{"database":"named-db","bucket":"EXACT_BUCKET_NAME"}}`. Only the entry for the resolved project applies. Bucket names are never derived from the project ID.

Emulators: set `FIRESTORE_EMULATOR_HOST`, `FIREBASE_AUTH_EMULATOR_HOST` and `FIREBASE_STORAGE_EMULATOR_HOST` to `host:port`, or pass `--firestore-emulator`, `--auth-emulator`, `--storage-emulator`. `--emulator-only` and any `demo-` project use no live identity and refuse a service whose endpoint is unset; `exec` needs all three. Start and stop emulators with `firebase emulators:start|exec`.

ADC from plain `gcloud auth application-default login` is rejected by Firebase Auth. Use `gcloud auth application-default login --client-id-file=/path/to/desktop-oauth-client.json` or select a service-account credential; the CLI creates no keys or IAM grants.

## Reads

```sh
node "$CLI" firestore collections --limit 25
node "$CLI" firestore collections --path records/one --limit 25
node "$CLI" firestore get --path records/one
node "$CLI" firestore query --path records --limit 25 --data '{"where":[{"field":"updatedAt","op":">=","value":1700000000},{"field":"keywords","op":"array-contains","value":"term"}],"orderBy":[{"field":"updatedAt","direction":"asc"}],"select":["name","updatedAt"]}'
node "$CLI" firestore query --group entries --data '{"where":[{"field":"details.rating","op":"==","value":3}]}'
node "$CLI" firestore count --path records --data '{"where":[{"field":"members","op":"array-contains-any","value":["one","two"]}]}'
node "$CLI" auth get --uid EXACT_UID          # or --email / --phone
node "$CLI" auth list --limit 25
node "$CLI" storage list --bucket EXACT_BUCKET --prefix images/ --limit 25
node "$CLI" storage metadata --bucket EXACT_BUCKET --object images/example.png
```

Paths, IDs and collection names are literal; nothing appends suffixes or infers an environment from a name. Filters are ANDed with operators `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not-in`, `array-contains`, `array-contains-any`; server index constraints still apply. Compose anything more complex in JavaScript.

Pages default to 25 items (max 1000) and return `count` for the page plus `pageInfo: {hasNextPage, endCursor, consistency:"live"}`. To continue, repeat the same options with `--after END_CURSOR`; cursors are opaque and bound to the query. Nothing auto-exhausts pages, so stop paging once you have what the question needs. `count` answers how-many questions without reading documents.

## Writes

```sh
node "$CLI" firestore create --path records/new --file record.json
node "$CLI" firestore replace --path records/one --file replacement.json
node "$CLI" firestore merge --path records/one --data '{"details":{"reviewed":true}}'
node "$CLI" firestore patch --path records/one --data '{"details.note":null,"details.obsolete":{"$type":"delete"}}'
node "$CLI" firestore patch --path records/one --file patch.json --precondition '{"updateTime":{"$type":"timestamp","seconds":1700000000,"nanoseconds":123}}'
node "$CLI" firestore delete --path records/one --precondition '{"exists":true}'
node "$CLI" firestore batch --file batch.json      # [{op,path,data?,precondition?}], 1–500 ops, one atomic commit
node "$CLI" auth create --file user.json           # also update --uid, delete --uid, claims-get --uid, revoke --uid
node "$CLI" auth claims-set --uid EXACT_UID --data '{"role":"editor"}'
node "$CLI" storage upload --bucket EXACT_BUCKET --object images/example.png --source ./example.png --if-generation-match 0
node "$CLI" storage download --bucket EXACT_BUCKET --object images/example.png --destination ./download.png
node "$CLI" storage delete --bucket EXACT_BUCKET --object images/example.png --if-generation-match GENERATION
```

- `create` fails if the document exists. `replace` sets the whole document. `merge` upserts the supplied fields. `patch` requires an existing document; dotted keys update nested fields, a map value replaces that map, and `{"$type":"delete"}` removes a field where `null` stores null. `delete` removes one document and leaves its subcollections.
- `patch` and `delete` accept `--precondition` with `updateTime` from a previous read or `exists`. Use `patch` with `updateTime` for a repair that must not overwrite a concurrent change; `replace` and `merge` are unconditional.
- A batch is one Firestore commit: all operations apply or none do, and oversized input is rejected rather than split. Auth and Firestore changes are never atomic together.
- Auth data is ordinary Admin SDK user properties; `claims-set` replaces all claims (`--data null` clears them). Storage transfers move bytes to the named file or object and return metadata; `--if-generation-match` guards against concurrent changes, and `download` overwrites the local file.

A receipt carries the resolved target, the resource identity and completion evidence; it is the verification for a write. A timeout, a killed process or an `OUTCOME_UNKNOWN` error means the write may have landed: read the resource before retrying, because the CLI never replays a mutation and nothing is rolled back.

Admin writes bypass security rules and application-layer logic, and Firestore or Storage triggers may run on them. Check how the application maintains derived data before repairing it directly.

## Firebase JSON values

Ordinary JSON stays ordinary data. Special values use exact shapes:

| Value | JSON |
|---|---|
| Timestamp (nanosecond precision) | `{"$type":"timestamp","seconds":1700000000,"nanoseconds":123}` |
| Document reference | `{"$type":"reference","project":"PROJECT_ID","database":"(default)","path":"records/one"}` |
| Bytes | `{"$type":"bytes","base64":"AAH/"}` |
| GeoPoint | `{"$type":"geopoint","latitude":1.2,"longitude":3.4}` |
| Int64 beyond safe JS range | `{"$type":"integer","value":"9223372036854775807"}` |
| Double with a whole-number value | `{"$type":"double","value":5}` |
| Ordinary map with a `$type` key | `{"$type":"map","value":{"$type":"ordinary-data"}}` |
| Remove field | `{"$type":"delete"}` |
| Server time | `{"$type":"serverTimestamp"}` |
| Increment | `{"$type":"increment","value":1}` |
| Array transforms | `{"$type":"arrayUnion","values":["a"]}` / `{"$type":"arrayRemove","values":["a"]}` |

Data read from a document can be written back unchanged: reads tag whole-number doubles because an untagged `5` is written as an int64, which breaks clients that expect a double. References must belong to the selected project and database. Transforms are write-only. Unsupported values, such as NaN or vectors, fail instead of being coerced; read them through JavaScript.

## Sensitive outputs

```sh
node "$CLI" auth link --kind reset-password --email exact@example.com    # also verify-email, sign-in (needs --file settings), change-email --new-email
node "$CLI" auth custom-token --uid EXACT_UID
```

These return links and tokens marked `sensitive: true`; keep them out of tickets, logs and chat unless the user asked for them. A custom token is exchanged by a client sign-in flow; it is not an ID token. Signing needs a service-account credential or IAM signing setup, and a `SIGNING_FAILED` error names the fix. Routine user listings omit password material and claims; Storage output omits download tokens. Script output may contain anything the script returns.

## JavaScript

```sh
node "$CLI" exec --code 'const s = await db.collection("records").limit(3).get(); return s.docs.map(d => ({path: d.ref.path, data: d.data()}));'
node "$CLI" exec --file ./repair.js
```

The script is an async function body. Return plain data (for example `snapshot.data()`), which is serialized with the value table above into `result.value`; whole-number doubles returned this way appear as plain numbers. Bindings: `app`, `db` (the selected database), `auth`, `storage`, `bucket` (or null), `target`, `sdk` (Admin app and Firestore helpers plus `getMessaging`), and `require`. Relative `require` and `import()` paths resolve from the skill, so load consumer files by absolute path. A script that throws reports `OUTCOME_UNKNOWN` with the error text, because nothing proves which of its writes landed first. Use the supplied `db` and `storage` rather than re-initializing them: Admin's convenience initializers reject the Firebase-login credential. Transactions, Messaging and other Admin services live here.

Scripts are trusted code with full process access. There is no sandbox, read-only mode, dry run or rollback, and emulator routing does not constrain what a script does.

## Scope

Use `firebase` for deployment, emulator lifecycle, rules, indexes and function logs; `flutterfire` for Flutter configuration; `gcloud` for IAM and infrastructure. This CLI holds no application logic: profile synchronisation, cascades and domain workflows belong in the application or an explicitly authored script.
