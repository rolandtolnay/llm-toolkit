import { DocumentReference, FieldValue, GeoPoint, Timestamp, type Firestore } from 'firebase-admin/firestore';
import { CliError, invalid, object } from './shared.js';

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
const own = (value: object, key: string) => Object.prototype.hasOwnProperty.call(value, key);
const plain = (value: object) =>
  Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null;

/**
 * A double whose value is a whole number. The pinned serializer writes every safe integer as int64,
 * so this uses its `_toProto` extension point (honoured by validation, writes, filters and cursors)
 * to keep the double type that Flutter clients depend on.
 */
export class FirestoreDouble {
  readonly _protoValueType = 'ProtoValue';
  constructor(readonly value: number) {}
  _toProto() {
    return { doubleValue: this.value };
  }
}

/** Under `useBigInt` every JS number read from Firestore is a double; tag whole numbers so a write keeps the type. */
export function fromFirestore(value: unknown): unknown {
  if (typeof value === 'number') return Number.isInteger(value) ? new FirestoreDouble(value) : value;
  if (Array.isArray(value)) return value.map(fromFirestore);
  if (value && typeof value === 'object' && plain(value)) {
    return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, fromFirestore(child)]));
  }
  return value;
}

function keys(value: Record<string, unknown>, expected: string[]): void {
  if (Object.keys(value).length !== expected.length || expected.some((key) => !own(value, key))) {
    invalid('Typed Firebase value has missing or unexpected properties.');
  }
}
function number(value: unknown): number {
  if (typeof value !== 'number' || !Number.isFinite(value)) invalid('Expected a finite numeric value.');
  return value;
}
function documentPath(value: unknown): string {
  if (
    typeof value !== 'string' ||
    !value ||
    value.split('/').some((p) => !p) ||
    value.split('/').length % 2 !== 0
  ) {
    invalid('Reference path must be a literal document path.');
  }
  return value;
}

/** Lossless JSON representation of supported Firebase values; never invokes toJSON. */
export function encode(value: unknown): Json {
  const active = new Set<object>();
  const unsupported = (): never => {
    throw new CliError('UNSUPPORTED_VALUE', 'Result contains an unsupported or cyclic value.');
  };
  function visit(v: unknown): Json {
    if (v === null || typeof v === 'string' || typeof v === 'boolean') return v;
    if (typeof v === 'number') return Number.isFinite(v) ? v : unsupported();
    if (typeof v === 'bigint') {
      return v >= BigInt(Number.MIN_SAFE_INTEGER) && v <= BigInt(Number.MAX_SAFE_INTEGER)
        ? Number(v)
        : { $type: 'integer', value: v.toString() };
    }
    if (typeof v !== 'object' || !v || active.has(v)) return unsupported();
    active.add(v);
    try {
      if (v instanceof FirestoreDouble) return { $type: 'double', value: v.value };
      if (v instanceof Timestamp)
        return { $type: 'timestamp', seconds: v.seconds, nanoseconds: v.nanoseconds };
      if (v instanceof Date)
        return Number.isFinite(v.getTime()) ? visit(Timestamp.fromDate(v)) : unsupported();
      if (v instanceof DocumentReference) {
        return {
          $type: 'reference',
          project: (v.firestore as Firestore & { projectId: string }).projectId,
          database: v.firestore.databaseId,
          path: v.path,
        };
      }
      if (v instanceof Uint8Array) return { $type: 'bytes', base64: Buffer.from(v).toString('base64') };
      if (v instanceof GeoPoint) return { $type: 'geopoint', latitude: v.latitude, longitude: v.longitude };
      if (v instanceof FieldValue) {
        // The pinned Firestore SDK exposes no public transform introspection API.
        const transform = v as FieldValue & { methodName?: string; operand?: unknown; elements?: unknown[] };
        switch (transform.methodName) {
          case 'FieldValue.delete':
            return { $type: 'delete' };
          case 'FieldValue.serverTimestamp':
            return { $type: 'serverTimestamp' };
          case 'FieldValue.increment':
            return { $type: 'increment', value: visit(transform.operand) };
          case 'FieldValue.arrayUnion':
            return { $type: 'arrayUnion', values: visit(transform.elements) };
          case 'FieldValue.arrayRemove':
            return { $type: 'arrayRemove', values: visit(transform.elements) };
          default:
            return unsupported();
        }
      }
      if (Array.isArray(v)) return v.map(visit);
      if (!plain(v)) return unsupported();
      const result = Object.fromEntries(Object.entries(v).map(([key, child]) => [key, visit(child)]));
      return own(v, '$type') ? { $type: 'map', value: result } : result;
    } finally {
      active.delete(v);
    }
  }
  return visit(value);
}

/** Decode parsed JSON into values belonging to the explicitly initialized database. SDK constructors validate ranges. */
export function decode(value: unknown, db: Firestore): any {
  function map(v: unknown): Record<string, any> {
    return Object.fromEntries(
      Object.entries(object(v, 'Map value')).map(([key, child]) => [key, visit(child)]),
    );
  }
  function visit(v: unknown): any {
    if (v === null || typeof v === 'string' || typeof v === 'boolean' || typeof v === 'number') return v;
    if (typeof v !== 'object' || !v) invalid('Input contains an unsupported value.');
    if (Array.isArray(v)) return v.map(visit);
    const tagged = v as Record<string, unknown>;
    if (!own(tagged, '$type')) return map(tagged);
    switch (tagged.$type) {
      case 'map':
        keys(tagged, ['$type', 'value']);
        return map(tagged.value);
      case 'timestamp':
        keys(tagged, ['$type', 'seconds', 'nanoseconds']);
        return new Timestamp(tagged.seconds as number, tagged.nanoseconds as number);
      case 'reference': {
        keys(tagged, ['$type', 'project', 'database', 'path']);
        if (
          tagged.project !== (db as Firestore & { projectId: string }).projectId ||
          tagged.database !== db.databaseId
        ) {
          invalid(
            'Reference project/database must match the resolved target; cross-database references require raw JavaScript.',
          );
        }
        return db.doc(documentPath(tagged.path));
      }
      case 'bytes': {
        keys(tagged, ['$type', 'base64']);
        const bytes = typeof tagged.base64 === 'string' ? Buffer.from(tagged.base64, 'base64') : undefined;
        if (!bytes || bytes.toString('base64') !== tagged.base64) invalid('Bytes require canonical base64.');
        return bytes;
      }
      case 'geopoint':
        keys(tagged, ['$type', 'latitude', 'longitude']);
        return new GeoPoint(tagged.latitude as number, tagged.longitude as number);
      case 'double':
        keys(tagged, ['$type', 'value']);
        return new FirestoreDouble(number(tagged.value));
      case 'integer': {
        keys(tagged, ['$type', 'value']);
        if (typeof tagged.value !== 'string' || !/^-?(0|[1-9][0-9]*)$/.test(tagged.value))
          invalid('Integer requires a decimal string.');
        const integer = BigInt(tagged.value);
        if (integer < -9223372036854775808n || integer > 9223372036854775807n)
          invalid('Integer is outside the signed int64 range.');
        return integer;
      }
      case 'delete':
        keys(tagged, ['$type']);
        return FieldValue.delete();
      case 'serverTimestamp':
        keys(tagged, ['$type']);
        return FieldValue.serverTimestamp();
      case 'increment': {
        keys(tagged, ['$type', 'value']);
        const operand = visit(tagged.value);
        if (typeof operand !== 'number') invalid('Increment requires a numeric value.');
        return FieldValue.increment(operand);
      }
      case 'arrayUnion':
      case 'arrayRemove': {
        keys(tagged, ['$type', 'values']);
        if (!Array.isArray(tagged.values) || tagged.values.length === 0)
          invalid('Array transform requires a nonempty values array.');
        const values = visit(tagged.values);
        return tagged.$type === 'arrayUnion'
          ? FieldValue.arrayUnion(...values)
          : FieldValue.arrayRemove(...values);
      }
      default:
        return invalid('Unknown Firebase value tag. Escape ordinary maps containing $type with the map tag.');
    }
  }
  return visit(value);
}
