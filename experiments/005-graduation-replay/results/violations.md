## All commits

| Rule | In CLAUDE.md | Commits without / with rule | Commits adding a violation | Net-new per 1k lines | Right way / wrong way (with rule) | Risk ratio (95% CI) |
|---|---|---|---|---|---|---|
| `es2023-array-methods` | 2026-01-24 | 297 / 698 | 0.7% → 0.0% | 0.179 → 0 | 30 / 0 | 0.09 (0.00–1.77) |
| `array-at` | 2026-01-24 | 297 / 698 | 0.0% → 0.0% | 0 → 0 | 6 / 0 | 0.43 (0.01–21.42) |
| `console-direct` | 2026-01-25 | 302 / 693 | 11.6% → 1.3% | 5.31 → 0.482 | 290 / 23 | 0.11 (0.06–0.23) |
| `localstorage-direct` | 2026-01-24 | 296 / 696 | 3.0% → 0.6% | 0.69 → 0.125 | 24 / 6 | 0.19 (0.06–0.61) |
| `supabase-in-ui` | 2026-01-20 | 167 / 736 | 3.6% → 0.3% | 1.428 → 0.039 | – / 2 | 0.08 (0.01–0.37) |
| `tailwind-color-classes` | 2026-02-01 | 480 / 515 | 14.0% → 0.4% | 14.909 → 0.084 | 2709 / 3 | 0.03 (0.01–0.11) |
| `hex-in-components` | 2026-02-07 → removed 2026-03-08 | 626 / 255 | 12.0% → 10.6% | 27.444 → 20.586 | 1555 / 322 | 0.88 (0.58–1.34) |
| `render-error-object` | 2026-01-24 | 273 / 628 | 2.2% → 0.5% | 0.261 → 0.076 | 16 / 3 | 0.22 (0.06–0.86) |
| `single-not-maybesingle` (soft) | 2026-02-01 | 480 / 515 | 2.3% → 0.0% | 0.501 → 0 | 6 / 0 | 0.04 (0.00–0.69) |
| `round-without-numeric` (soft) | 2026-02-01 | 18 / 51 | 50.0% → 23.5% | 11.836 → 6.87 | 31 / 43 | 0.47 (0.24–0.93) |

## Commits co-authored by Claude only

| Rule | In CLAUDE.md | Commits without / with rule | Commits adding a violation | Net-new per 1k lines | Right way / wrong way (with rule) | Risk ratio (95% CI) |
|---|---|---|---|---|---|---|
| `es2023-array-methods` | 2026-01-24 | 258 / 647 | 0.8% → 0.0% | 0.194 → 0 | 27 / 0 | 0.08 (0.00–1.66) |
| `array-at` | 2026-01-24 | 258 / 647 | 0.0% → 0.0% | 0 → 0 | 6 / 0 | 0.40 (0.01–20.07) |
| `console-direct` | 2026-01-25 | 263 / 642 | 12.2% → 0.6% | 4.653 → 0.158 | 265 / 7 | 0.05 (0.02–0.14) |
| `localstorage-direct` | 2026-01-24 | 257 / 645 | 3.1% → 0.3% | 0.682 → 0.09 | 24 / 4 | 0.10 (0.02–0.47) |
| `supabase-in-ui` | 2026-01-20 | 153 / 669 | 3.9% → 0.1% | 1.454 → 0.021 | – / 1 | 0.04 (0.01–0.31) |
| `tailwind-color-classes` | 2026-02-01 | 434 / 471 | 15.2% → 0.4% | 15.728 → 0.093 | 2483 / 3 | 0.03 (0.01–0.11) |
| `hex-in-components` | 2026-02-07 → removed 2026-03-08 | 552 / 254 | 11.8% → 10.6% | 29.305 → 20.587 | 1554 / 322 | 0.90 (0.59–1.38) |
| `render-error-object` | 2026-01-24 | 235 / 588 | 2.5% → 0.2% | 0.276 → 0.027 | 16 / 1 | 0.07 (0.01–0.55) |
| `single-not-maybesingle` (soft) | 2026-02-01 | 434 / 471 | 2.1% → 0.0% | 0.485 → 0 | 6 / 0 | 0.05 (0.00–0.83) |
| `round-without-numeric` (soft) | 2026-02-01 | 18 / 41 | 50.0% → 26.8% | 11.836 → 7.919 | 26 / 40 | 0.54 (0.27–1.06) |

## Share of commits adding a violation, between rule changes

Bold: the rule was in CLAUDE.md for that whole window.

| Rule | start → 01-20 | 01-20 → 01-24 | 01-24 → 01-25 | 01-25 → 02-01 | 02-01 → 02-07 | 02-07 → 03-08 | 03-08 → end |
|---|---|---|---|---|---|---|---|
| `es2023-array-methods` | 0.0% (0/181) | 2.8% (2/72) | **0.0% (0/46)** | **0.0% (0/169)** | **0.0% (0/17)** | **0.0% (0/258)** | **0.0% (0/252)** |
| `array-at` | 0.0% (0/181) | 0.0% (0/72) | **0.0% (0/46)** | **0.0% (0/169)** | **0.0% (0/17)** | **0.0% (0/258)** | **0.0% (0/252)** |
| `console-direct` | 11.1% (20/181) | 11.1% (8/72) | 13.0% (6/46) | **5.9% (10/169)** | **0.0% (0/17)** | **0.0% (0/258)** | **0.0% (0/252)** |
| `localstorage-direct` | 3.9% (7/180) | 2.8% (2/72) | **0.0% (0/46)** | **2.4% (4/167)** | **0.0% (0/17)** | **0.0% (0/258)** | **0.0% (0/252)** |
| `supabase-in-ui` | 3.7% (6/161) | **1.4% (1/71)** | **0.0% (0/38)** | **0.0% (0/144)** | **0.0% (0/11)** | **0.0% (0/240)** | **0.4% (1/238)** |
| `tailwind-color-classes` | 28.7% (52/181) | 8.3% (6/72) | 6.5% (3/46) | 3.5% (6/169) | **0.0% (0/17)** | **0.8% (2/258)** | **0.0% (0/252)** |
| `hex-in-components` | 8.2% (13/158) | 28.6% (20/70) | 8.1% (3/37) | 12.1% (17/141) | 27.3% (3/11) | **10.6% (25/236)** | 9.2% (21/228) |
| `render-error-object` | 2.4% (4/165) | 1.4% (1/71) | **2.7% (1/37)** | **0.0% (0/148)** | **0.0% (0/12)** | **0.4% (1/239)** | **0.9% (2/229)** |
| `single-not-maybesingle` | 3.3% (6/181) | 2.8% (2/72) | 2.2% (1/46) | 1.2% (2/169) | **0.0% (0/17)** | **0.0% (0/258)** | **0.0% (0/252)** |
| `round-without-numeric` | – | – | 16.7% (1/6) | 63.6% (7/11) | **100.0% (1/1)** | **37.5% (6/16)** | **17.1% (6/35)** |

## Skipped commits

- `42e3275`: Squash-import of a 67-commit branch written in a separate repository, so which CLAUDE.md its sessions saw is unknown
- `3095c27`: Consolidates 86 existing SQL files into schema.sql (copies code already in the repo)
- `d3316fc`: Moves existing SQL files into new folders (copies code already in the repo)
- `7eeaf44`: Full schema sync dump for a database switch (copies code already in the repo)
