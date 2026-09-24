# Functionality Audit — compound-knowledge

**Date:** 2026-09-24 · **Scope:** everything in the repo, weighted toward what actually runs · **Code changed:** none (report only)

Most of this repo is theory (Markdown). The one piece that executes is the **WGH Dispatch dashboard** (`dashboard/index.html`, copied byte-for-byte to `docs/index.html` and served by GitHub Pages). That's where most of the findings below are.

Severity scale: **P0** feature unusable · **P1** major feature broken or gives wrong results · **P2** partial or edge-case breakage · **P3** minor.
Evidence tags: **VERIFIED** = observed by running it (headless Chromium with a stubbed `supabase-js`) · **STATIC** = code reading · **DOCS** = confirmed against Supabase's own documentation · **LIVE** = read-only check of the deployed Supabase/GitHub state.

---

## TL;DR

1. **The live dashboard can't work right now.** GitHub Pages serves it (last build 2026-02-28 succeeded), but the Supabase project it talks to (`Agent-phone`, `yqegairtdxjxyquprppr`) is **paused/INACTIVE**. Visitors get a page stuck on "CONNECTING".
2. **Even when it's connected, the live feed hides new messages.** Once there are more messages than fit on screen, the view is pinned to the **oldest** messages and each new live message is inserted off-screen above it (CK-1).
3. **The documented deploy path can't work.** The README says to host the page in a public Supabase Storage bucket, but Supabase serves HTML from Storage as `text/plain`, so visitors would see source code (CK-2). The later `docs/` + GitHub Pages copy works around this, but the README was never updated.
4. The status pill never changes colour: "LIVE" and "OFFLINE" are both drawn in the blue "connecting" style (CK-3).
5. The theory docs present the graduation pipeline as a proven pattern, but this repo's own Experiment 003 measured it at **0% graduation**, with an end-to-end run that "never completes" (CK-11).

---

## Live deployment status (LIVE)

| Thing | State | Consequence |
|---|---|---|
| GitHub Pages (`main` → `/docs`) | Enabled, built successfully 2026-02-28 (run #1, commit `8a64384`). The repo is **public**. | The dashboard is publicly reachable, and the publishable Supabase key in it is public. |
| Supabase project `Agent-phone` (`yqegairtdxjxyquprppr`) | **INACTIVE (paused)**, with no edge functions | History query and realtime subscription both fail; the page never leaves "CONNECTING". |
| `phone_messages` schema, RLS, realtime publication | **Not verifiable.** The DB is paused, and the schema isn't in this repo. | The dashboard depends on a table defined elsewhere. If `phone_messages` isn't in the `supabase_realtime` publication, or RLS blocks `anon` SELECT, the feed stays empty with no visible error (see CK-7). |

---

## What works (VERIFIED)

- The history query is shaped correctly: `phone_messages` → `select id, created_at, sender, content` → `channel = 'room:<id>'` → newest 200.
- The realtime subscription is shaped correctly: `postgres_changes` INSERT on `public.phone_messages` with `filter: channel=eq.room:<id>`.
- Sender and content are HTML-escaped before rendering. Escaping covers all interpolated text, so there's no injection from message content.
- The room-entry form writes `?room=` into the URL without a reload, then connects.
- Message and agent counters are correct (200 history + 1 live → `201` / `4`). Per-sender colours are stable.

---

## Findings

### CK-1 · P1 · Live feed shows the oldest messages; new messages arrive off-screen — VERIFIED
- **Evidence:** `#feed-container` uses `flex-direction: column-reverse` (`dashboard/index.html:182`, commented "newest at top without JS reorder"). The JS *also* prepends each new row to the top of `#feed` (`:606-611`). Together these reverse the order twice. A `column-reverse` scroll container starts scrolled to the **bottom** of its content, and the bottom of `#feed` holds the oldest rows.
- **Observed:** after 200 history rows loaded in a 1280×800 viewport, the visible rows were `#0 … #11` (the oldest). A live insert (`LIVE MESSAGE 1`) landed at the top of `#feed`, **outside the viewport**. `scrollTop` stayed at 0 and nothing new was visible.
- **Fix:** keep one ordering mechanism. Either make `#feed-container` a normal block container (`flex-direction: column`, or no flex) and keep prepending, or keep `column-reverse` and **append** rows instead. *Checked in a patched copy: switching `:182` to `flex-direction: column` puts `#199` on top, and a live insert shows up at the top of the viewport.*

### CK-2 · P1 · README deploy instructions (Supabase Storage) serve the page as plain text — DOCS
- **Evidence:** `dashboard/README.md:18-27` says to upload `index.html` to a public Storage bucket and open its public URL. Supabase's Storage quickstart says: "For security, HTML files are returned as plain text." Visitors would see source code, not a dashboard.
- **Note:** commit `8a64384` ("Add docs/ for GitHub Pages deployment") is the real deployment, but the README still documents only Storage and never mentions Pages or `docs/`.
- **Fix:** replace the Storage section with the Pages setup (or any static host). Mention that `docs/index.html` is what Pages serves.

### CK-3 · P2 · Status pill is always blue ("LIVE" and "OFFLINE" look the same) — VERIFIED
- **Evidence:** `setStatus()` (`:553-557`) sets `className = 'connecting'`, then *adds* the real state, which yields `connecting connected` or `connecting disconnected`. All three rules have equal specificity, and `#status-pill.connecting` (`:124`) comes after `.connected` (`:112`) and `.disconnected` (`:118`), so it always wins.
- **Observed:** computed colour was `rgb(79,195,247)` (accent blue) for LIVE, OFFLINE and "no room". Only the text changes. For a monitoring page, the colour is the main health signal.
- **Fix:** `$statusPill.className = state;` *Checked in a patched copy: LIVE turns green `rgb(76,175,130)` and OFFLINE turns red `rgb(240,80,110)`.*

### CK-4 · P2 · "Room ID is the access model" isn't access control — STATIC (RLS unverifiable while paused)
- **Evidence:** `dashboard/README.md:16`. The publishable key is embedded in a public repo and on a public Pages site (`index.html:493-494`). For `postgres_changes` to reach an anonymous viewer, RLS must allow `anon` SELECT on `phone_messages`. A policy can't see which room the page has open, so any key holder can almost certainly run `GET /rest/v1/phone_messages?select=*` and read **every room**. Room IDs are only obscurity.
- **Fix:** if the messages are sensitive, gate them with a signed per-room token (an Edge Function that checks it, or a Realtime Broadcast channel with authorization), or make the policy require a secret room key sent as a header/claim.

### CK-5 · P2 · Messages posted while history is loading are lost — STATIC
- **Evidence:** `boot()` subscribes only after `loadHistory()` resolves (`:704-706`). Rows inserted between the history SELECT and the channel reaching `SUBSCRIBED` are in neither result set and never appear.
- **Fix:** subscribe first and buffer events, then load history, then merge and de-duplicate by `id`.

### CK-6 · P3 · "Duration" ignores history and uses the client clock — VERIFIED
- **Evidence:** `firstMsgAt` is set only for live messages (`:598`). With 200 history rows it shows `—` until the first live message, then `0s`. It subtracts the server's `created_at` from the browser's `Date.now()`, so clock skew can produce negative values like `-1s` (`formatDuration`, `:543-551`).
- **Fix:** seed `firstMsgAt` from the oldest loaded row. Clamp at 0.

### CK-7 · P3 · CDN failure or empty/failed history leaves the user staring at a spinner — VERIFIED / STATIC
- If `cdn.jsdelivr.net` is blocked, `supabase` is undefined, `boot()` throws `ReferenceError`, and the pill stays on "CONNECTING" with no message (VERIFIED).
- A history error is only `console.error`'d (`:627-630`). An RLS denial or missing table shows as a normal-looking empty feed (STATIC).
- `@supabase/supabase-js@2` is not pinned to a minor version (`:7`).
- **Fix:** show an error state in the feed; pin the library version.

### CK-8 · P3 · "No room" screen shows two contradictory states — VERIFIED
With no `?room=`, the room-entry form **and** "Waiting for agent activity..." are both displayed (`:461-476`, `:729`). Hide `#feed-container` until a room is set.

### CK-9 · P3 · Long-running sessions degrade — STATIC / DOCS
- `messages[]` and the DOM grow without bound (`:599`, `:604-611`). Cap at N rows.
- Supabase docs note that public (publishable-key) Realtime connections are limited to 24 hours unless upgraded with user auth. A wall-mounted dashboard will silently go stale, and because of CK-3 the pill won't turn red.

### CK-10 · P3 · Two copies of the app; one README command doesn't work — STATIC
- `docs/index.html` is a manual copy of `dashboard/index.html` (identical today). Every fix above has to be made twice, or Pages will drift. Consider making `docs/` the only copy, or adding a copy step.
- `open dashboard/index.html?room=test` (`dashboard/README.md:38`) makes macOS `open` look for a file literally named `index.html?room=test`. Use the `npx serve` route that follows it.

### CK-11 · P2 (doc truth) · "Proven" pattern contradicted by the repo's own measurement — STATIC
- The README describes `patterns/` as "Confirmed patterns — things we've proven work". `patterns/graduation-pipeline.md` presents observations → KB → locked rules as the lifecycle.
- `experiments/003-pipeline-lifecycle-trace.md` §4-5 in the same repo reports: observations → KB graduation **0%**; "The full pipeline has never produced an end-to-end graduation"; 2 CRITICAL breaks (observations.md is a dead end; context-loader.sh doesn't inject KB files). The only path that works end-to-end is the Raw Log → `rules.jsonl` bypass.
- **Fix:** add a "Status (per Exp. 003)" note to the pattern doc, or move it out of `patterns/` until the breaks are fixed.

### CK-12 · P3 · Experiments can't be reproduced from this repo — STATIC
- Experiments 002-004 measure files and scripts that live outside the repo (`~/.claude/knowledge_base/`, `CODEX.md`, `rules.jsonl`, `insight-detect.sh`, `auto-graduate.sh`, `sleep-agent.sh`, `inject-rules.sh`, `context-loader.sh`).
- Token counts are `chars / 4` estimates, not tokenizer counts. Experiment 001 itself notes that symbols tokenize unevenly.
- Nothing here can be re-run to check the numbers.

### CK-13 · P3 · README structure is out of date — STATIC
`README.md` "Structure" lists only foundations/patterns/experiments/models. It omits `dashboard/` (the only executable code) and `docs/` (the live public site).

---

## Suggested order of work

1. Decide whether the dashboard should be live. If yes, restore the `Agent-phone` Supabase project, then check that `phone_messages` is in the `supabase_realtime` publication and what its RLS allows.
2. Fix CK-1 (scroll/order) and CK-3 (pill colour). Both are one-line changes; make them in both copies (CK-10).
3. Rewrite the README deploy section for Pages (CK-2). Decide whether room-ID-as-secret is acceptable (CK-4).
4. Subscribe-then-load (CK-5), plus the P3 polish.

## How this was checked

- The dashboard was driven in headless Chromium with the jsDelivr `supabase-js` request replaced by a stub. The stub returned 200 history rows and could push realtime INSERTs and channel status changes on demand. Assertions used computed styles and element bounding boxes against the scroll container.
- Deployed state came from the Supabase management API (project status, edge-function list; read-only) and the GitHub API (repo visibility, Pages flag, Pages build run).
- The Supabase platform behaviours cited (HTML from Storage served as plain text; 24h public Realtime limit) are quoted from Supabase's documentation.
