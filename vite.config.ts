import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  // GitHub Pages serves the site from /Bridge-Master/.
  base: '/Bridge-Master/',
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: false,
      includeAssets: ['favicon.svg', 'apple-touch-icon.png'],
      manifest: {
        name: 'Bridge Master',
        short_name: 'Bridge Master',
        description: 'Declarer-play training: 540 Bridge Master deals against defenders who shift their cards to beat any line but the best.',
        theme_color: '#0b1712',
        background_color: '#08110e',
        display: 'standalone',
        orientation: 'any',
        start_url: '.',
        scope: '.',
        icons: [
          { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Everything, so the app plays offline: every deal set, the solver worker (≈0.7 MB with DDS inlined), fonts.
        globPatterns: ['**/*.{js,css,html,svg,png,woff2,webmanifest}'],
        maximumFileSizeToCacheInBytes: 6 * 1024 * 1024,
        navigateFallback: 'index.html',
        cleanupOutdatedCaches: true,
      },
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  worker: { format: 'es' },
  test: {
    environment: 'node',
    globals: true,
    // bridge-dds imports "./lib/dds" without an extension, which Node's own ESM loader refuses.
    server: { deps: { inline: ['bridge-dds'] } },
    testTimeout: 600_000,
  },
});
