// Cloud progress: Google sign-in and a Firestore document per user, so stars
// follow you between phone and computer. Firebase is loaded lazily (only once
// you sign in, or on start-up if you were signed in before).
//
// Offline first: progress is always saved locally (progressStore). Each change
// is queued in localStorage and pushed when signed in and online — on
// sign-in, on the browser's `online` event, on start-up, after each change.
// Pulls merge remote progress in (the better star wins).

import { create } from 'zustand';
import type { User } from 'firebase/auth';
import { useProgress, type ProgressMap } from '@/store/progressStore';
import { FIREBASE_CONFIG, PROGRESS_COLLECTION } from './firebaseConfig';

export type CloudStatus = 'off' | 'loading' | 'signedOut' | 'signedIn';

interface CloudState {
  status: CloudStatus;
  user: { name: string; email: string; photo: string | null } | null;
  /** Deals changed locally and not yet in the cloud. */
  pending: number;
  syncing: boolean;
  online: boolean;
  error: string | null;
}

export const useCloud = create<CloudState>(() => ({
  status: 'off',
  user: null,
  pending: readPending().length,
  syncing: false,
  online: typeof navigator === 'undefined' ? true : navigator.onLine,
  error: null,
}));

const SIGNED_IN_KEY = 'bridgeMaster.signedIn';
const PENDING_KEY = 'bridgeMaster.pending';

function readPending(): string[] {
  try {
    return JSON.parse(localStorage.getItem(PENDING_KEY) ?? '[]') as string[];
  } catch {
    return [];
  }
}

function writePending(ids: string[]): void {
  try {
    localStorage.setItem(PENDING_KEY, JSON.stringify(ids));
  } catch {
    /* private mode */
  }
  useCloud.setState({ pending: ids.length });
}

type Fb = {
  auth: import('firebase/auth').Auth;
  db: import('firebase/firestore').Firestore;
  authMod: typeof import('firebase/auth');
  fsMod: typeof import('firebase/firestore');
};

let fb: Promise<Fb> | null = null;
let uid: string | null = null;

function loadFirebase(): Promise<Fb> {
  if (!fb) {
    fb = (async () => {
      const [{ initializeApp, getApps }, authMod, fsMod] = await Promise.all([import('firebase/app'), import('firebase/auth'), import('firebase/firestore')]);
      const app = getApps()[0] ?? initializeApp(FIREBASE_CONFIG);
      const auth = authMod.getAuth(app);
      const db = fsMod.getFirestore(app);
      authMod.onAuthStateChanged(auth, (user) => void onUser(user));
      return { auth, db, authMod, fsMod };
    })();
    fb.catch(() => {
      fb = null;
    });
  }
  return fb;
}

async function onUser(user: User | null): Promise<void> {
  uid = user?.uid ?? null;
  if (!user) {
    useCloud.setState({ status: 'signedOut', user: null });
    try {
      localStorage.removeItem(SIGNED_IN_KEY);
    } catch {
      /* ignore */
    }
    return;
  }
  try {
    localStorage.setItem(SIGNED_IN_KEY, '1');
  } catch {
    /* ignore */
  }
  useCloud.setState({ status: 'signedIn', user: { name: user.displayName ?? 'Signed in', email: user.email ?? '', photo: user.photoURL }, error: null });
  await sync(true);
}

/** Pull the cloud copy into local progress, then push what the cloud lacks (all of it after sign-in, else the queue). */
async function sync(full: boolean): Promise<void> {
  if (!uid || !navigator.onLine || useCloud.getState().syncing) return;
  useCloud.setState({ syncing: true });
  try {
    const { db, fsMod } = await loadFirebase();
    const ref = fsMod.doc(db, PROGRESS_COLLECTION, uid);
    if (full) {
      const snap = await fsMod.getDoc(ref);
      const remote = (snap.data()?.deals ?? {}) as ProgressMap;
      useProgress.getState().absorb(remote);
    }
    const ids = full ? Object.keys(useProgress.getState().deals) : readPending();
    if (ids.length > 0) {
      const all = useProgress.getState().deals;
      const deals: ProgressMap = {};
      for (const id of ids) if (all[id]) deals[id] = all[id]!;
      await fsMod.setDoc(ref, { deals, updated: fsMod.serverTimestamp() }, { merge: true });
    }
    const sent = new Set(ids);
    writePending(readPending().filter((id) => !sent.has(id)));
    useCloud.setState({ error: null });
  } catch (e) {
    useCloud.setState({ error: (e as Error).message });
  } finally {
    useCloud.setState({ syncing: false });
  }
}

/** Start-up: hook progress changes to the queue, restore a previous sign-in, sync on reconnect. */
export function initCloud(): void {
  useProgress.setState({
    onChange: (id) => {
      const ids = readPending();
      if (!ids.includes(id)) writePending([...ids, id]);
      void sync(false);
    },
  });
  window.addEventListener('online', () => {
    useCloud.setState({ online: true });
    void sync(true);
  });
  window.addEventListener('offline', () => useCloud.setState({ online: false }));
  let wasSignedIn = false;
  try {
    wasSignedIn = localStorage.getItem(SIGNED_IN_KEY) === '1';
  } catch {
    /* ignore */
  }
  if (wasSignedIn) {
    useCloud.setState({ status: 'loading' });
    loadFirebase().catch(() => useCloud.setState({ status: 'signedOut' }));
  } else {
    useCloud.setState({ status: 'signedOut' });
  }
}

export async function signIn(): Promise<void> {
  useCloud.setState({ status: 'loading', error: null });
  try {
    const { auth, authMod } = await loadFirebase();
    await authMod.signInWithPopup(auth, new authMod.GoogleAuthProvider());
  } catch (e) {
    const code = (e as { code?: string }).code ?? '';
    useCloud.setState({ status: uid ? 'signedIn' : 'signedOut', error: code === 'auth/popup-closed-by-user' ? null : friendly(code, (e as Error).message) });
  }
}

export async function signOut(): Promise<void> {
  const { auth, authMod } = await loadFirebase();
  await authMod.signOut(auth);
}

function friendly(code: string, message: string): string {
  if (code === 'auth/network-request-failed') return 'You seem to be offline — sign in once you are connected.';
  if (code === 'auth/unauthorized-domain') return 'This site is not yet authorised for sign-in in the Firebase console.';
  if (code === 'auth/operation-not-allowed') return 'Google sign-in is not enabled for this Firebase project yet.';
  if (code === 'auth/popup-blocked') return 'The sign-in window was blocked — allow pop-ups and try again.';
  return message;
}
