import type { Bucket, FileMetadata } from '@google-cloud/storage';
import { access } from 'node:fs/promises';
import {
  CliError,
  cursor,
  invalid,
  limit,
  pageInfo,
  required,
  text,
  uncursor,
  type Options,
} from './shared.js';

function metadata(m: FileMetadata) {
  // Do not expose Firebase download tokens or arbitrary custom metadata in routine output.
  return {
    name: m.name ?? null,
    bucket: m.bucket ?? null,
    generation: m.generation ?? null,
    metageneration: m.metageneration ?? null,
    size: m.size ?? null,
    contentType: m.contentType ?? null,
    crc32c: m.crc32c ?? null,
    md5Hash: m.md5Hash ?? null,
    updated: m.updated ?? null,
  };
}
export async function runStorage(
  bucket: Bucket,
  action: string,
  options: Options,
  target: unknown,
): Promise<unknown> {
  if (action === 'list') {
    const size = limit(options);
    const prefix = text(options, 'prefix') ?? '';
    const scope = { target, prefix, size };
    const token = uncursor(text(options, 'after'), scope);
    if (token !== undefined && typeof token !== 'string') invalid('Invalid Storage continuation.');
    const [files, next] = await bucket.getFiles({
      prefix,
      maxResults: size,
      pageToken: token,
      autoPaginate: false,
    });
    return {
      objects: files.map((f) => metadata(f.metadata)),
      count: files.length,
      pageInfo: pageInfo(next?.pageToken ? cursor(scope, next.pageToken) : null),
    };
  }
  const name = required(options, 'object');
  const file = bucket.file(name);
  const generation = text(options, 'if-generation-match');
  if (generation !== undefined && !/^\d+$/.test(generation))
    invalid('--if-generation-match must be a nonnegative decimal generation.');
  switch (action) {
    case 'metadata':
      return { object: metadata((await file.getMetadata())[0]) };
    case 'download': {
      const destination = required(options, 'destination');
      await file.download({ destination });
      return { name, bucket: bucket.name, destination, completed: true };
    }
    case 'upload': {
      const source = required(options, 'source');
      try {
        await access(source);
      } catch {
        throw new CliError('FILE_ERROR', 'Cannot read upload source file.');
      }
      const [uploaded] = await bucket.upload(source, {
        destination: name,
        resumable: false,
        ...(generation !== undefined ? { preconditionOpts: { ifGenerationMatch: generation } } : {}),
      });
      return { object: metadata(uploaded.metadata), completed: true };
    }
    case 'delete':
      await file.delete(generation !== undefined ? { ifGenerationMatch: generation } : {});
      return { name, bucket: bucket.name, completed: true };
    default:
      return invalid('Unknown Storage operation.');
  }
}
