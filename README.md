# Bridge Master

Declarer-play training in the browser, made for playing on a phone: the 540 deals of Fred Gitelman's **Bridge Master** (as published on Bridge Base Online), against defenders who — like the original — shift their cards to beat any line but the best one.

**Play:** https://dragonkyro.github.io/Bridge-Master/ (add it to your home screen; it works offline).

## Features

- **540 deals** in 5 levels (Beginner → World Class) and their A–D sets, each with the auction, the opening lead and the full commentary.
- **Rigged defence.** Follow the solution and the defenders play BBO's scripted defence. Leave it and they play double dummy — and, while the key part of the hand is still in progress, switch to any of BBO's alternative layouts that fits every card you've seen and beats your line. Only the right line makes. Every deal is tested: the solution always makes.
- **Solution player.** BBO's step-by-step review: the four hands, the cards the commentary is talking about lit up, the trick in the middle, the commentary growing a phrase at a time. Autoplay, step, or scrub.
- **Stars.** Gold for a clean solve, silver if you used undo or had looked at the solution. Saved on the device; sign in with Google to keep phone and computer in step.
- **Offline.** The whole app — every deal and the solver — is cached after the first visit. Progress made offline syncs when you reconnect.
- **The table.** Cards drawn in code (four-colour or red/black), hands that deal in and close up, your card flying from the hand, the defenders' cards flipping in from their seats, the winning card lighting up before the trick sweeps off, a trick meter, synthesized sounds. One-tap play or tap-to-raise, three paces, reduced-motion support.

## How the rigging works

BBO's review of each deal is a narrative: the right line, then "notice that if…" side lines and alternative layouts ("if East had held…"). The build step (`scripts/build-deals.ts`) reconstructs every position of that review, picks the solution (the longest review line that still makes double dummy), and keeps the alternative layouts on which the solution still makes. During play:

- On the solution, defenders play the review's cards.
- Off it, the defenders use **DDS** (Bo Haglund's double-dummy solver, compiled to WebAssembly) and choose the most natural of the best cards.
- If you go off the solution while the critical part of the hand is still being played, the app checks the alternative layouts that fit everything you've seen. If one of them beats your line and your current one doesn't, the defenders "had" that one all along.

## Development

```bash
npm install
npm run dev          # http://localhost:5173/Bridge-Master/
npm run test:run     # unit tests + every deal played with real DDS (~30 s)
npm run build        # type-check, build, service worker → dist/
npm run deals        # rebuild src/data from data/bbo_bridgemaster
```

Stack: TypeScript, React 19, Zustand, Vite, Vitest, `bridge-dds` (DDS in WebAssembly, in a Web Worker), Firebase Auth + Firestore (lazy-loaded), `vite-plugin-pwa`.

Layout: `src/bridge` (cards, PBN, play rules) · `src/dd` (solver + worker) · `src/game` (script tracking, rigging, defence) · `src/data` (generated deal files) · `src/store` (table, progress, prefs) · `src/net` (sign-in and sync) · `src/ui` (pages, table, solution player, card art, styles). See `CLAUDE.md` for the details.

## Deploying

Pushing to `main` runs `.github/workflows/deploy.yml` (tests, build, GitHub Pages). One-time setup:

1. GitHub repo → Settings → Pages → Source: **GitHub Actions**.
2. Firebase console (project `github-games-e7c7d`) → Authentication → Sign-in method → enable **Google**; Authentication → Settings → Authorized domains → add `dragonkyro.github.io`.
3. Firestore rules: `npm run deploy:rules` (already deployed).

## Data

`data/bbo_bridgemaster/` holds the scraped deals (`scripts/scrape_bbo_bridgemaster.py`). `data/themes/` and `bridge_themes.csv` are an earlier set of made-up themed hands, kept for later.

## Credits

Deals, auctions and commentary: Fred Gitelman's Bridge Master, via Bridge Base Online. Double-dummy analysis: DDS by Bo Haglund and Soren Hein, via the `bridge-dds` package (Apache 2.0). Card art adapted from the tractor project.
