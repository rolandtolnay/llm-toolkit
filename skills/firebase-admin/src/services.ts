import { createRequire } from 'node:module';
import { initializeApp, deleteApp, type App } from 'firebase-admin/app';
import { getAuth, type Auth } from 'firebase-admin/auth';
import { Firestore } from 'firebase-admin/firestore';
import { Storage } from '@google-cloud/storage';
import type { Resolved } from './context.js';
import { CliError } from './shared.js';

export class Services {
  app: App;
  private db?: Firestore;
  private authService?: Auth;
  private storageService?: Storage;
  constructor(readonly resolved: Resolved) {
    this.app = initializeApp({
      projectId: resolved.target.project,
      credential: resolved.credential,
      ...(resolved.target.bucket ? { storageBucket: resolved.target.bucket } : {}),
    });
  }
  firestore(): Firestore {
    return (this.db ??= new Firestore({
      projectId: this.resolved.target.project,
      databaseId: this.resolved.target.database,
      auth: this.resolved.googleAuth,
      preferRest: true,
      useBigInt: true,
    }));
  }
  auth(): Auth {
    if (!this.authService) {
      this.authService = getAuth(this.app);
      // Admin Auth has no public retry switch. Pinned compatibility boundary: disable transport
      // replay (including auto-ID create) before any request can be sent.
      const client = (this.authService as any).authRequestHandler?.httpClient;
      if (!client || !('retry' in client))
        throw new CliError(
          'COMPATIBILITY_ERROR',
          'Admin Auth transport changed; refusing requests until the adapter is updated.',
        );
      client.retry = { maxRetries: 0 };
    }
    return this.authService;
  }
  storage(): Storage {
    if (!this.storageService) {
      // Storage 8 uses google-auth-library 9 (plain headers), while Firestore uses 11
      // (Headers objects). Use Storage's own OAuth client with the shared credential.
      const require = createRequire(import.meta.url);
      const storageRequire = createRequire(require.resolve('@google-cloud/storage'));
      const { OAuth2Client } = storageRequire('google-auth-library');
      const client = new OAuth2Client();
      client.refreshHandler = async () => {
        const token = await this.resolved.credential.getAccessToken();
        return { access_token: token.access_token, expiry_date: Date.now() + token.expires_in * 1000 };
      };
      this.storageService = new Storage({
        projectId: this.resolved.target.project,
        authClient: client,
        retryOptions: { autoRetry: false },
      });
    }
    return this.storageService;
  }
  async close(): Promise<void> {
    await this.db?.terminate();
    await deleteApp(this.app);
  }
}
