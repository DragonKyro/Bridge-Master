// Settings and account, in one modal.

import { signIn, signOut, useCloud } from '@/net/cloud';
import { usePrefs, type Speed } from '@/store/prefsStore';
import { Icon } from './Icon';

function Toggle({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return <button type="button" className="toggle" role="switch" aria-checked={on} aria-label={label} onClick={() => onChange(!on)} />;
}

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const prefs = usePrefs();
  return (
    <div className="backdrop" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal panel" role="dialog" aria-label="Settings">
        <h2>
          Settings
          <button type="button" className="icon-btn modal-close" onClick={onClose} aria-label="Close">
            <Icon name="close" />
          </button>
        </h2>
        <div className="setting-row">
          <span className="setting-label">
            Four-colour suits
            <span className="setting-hint">♦ orange and ♣ green, as at most clubs</span>
          </span>
          <Toggle on={prefs.fourColor} onChange={(v) => prefs.set({ fourColor: v })} label="Four-colour suits" />
        </div>
        <div className="setting-row">
          <span className="setting-label">
            One-tap play
            <span className="setting-hint">Off: tap a card to raise it, tap again to play</span>
          </span>
          <Toggle on={prefs.oneTap} onChange={(v) => prefs.set({ oneTap: v })} label="One-tap play" />
        </div>
        <div className="setting-row">
          <span className="setting-label">Sounds</span>
          <Toggle on={prefs.sound} onChange={(v) => prefs.set({ sound: v })} label="Sounds" />
        </div>
        <div className="setting-row">
          <span className="setting-label">Pace</span>
          <span className="segmented">
            {(['relaxed', 'normal', 'fast'] as Speed[]).map((s) => (
              <button key={s} type="button" aria-pressed={prefs.speed === s} onClick={() => prefs.set({ speed: s })}>
                {s[0]!.toUpperCase() + s.slice(1)}
              </button>
            ))}
          </span>
        </div>
        <Account />
      </div>
    </div>
  );
}

export function Account() {
  const { status, user, pending, syncing, online, error } = useCloud();
  return (
    <div className="account">
      <div className="account-h">Progress sync</div>
      {status === 'signedIn' && user ? (
        <div className="account-row">
          {user.photo ? <img className="account-photo" src={user.photo} alt="" referrerPolicy="no-referrer" /> : <Icon name="user" />}
          <span className="account-who">
            {user.name}
            <span className="setting-hint">
              {!online ? `Offline — ${pending} to sync when you reconnect` : syncing ? 'Syncing…' : pending > 0 ? `${pending} waiting to sync` : 'Stars synced across your devices'}
            </span>
          </span>
          <button type="button" className="btn btn-ghost" onClick={() => void signOut()}>
            Sign out
          </button>
        </div>
      ) : (
        <div className="account-row">
          <Icon name={online ? 'cloud' : 'cloudOff'} />
          <span className="account-who">
            Stars are saved on this device.
            <span className="setting-hint">Sign in to keep them in step between your phone and computer.</span>
          </span>
          <button type="button" className="btn" disabled={status === 'loading' || !online} onClick={() => void signIn()}>
            {status === 'loading' ? 'Signing in…' : 'Sign in with Google'}
          </button>
        </div>
      )}
      {error && <p className="account-error">{error}</p>}
    </div>
  );
}
