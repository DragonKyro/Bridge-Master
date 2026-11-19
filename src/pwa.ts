// Offline: the service worker (vite-plugin-pwa / Workbox) precaches the whole
// app — every deal set, the DDS solver, fonts — so after the first visit the
// app opens and plays with no connection. New builds install in the
// background and take over on the next launch.

import { registerSW } from 'virtual:pwa-register';

export function registerOffline(): void {
  if (import.meta.env.DEV || !('serviceWorker' in navigator)) return;
  registerSW({ immediate: true });
}
