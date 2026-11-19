# CLAUDE.md

Context for Claude working in this repo.

## What this is

Bridge Master as a static web app for GitHub Pages (`https://dragonkyro.github.io/Bridge-Master/`), built for playing on a phone. The 540 deals of BBO's Bridge Master (Fred Gitelman), scraped into `data/bbo_bridgemaster/`, each with auction, opening lead, commentary and BBO's review. You declare as South; the defenders are rigged so only the solution's line makes. Stars track solved deals (gold: clean, silver: with undo or after viewing the solution), saved locally and synced through Firestore when signed in with Google. Works offline (PWA). Single player — no rooms, no multiplayer.

The made-up themed hands (`data/themes/`, `bridge_themes.csv`) are on the back burner: kept, not used by the app. The old Python/arcade app was removed (it's in git history before the web rewrite).

## Tech stack

TypeScript, Vite 6, React 19, Zustand, Vitest. DDS (Bo Haglund's double-dummy solver) as WebAssembly from the `bridge-dds` npm package, run in a Web Worker. Firebase (Auth with Google + Firestore), lazy-loaded. `vite-plugin-pwa` (Workbox) for offline. Card art is drawn in code (`src/ui/cards/cardArt.ts`, adapted from `../tractor`); no image assets besides the app icons. Fonts self-hosted via @fontsource (Inter, Playfair Display).

## Commands

- `npm run dev` · `npm run build` (tsc + vite build + service worker) · `npm run preview`
- `npm run test:run` — all tests, including `src/game/simulate.test.ts`, which plays every deal with real DDS (~30 s): the solution must make on all 540 with no layout switch.
- `npx tsc --noEmit -p .`
- `npm run deals` — rebuild `src/data/sets/*.json` + `src/data/catalog.json` from `data/bbo_bridgemaster/` (~15 s). The generated files are committed (CI doesn't run the pipeline). Re-run the simulation test after changing it.
- `npm run fix-lock` — **run after any `npm install` that changes package-lock.json.** This machine installs through a corporate Artifactory mirror (`NPM_CONFIG_REGISTRY`), which writes mirror URLs into the lockfile; GitHub Actions can't reach them. The script points every `resolved` URL back at registry.npmjs.org (integrity hashes stay valid). The lockfile must contain no `drwholdings` URLs.
- `npm run deploy:rules` — deploy `firestore.rules`. Confirm with the user first (shared project).
- `python scripts/make-icons.py` — redraw `public/` icons (needs Pillow).
- `scripts/scrape_bbo_bridgemaster.py` — the original scraper (Python, websocket + a browser); only needed to re-scrape.

## Architecture

Import directions: `ui → store → game → dd/bridge/data`; `net` is used by `store`-level code and the UI only. Path alias `@/` → `src/`.

- **`src/bridge/`** — pure bridge: `cards.ts` (card = suit + rank, `'SA'`, `'HT'`; seats N E S W clockwise; strain `S H D C N`), `deal.ts` (layouts, PBN parse/write — DDS wants PBN from North; the data's PBN starts at South), `play.ts` (`replay` with legality, `trickWinner`, `legalPlays`, `equivalent`, `playsFromCards`).
- **`src/dd/`** — `solver.ts` (`DdSolver` over bridge-dds: `scores` for every legal card, `declarerMax`, `canMake`), `worker.ts` (the solver thread), `client.ts` (`ddApi`: promise RPC to the worker; `warmUpSolver()`).
- **`src/game/`** — the rules of the trainer, pure except via a `DdApi`: `hand.ts` (`HandState`: plays, the defenders' current layout, script tracking, `claimFrom`), `engine.ts` (`declarerPlays` with the rigging check, `defenderCard`, `claimStepCard`; `localApi` wraps a `DdSolver` for tests/the worker), `rig.ts` (`findPunisher`), `defence.ts` (`naturalCard`: which of the DD-best cards a person would play), `claim.ts` (`canClaim`, `claimPlay`).
- **`src/data/`** — `types.ts` (the `Deal` format), `load.ts` (catalog bundled; sets lazy via `import.meta.glob`), generated `catalog.json` + `sets/L<level><set>.json`.
- **`src/store/`** — `playStore` (the table: open / begin / play / undo / restart / claim / skipClaim; paces the defenders; settles the attempt as soon as the contract is made or beaten; a `session` counter stops stale async work), `progressStore` (stars in localStorage, `mergeDeal` / `mergeProgress`), `prefsStore` (four-colour, one-tap, sounds, pace).
- **`src/net/`** — `firebaseConfig.ts` (the "Bridge Master" web app in `github-games-e7c7d`), `cloud.ts` (lazy Firebase; Google sign-in by popup; offline queue of changed deal ids in localStorage, pushed on sign-in / `online` / each change; full pull + merge on sign-in and reconnect).
- **`src/ui/`** — `App.tsx` + `router.ts` (hash routes `#/`, `#/level/N`, `#/deal/1A-7`, `#/deal/1A-7/solution`), `pages/` (Home, LevelPage), `table/` (TablePage, HandFan, Trick + DefenderSeat + compass, Auction, History (trick list + auction: side panel / sheet), Result, `flight.ts`), `solution/SolutionPlayer.tsx` (BBO's review as a step player), `shared/` (Icon, Stars, text helpers for suits/calls/contracts, HandDiagram, Settings + Account), `cards/` (cardArt, CardView), `sounds.ts` (Web Audio), `styles/` (theme, pages, table, solution CSS).
- **`src/pwa.ts`** — registers the service worker (production only).

## The rigging (load-bearing)

BBO Bridge Master "cheats": the defenders' cards change to beat any line but the best. Here:

1. **Data** (`scripts/build-deals.ts` + `scripts/lib/raw.ts`). BBO's review is a narrative with rewinds ("Notice that if…") and alternative layouts ("if East had…"). `reconstruct` rebuilds the play line and full layout at every review step (steps that change North/South or can't be explained are `foreign`). The **solution** is the longest review line (a leaf before a rewind, or the last) after which declarer can still make double dummy on the layout shown; that layout is the one dealt. **Alternatives** (`deal.alts`) are the review's other layouts with the same N/S on which the solution still makes at every declarer step where the dealt layout does (the fairness filter). Deals with no making line (24) get no script and no alternatives (pure DD defence on a review layout that makes); `repair()` exists for layouts that don't make at all (none currently).
2. **Play** (`src/game/hand.ts`, `engine.ts`). While declarer follows the script the defenders play the script's cards — BBO's realistic defence; some solutions rely on it (`deal.scriptedDefence`, 29 deals). An equivalent card (nothing between them outside that hand) stays on the script, swapping the two in the rest of it. Any other departure leaves the script for good (unless the exact scripted position recurs, on the dealt layout): defenders then play double dummy (`naturalCard` among the best), and **only while the hand is still within the script's length** a declarer card triggers `findPunisher`: if declarer can still make on the current layout but some alternative that fits every card seen beats them, the layout switches. After the script's span the layout is frozen — switching later could punish a correct guess the commentary resolves by inference.
3. **Invariant, tested**: following the solution makes on every deal with zero switches (`simulate.test.ts`). Changing the pipeline, `hand.ts` script tracking, or the defence must keep that test green.

An attempt ends as soon as the contract is made or beaten.

## Claims (`src/game/claim.ts`)

A claim plays the rest out fast and counts as made, so it must never be wrong and never skip the lesson:

- **Offered only** past the script's length (`plays.length >= script.length`), with declarer's side on lead.
- **Sound against any defenders**: the check sees North's and South's cards and the *set* of unseen cards, never the E/W split. A trick is sure when declarer's side plays a card beating every unseen card of the suit that could still be out (after r rounds of a suit at most unseen − r remain, and the defenders may have kept the highest). While a defender could still hold a trump only trump leads count; side winners and ruffs count once the trumps are surely gone.
- **Obvious**: *every* order of sure tricks must reach the tricks needed, with partner following a fixed policy (low on a winning lead, cheapest winner on a low lead, a non-winner discard). If it takes unblocking or the right entry order, there's no claim. Out of the search budget: no claim.
- Played out by `claimPlay` (the same model, from the claim's start) and the usual defence; `claim.test.ts` checks every claim offered along the solution and along random lines, against the dealt cards and reshuffled unseen cards with double-dummy defenders. Changing the model must keep it green.

The table also shows the bidding and the trick history at all times: a side panel at ≥ 1180 px (`HistoryPanel`), the History sheet (Tricks / Auction tabs) on phones.

## Firebase (shared project)

Project `github-games-e7c7d` (shared with tractor, catan, social-deduction, …; those use only the Realtime Database). Bridge Master uses **Firestore** `(default)` (nam5) and Auth:

- `firestore.rules` is the **whole project's** Firestore rule set (Bridge Master was the first Firestore user). It allows only `bridgeMaster/{uid}` read/write by that uid. Another app adding Firestore must merge into this file. Deploy with `npm run deploy:rules` (`firebase.json` here only configures Firestore, so the RTDB rules are untouched).
- Document: `bridgeMaster/{uid}` = `{ deals: { "1A-7": { b: 1|2, t: tries, at: ms } }, updated }`, written with `setDoc(..., { merge: true })`.
- Google sign-in must be enabled in the console (Authentication → Sign-in method) and `dragonkyro.github.io` listed under Authorized domains.

## Conventions

- Arcade-era conventions are gone; South is always declarer, West always leads.
- State is plain JSON. `HandState` is immutable (functions return new objects).
- Every animation has a `prefers-reduced-motion` fallback (`theme.css` bottom).
- Suit colours: CSS vars `--suit-S/H/D/C` on the dark UI; the cards use `SUIT_INK`. Four-colour default (♦ orange, ♣ green); `.suits-two` switches to red/black.
- Fanned cards show ~37% of their width; card-width vars in `table.css` are sized so 13 fit with the index visible.
- Don't commit or push unless asked; pushing `main` deploys (`.github/workflows/deploy.yml`: tests, build, Pages).
