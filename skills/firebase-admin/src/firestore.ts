import {
  DocumentReference,
  FieldPath,
  Timestamp,
  type DocumentSnapshot,
  type Firestore,
  type OrderByDirection,
  type Precondition,
  type Query,
  type WhereFilterOp,
  type WriteBatch,
} from 'firebase-admin/firestore';
import {
  CliError,
  classify,
  cursor,
  input,
  invalid,
  limit,
  object,
  pageInfo,
  required,
  text,
  uncursor,
  type Options,
} from './shared.js';
import { decode, encode, fromFirestore } from './values.js';

type Target = { project: string; database: string };
type Order = { field: string; direction: OrderByDirection };
type Mutation = { op: string; path: string; data?: unknown; precondition?: unknown };
type ProtoTime = { seconds?: number | string | { toString(): string }; nanos?: number };
type CommitResponse = { commitTime?: ProtoTime; writeResults?: { updateTime?: ProtoTime }[] };
// WriteBatch.commit() installs automatic retry codes; the pinned one-commit method accepts an empty set.
type CommitBatch = { _commit(options: { retryCodes: number[] }): Promise<CommitResponse> };

const operations = new Set(['create', 'replace', 'merge', 'patch', 'delete']);
const operators = new Set([
  '<',
  '<=',
  '==',
  '!=',
  '>=',
  '>',
  'array-contains',
  'in',
  'not-in',
  'array-contains-any',
]);
const inequalities = new Set(['<', '<=', '!=', '>=', '>', 'not-in']);
const own = (value: object, key: string) => Object.prototype.hasOwnProperty.call(value, key);

function only(value: Record<string, unknown>, allowed: string[], label: string): void {
  if (Object.keys(value).some((key) => !allowed.includes(key)))
    invalid(`${label} contains unsupported properties.`);
}
function path(value: unknown, document: boolean): string {
  if (
    typeof value !== 'string' ||
    !value ||
    value.split('/').some((p) => !p) ||
    (value.split('/').length % 2 === 0) !== document
  ) {
    invalid(
      document
        ? 'Expected a literal document path (an even number of segments).'
        : 'Expected a literal collection path (an odd number of segments).',
    );
  }
  return value;
}
function field(value: unknown): string {
  if (typeof value !== 'string' || !value || value.split('.').some((p) => !p))
    invalid('Field must be a nonempty dotted field path.');
  return value;
}
function fieldPath(value: string): FieldPath {
  return value === '__name__' ? FieldPath.documentId() : new FieldPath(...value.split('.'));
}
function precondition(value: unknown, db: Firestore): Precondition | undefined {
  if (value === undefined) return undefined;
  const spec = object(value, 'Precondition');
  only(spec, ['exists', 'updateTime'], 'Precondition');
  if (own(spec, 'exists') === own(spec, 'updateTime'))
    invalid('Precondition requires exactly one of exists or updateTime.');
  if (own(spec, 'exists')) {
    if (typeof spec.exists !== 'boolean') invalid('Precondition exists must be boolean.');
    return { exists: spec.exists };
  }
  const timestamp = decode(spec.updateTime, db);
  if (!(timestamp instanceof Timestamp)) invalid('Precondition updateTime must be a typed timestamp.');
  return { lastUpdateTime: timestamp };
}
function parsePrecondition(options: Options): unknown {
  const raw = text(options, 'precondition');
  if (raw === undefined) return undefined;
  try {
    return JSON.parse(raw);
  } catch {
    return invalid('--precondition must be a JSON object.');
  }
}
function addMutation(
  batch: WriteBatch,
  mutation: Mutation,
  db: Firestore,
): { op: string; id: string; path: string } {
  if (!operations.has(mutation.op)) invalid('Batch op must be create, replace, merge, patch, or delete.');
  const ref = db.doc(path(mutation.path, true));
  if (mutation.precondition !== undefined && !['patch', 'delete'].includes(mutation.op)) {
    invalid(
      'Preconditions are supported only for patch/delete. Create already requires absence; replace/merge use unconditional set semantics.',
    );
  }
  const condition = precondition(mutation.precondition, db);
  if (mutation.op === 'delete') {
    if (own(mutation, 'data')) invalid('Delete does not accept data.');
    batch.delete(ref, condition);
  } else {
    const data = decode(mutation.data, db);
    switch (mutation.op) {
      case 'create':
        batch.create(ref, data);
        break;
      case 'replace':
        batch.set(ref, data);
        break;
      case 'merge':
        batch.set(ref, data, { merge: true });
        break;
      case 'patch':
        condition ? batch.update(ref, data, condition) : batch.update(ref, data);
        break;
    }
  }
  return { op: mutation.op, id: ref.id, path: ref.path };
}
function timestamp(value: ProtoTime | undefined): Timestamp {
  if (!value || value.seconds === undefined)
    throw new CliError(
      'OUTCOME_UNKNOWN',
      'Commit response lacks a completion timestamp. Verify the target before retrying.',
    );
  return new Timestamp(Number(value.seconds.toString()), value.nanos ?? 0);
}
function identity(snapshot: DocumentSnapshot, data = snapshot.data()): Record<string, unknown> {
  return {
    id: snapshot.id,
    path: snapshot.ref.path,
    data: fromFirestore(data ?? {}),
    createTime: snapshot.createTime ?? null,
    updateTime: snapshot.updateTime ?? null,
  };
}

async function collections(db: Firestore, options: Options, target: Target): Promise<unknown> {
  const parent = text(options, 'path');
  if (parent !== undefined) path(parent, true);
  const size = limit(options);
  const scope = { type: 'firestore.collections', target, parent: parent ?? null };
  const after = uncursor(text(options, 'after'), scope);
  if (after !== undefined && typeof after !== 'string') invalid('Invalid collections continuation.');
  // listCollections() fetches every ID; the page is cut by ID order so continuation stays live.
  const refs = await (parent ? db.doc(parent) : db).listCollections();
  const ids = refs
    .map((ref) => ref.id)
    .sort()
    .filter((id) => after === undefined || id > after);
  const page = ids.slice(0, size);
  const next = ids.length > size ? cursor(scope, page.at(-1)) : null;
  return {
    collections: page.map((id) => ({ id, path: parent ? `${parent}/${id}` : id })),
    count: page.length,
    pageInfo: pageInfo(next),
  };
}

function projected(
  snapshot: DocumentSnapshot,
  select: string[] | undefined,
): Record<string, unknown> | undefined {
  if (select === undefined) return snapshot.data();
  // Null-prototype containers keep a literal "__proto__" field name as plain data.
  const data: Record<string, any> = Object.create(null);
  for (const name of select) {
    const value = name === '__name__' ? undefined : snapshot.get(fieldPath(name));
    if (value === undefined) continue;
    const segments = name.split('.');
    let into = data;
    for (const segment of segments.slice(0, -1)) into = into[segment] ??= Object.create(null);
    into[segments.at(-1)!] = value;
  }
  return data;
}
async function query(db: Firestore, action: string, options: Options, target: Target): Promise<unknown> {
  const collection = text(options, 'path');
  const group = text(options, 'group');
  if ((collection === undefined) === (group === undefined))
    invalid('Use exactly one of --path collection or --group collection-id.');
  if (collection !== undefined) path(collection, false);
  if (group !== undefined && group.includes('/')) invalid('--group must be a collection ID, not a path.');
  const supplied = await input(options, false);
  const spec = object(supplied === undefined ? {} : supplied, 'Query specification');
  only(spec, ['where', 'orderBy', 'select'], 'Query specification');
  for (const key of ['where', 'orderBy', 'select']) {
    if (spec[key] !== undefined && !Array.isArray(spec[key])) invalid(`Query ${key} must be an array.`);
  }
  let q: Query = collection !== undefined ? db.collection(collection) : db.collectionGroup(group!);
  const filters: { field: string; op: WhereFilterOp; value: unknown }[] = [];
  const inequalityFields = new Set<string>();
  for (const item of spec.where ?? []) {
    const filter = object(item, 'Query filter');
    only(filter, ['field', 'op', 'value'], 'Query filter');
    const name = field(filter.field);
    if (typeof filter.op !== 'string' || !operators.has(filter.op) || !own(filter, 'value'))
      invalid('Query filter requires a supported op and value.');
    const value = decode(filter.value, db);
    filters.push({ field: name, op: filter.op as WhereFilterOp, value: encode(value) });
    q = q.where(fieldPath(name), filter.op as WhereFilterOp, value);
    if (inequalities.has(filter.op) && name !== '__name__') inequalityFields.add(name);
  }
  const orders: Order[] = [];
  for (const item of spec.orderBy ?? []) {
    const order = object(item, 'Query ordering');
    only(order, ['field', 'direction'], 'Query ordering');
    const name = field(order.field);
    const direction = order.direction === undefined ? 'asc' : order.direction;
    if (direction !== 'asc' && direction !== 'desc') invalid('Order direction must be asc or desc.');
    if (orders.some((o) => o.field === name) || orders.some((o) => o.field === '__name__'))
      invalid('Order fields must be unique, with documentId (__name__) last.');
    orders.push({ field: name, direction });
  }
  const direction = orders.at(-1)?.direction ?? 'asc';
  const explicitId = orders.at(-1)?.field === '__name__' ? orders.pop() : undefined;
  // Make the backend's implicit inequality ordering explicit so cursor values cover the full ordering.
  for (const name of [...inequalityFields].sort()) {
    if (!orders.some((o) => o.field === name)) orders.push({ field: name, direction });
  }
  orders.push(explicitId ?? { field: '__name__', direction });
  for (const order of orders) q = q.orderBy(fieldPath(order.field), order.direction);
  const select: string[] | undefined = spec.select?.map(field);
  const scope = {
    type: 'firestore.query',
    target,
    collection: collection ?? null,
    group: group ?? null,
    filters,
    orders,
    select: select ?? null,
  };
  if (action === 'count') {
    const result = await q.count().get();
    return { count: result.data().count, countScope: 'query-total', consistency: 'live' };
  }
  const size = limit(options);
  const continuation = uncursor(text(options, 'after'), scope);
  if (continuation !== undefined) {
    if (!Array.isArray(continuation) || continuation.length !== orders.length)
      invalid('Invalid query continuation values.');
    const values = continuation.map((v) => decode(v, db));
    if (!(values.at(-1) instanceof DocumentReference))
      invalid('Query continuation must include document identity.');
    q = q.startAfter(...values);
  }
  // Fetch ordered fields alongside the projection so the cursor never needs a second read of the last document.
  if (select !== undefined) {
    const fields = new Set([...select, ...orders.map((o) => o.field)]);
    // A parent projection already includes its descendants; overlapping masks are rejected by the service.
    const mask = [...fields].filter(
      (name) => ![...fields].some((parent) => parent !== name && name.startsWith(`${parent}.`)),
    );
    q = q.select(...mask.map(fieldPath));
  }
  const snapshot = await q.limit(size + 1).get();
  const docs = snapshot.docs.slice(0, size);
  const last = docs.at(-1);
  const next =
    snapshot.docs.length > size && last
      ? cursor(
          scope,
          orders.map((o) =>
            encode(o.field === '__name__' ? last.ref : fromFirestore(last.get(fieldPath(o.field)))),
          ),
        )
      : null;
  return {
    documents: docs.map((doc) => identity(doc, projected(doc, select))),
    count: docs.length,
    pageInfo: pageInfo(next),
    readTime: snapshot.readTime,
  };
}

/** Native bounded reads and single-commit mutations. The caller adds the target envelope and encodes results. */
export async function runFirestore(
  db: Firestore,
  action: string,
  options: Options,
  target: Target,
): Promise<unknown> {
  let sent = false;
  try {
    if (action === 'collections') return await collections(db, options, target);
    if (action === 'query' || action === 'count') return await query(db, action, options, target);
    if (action === 'get') {
      const snapshot = await db.doc(path(required(options, 'path'), true)).get();
      if (!snapshot.exists)
        throw new CliError('NOT_FOUND', 'The requested Firestore document does not exist.');
      return { ...identity(snapshot), readTime: snapshot.readTime };
    }
    let mutations: Mutation[];
    if (action === 'batch') {
      const data = await input(options);
      if (!Array.isArray(data) || data.length === 0 || data.length > 500)
        invalid('Batch must contain 1..500 operations and is never split.');
      mutations = data.map((item) => {
        const mutation = object(item, 'Batch operation');
        only(mutation, ['op', 'path', 'data', 'precondition'], 'Batch operation');
        if (typeof mutation.op !== 'string') invalid('Batch operation requires an op.');
        return mutation as Mutation;
      });
    } else {
      mutations = [
        {
          op: action,
          path: required(options, 'path'),
          precondition: parsePrecondition(options),
          ...(action !== 'delete' ? { data: await input(options) } : {}),
        },
      ];
    }
    const batch = db.batch();
    const identities = mutations.map((mutation) => addMutation(batch, mutation, db));
    sent = true;
    const response = await (batch as unknown as CommitBatch)._commit({ retryCodes: [] });
    const commitTime = timestamp(response.commitTime);
    const receipts = identities.map((id, i) => ({
      ...id,
      completed: true,
      updateTime: timestamp(response.writeResults?.[i]?.updateTime ?? response.commitTime),
    }));
    return action === 'batch'
      ? { completed: true, atomic: true, count: receipts.length, commitTime, writes: receipts }
      : { ...receipts[0], commitTime };
  } catch (error) {
    throw classify(error, sent);
  }
}
