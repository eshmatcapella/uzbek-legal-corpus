# Daily review log

Purpose: a standing, self-directed R&D cadence for this project. Each entry is
one day's session. The brief is deliberately open — invent the approach, don't
just run a checklist. Multi-day threads are normal and expected; a thread stays
"active" until it resolves, not until a calendar day ends.

How to use this file each session:
1. Read "Active threads" below. Continue one if it's mid-flight.
2. Otherwise pull the next-highest-value item from "Backlog" (rotate across
   the three focus areas rather than draining one), or invent a new angle the
   backlog hasn't captured yet — the backlog is a floor, not a ceiling.
3. Do real work: write code, run it against corpus.duckdb, measure the result.
   A day that ends in "I looked into X" without a number, a commit, or a
   concrete artifact is a day that didn't happen.
4. Run `python verify_transfer.py` before closing out — it must stay green.
5. Append a dated entry to "Log" (below Active threads), update Active threads
   and Backlog to reflect new state, and commit with a message describing
   what changed and why.

---

## Active threads

- **`repeal_clause.target_locator` surfaced: built and closed 2026-09-21.**
  Picked up the Data currency backlog item flagged 2026-09-18 ("isn't
  surfaced anywhere yet") — every partial repeal-list item (an act that
  voids one specific article of another act, not the whole thing) already
  had its target article/band recorded in `target_locator`, but neither app
  showed it, so a reader had no way to see that an act which reads
  "current law" in the whole-act `v_act_currency` sense might still have
  individual provisions dead. Built `v_act_partial_repeal` in
  `build_links.py`, right after `v_act_currency`: one row per `dst_doc_id`
  (article-voiding acts only, i.e. `target_locator IS NOT NULL`), aggregating
  count of voided provisions, the distinct locator text, and the most
  recent voiding act/date (joined through `repeal_clause.src_doc_id ->
  act.doc_date`, since `repeal_clause.cited_date` is the *target* act's own
  adoption date, not the repeal date — easy to get backwards, checked
  carefully against the schema comment before writing the join).
  **Measured, corpus-wide**: 137 acts (of the acts named anywhere in
  `repeal_clause`) have at least one individually-voided provision while
  remaining current law overall — 384 are article-level (`modda`), 14 are
  numbered-item-level (`band`); zero `qism`/`bob`/`paragraf` locators exist
  in the actual data even though the regex allows them (not a bug — just
  what the corpus's repeal lists happen to name). Of the 137, 28 *also* have
  a later whole-act repeal on record — the natural legislative lifecycle of
  "several cleanup laws prune individual articles over the years, then a
  final act repeals what's left," both signals correctly coexisting rather
  than conflicting. Checked where this actually lands in the two apps'
  existing data before building UI: 20 of the LLC dossier's 129
  distinct implementing acts (`llc_implementing_act`) carry this signal (2
  of 74 `cites_cc_foundation`, 19 of the rest under `names_llc_law`, one
  act counted in both routes) — a real, non-trivial fraction of "acts this
  dossier calls live" that had zero visibility into partial death. Wired
  into both apps the same way the existing 🔴 whole-act badge works: a new
  ⚠️ marker on the act's expander header plus an `st.warning()` inside
  naming the count, the locators, and who voided them most recently —
  `app_llc.py`'s `page_acts()` (LEFT JOIN alongside the existing
  `llc_implementing_act` query) and `app_hierarchy.py`'s `page_article()`
  realization-pyramid loop (LEFT JOIN alongside the existing
  `v_act_currency` join, same GROUP BY extension). Verified live in both
  running apps via Playwright — screenshotted the LLC dossier's
  `names_llc_law` route showing 12+ ⚠️-marked acts with one expanded
  (2011 amendment act: "6 provisions individually voided... most recently
  on 2025-07-10"), and the General Part explorer's Article 14 (cited by a
  2016 act with 6 voided provisions, one of which is directly relevant:
  Article 14 of *that citing act itself* was later gutted, "14-modda ...
  toʻrtinchi qism deb hisoblansin" visible in the same evidence snippet).
  Re-ran `build_links.py` against the existing `corpus.duckdb` (not a
  from-scratch rebuild — only this file changed); `repeal_clause`,
  `article_amendment`, and edge counts are byte-for-byte identical to
  2026-09-20's run, confirming the new view is additive and touches no
  existing table. Re-ran `build_llc.py`: `llc_implementing_act` numbers
  (74/74 route counts, 13/74 superseded on `cites_cc_foundation`) unchanged.
  `pyflakes build_links.py app_hierarchy.py app_llc.py`: clean.
  `verify_transfer.py`: all checks green, same INFO-line numbers as
  2026-09-20 (248 superseded acts, 494 stale edges — this feature doesn't
  touch whole-act supersession at all, by design). This closes the backlog
  item outright — nothing scoped to `target_locator` visibility is left
  open. Possible future angle, not pursued today: the same "count of
  individually-voided provisions" signal could be surfaced on
  `app_hierarchy.py`'s `page_structure()` tree view too (currently only
  shows realizing-act counts, no currency at all there) — not done since
  today's brief was specifically "surface `target_locator`", and
  `page_structure()`'s existing scope is Civil Code structure, not
  third-party acts' own internal currency.

- **Gold-set scoring layer: built 2026-09-20, baseline measured, thread
  open for the next sampling round.** Picked up the Extractor backlog's
  longest-standing open item ("Build the gold set") — `build_gold_sample.py`
  (2026-09-15) drew reproducible samples but had no annotation-storage or
  scoring script, so every session's precision/recall claim was a fresh,
  unsaved read-by-hand with no persisted number to compare against over
  time. Built that missing layer: `gold_citations.json` (committed,
  hand-verified ground truth — 50 anchor occurrences, drawn via
  `build_gold_sample.py --seed 20260920`, each hand-read against the raw
  Uzbek text and against `citation_extractor.py`'s own stop-word/anchor
  rules) and `score_gold.py` (the scorer, re-runnable any time the
  extractor changes). Two design decisions worth keeping in mind for future
  rounds: (1) precision is scored per-anchor (does everything this anchor
  produced belong there) but recall is scored against the *whole field's*
  `extract()` output, not just this anchor's bucket — deliberately
  different scopes, because the 2026-09-17 false-alarm lesson (a citation
  attributed to a *different*, nearby anchor isn't a miss) would otherwise
  reproduce itself inside the scorer. (2) `qism` (article-part) is recorded
  per citation but excluded from the headline score — it isn't consumed by
  any downstream table/view yet (see Backlog, "Qism-level grain"), and one
  gold record (gold_id 6) is a live example of why conflating it in would
  be misleading: `extract()`'s documented, already-known "qism range
  collapses to its last ordinal" gap (backlog item, found 2026-09-15) means
  gold_id 6's `expected` can only encode the single ordinal the current
  `Citation` schema is capable of returning, not the true two-part ground
  truth — scoring that as a precision failure would conflate a load-bearing
  article-level correctness bug with a non-load-bearing grain limitation
  that's already tracked separately. Baseline result: **precision 68/68
  (100%), recall 68/68 (100%)** on this 50-window sample — every one of the
  50 read by hand matched what `citation_extractor.py` already produces,
  including several non-trivial cases (plenum-resolution titles correctly
  producing only a bare `act` citation via the `qarori`/`axborotnoma`/`№`
  stop words, `self_reference` anchors with no pinned article correctly
  producing *nothing* at all — confirmed this is `extract()`'s deliberate,
  existing design: the bare-act fallback only fires for
  `kind=='fuqarolik_kodeksi'`, not `self_reference`/`fk_alias`, not a gap —
  and two cases where a second, different code's own article list sitting
  right after the Code's citation in the same sentence is correctly
  excluded by `RE_STOP`'s `kodeksining`/`Qonunining`). This breaks the
  9-session "always finds a bug" streak (see Backlog note) — a legitimate,
  informative result in itself (the extractor's edge cases from 9 prior
  hand-read sessions are holding up), not a failure of today's session.
  **Still open**: only 50/~3251 candidate anchor windows (2599 hit + 652
  empty, corpus-wide) are in the gold set so far — a 100% score on 50
  windows is a promising baseline, not proof the extractor is bug-free
  corpus-wide. Next Extractor-rotation session should either (a) draw and
  annotate another disjoint 50-window batch with a new `--seed` and merge
  it into `gold_citations.json` (grow the set, tighten the confidence
  interval), or (b) if a future hypothesis-driven session finds and fixes a
  new bug, add a targeted gold record for that exact case so it's a
  permanent regression check, not just a one-time fix. Either way, run
  `score_gold.py` after any `citation_extractor.py` change from now on —
  it's a real regression signal that didn't exist before today.

  **2026-09-22: grew the set to 100, found one small real gap.** Followed
  path (a) above — `build_gold_sample.py --seed 20260922 --n 50` (confirmed
  disjoint from the 09-20 batch: zero `(row_id, field, anchor_start)`
  overlap), read all 50 windows by hand against the raw Uzbek text, merged
  into `gold_citations.json` as `gold_id` 50-99. 49/50 read exactly as
  `extract()` already produces (including a `self_reference` anchor scoped
  correctly to stop right where the *next* `mazkur Kodeksning` anchor takes
  over — the same 2026-09-17 "different anchor, not a miss" mechanic this
  scorer's recall/precision split exists to handle, confirmed still working
  as designed rather than assumed). The 50th (`gold_id` 52, row 46605, the
  Code's own cross-reference commentary) is a real, if tiny, gap: LexUZ
  writes "mazkur Kodeksning 65-bobi[ning] 1-paragrifi" — misspelling
  "paragrafi" as "paragrifi" — identically twice in the same row. The
  chapter+section lookahead inside `extract()` requires the literal
  substring "paragraf", so both occurrences fall back to a bare
  chapter-65 citation, silently losing the section-1 grain (this *is*
  downstream-visible, unlike `qism`: `dst_kind` would read `section` not
  `chapter`, a real `link_edge` column, so it doesn't get the same
  qism-style exclusion from scoring). Measured corpus-wide before deciding
  what to do about it: exactly one other row anywhere in the corpus
  contains any "paragrif" spelling (row 25664), and it's entirely about a
  different Cabinet committee's own *nizom* — no "Fuqarolik"/"FK" anchor
  anywhere in that row at all, so it was never even a candidate row for
  this extractor. That makes the real, in-scope footprint exactly 2
  occurrences in exactly 1 row, corpus-wide. Recorded the gold entry with
  its true (typo-corrected) expected output rather than silently matching
  today's coarser behavior — `verdict: known_gap`, not `correct` — so the
  score is honest rather than inflated. **Not fixed**, on the same
  single-occurrence-scope precedent this project already applied to the
  2026-09-15 chapter+paragraph space-separator gap (1 occurrence, also left
  unfixed despite a similarly cheap possible fix) — added to Backlog
  instead (see Extractor recall/precision) rather than special-casing one
  more spelling variant into the regex for a single row. **New combined
  score: precision 217/218 (99.5%), recall 217/218 (99.5%)** on 100
  windows — the one mismatch is exactly the gap above (1 FP + 1 FN, same
  underlying cause), everything else confirmed correct. This is a more
  informative number than the previous batch's 100/100: it's the gold
  set's first genuine, on-the-record miss, and it's now a permanent
  regression check (`score_gold.py` will flag it again immediately if
  `citation_extractor.py` changes touch the chapter+section lookahead, and
  will flag it as *fixed* — precision/recall ticking back to 218/218 — the
  day someone adds the "paragrif" spelling to the regex). Thread stays
  open: 100/~3251 candidate windows is still a first few batches, not
  corpus-wide coverage; next round, draw and annotate another disjoint
  batch with a fresh `--seed`.

- **`repeal_clause` whole-act/partial-repeal conflation: fixed 2026-09-18,
  closed.** Investigating whether the General Part explorer (`app_hierarchy.py`,
  which unlike the LLC dossier never surfaced act-level currency at all)
  should show a 🔴 badge for superseded realizing acts, first measured the
  underlying numbers directly against `corpus.duckdb` rather than trusting
  the existing "357 acts provably superseded" stat — and found that stat
  itself was substantially wrong. Two compounding bugs in `repeal_clause`/
  `v_act_currency` (both in `build_links.py`), found by reading raw text,
  not by inspecting the SQL first: (1) a "kuchini yoʻqotgan deb topilsin"
  repeal-list item was always treated as voiding the *whole* quoted act, but
  398/885 (45%) of items actually read "...gi NNN-sonli Qonunining
  (Axborotnomasi, YYYY, № N, N-modda) M-moddasi ... kuchini yoʻqotgan deb
  topilsin" — Article M of that act loses force, not the act itself (the
  parenthetical is a bibliographic gazette locator, not a target, and was
  being misread as one until a corpus-wide sample confirmed the pattern:
  verified directly inside doc -8151376's own repeal list, which has both
  kinds side by side — items 1-2 are genuine whole-act repeals of the two
  old LLC laws, items 3-21 each void exactly one article of an unrelated
  act). (2) `v_act_currency`'s `LEFT JOIN repeal_clause` silently fanned out
  — some acts are named in more than one repeal_clause row (up to 35, for
  one omnibus 2021 law whose individual articles were voided piecemeal by
  35 later cleanup acts) — so the view, despite looking like one row per
  `doc_id`, wasn't; any downstream `JOIN v_act_currency ON doc_id` (both
  apps do this) silently multiplied whatever it was counting. Confirmed live
  in `app_llc.py`'s `page_currency()` "Superseded acts still feeding the
  realization graph" table, which was overcounting per-act edge totals
  before the fix. Fixed both at the source: `repeal_clause` gained a
  `target_locator` column (NULL = whole act, else the article/qism/band/bob/
  paragraf text voided) computed from the same regex family already used
  elsewhere in the file; `v_act_currency` now only treats `target_locator IS
  NULL` rows as `superseded`, deduplicated to one row per `dst_doc_id` via
  `QUALIFY row_number() ... = 1` (picking the earliest repeal when an act is
  redundantly re-repealed). Net effect, corpus-wide: "acts provably
  superseded" 357 -> **248** (-31%), "stale realization edges" 1115 ->
  **494** (-56%); LLC's own `cites_cc_foundation` route 15/74 -> **13/74**
  superseded. The 2001 LLC Law itself (the load-bearing verify_transfer
  check) stays correctly `superseded` — it's one of the genuine whole-act
  items. Then built the originally-scoped feature on the corrected data:
  `page_article()` in `app_hierarchy.py` now joins `v_act_currency` and
  shows a 🔴 badge + `st.error` per superseded realizing act, a per-tier
  "N superseded" count, and a "Hide superseded acts" toggle — **off** by
  default (unlike the LLC dossier's `value=True`), because this page spans
  all 386 General Part articles and 4 of them (art. 21, 62, 290, 291 — art.
  62 is the LLC's own Civil Code anchor, the same one 2026-09-16 already
  flagged as having zero live LLC-slice evidence) have realizing acts that
  are *exclusively* superseded; a warning banner explains why nothing shows
  when the toggle empties a tier, mirroring `app_llc.py`'s existing pattern.
  Verified live in both apps via Playwright (screenshots of the badge, the
  toggle hiding/revealing, and the all-dead warning on Article 62) and
  `verify_transfer.py` stayed green (`sup`/`stale` INFO lines recompute from
  the same query, no check needed updating). This closes the thread —
  `target_locator` is stored and available but not yet surfaced anywhere in
  either app (see Backlog).

- **LLC implementing-acts currency default: closed 2026-09-16.** Picked up
  the open half of the "Propagate currency into the LLC dossier" backlog
  item (see Backlog, Data currency) — whether `page_acts`/
  `llc_implementing_act` should gate "implements" by currency at the data
  layer by default, instead of today's opt-in `hide_dead` UI toggle.
  Measured first, then found and fixed two real bugs the measurement
  surfaced, then decided. See Log for full detail: **decision is to keep
  the opt-in toggle** — article 62 (the LLC's own defining Civil Code
  anchor) has zero surviving, non-superseded implementing evidence at all,
  so a hard data-layer gate would make the dossier's most central article
  show nothing with no way to recover it. Along the way, fixed a real
  fan-out bug from two foundation articles (45, 62) each anchoring more
  than one LLC stage: `build_llc.py`'s `n_hits` used `count(*)` where the
  `llc_norm` join fans out per stage, inflating hit counts for 9 acts
  (total 368 -> 307, -16.6%); `app_llc.py`'s `page_norm` "Below" section
  read `v_llc_realization` without deduping across stages, silently
  doubling every citation shown for those 2 articles. Both fixed, measured
  before/after, verified live in the running app via Playwright, and
  `verify_transfer.py` stayed green. This closes the backlog item fully —
  nothing scoped to it is left open.

- **Amendment chains: built 2026-09-11, list-swallowing residual fixed
  2026-09-13, UI wiring done 2026-09-14. Thread closed.** New
  `article_amendment` table + `v_article_currency` view, mined from the
  per-article `amendment_note` field rather than the backlog's
  originally-proposed "kiritilsin"-clause detector (see Log for why that
  approach was rejected first). 8 of `verify_transfer.py`'s 9 long-standing
  unexplained `structure_missing_articles`/`md_only` gaps now resolve to an
  exact voiding law + date. Of the two residuals flagged 2026-09-11: (1) the
  list-swallowing bug ("65 va 66-moddalar" only registering its last member)
  is **fixed and measured 2026-09-13** — see Log, 10/594 clauses corpus-wide
  were affected (28 target articles, 18 previously dropped), not just the 1
  occurrence originally spotted. (2) amending-act resolution still caps at
  5.6% (33/594 clauses) because `act.doc_number` is empty corpus-wide, same
  root cause as `repeal_clause`'s own unresolved tail — not a parsing gap, a
  data-acquisition one, left as-is. **UI wiring done 2026-09-14** — see Log
  for the full detail: `page_article()` in `app_hierarchy.py` and
  `page_norm()`/`page_skeleton()`/`page_currency()` in `app_llc.py` now
  surface `v_article_currency`/`article_amendment` directly (per-article
  amendment count, last change type/date, a ⚠️ for removed/voided parts, and
  the full dated history on demand). Verified live in both apps with
  Playwright, not just by reading the diff. This closes the thread — nothing
  scoped to `article_amendment` is left open; residual (2) above stays a
  documented data-acquisition gap, not further pipeline or UI work.

- **Repeal resolution: closed 2026-09-09.** The 45/885 residual left after
  2026-09-06's tiered fallback is now fully characterized — every single
  one is a genuine corpus-coverage gap, not an extraction or matching bug.
  Root-caused by reading all 45 full clause texts (not the 60-char preview
  used in the original 09-06 triage) plus a corpus-wide type breakdown: of
  856 `Qonuni` (law) citations, 82.8% resolve at the exact tier; of 24
  `Qarori` (resolution) and 3 `Farmon` (decree) citations, **0%** do —
  confirmed not incidental by searching the whole `act` table for the most
  common missing kind ("...amalga kiritish tartibi toʻgʻrisida", the
  enactment-procedure resolution issued alongside a new Code): exactly
  **one** such act exists in the entire 24,267-row corpus (the 1992
  Constitution's own), none for the Labor/Urban-Planning/Housing/Civil-
  Procedure/Economic-Procedure Codes whose enactment resolutions are cited
  by name. The other main cluster (13 of the 45, all from one citing act,
  row 16788) cites Qoraqalpogʻiston Respublikasi (Karakalpakstan) statutes
  on 8 distinct dates — verified directly that **zero** acts exist in the
  corpus on 6 of those 8 dates, and the 2 with same-day acts have no
  candidate anywhere near a title match; this national-legislation corpus
  simply doesn't carry Karakalpakstan's own sub-national lawmaking. A
  residual few (4 items, all pre-1991 Soviet-era Presidium/Cabinet
  decrees) have zero acts at all on their cited date, same story. Shipped
  a small, additive fix in `build_links.py`: when no tier resolves a
  clause, check the word immediately following the quoted title, and if
  it's `Qaror`/`Farmon` (not `Qonun`), tag `match_method =
  'unresolved:non-statute'` instead of bare `'unresolved'` — turns
  "unresolved, cause unknown" into "verified: target act type isn't in
  this corpus" for 27 of the 45 (24 Qarori + 3 Farmon, cheap and
  unambiguous by regex). The remaining 18 (13 Qoraqalpogʻiston + 4 old-era,
  no comparably cheap detector) stay generic `unresolved` but are now
  documented here in full instead of deferred. Reran `build_links.py`:
  `repeal_clause` resolution count unchanged at 840/885 (this is a
  label-only change, no new edges invented) — `by match_method` now reads
  `{'date+title': 710, 'date+substring': 81, 'date+fuzzy:*': 48,
  'unresolved:non-statute': 27, 'unresolved': 18}`. Reran `build_llc.py`:
  no LLC-slice numbers changed (none of the 45 touch the LLC Law). Grepped
  both apps for `match_method` first: neither filters on its value, only
  counts rows and reads `dst_doc_id`/`evidence`, so the new label is safe.
  **Decision: this thread is done, not deferred.** There is no further
  extractor or matching work available here — the gap is that the source
  corpus (LexUZ's national-level act index) doesn't carry these document
  types/jurisdictions at all, which is a data-acquisition question (adding
  Qaror/Farmon/Karakalpakstan documents to the raw parquet), not a
  pipeline bug, and out of scope for `build_links.py` to solve. If the
  project owner ever sources a corpus update that adds these, `unresolved:
  non-statute`'s count is the first thing to recheck — a re-run should
  drop it toward zero without any code change.

- **Superscript-article resolution: fixed and measured 2026-09-08, one small
  residual left.** `Citation.doc_id` classified a cited article by comparing
  its raw integer value against `CODE_LAST_ARTICLE` (1199) — but superscript
  articles are cited with the suffix digit concatenated onto the base number
  ("173-7" is written "1737", matching `norm_unit.article_number`), so any
  superscript citation whose concatenated form exceeds 1199 got misclassified
  as "outside the Code" and silently dropped by `build_links.py`'s
  `if dst_doc is None: continue` — never even an unresolved/dangling edge, just
  gone. Found by replicating `build_links.py`'s exact extraction loop
  corpus-wide and filtering for `c.doc_id is None`: exactly **4** real
  citations hit this in the whole corpus (173-7 and 259-1 via a `Fuqarolik
  kodeksi` anchor; 626-1 and 1107-1, both Special Part, via an `FK` alias and a
  bare anchor respectively) — all 4 manually confirmed as genuine, correctly-
  anchored Civil Code citations, not false positives. Also discovered along
  the way: `norm_unit` only ever populated the General Part (articles 1-385,
  confirmed by `SELECT DISTINCT doc_id FROM norm_unit` returning only
  `-111189`) — a scope decision already documented in `build_corpus_db.py`'s
  M0 docstring, not a bug — so the two Special Part hits (626-1, 1107-1) were
  never going to resolve to a `dst_norm_id` either way; the fix's job for
  those two is only to stop dropping the edge entirely, matching how every
  *other* Special Part citation (e.g. a plain "700-moddasi") already produces
  an edge with `dst_norm_id = NULL` rather than no edge at all. Fixed by
  reclassifying any concatenated value past `CODE_LAST_ARTICLE` by its base
  article (`n //= 10`) before the General/Special Part comparison — safe
  because no plain article number exceeds 1199, so anything past it can only
  be this concatenation. Added 4 new self-tests exercising exactly the two
  General Part cases, one Special Part case, and a control (plain "700" must
  stay `DOC_SPECIAL`, unaffected). 32/32 extractor self-tests pass (was 28).
  Reran `build_links.py`: edge count 6791 -> 6795 (+4, exactly the 4 found),
  each new edge inspected directly — the two General Part ones resolved to
  the correct `dst_norm_id` (`-111189-a1737`, `-111189-a2591`), the two
  Special Part ones landed as plain unresolved-to-norm edges (`dst_norm_id
  NULL`, `dst_dangling = false`), exactly as predicted. Reran
  `measure_extractor_recall.py`: still 0 real misses on article/chapter
  recall, qism/band residual unchanged at 7/640 (this fix doesn't touch qism
  attachment). Reran `build_llc.py`: no LLC-slice numbers changed (none of
  the 4 new edges touch the LLC Law or its foundation articles).
  **One residual found but not fixed**: row 1390's citation is actually a
  *range*, "173 – 1737-moddalari", meaning "article 173 through its
  superscript children 173-1..173-7" (8 provisions) — but `_expand`'s
  malformed-range guard (rejects any range wider than 200, to catch garbled
  text) sees `1737 - 173 = 1564` and falls back to a 2-item list of just the
  literal endpoints, so 173-1 through 173-6 (6 provisions) never get cited at
  all even after today's fix, which only rescued the "1737" endpoint itself.
  Checked corpus-wide whether this generalizes: 49 raw occurrences of a
  range spanning more than 200 exist in the corpus, but 48 of them are in
  *other* codes (Criminal Code, Criminal Procedure Code, etc., citing their
  own superscript ranges) that never sit inside a `Fuqarolik kodeksi`/FK-alias/
  self-reference anchor, so the extractor correctly never touches them — row
  1390 is the only one that lands inside a real Civil Code anchor. Genuinely
  a single-occurrence gap (6 missing edges from 1 citation), so left
  undone rather than special-cased into `_expand` for one instance — recorded
  as a Backlog item in case a future corpus update introduces more of these.

- **Repeal resolution: tiered fallback shipped, 45 items still genuinely
  unresolved.** 2026-09-06 added `date+substring` and `date+fuzzy` fallback
  tiers to `build_links.py`'s exact `(date, title)` repeal match, taking
  resolution from 710/885 (80.2%) to 840/885 (94.9%). See Log for the full
  design and measurement. The 45 still unresolved split into two kinds: 13
  `no_date_match` (the cited date matches no act in the corpus at all — the
  clause's own date field may be a transcription slip, or the target act
  genuinely isn't in this 24,267-act corpus; not investigated further) and
  32 `fuzzy_no_clear_winner` (a date match exists but no candidate clears the
  0.80-ratio/0.15-gap acceptance bar — several looked like genuinely
  different acts on inspection, e.g. cid 439/442's "sudyalarning malaka
  hay'atlari" item has no close title match on its date at all). Next step,
  if this thread is picked up again: read the 32 fuzzy-rejected cases' full
  quoted titles by hand (not just the 60-char preview used for triage
  today) — some may be reconstructable amending-act titles the way the
  `date+substring` tier handles the common case, just with a middle phrase
  (e.g. "...ga qaratilgan oʻzgartirishlar...") that breaks the plain
  substring test. Diminishing returns territory: 45/885 (5%) residual is
  already small, and the two batches above suggest what's left is a mix of
  real gaps and un-parseable one-offs rather than one more systematic
  pattern.

- **"Qonun" precision thread: closed.** See Log — the bare-nominative
  "Qonun" misattribution (2026-09-04) is fixed, measured, and verified: 38
  raw edges removed (19 article_text + 19 cross_references, 15 distinct
  citing rows), 2 correctly-weaker "act" edges added back where no real
  provision was left to pin, net -36 (6827 -> 6791). The broader hypothesis
  ("this generalizes to qaror/farmon/nizom") was measured and **falsified
  as a live bug**: those three nouns' bare-nominative forms were checked
  against every Civil-Code anchor window in the corpus and cause **zero**
  actual misattributions today (nizom's bare form was already caught by
  RE_STOP pre-existing; qaror/farmon's bare capitalized forms simply never
  sit adjacent to an unstopped modda/bob clause in the current text). Left
  those three alone rather than adding untested stop words for a gap with
  no measured impact — see Log for the exact counts and reasoning. New
  angle if this ever needs revisiting: re-run
  `measure_bare_act_names.py`-style check (not committed — throwaway,
  reproducible from citation_extractor._anchors()) after any large corpus
  update, since new acts could introduce the gap qaror/farmon/nizom don't
  have today.

- **Precision, more broadly: still open beyond "Qonun".** The "Qonun" fix
  was one specific, measured misattribution pattern. **The "wrong doc_id
  resolution" hypothesis named here was tried 2026-09-08 and paid off** — see
  the superscript-article thread above — though it turned out to be a silent
  recall drop (a real citation producing zero edges) rather than a precision
  misattribution (a real citation landing on the wrong target); still no gold
  set exists (see Backlog). **2026-09-10 tried three more hypotheses**
  (FK-alias definition generalizing to a non-Civil-Code meaning,
  `RE_STOP_ABBR` false-stopping on a non-code acronym, a chapter-list
  wrongly inheriting one paragraph tag) — all three measured corpus-wide and
  falsified/zero-impact, see Log — **but found and fixed a real one along
  the way**: comma-punctuated "N-bobi, M-paragrafi" wasn't recognized as a
  chapter+paragraph attachment at all (3 occurrences), and fixing it exposed
  a second, smaller bug (one of the 3 then resolved to a struct node that
  doesn't exist and got silently dropped — fixed with a chapter-level
  fallback, same principle as the article-level dangling fallback).
  **2026-09-12 found and fixed the biggest precision bug of this whole
  thread**: "qonunning" — the genitive of "qonun" *without* the "-i-"
  thematic vowel (qonun+ning, as opposed to already-stopped qonuni+ning) —
  was never added to `RE_STOP` at all, in either case. 131 real Civil-Code
  misattributions fixed corpus-wide (118 capitalized "Qonunning" + 13
  lowercase "qonunning" — LexUZ doesn't reliably capitalize it even for a
  named act), more than 3x the original bare-"Qonun" fix's 25. See Log for
  the full measurement, the collateral-damage false alarm investigation, and
  why bare "Farmonning"/ordinal-qism/"dan...gacha" ranges were tried and
  falsified along the way. **2026-09-15 built a reusable sampling tool
  (`build_gold_sample.py`, see Backlog "Build the gold set") instead of an
  unsaved one-off query, drew a fresh 50-window stratified sample, and read
  every window by hand** — found and fixed **three** real bugs in one
  sitting (a missing "kodeksning" stop-word, a bare-space "N modda" surface
  form, and list-embedded "N-M"/"N — M" sub-ranges never expanding), plus a
  confidence-hierarchy bug the third fix exposed in `build_links.py`. See
  Log for full measurement of each — net `link_edge` 6667 -> 9402. This
  brings the "read a sample, hypothesize, measure" streak to **8 sessions
  running** with a real, fixable gap found every time (qism/band 09-04,
  Qonun 09-05, doc_id 09-08, chapter+paragraph comma-attachment 09-10,
  qonunning 09-12, and all three of today's). "wrong qism attachment beyond
  what's already checked" and "other stop-word gaps not yet hypothesized"
  remain unsearched, and now there's a committed tool to search them with
  (any `--seed` draws a fresh disjoint sample) rather than a from-scratch
  query each time. The repeal-resolution thread this note used to point to
  is now closed (see Active threads, 2026-09-09) — its 45-item residual
  turned out to be corpus coverage, not extractor precision, so it's not a
  substitute rotation target here. Cleanup was fully drained 2026-09-07 and
  re-confirmed empty 2026-09-10. Rotation since: Extractor 09-10, Data
  currency 09-11, Extractor 09-12, Data currency 09-13 (fixed the amendment-
  chain list-swallowing residual), Data currency 09-14 (UI wiring for
  `article_amendment`/`v_article_currency`), Extractor 09-15, Data currency
  09-16 (closed the LLC implementing-acts currency-default question, see
  Active threads and Log), Extractor 09-17 (another fresh gold-sample round —
  a doubled-en-dash range collapse and a missing-vowel anchor gap, see Log —
  now **9/9** sampling sessions with a real, fixable bug found), Data
  currency 09-18 (found and fixed the `repeal_clause` whole-act/partial-
  repeal conflation and its `v_act_currency` join fan-out while building the
  General Part explorer's currency badge — see Active threads and Log),
  Cleanup 09-19 (first actual working Cleanup session since 09-07 — a
  `pyflakes` pass found and fixed 9 real dead-code/import issues, see
  Active threads and Log), Extractor 09-20 (built the gold-set scoring
  layer, `gold_citations.json` + `score_gold.py`, baseline 100%/100% on 50
  windows — see Active threads and Log; first sample not to find a new bug,
  breaking the 9-session streak), Data currency 09-21 (built and shipped
  `v_act_partial_repeal`, the "which articles of this act have been
  individually voided" signal flagged as unbuilt 2026-09-18 — see Active
  threads and Log), Extractor 09-22 (grew the gold set to 100 records with
  a second disjoint 50-window batch, seed 20260922; found and documented
  one small real gap — a "paragrafi"/"paragrifi" misspelling losing
  chapter+section grain in exactly 1 row/2 occurrences — see Active
  threads, Backlog, and Log; new combined score 217/218 = 99.5% precision
  and recall), Cleanup 09-23 (added `vulture` to the toolchain alongside
  `pyflakes`, found and fixed 6 real dead-code items pyflakes structurally
  cannot catch — see Active threads and Log) — of the last five sessions
  (09-19 through 09-23), Cleanup has two, Data currency has two, Extractor
  has one; next session should prefer Extractor or Data currency over
  Cleanup, which just went twice in five days.

- **Cleanup: fully drained 2026-09-07, re-confirmed empty 2026-09-10.** All
  four backlog items (dead prototypes, `test_transfer_e2e.py` redundancy,
  one-off exploration scripts, `hierarchy_engine.py`'s f-string SQL) were
  resolved in one session — see Log. 2026-09-10 re-audited every remaining
  `execute(f"...")` call in the repo before picking a different rotation
  target: all of them interpolate only the same hardcoded `PARQUET` path
  constant (the established, safe pattern this project's f-string-SQL rule
  is actually about), none interpolate a runtime/data-derived value. Nothing
  left open here unless a future session finds something new to add to the
  Backlog's Cleanup section. **2026-09-16**: found and deleted one more,
  opportunistically while working elsewhere — `demo_llc.py`, same class as
  the four scripts removed 2026-09-07 (hardcoded, nonexistent Windows path,
  zero references anywhere in the repo). Still nothing left open here.
  **2026-09-19**: this session's turn in the rotation, and the manual
  execute-f-string re-audit (above) stayed clean, so widened what "cleanup"
  means instead of re-confirming the same empty backlog a third time — ran
  `python3 -m pyflakes *.py` over the whole repo (first install: not a
  dependency the project already had) and found 9 real issues across 5
  files (`build_llc.py`, `app_hierarchy.py`, `app_llc.py`, `parser.py`,
  `test_transfer_e2e.py`): dead locals never read again (`run_id`,
  `found_arts`, `by_id`), two unused imports, two f-strings with no
  placeholder. Fixed all 9, verified `pyflakes *.py` is clean (0 issues),
  re-ran `build_llc.py` against the existing `corpus.duckdb` and confirmed
  identical output, and checked both apps live via Playwright. See Log for
  full detail. Nothing left open here — but this is now a repeatable check
  (`pyflakes *.py`, not previously part of this project's toolchain) worth
  running again on a future Cleanup rotation rather than assuming it stays
  empty forever the way the original four backlog items did.
  **2026-09-23**: re-ran `pyflakes *.py` first — clean, 0 issues, confirming
  09-19's fixes held. Rather than re-confirm the same empty pyflakes result a
  second time, widened the toolchain again: installed `vulture` (a dead-code
  detector that does whole-repo unused-symbol analysis pyflakes structurally
  can't — pyflakes only flags unused imports/locals within a single scope,
  not an unused module-level constant or a written-but-never-read instance
  attribute). At default confidence it found nothing; at `--min-confidence
  60` it flagged 7 candidates across 6 files. Verified every one by hand
  (grepped the whole repo for each symbol, read the surrounding code) before
  touching anything — vulture's own docs warn it has no cross-file call-graph
  and flags real false positives, so each finding got the same "verify
  before fixing" treatment as pyflakes's hits, not a blind auto-fix. One
  (`app_llc.py`'s unused `t_` tuple-unpack element) was already following
  this codebase's `_`-prefix-for-unused convention and just needed the
  rename to plain `_`, not a real bug — fixed as a free 1-line nit while in
  the file, not counted as a "found bug." The other 6 were genuine, each
  verified independently:
  (1) `build_corpus_db.py`'s module-level `TIER` dict was never read
  anywhere — the actual doc_type-to-tier mapping is a hardcoded `CASE`
  expression inline in the `act` INSERT (found by grepping `tier` across the
  file), so the dict was a stale, unreferenced duplicate of logic that had
  already moved inline; deleted it and moved its explanatory comment down to
  sit on the `CASE` that's actually load-bearing now, instead of orphaned
  above an unrelated dict.
  (2) `citation_extractor.py`'s `RE_FK_ALIAS_DEF` regex (matching "bundan
  buyon matnda FK deb", the clause defining the FK abbreviation) was compiled
  but never called from `extract()` or anywhere else — `build_links.py:129`
  independently reimplements the identical pattern as a raw SQL
  `regexp_matches` string against the parquet directly, which is the version
  actually driving `allow_fk_alias` corpus-wide. The Python regex was a dead
  duplicate of logic that lives in SQL now; deleted it (kept the SQL version,
  since that's the one actually exercised and tested via `verify_transfer.py`
  AC5).
  (3) `structure_parser.py`'s `ROMAN` dict (roman numeral -> int) was never
  read — `RE_PART` captures the roman numeral as a raw string used directly
  in `node_id`, and each part's `ordinal` field comes from a simple
  incrementing counter (`counters["part"] += 1`), not a numeral conversion;
  deleted the dead dict.
  (4) `test_transfer_e2e.py`'s `EXPECTED_MISSING_ARTICLE = "168"` constant
  sat unused while the one test it should parametrize
  (`test_edge_missing_article_168`) hardcoded the literal `"168"` directly —
  inconsistent with every sibling `EXPECTED_*` constant in the same file,
  which are all actually threaded into their tests. Fixed the test to use
  the constant instead of deleting it, matching the established pattern.
  (5) `parser.py`'s `ContextTracker.paragraph_division` attribute is
  genuinely tracked (set from `PARAGRAPH_DIV_PATTERN`, reset on each new
  chapter) but `snapshot()` — the method that turns the tracker into the
  `structural_hierarchy` field written to `parsed_articles.json` — silently
  dropped it, keeping only part/section/chapter/subsection. This directly
  contradicts the module's own docstring, which lists "Paragraph Division"
  as a tracked structural-context feature. Confirmed the pattern is real,
  not a null-forever dead field: an independent regex count against the raw
  markdown found exactly 10 `§`-division headers, matching the "10/10"
  `--verify` check parser.py already runs on itself. Added
  `"paragraph_division": self.paragraph_division` to `snapshot()`'s returned
  dict — one line, matching how part/section/chapter/subsection already
  flow through the identical mechanism. Regenerated `parsed_articles.json`
  via `python3 parser.py --verify`: all 10/10 checks still pass, and a
  before/after diff (scripted, not eyeballed) confirmed **zero** change to
  any other field on any of the 394 articles — only the new key, populated
  for exactly 109 articles across the 10 real `§` divisions, matching the
  regex count exactly. Checked whether this needed a `build_corpus_db.py`
  rerun: grepped the whole repo for `structural_hierarchy` and found it's
  produced by `parser.py` but consumed by *nothing* downstream — not
  `build_corpus_db.py`'s English-transfer alignment (which only reads
  `title`/`clean_text`/`article_number_display`/`heading_type`/`titleless`/
  `repealed`/`line_range`/`db_article_number_key`), not either Streamlit app.
  So this fix makes the shipped `parsed_articles.json` artifact honest about
  what it tracks, with zero effect on `corpus.duckdb` or either app — no
  rebuild needed, and none done.
  (6) `build_llc.py`'s `LLC_OKOZ = "03.03.05.04"` constant was never read in
  its own file. Before deleting it, checked whether it *should* have been
  wired into something — cross-referenced it against the independently-built
  OKOZ classification axis (`build_okoz.py`) rather than assuming it was
  simple dead weight, since the two axes (curated LLC foundation mapping vs.
  regex-parsed OKOZ tree) had never been checked against each other before.
  Confirmed `03.03.05.04` is a real, correctly-spelled OKOZ leaf ("Limited
  Liability Company. Additional Liability Company") — not a typo or
  hallucinated code. But queried `okoz_assignment` corpus-wide and found
  **zero** General Part structural nodes are ever classified under
  `03.03.05.*` (the "Business Partnerships and Companies" branch, LLC's own
  parent) at all: article 62 (the LLC's Civil Code anchor) resolves instead
  to the coarser sibling `03.03.04.00` ("Commercial Organisations"), because
  its containing struct_node (`C4.S2`, articles 58-72) is literally titled
  "Commercial Organizations" in the Code's own structure and the General
  Part isn't subdivided any finer than that at the struct_node level — OKOZ
  classification here is a title-literal match to the Code's own section
  headings, not a semantic one, so it can't reach LLC-specific granularity
  without a struct_node split this project has no reason to make today. Not
  a bug in either axis — `LLC_OKOZ`'s value is correct as a label for the
  *institution*, `okoz_assignment`'s value is correct as a classification of
  the *section that contains it*; they're deliberately different grains that
  happen to both be right. Confirmed `app_llc.py`'s sidebar caption already
  displays "OKOZ 03.03.05.04" correctly as a hardcoded literal (not imported
  from `build_llc.py` — checked, and found this project's apps never import
  build-layer constants; `app_llc.py` already keeps its own local duplicates
  of `LLC_LAW_CURRENT`/`LLC_LAW_PRIOR`/`DOC_GENERAL` rather than importing
  them, an established convention, not an oversight to fix). So the constant
  really was dead in its own file with no wiring gap to close; deleted it.
  All 6 fixes verified together: `pyflakes *.py` and `vulture *.py
  --min-confidence 60` both clean afterward; `python3 -m py_compile` on
  every touched file; `score_gold.py` unchanged at 217/218 (confirms the
  `citation_extractor.py` deletion is behaviorally inert); all 14
  `test_transfer_e2e.py` tests pass, including the fixed one;
  `python3 -m unittest`/47/47 extractor self-tests and `verify_transfer.py`
  both green. Re-ran `build_llc.py` against the existing `corpus.duckdb` (the
  one file among the six with pipeline side effects) and confirmed every
  table's row count identical before/after — then **discarded** the
  resulting `corpus.duckdb` diff rather than committing it: the bytes
  differed (DuckDB's `CREATE OR REPLACE TABLE` doesn't serialize
  deterministically) but every table's content was confirmed identical, so
  committing it would have been exactly the "large binary diff for no
  reason" this project's own build hygiene rule warns against. Checked both
  apps live via Playwright (screenshots, not just a page-load check): loaded
  `app_llc.py`'s `page_acts()` — the function with the `t_` rename — and
  expanded a real row to confirm the tuple-unpack still renders correctly;
  loaded `app_hierarchy.py` for the general no-exception check the other
  five fixes need (none of them touch its code path directly). Nothing left
  open here; `vulture *.py --min-confidence 60` is now a second repeatable
  check worth re-running on the next Cleanup rotation, the same way 09-19
  established `pyflakes` as one.

- **Smaller, lower-priority residual: qism/band tail truncation.** The
  qism/band attachment check added today (see Log) has 10 residual misses
  out of 667 checked (1.5%). Sampled 3 and confirmed the root cause for all
  3: the qism/band tail lookup inside `extract()` is
  `window[m.end():m.end()+60]`, and `window` is capped by the anchor's own
  limit (next anchor's start, or `+WINDOW`) — when a citation lands close to
  that limit, the internal tail is shorter than 60 chars and the qism/band
  clause just past it is never seen, even though it's well within a raw
  60-char slice of the underlying text. Confirmed window slack of 4-14 chars
  (vs. the 60 needed) for 2 of 3 sampled misses; the third had two citations
  for the same article, one truncated (slack 0) and one with ample slack
  (249) that still missed for a reason not yet diagnosed. Small enough
  (1.5%) that it's not worth interrupting the "Qonun" precision thread for,
  but worth a future pass: either widen the window when a modda-with-tail
  match is the last thing found before the limit, or search the raw text
  directly (bounded by the *next* anchor, not `+60` past a truncated
  window) instead of re-slicing an already-cut window. Note: one of the 3
  originally-sampled misses (row 2767) is now gone on its own — it was the
  same "Qonun 19-moddasi" misattribution the 2026-09-05 fix removed, not a
  real qism/band truncation case. Residual count after that fix: 7/640
  (was 10/667) — still open, still small, still not touched.

---

## Backlog

### Extractor recall/precision
- ~~**Build the gold set.**~~ **Scoring layer built 2026-09-20, grown to 100
  records 2026-09-22** — see Active threads and Log for the full detail.
  `gold_citations.json` (100 hand-verified anchor occurrences, two disjoint
  50-window batches) + `score_gold.py` (the scorer) now exist; current
  score **precision 217/218 (99.5%), recall 217/218 (99.5%)** — the one
  mismatch is the documented "paragrif" spelling gap below, recorded with
  its true expected output rather than silently marked correct. Not closed
  outright — 100 windows is still two batches, not corpus-wide coverage
  (2599 hit + 652 empty candidate windows exist). **Next step, whenever
  Extractor rotation comes up again**: draw another disjoint batch with a
  new `--seed`, hand-annotate it, and merge into `gold_citations.json` to
  grow the set — or add a targeted record for any new bug a hypothesis-driven
  session finds, so fixes become permanent regression checks instead of
  one-time. What changed getting here: `build_gold_sample.py` (2026-09-15)
  built the reusable, seeded, stratified sampler over real anchor windows
  (half `extract()`-produced-a-citation, half empty); 2026-09-17's sample
  found a false alarm — a citation that looked like a recall miss in one
  anchor's *display* window but was actually caught by `extract()` via a
  different, nearby anchor occurrence — which is why `score_gold.py` scores
  recall against the whole field's `extract()` output rather than each
  anchor's own local bucket (see Active threads for the full reasoning).
  Hypothesis-driven sampling had found a real, fixable bug in every one of
  9 sessions running before 2026-09-20 (qism/band 09-04, Qonun 09-05, doc_id
  09-08, chapter+paragraph comma-attachment 09-10, qonunning 09-12, three on
  09-15, two more on 09-17); 2026-09-20's batch was the first to come back
  clean (100/100); 2026-09-22's batch found one small real gap (see below) —
  see Active threads for the full measurement of each.
- **LexUZ misspells "paragrafi" as "paragrifi" in one row — chapter+section
  grain silently lost.** Found 2026-09-22 while annotating the second
  gold-set batch (see Active threads): row 46605 (the Civil Code's own
  cross-reference commentary) writes "mazkur Kodeksning 65-bobi[ning]
  1-paragrifi" — twice, identically, in the same row — instead of
  "paragrafi". `extract()`'s chapter+section lookahead only matches the
  literal substring "paragraf", so both occurrences fall back to a bare
  chapter-65 citation, losing the section-1 grain (`dst_kind` would read
  `chapter` instead of `section` in `link_edge` — a real column, unlike
  `qism`, so this one isn't exempt from scoring the way qism-grain issues
  are). Measured corpus-wide: exactly one other row anywhere has any
  "paragrif" spelling (row 25664), and it's about an unrelated Cabinet
  committee's own *nizom* with no Civil-Code/FK anchor anywhere in that row
  at all — never a candidate row for this extractor in the first place. So
  the real, in-scope footprint is exactly 2 occurrences in exactly 1 row,
  corpus-wide. Not fixed today — same single-occurrence-scope precedent
  this project already applied to the 2026-09-15 chapter+paragraph
  space-separator gap (1 occurrence, also left unfixed despite a similarly
  cheap fix) — but recorded as a `known_gap` gold record (`gold_id` 52,
  see `gold_citations.json`) with its true expected output, so it's a
  standing, honest regression check rather than a silently-inflated score.
  If ever picked up: add `paragraf|paragrif` (or a small edit-distance
  tolerance) to both `RE_CLAUSE`'s unit alternation and the chapter+section
  lookahead's literal match inside `extract()`.
- **`RE_STOP`'s `break`-vs-`continue` design.** Once a stop-word is found in
  the gap before a clause, `extract()` abandons the *rest* of that anchor's
  window, not just the one stopped clause — a deliberate, conservative
  choice (don't guess which later numbers belong to the Code vs. the
  just-named other act). Measured 2026-09-12: checked all 552 windows where
  this currently fires with clauses still remaining afterward, and every
  remaining clause genuinely belongs to whatever act triggered the stop, not
  the Code — so it's not a live bug today. But it's a design assumption
  that would break if a future corpus update introduced a window shaped like
  "[Code citation A] ... [other act mention] ... [Code citation B, still
  clearly the Code's]" — worth re-checking this same way after any large
  corpus update, rather than assuming it still holds.
- **Range citation spanning a superscript boundary loses its middle articles.**
  Found 2026-09-08 while fixing the `doc_id` bug (see Active threads): a
  range like "173 – 1737-moddalari" means "article 173 through its
  superscript children 173-1..173-7" (8 provisions), but `_expand`'s
  malformed-range guard (rejects spans over 200, meant to catch garbled text)
  sees a raw gap of 1564 and falls back to a 2-item list of just the literal
  endpoints — so 173-1 through 173-6 (6 provisions) never get an edge at all.
  Confirmed corpus-wide this is a single occurrence today (48 of 49 similar
  wide-range citations are in other codes, outside any Civil Code anchor) —
  not fixed given the 1-occurrence scope, but worth a real fix (detect when
  both range endpoints share the same integer division by 10, i.e. the same
  base article, and expand to the base plus every superscript child between
  the two suffix digits) if a future corpus update adds more of these.
- ~~**Bare-nominative act-name gap in RE_STOP, beyond "Qonun".**~~ **Measured
  2026-09-05, falsified as a live bug**: qaror/farmon/nizom's bare
  capitalized forms cause zero actual misattributions in the current corpus
  (nizom's bare form was already in RE_STOP; qaror/farmon never sit next to
  an unstopped modda/bob clause). Only "Qonun" itself needed the fix. See
  Active threads and Log. **Re-checked 2026-09-12 for the "-ning"-without-"i"
  genitive specifically** (the gap that made "qonunning" real, see Log): 0
  raw corpus occurrences of "Qarorga/Qarorning/Farmonga" precede a clause at
  all, and "Farmonning"/"farmonning" (15+1 occurrences) measured 0 actual
  anchor-window impact — falsified again, same nouns, different surface
  form.
- ~~Measure recall against a second independent signal (`cross_references`
  vs `article_text` on the same row).~~ **Tried 2026-09-03, hypothesis
  falsified**: 4249/4272 (99.5%) of cross_references-sourced Civil Code
  article citations have no matching article_text citation on the same row —
  but manual inspection of samples shows this is because `cross_references`
  is LexUZ editorial commentary pointing at topically related provisions in
  OTHER acts (e.g. a Water Code article's footnote citing an unrelated Civil
  Code contract-law article), not a restatement of what article_text says.
  The two fields are independently informative, not redundant, so agreement
  between them isn't a validity signal. Superseded by the naive-regex method
  in the Log entry below, which found the real recall gap (zero, for the
  forms it covers).
- **Qism-level (article-part) grain.** 689 edges now carry a `dst_qism`
  attribute (was 522 before 2026-09-04's attachment fix — see Log). The
  original scope decision (grain stays article-level) hasn't been
  revisited: worth a measurement pass on whether citing at the qism level
  would change which stage/institution the citation should attach to, now
  that the underlying data is meaningfully more complete.
- **One remaining chapter+paragraph-list attachment gap (single occurrence).**
  Found 2026-09-10 while fixing the comma-punctuated case (see Log): row
  25634's `cross_references` reads "Fuqarolik kodeksi 4-bobining 1
  (“Umumiy qoidalar”) va 2-paragraflari" — a *list* of two paragraphs for
  one chapter, with a parenthetical section title sitting between the first
  paragraph number and the "va" that introduces the second. The section
  lookahead regex only tries a single `\d+-paragraf` immediately after the
  bob match, so this produces a bare chapter-4 citation with no paragraph
  grain at all (not dropped, just coarser — same fallback the comma fix
  added now applies). Confirmed corpus-wide this is exactly 1 occurrence
  (searched for `bob\w*\s+\d+\s*\(.{0,40}\)\s*va\s*\d+\s*-\s*paragraf`-shaped
  text), so not fixed today given the single-occurrence scope and the
  parenthetical-skipping complexity a real fix would need — worth a look if
  a future corpus update introduces more of these.
- **"hamda" not recognized as a list conjunction, only "va".** Found
  2026-09-15 while fixing the space-separator gap (see Log): row 24219 reads
  "Fuqarolik kodeksining 11-12 hamda 14 moddalari" — `_expand`'s top-level
  split only recognizes "," and "va" between numbers, so "hamda" ("as well
  as") breaks the list there; today's fix already recovers "11-12" as an
  embedded sub-range independently, but a bare number joined only by "hamda"
  (like the "14" here) still comes through fine only because it's the last
  item before the unit word, not because "hamda" is understood — a case
  shaped like "14 hamda 20-moddasi" (hamda-joined, nothing after) would
  still lose "14". **Measured corpus-wide 2026-09-22** (regex search for
  `\d+(?:\s*[-–—]\s*\d+)?\s+hamda\s+\d+\s*[-–—]?\s*(modda|bob|paragraf)`
  across all three source fields): 3 raw occurrences total, of which 2 are
  inside `Fuqarolik protsessual kodeksi` (FPK) text — already correctly
  excluded entirely by `RE_STOP_ABBR`, not this project's Code at all — and
  only 1 (the row 24219 case already known) is a genuine in-scope Civil
  Code citation. Same tiny single-occurrence shape as the "paragrif"
  spelling gap found the same day (see Log/Active threads) — not worth
  fixing today for the same reason, but now a real measured count instead
  of "not measured."
- **Chapter+paragraph's own space-separator gap.** Found 2026-09-15 while
  fixing the main space-separator gap (see Log): row 42566 reads
  "22-bobining 2 paragrafi" (space, no hyphen) — the *main* `RE_CLAUSE` fix
  covers `modda`/`bob`/`paragraf` directly, but the separate chapter+section
  lookahead (`sec = re.match(r"\s*,?\s*(\d+)\s*-\s*paragraf", ...)`) still
  requires a hyphen on its own, unfixed regex. Not a dropped citation today
  — the chapter (22) still gets cited, just without the paragraph grain,
  same fallback as every other unresolvable-paragraph case — so this is a
  precision refinement, not a recall gap. Confirmed corpus-wide this is
  exactly 1 occurrence today; left alone given the single-occurrence scope,
  worth revisiting alongside the chapter+paragraph-list gap above if a
  corpus update adds more.
- **Qism range collapses to its last ordinal only.** Found 2026-09-15 (see
  Log): "FK 154-moddasining ikkinchi — toʻrtinchi qismlarida" (parts two
  through four) — `RE_QISM`'s tail search only matches one ordinal
  immediately before "qism", so `Citation.qism` records just "toʻrtinchi
  qism" (part four), silently losing that parts two and three are also
  cited. Not measured corpus-wide or fixed today — `qism` is documented in
  `citation_extractor.py` as "kept for a future finer grain" and isn't
  consumed by any downstream table/view yet (see the "Qism-level grain" item
  above), so this is lower priority than a bug that changes an actual
  `link_edge` row. Worth fixing together with that item if qism grain ever
  becomes load-bearing.
- **"boʻlim" (Part, the structural level above chapter) is never a
  recognized citation unit.** Found 2026-09-17 while reading a gold sample
  (see Log): "Fuqarolik kodeksining IV-boʻlimi" cites Part IV of the Code by
  roman numeral, but `RE_CLAUSE` only recognizes `modda`/`bob`/`paragraf` as
  unit words, so a bare Part-level citation (no chapter/article alongside
  it) falls all the way back to a coarse act-level citation, losing the
  Part distinction entirely. Measured corpus-wide
  (`Fuqarolik\s+kodeks\w*\s+[IVXLC]+\s*-\s*boʻlim\w*`): 6 occurrences, all
  genuine. Not fixed today — unlike the other regex-only fixes this
  session, adding a real Part-level grain means a new `target_kind`
  ("section"/"part"), roman-numeral parsing, and touching whatever in
  `build_links.py`/both apps would need to consume it, which isn't
  justified by a 6-occurrence count alone. Worth building if a future
  corpus update raises that count, or if the Qism-level-grain backlog item
  above is ever picked up (same "is a coarser-than-article grain worth
  modeling" question, one level up the hierarchy instead of down).

### Data currency
- ~~**175/885 repeal items still unresolved.**~~ **Fixed 2026-09-06, residual
  fully characterized and closed 2026-09-09**: tiered `date+substring`/
  `date+fuzzy` fallback resolved 130 of them (840/885, 94.9%); the last 45
  are a genuine corpus-coverage gap (Qaror/Farmon document types and
  Qoraqalpogʻiston Republic acts the source corpus barely carries), not a
  matching bug — 27 of the 45 now tagged `unresolved:non-statute` so the
  gap is visible in the data itself. See Log 2026-09-06 and 2026-09-09.
- ~~**Amendment chains, not just repeals.**~~ **Done differently than
  proposed, 2026-09-11**: rather than detecting "kiritilsin"-style clauses
  inside amending acts' own free text (noisy, would need repeal_clause's
  numbered-list parsing all over again), mined the `amendment_note` field
  LexUZ already attaches per Civil Code article — a new `article_amendment`
  table (594 events, 425/1197 articles touched) and `v_article_currency`
  view. See Log. Amending-act resolution still caps around 5.6% (33/594) for
  the same root cause as `repeal_clause`'s — `act.doc_number` is empty
  corpus-wide — documented as a residual, not re-litigated.
- ~~**Article-amendment list-swallowing residual from 2026-09-11.**~~ **Fixed
  2026-09-13**: a multi-article list/range clause ("65 va 66-moddalar
  ... kiritilgan") only registered its *last* member — same class of
  list-swallowing gap as the qism/band and chapter+paragraph list bugs found
  on other threads. Fixed by reusing `citation_extractor.RE_CLAUSE`/`_expand`
  (the same list/range grammar the extractor itself uses, already covered by
  32+ self-tests) instead of `build_links.py`'s own narrower
  `(\d+)...modda` search. Measured corpus-wide: 10/594 amendment clauses are
  actually multi-member lists or ranges (28 target articles total, not 10) —
  594 clauses now produce 612 `article_amendment` rows, one per target
  article. Confirmed correct on inspection: article 65's own amendment event
  now exists (`v_article_currency` shows it `voided` on 2014-05-14, matching
  article 66's neighboring entry); a 7-member superscript range
  ("1731 — 1737-moddalar") now resolves all 7 to real `norm_unit` rows
  (`-111189-a1731` .. `a1737`), not just the endpoint. See Log.
- **Remaining article-amendment residuals from 2026-09-11** (see Log for full
  detail): (1) 5/594 clauses are chapter/paragraph-level (no article number
  at all, e.g. "42-bobning nomi ... tahririda") and get no
  `target_article_number` — correct behavior, just worth knowing if a future
  session wants chapter-level currency too. (2) amending-act resolution
  (33/594 clauses) only fires when the amending act's own title names
  "Fuqarolik kodeks" — most amendment acts are omnibus bills ("ayrim qonun
  hujjatlariga oʻzgartirish...") that don't, and without `doc_number` there's
  no safe way to disambiguate same-day candidates by number; not worth
  chasing further without a corpus update that populates `doc_number`.
- ~~**Propagate currency into the LLC dossier's implementing-acts list.**~~
  **Closed 2026-09-16.** Article-level currency was surfaced in both apps
  2026-09-14 (via `v_article_currency`). The remaining open half — whether
  `v_act_currency`-driven filtering of `page_acts`/`llc_implementing_act`
  should gate "implements" by default at the data layer, instead of today's
  opt-in `hide_dead` toggle — got the measurement pass this item asked for,
  2026-09-16: **decision is no, keep the opt-in toggle.** Article 62 (the
  Civil Code's own definition of the LLC) has zero non-superseded
  implementing evidence at all — a hard default gate would make the
  dossier's most central article show nothing, with no way to recover the
  evidence short of finding and flipping a setting most readers wouldn't
  know exists. See Active threads and Log for the full measurement
  (15/74 acts, 94/307 hits of `cites_cc_foundation` evidence are
  superseded) and for two real fan-out bugs found and fixed along the way
  (`build_llc.py`'s `n_hits`, `app_llc.py`'s `page_norm` citation list).
  **Note 2026-09-18**: the 15/74 count above was itself measured against the
  pre-fix, over-broad `derived_status`; on the corrected data it's 13/74 (see
  Active threads and Log, 2026-09-18) — the "keep the opt-in toggle" decision
  and its reasoning (article 62 has zero surviving evidence either way) are
  unaffected.
- ~~**`repeal_clause.target_locator` isn't surfaced anywhere yet.**~~ **Built
  and closed 2026-09-21**: new `v_act_partial_repeal` view (one row per
  voided-but-not-whole-act `dst_doc_id`, 137 acts corpus-wide) wired into
  both apps as a ⚠️ marker alongside the existing 🔴 whole-act badge. See
  Active threads and Log for the full measurement (20/129 LLC implementing
  acts carry this signal) and the two apps' exact wiring.
- **OKOZ classification can't express LLC-specific granularity anywhere in
  the General Part today.** Found 2026-09-23 while deciding whether
  `build_llc.py`'s dead `LLC_OKOZ = "03.03.05.04"` constant should be wired
  into something (see Active threads' Cleanup entry for the full
  investigation). Measured corpus-wide: `okoz_assignment` never classifies
  any General Part struct_node under the `03.03.05.*` branch ("Business
  Partnerships and Companies", LLC's own OKOZ parent) — article 62 (the
  LLC's Civil Code anchor) lands on the coarser sibling `03.03.04.00`
  ("Commercial Organisations") instead, because its containing struct_node
  (`C4.S2`, arts 58-72) is titled exactly that in the Code's own structure
  and the General Part isn't subdivided any finer at the struct_node level.
  Not a bug — `build_okoz.py`'s classifications are title-literal matches to
  the Code's own section headings, and are correct at that grain — but it
  means the OKOZ axis and the LLC dossier's own institution-level curation
  can never agree at a finer grain than "Commercial Organisations" without a
  new struct_node (e.g. splitting `C4.S2` the way the LLC Law's own chapters
  already split the institution). Worth a look only if OKOZ-level filtering
  or breadcrumbs ever need to distinguish LLC-specific provisions from
  general commercial-organization ones within the General Part — not
  scoped or justified by today's single dead-constant finding alone.

### Cleanup
- ~~**Retire superseded prototypes.**~~ **Done 2026-09-07**: deleted
  `hierarchy_engine.py`, `app_deep.py`, `app.py` — confirmed zero references
  anywhere else in the repo (only `app_deep.py` importing `hierarchy_engine`,
  both removed together) before deleting. This also fully closes the
  `hierarchy_engine.py` f-string-SQL item below (the file is gone, not just
  patched).
- ~~**`test_transfer_e2e.py` redundancy.**~~ **Diffed and partially retired
  2026-09-07**: NOT fully redundant as this item assumed — Tier 1/2/3
  (14 tests) are a genuinely independent second markdown-parser
  implementation plus hardcoded-ground-truth checks, distinct in kind from
  `verify_transfer.py`'s pipeline-output checks (same "naive detector"
  philosophy as `measure_extractor_recall.py`). Only Tier 4 (its own
  AC1-AC3, 3 tests) was actually redundant — and partly dead code, testing a
  "post-M2" schema (english text added to the parquet) the pipeline never
  built. Removed Tier 4 only; kept and documented the rest. See Log.
- ~~**One-off exploration scripts.**~~ **Done 2026-09-07**: deleted
  `analyze_civil_code.py`, `analyze_fk.py`, `analyze_fk_deep.py`,
  `find_civil_code.py` — all four hardcoded a Windows path
  (`c:/uzbek-legal-corpus/...`) that doesn't exist in this (or any Linux)
  environment, so none were runnable as-is; nothing worth folding forward,
  every query they ran is superseded by a real pipeline table or measurement
  script.
- ~~**`hierarchy_engine.py`'s f-string SQL.**~~ **Closed 2026-09-07** by
  deleting the file (see above) rather than patching it, since it was
  already confirmed dead.
- ~~**`pyflakes`-class dead code beyond unused imports/locals.**~~ **Found and
  fixed 2026-09-23** via a new `vulture` pass (see Active threads and Log for
  the full detail on all 6): a dead module-level dict duplicated by an inline
  SQL `CASE` (`build_corpus_db.py`'s `TIER`), a dead regex duplicated by raw
  SQL in `build_links.py` (`citation_extractor.py`'s `RE_FK_ALIAS_DEF`), a
  dead roman-numeral dict superseded by a plain counter
  (`structure_parser.py`'s `ROMAN`), an unused test constant wired into its
  test instead of deleted (`test_transfer_e2e.py`'s
  `EXPECTED_MISSING_ARTICLE`), a tracked-but-never-serialized parser field
  fixed to match its own docstring's claim (`parser.py`'s
  `paragraph_division` — see Active threads for why this needed no
  `corpus.duckdb` rebuild), and a dead OKOZ-code constant kept unwired after
  confirming, corpus-wide, that no General Part struct_node is classified
  finer than "Commercial Organisations" today (`build_llc.py`'s `LLC_OKOZ` —
  see Active threads for the full cross-axis measurement). `vulture *.py
  --min-confidence 60` is now clean and is a second repeatable Cleanup check
  alongside `pyflakes`.

---

## Log

### 2026-09-23 — Cleanup rotation: added `vulture` to the toolchain, found and fixed 6 real dead-code items pyflakes can't catch

Rotation note from 09-22 flagged Cleanup or Data currency as due (Extractor
had gone twice in four days: 09-20, 09-22). Picked Cleanup — its own
rotation note (09-19) had already flagged `pyflakes` as worth re-running
periodically rather than assumed permanently clean, and it hadn't been
re-run since.

**Environment note** (same cold-start pattern as every session since
09-19): fresh clone had `duckdb`, `streamlit`, `playwright`, `pyflakes`
missing, plus `git-lfs` itself not installed at the OS level this time —
`articles/train-00000-of-00001.parquet` came down as a 134-byte LFS pointer
(`git lfs ls-files` failed with "not a git command" until `apt-get install
-y git-lfs` + `git lfs install --local` + `git lfs pull`). Confirmed the
pulled file is correct before using it: 163,356,047 bytes, sha256
`e7a30c53...` matching the pointer's own recorded oid, 54,173 parquet rows.
`build_llc.py` failing with `InvalidInputException: No magic bytes found`
on the first attempt was this same gotcha, not a code bug — same failure
mode 09-22's log entry already documented for a truncated parquet.

**What was done**: `python3 -m pyflakes *.py` first, to check whether
09-19's fixes had held and whether anything new had crept in — clean, 0
issues. Rather than stop there (a second "still empty" confirmation adds
little), installed `vulture`, a dead-code detector pyflakes structurally
can't replicate: pyflakes only catches unused imports/locals within a
single function scope, not an unused module-level constant or a tracked-
but-never-read instance attribute, both of which need whole-file (or
whole-class) analysis. `vulture *.py` at its default confidence found
nothing; `--min-confidence 60` (vulture's own docs note lower confidence
trades more false positives for more real findings) surfaced 7 candidates
across 6 files. Verified every one by hand before changing anything —
grepped the whole repo for each symbol and read the surrounding code —
since vulture has no cross-file call graph and a "write-only-looking"
attribute can still be a deliberate design choice (this project has
precedent for that: `qism`'s own docstring explicitly says it's "kept for
a future finer grain" and isn't wired in yet, which is not a bug).

**Found and fixed** (full investigation and reasoning for each in Active
threads' Cleanup entry — kept there rather than duplicated in full here):
1. `build_corpus_db.py`'s `TIER` dict — dead, duplicated by an inline SQL
   `CASE` that's the actual source of truth. Deleted; moved its comment to
   sit on the `CASE` instead.
2. `citation_extractor.py`'s `RE_FK_ALIAS_DEF` — dead, duplicated by a raw
   SQL `regexp_matches` in `build_links.py:129` that's what actually drives
   `allow_fk_alias` corpus-wide. Deleted the Python copy.
3. `structure_parser.py`'s `ROMAN` dict — dead; roman numerals are kept as
   raw strings for `node_id`, and `ordinal` comes from a plain counter, not
   a numeral conversion. Deleted.
4. `test_transfer_e2e.py`'s `EXPECTED_MISSING_ARTICLE` — unused while its
   own test hardcoded the literal `"168"` instead, unlike every sibling
   `EXPECTED_*` constant in the file. Wired the constant into the test
   rather than deleting it, matching the established pattern.
5. `parser.py`'s `ContextTracker.paragraph_division` — genuinely tracked
   (10 real `§`-division headers, confirmed by an independent regex count
   matching the parser's own `--verify` "10/10" check) but silently dropped
   by `snapshot()` before reaching `parsed_articles.json`, contradicting the
   module docstring's own claim of tracking it. Added it to `snapshot()`'s
   output. Confirmed via a scripted before/after diff that this is the
   *only* change to the regenerated JSON (109 articles now carry a non-null
   value, zero other fields touched on any of the 394 articles), and
   confirmed via a repo-wide grep that `structural_hierarchy` (the field
   that carries it) is produced by `parser.py` but consumed by nothing
   downstream today — not `build_corpus_db.py`'s English-transfer
   alignment, not either app — so this fix has zero effect on
   `corpus.duckdb` and needed no pipeline rebuild.
6. `build_llc.py`'s `LLC_OKOZ = "03.03.05.04"` — before deleting, checked
   whether it should have been wired into something instead by
   cross-referencing it against `build_okoz.py`'s independently-built OKOZ
   axis, since the two had never been checked against each other. Confirmed
   `03.03.05.04` is a real, correctly-spelled OKOZ leaf ("Limited Liability
   Company. Additional Liability Company"), then measured corpus-wide that
   `okoz_assignment` never classifies any General Part struct_node under
   `03.03.05.*` at all — article 62 lands on the coarser sibling
   `03.03.04.00` ("Commercial Organisations") instead, because its
   containing struct_node is literally titled that in the Code's own
   structure and isn't subdivided any finer. Not a bug in either axis, just
   two deliberately different grains — see Backlog (Data currency) for the
   finding, written up as a possible future angle, not an open bug. Deleted
   the constant; confirmed `app_llc.py`'s sidebar caption already shows the
   same code correctly as its own hardcoded literal (apps in this project
   don't import build-layer constants — `app_llc.py` already keeps local
   duplicates of `LLC_LAW_CURRENT`/`LLC_LAW_PRIOR`/`DOC_GENERAL` rather than
   importing them, an established convention).

Also fixed, opportunistically, while in `app_llc.py`'s `page_acts()` for
finding 6's context: renamed an unused tuple-unpack element from `t_` to
`_`, matching this codebase's own unused-variable convention. Not counted
as a "found bug" — it was already harmless, just inconsistently named.

**Measured/verified**: `pyflakes *.py` and `vulture *.py --min-confidence
60` both clean after the fixes. `python3 -m py_compile` on all 6 touched
files. `python score_gold.py`: unchanged at **217/218 (99.5%)** precision
and recall — confirms the `citation_extractor.py` deletion is behaviorally
inert, not just "looks safe." `python3 -m unittest test_transfer_e2e`: all
14 tests pass, including the fixed `test_edge_missing_article_168`.
`python citation_extractor.py`: 47/47 self-tests pass. Re-ran `build_llc.py`
against the existing `corpus.duckdb` (the one touched file with pipeline
side effects) and confirmed every table's row count identical before/after
(`llc_stage` 8, `llc_norm` 100, `llc_implementing_act` 132, and all other
tables' counts matched too, checked programmatically, not just the three
LLC ones) — then **discarded** the resulting `corpus.duckdb` binary diff
rather than committing it, since DuckDB's `CREATE OR REPLACE TABLE` doesn't
serialize deterministically byte-for-byte even with identical content;
committing it would have been exactly the "large binary diff for no
reason" this project's own build hygiene rule warns against, for a change
already proven to be a no-op. Checked both apps live via Playwright
(screenshots, not just a page-load check): `app_llc.py`'s `page_acts()`
(the function with the `t_`→`_` rename) loads and its row expanders render
evidence text correctly; `app_hierarchy.py` loads with no exception (the
other 5 fixes don't touch its code path). `python verify_transfer.py`:
**all checks green**, identical INFO numbers to 09-22 (248 superseded acts,
494 stale edges, 9531 `link_edge` rows, 386/386 OKOZ-classified) — expected,
since none of today's fixes touch extraction, links, or OKOZ assignment
logic.

**Decided not to pursue today**: wiring `LLC_OKOZ`'s underlying question
(finer OKOZ granularity for the LLC within the General Part) into a real
fix — recorded as a Backlog item instead, since nothing today's session
found justifies a new struct_node split on its own.

### 2026-09-22 — Extractor rotation: grew the gold set to 100 records, found and documented one real grain gap

Rotation note from 09-21 flagged Extractor and Cleanup as due (Data
currency had gone twice in three days). Picked Extractor's gold-set thread
over a fresh Cleanup pass — it had an explicit, already-recorded next step
("draw another disjoint batch with a new `--seed`") rather than an
open-ended re-audit, and growing a committed, scored ground-truth set is
higher-leverage than re-confirming Cleanup is still empty a third time.

**Environment note** (same cold-start gotcha as every session 09-19
onward): fresh clone had neither `git-lfs`, `duckdb`, `pyflakes`, nor
`streamlit` installed, and HEAD was detached one commit behind origin/main
— installed all four and ran `git fetch origin main && git checkout -B
main origin/main` to resync, same fix as prior sessions. `git lfs pull`
was also needed this time (the raw parquet came down as a 134-byte LFS
pointer, not the real 163MB file) — `verify_transfer.py`'s AC3 check
caught this immediately and correctly (`InvalidInputException: No magic
bytes found`) rather than silently passing on a truncated file, which is
exactly what that check is for.

**What was done**: `python build_gold_sample.py --n 50 --seed 20260922`
drew a fresh stratified sample (candidate pool unchanged from 09-20:
2599 hit + 652 empty windows, confirming no corpus drift). Verified it was
fully disjoint from the existing 50 records by `(row_id, field,
anchor_start)` before reading — zero overlap. Read all 50 windows by hand
against the raw Uzbek parquet text and `citation_extractor.py`'s own
stop-word/anchor rules, the same way 09-15/09-17/09-20 did. Spent extra
care re-verifying, not just assuming, a few structurally tricky cases
matched the *design*, not just "looked plausible": a 39-citation
list/range spanning "14, 236 — 258, 325 — 339-moddalari" (counted the
range math by hand: 1 + 23 + 15 = 39, matched); a window where two
separate `mazkur Kodeksning` self-reference anchors sit close together
("...57-bobi (985—1004-moddalar)... 58-bobi (1023—1030-moddalar)...") —
confirmed the *first* anchor's own bucket correctly stops at chapter 57's
content and does NOT reach into chapter 58, because `extract()`'s window
limit is the *next* anchor's start position, not a fixed character count;
chapter 58's citations belong to that second anchor's own (unsampled)
occurrence, not a miss on this one — this is the exact mechanic the
2026-09-17 "different anchor, not a miss" lesson put in place, confirmed
still working as designed rather than assumed.

**Found**: 49/50 windows matched `extract()`'s current output exactly.
The 50th (row 46605, the Civil Code's own cross-reference commentary)
reads "mazkur Kodeksning 65-bobi[ning] 1-paragrifi" — LexUZ misspells
"paragrafi" as "paragrifi", identically, twice in the same row (confirmed
by reading the full row text, not just the sampled window). `extract()`'s
chapter+section lookahead requires the literal substring "paragraf", so
both occurrences fall back to a bare chapter-65 citation, silently losing
the section-1 grain. This *is* downstream-visible unlike `qism` (a real
`link_edge` column, `dst_kind`, would read `chapter` instead of `section`)
so it doesn't get the same "not load-bearing yet" exemption qism-grain
issues get. Measured corpus-wide before deciding what to do: searched
every `article_text`/`cross_references`/`amendment_note` field for any
"paragrif" spelling — exactly one other row (25664) has one, and it's
entirely about an unrelated Cabinet committee's own *nizom* (no
"Fuqarolik"/"FK" anchor anywhere in that row at all, confirmed by
substring search), so it was never even a candidate row for this
extractor. Real in-scope footprint: 2 occurrences, 1 row, corpus-wide.

**Decision: documented, not fixed**, same single-occurrence-scope
precedent this project already applied 2026-09-15 to the chapter+paragraph
space-separator gap (1 occurrence, left unfixed despite an equally cheap
possible fix) — a corpus-wide search that turns up exactly one row isn't
worth widening a regex for today, but it's cheap to fix later (add
`paragraf|paragrif` to `RE_CLAUSE`'s unit alternation and the
chapter+section lookahead) if a corpus update ever makes it recur. Added
to Backlog. Recorded the gold entry (`gold_id` 52) with its true,
typo-corrected expected output rather than silently marking it "correct"
to match today's coarser behavior — `verdict: known_gap` — so `score_gold.py`
reports an honest miss instead of an inflated 100%, and the record becomes
a permanent regression check: precision/recall will tick back to 218/218
automatically the day someone does fix the spelling gap.

**Measured**: merged both batches into `gold_citations.json` (100 records,
`gold_id` 0-99, `_meta.batches` records both seeds). `python score_gold.py`:
**precision 217/218 (99.5%), recall 217/218 (99.5%)** — the single
mismatch is exactly the "paragrif" gap (1 FP + 1 FN, same underlying
cause), zero drift, everything else confirmed correct. This is a more
informative number than 09-20's clean 100/100: it's the gold set's first
genuine on-the-record miss rather than an unbroken streak that could read
as "nothing's ever been found because nothing's being looked for hard
enough." `python citation_extractor.py`: 47/47 self-tests still pass
(untouched — no extractor code changed today, only the gold-set data
file). `pyflakes build_gold_sample.py score_gold.py citation_extractor.py`:
clean. `python verify_transfer.py`: **all checks green**, identical
numbers to 09-21 (248 superseded acts, 494 stale edges, 9531 `link_edge`
rows) — expected, since nothing in the pipeline itself changed, only the
gold-set JSON (not read by any pipeline script).

**Decided not to pursue today**: fixing the "paragrif" gap itself (see
above — single-occurrence precedent). Also considered, and set aside in
favor of the gold-set's explicit next step: the "hamda" list-conjunction
backlog item (measured today as a side check while reading windows —
3 raw corpus occurrences total, only 1 inside a real Civil Code anchor,
same tiny single-occurrence shape as the paragraf gap — not written up as
its own thread since the backlog entry already exists and the count
doesn't change its "not worth fixing yet" status).

### 2026-09-21 — Data currency rotation: built `v_act_partial_repeal`, surfaced individually-voided-provision currency in both apps

Rotation note from 09-20 flagged Data currency as the longer-idle of the
two threads (last touched 09-18 vs. Extractor's 09-20). Checked the Data
currency backlog: only one item wasn't struck through — "`target_locator`
isn't surfaced anywhere yet," flagged 2026-09-18 the same day
`target_locator` itself was built (the column recording which single
article/band of a *partially* repealed act was voided) but never wired
into anything downstream. Picked that up rather than re-measuring an
already-closed item.

**Environment note** (same cold-start gotcha as 09-19/09-20): fresh clone
had neither `git-lfs`, `duckdb`, `pyflakes`, `streamlit`, nor `playwright`
installed; installed all five. `git status` showed HEAD detached from
`refs/heads/main` one commit *behind* a stale cached `origin/main` — a
`git fetch origin main` resolved it immediately (local `main` was just
behind, `git checkout -B main origin/main` fixed it) — huge relief this was
the same one-fetch staleness 09-19 already diagnosed, not new data loss.

**What was built**: `v_act_partial_repeal` in `build_links.py`, a view
aggregating `repeal_clause` rows where `target_locator IS NOT NULL` (an
act voided one specific provision of another act, not the whole thing) by
`dst_doc_id` — count of voided provisions, the distinct locator text, and
the most recent voiding act/date. One subtlety worth flagging for future
readers of this table: `repeal_clause.cited_date` is the *target* act's
own adoption date (used upstream to resolve `dst_doc_id` by date+title),
not the date of the repeal itself — the repeal date has to come from
`act.doc_date` for `src_doc_id`, joined in explicitly. Got this right by
re-reading the `repeal_clause` build loop's column order before writing
the join, not by trial and error against the output.

**Measured, corpus-wide**: 137 acts have at least one individually-voided
provision while remaining current law overall (not the 45%/398 raw
`repeal_clause` items — that's items, this is distinct acts). 384 of the
398 partial items are article-level (`modda`), 14 are numbered-item-level
(`band`); zero `qism`/`bob`/`paragraf` locators occur in the actual data
even though `re_target_locator` (built 09-18) allows all four — not a bug,
just what the corpus's repeal lists happen to name in practice, confirmed
by grouping every distinct `target_locator` value and pattern-matching the
unit word. 28 of the 137 *also* have a later whole-act repeal on record —
inspected a couple by hand, and this is the ordinary legislative lifecycle
(cleanup laws prune individual articles over several years, then a final
act repeals whatever's left), not a data conflict — both signals correctly
coexist rather than needing to be reconciled into one.

**Where this actually lands**: checked against the LLC dossier's own data
before building UI, since "worth a look" backlog items sometimes turn out
to hit zero real rows. They don't here — 20 of `llc_implementing_act`'s 129
distinct acts carry this signal (2 of 74 under `cites_cc_foundation`, 19
under `names_llc_law`, one act counted under both routes), meaning roughly
1 in 6 acts the dossier calls "implementing" had zero visibility into
partial death before today: an act reading as fully "current" in the
existing whole-act `derived_status` sense could still have had several of
its own provisions individually gutted by later cleanup laws.

**UI wiring**: mirrored the existing 🔴 whole-act-superseded pattern rather
than inventing a new one. `app_llc.py`'s `page_acts()` — `LEFT JOIN
v_act_partial_repeal` alongside the existing `llc_implementing_act` query,
a ⚠️ appended to the expander header, and an `st.warning()` inside naming
the count, the locators, and who voided them most recently.
`app_hierarchy.py`'s `page_article()` realization-pyramid loop — the same
pattern, `LEFT JOIN v_act_partial_repeal` alongside the existing
`v_act_currency` join (extended the `GROUP BY` list to match), same ⚠️ +
`st.warning()`. Verified live in both running apps via Playwright, not
just by reading the diff: screenshotted the LLC dossier's `names_llc_law`
route with `hide_dead` on, showing a dozen ⚠️-marked "current law" acts and
one expanded (a 2011 amendment act: "Still current law overall, but 6 of
its own provisions (11-moddasi, 19-moddasi, 22-moddasi, 23-moddasi,
6-moddasi, 8-moddasi) have been individually voided — most recently by
[...] on 2025-07-10"); and the General Part explorer's Article 14, cited
by a 2016 act itself later shown to have 6 voided provisions — one of
which is directly visible in the same evidence snippet already displayed
("14-modda ... toʻrtinchi qism deb hisoblansin", i.e. that citing act's own
Article 14 was later gutted, an almost-too-neat coincidence confirmed by
reading the actual text, not assumed from the article number matching).

**Verification**: re-ran `build_links.py` against the existing
`corpus.duckdb` (only this file changed, no full rebuild) — `repeal_clause`
(885 items, 840 resolved), `article_amendment` (594 clauses -> 612 rows),
and `link_edge` (9531) counts are byte-for-byte identical to 2026-09-20's
last run, confirming the new view is purely additive. Re-ran `build_llc.py`
— `llc_implementing_act` route/tier counts and the 13/74 `cites_cc_foundation`
superseded count are unchanged. `pyflakes build_links.py app_hierarchy.py
app_llc.py`: clean. `python verify_transfer.py`: **all checks green**, same
INFO-line numbers as 2026-09-20 (248 acts provably superseded, 494 stale
realization edges) — this feature is a new, additive currency signal, not
a change to whole-act supersession, so nothing there was expected to move
and nothing did.

**Scope explicitly not done today**: `page_structure()` in
`app_hierarchy.py` (the structural tree view) still shows only realizing-act
counts with no currency signal of any kind — a future session could extend
this same view there, but that page's existing scope is Civil Code
structure, not third-party acts' own internal currency, so it wasn't part
of today's "surface `target_locator`" brief.

### 2026-09-20 — Extractor rotation: built the gold-set annotation/scoring layer (`gold_citations.json` + `score_gold.py`), baseline precision/recall 100%/100% on 50 hand-verified windows

Rotation note from 09-19 said Extractor or Data currency was due (each two
of the last five). Checked the Extractor backlog: "Build the gold set" was
still open after `build_gold_sample.py` (09-15) — a reusable sampler
existed, but nothing turned its output into a persisted score. That gap
was explicitly flagged 09-17 as worth revisiting given hypothesis-driven
sampling's 9/9 hit rate, so picked it up rather than drawing yet another
one-off sample to read and discard.

**Environment note first**: this session started from a fresh clone with
neither `duckdb` (Python package) nor `git-lfs` installed, and
`articles/train-00000-of-00001.parquet` was still an unresolved LFS
pointer (134 bytes, not the real 163MB file) — `build_gold_sample.py`
failed immediately with a DuckDB "no magic bytes" error. Installed
`git-lfs`, ran `git lfs pull`, and `pip install duckdb`; unrelated to
today's actual work but recording it in case a future session hits the
same cold-start failure and wastes time suspecting a corpus bug instead.

**What was built**: `gold_citations.json` — 50 hand-verified anchor
occurrences (drawn via `python build_gold_sample.py --seed 20260920`, half
"hit" windows where `extract()` produced a pinned citation, half "empty"
where it didn't), each read against the raw Uzbek text and against
`citation_extractor.py`'s own stop-word/anchor logic, not just skimmed —
and `score_gold.py`, the scorer. Added `anchor_start`/`anchor_end` to
`build_gold_sample.py`'s output (small, additive) so the scorer can
recompute exactly which citations a specific anchor occurrence produces,
instead of matching on approximate window text.

Two scoring-design decisions, both load-bearing for why the number is
trustworthy rather than accidentally lenient:
1. **Precision is scored per-anchor; recall is scored against the whole
   field's `extract()` output.** The 09-17 log entry found a false alarm:
   a citation that looked like a recall miss in one anchor's local display
   window was actually produced by `extract()`, just attributed to a
   *different*, nearby anchor occurrence in the same text. Scoring recall
   against each anchor's own bucket (the same-scope choice a naive gold
   set would make) would silently reproduce that exact false alarm inside
   the "regression-testable" score meant to prevent this kind of mistake.
   Verified the asymmetry matters by construction, not just in theory: the
   scorer's recall check walks `all_cites` from a full `extract()` call on
   the entire field text, matching by signature tuple
   `(target_kind, article, struct_number, section_number, listing)`,
   independent of which anchor produced it.
2. **`qism` (article-part) is tracked but excluded from the headline
   score.** It isn't consumed by any downstream table/view yet (Backlog:
   "Qism-level grain"), and gold_id 6 is a concrete example of why folding
   it in would be misleading: the text reads "642-moddasining ikkinchi va
   uchinchi qismlari" (parts two AND three), but `extract()` has a known,
   already-tracked gap (Backlog, found 2026-09-15) where a qism range
   collapses to just its last ordinal — `Citation.qism` is a single string
   field, structurally incapable of holding "parts two and three" today.
   Recording that as a precision failure in the headline number would
   conflate a load-bearing article-level bug class with a
   known-non-load-bearing grain limitation that already has its own
   backlog entry — so `expected` records what the current `Citation`
   schema can express, and the gap is documented in the gold record's
   `notes` field and in `score_gold.py`'s separate, non-headline
   `grain_mismatch` counter instead.

**Baseline result**: `python score_gold.py` → **precision 68/68 (100%),
recall 68/68 (100%)**, 0/50 drift, 0 qism grain mismatches surfaced today
(gold_id 6's is pre-recorded as a known limitation, not a fresh mismatch,
since `expected` was built to match what the schema can express — see
above). All 50 read cases held up, including non-trivial ones: 8 plenum
resolution titles correctly reduced to a bare `act` citation via the
`qarori`/`axborotnoma`/`№` stop words (a resolution *about* the Code isn't
a Code article, and the Code's own gazette-publication parenthetical
listing "56-modda, 241-modda, ..." is a bibliographic locator, not a list
of cited articles — both previously-fixed classes of bug, still holding);
6 `self_reference` anchors with no pinned article number correctly
producing *no* citation at all (confirmed this is `extract()`'s deliberate
design — the bare-`act` fallback only fires for
`kind == 'fuqarolik_kodeksi'`, not `self_reference`/`fk_alias`, since an
article-less "this Code provides for..." inside the Code's own text isn't
a meaningful citation edge the way an external act naming the Code is);
2 cases where a second, different code's own article list sitting in the
same sentence right after the Civil Code's citation is correctly excluded
by `RE_STOP`'s `kodeksining`/`Qonunining`. No new bug found — the first of
10 sampling sessions (09-04 through 09-20) not to. That's a real,
informative result the scoring layer now preserves as a comparable number
instead of losing it the way every prior session's read-and-discard
sample would have.

**Scope explicitly not done today**: only 50 of ~3251 candidate anchor
windows (2599 hit + 652 empty, corpus-wide) are annotated — this is a
first batch establishing the scoring layer and a baseline, not corpus-wide
coverage. See Active threads and Backlog for what a future Extractor
session should do with it (grow the set with a new `--seed` batch, or add
a targeted record any time a new bug is found and fixed, so fixes become
permanent regression checks).

`verify_transfer.py`: all checks green, unaffected (`corpus.duckdb` was
not touched — this thread's artifacts are two new/modified pure-Python
files plus a committed JSON gold set, no pipeline script ran against the
database). `python citation_extractor.py`: 47/47 self-tests still pass.
`pyflakes score_gold.py build_gold_sample.py`: clean.

### 2026-09-19 — Cleanup rotation: ran a static-analysis pass (`pyflakes`) over the whole repo, found and fixed 9 real dead-code/import issues across 5 files

Rotation note from 09-18 said next session should prefer Cleanup (it hadn't
had an actual working session, only two re-confirms of empty, since
2026-09-07). Checked the Backlog's Cleanup section first — genuinely empty,
every item struck through — so this session's job was to invent a new
angle rather than pull a queued item, per the brief.

First confirmed 09-18's two commits (`3e61579`, `676e8f0`) had actually
reached `origin/main` this time (`git fetch origin main` showed local
`main` was just a stale cached ref, one `fetch` away from matching
`origin/main` exactly) — no recurrence of the "commit sound but branch
pointer left behind" risk 09-18's log entry flagged, just ordinary
freshclone staleness. Also had to `apt-get install git-lfs` and
`git lfs pull` before anything could run — the raw parquet arrives as a
134-byte LFS pointer in a fresh container, same gotcha 09-18 hit and noted;
recording it again since it's now happened on back-to-back days and is
clearly not a one-off. Worth a `SETUP.md`/README note for future sessions
so it doesn't have to be rediscovered by a failing `InvalidInputException:
No magic bytes found` each time.

New angle: rather than re-grepping for `execute(f"...")` patterns (already
fully audited 2026-09-07/09-10, still clean today — every f-string
interpolation is one of `PARQUET`/`CC_GENERAL_PART`/`LLC_LAW_CURRENT`-style
hardcoded constants, confirmed again by re-reading all 27 occurrences
across the repo, zero data-derived values), ran `python3 -m pyflakes *.py`
across the whole repo — a class of bug the manual f-string audits and
gold-sample reading never targeted: dead locals, unused imports, and
accidental f-strings with nothing to interpolate. **9 findings, all real,
none false positives** (checked each by hand — unlike the AST-based
same-file usage-count script tried first, which threw 2 false positives on
cross-module calls before being discarded in favor of `pyflakes`):

- `build_llc.py`: `run_id = datetime.now(...)` computed in `main()` but
  never used — unlike its siblings `build_corpus_db.py` and `build_links.py`,
  which both compute an identical-shaped `run_id` *and* actually log/persist
  it (`extraction_run.run_id`, `link_edge.run_id`) for build provenance.
  `build_llc.py` has no such provenance table and never referenced the
  variable again — vestigial, almost certainly copy-pasted from
  `build_links.py`'s `main()` boilerplate when the file was created and
  never wired in. Removed it and the now-unused `datetime`/`timezone`
  import rather than half-wiring provenance tracking for one script when
  the other two don't share a table for it either — that would be a new
  feature, not a cleanup, and out of today's scope.
- `build_llc.py`: `found_arts = sorted({a for s in FOUNDATION.values() ...})`
  computed right before the `cites_cc_foundation` INSERT but never
  referenced in the query, which instead filters via `llc_norm.layer =
  'foundation'` (a join-based approach). Leftover from an earlier,
  presumably explicit-filter implementation. Removed.
- `app_hierarchy.py`: `by_id = {n[0]: n for n in nodes}` in `page_structure()`
  built but never read (the function only needs `kids`, the parent->children
  map, built separately). Removed.
- `app_llc.py`: `import re` unused (no `re.` call anywhere in the file).
  Removed. Also `st.subheader(f"Tier 3 · ...")` — an f-string with no
  `{}` placeholder, harmless but wrong; dropped the stray `f`.
- `parser.py`: `import os` unused (`os.path`/`os.*` never called — the file
  uses `pathlib.Path` throughout instead). Removed. Also one
  `print(f"[ERROR] ...")` with no placeholder — dropped the stray `f`,
  same class as `app_llc.py`'s.
- `test_transfer_e2e.py`: `import json` and `import sys` both unused
  (`os`/`re`, imported alongside, are genuinely used — checked before
  touching either).

Measured before/after: `python3 -m pyflakes *.py` — 9 issues -> 0
(`exit=0`). Every removed local was a pure dead-end (never read again in
its own function); none were "removed but should have been used" bugs
disguised as dead code, confirmed for the two most suspicious ones
(`build_llc.py`'s `run_id`/`found_arts`) by reading the surrounding query
and checking neither the schema nor the WHERE/JOIN clauses ever needed
them.

Verified live, not just by diffing: re-ran `python3 build_llc.py` (the one
script whose function body changed, not just an import line) against the
existing `corpus.duckdb` — output identical to before the edit (8 stages,
100 `llc_norm` rows, 132 `llc_implementing_act` rows, same per-stage/per-tier
breakdown) — then reverted the resulting `corpus.duckdb` diff (`git checkout
-- corpus.duckdb`) since the content was byte-for-byte equivalent in every
table's row count and the diff was pure re-serialization noise, not a real
data change; no reason to carry a 52MB binary diff for a no-op rebuild.
Also ran `python3 test_transfer_e2e.py` (14/14 pass, unaffected by the
import removal) and started both `app_hierarchy.py` and `app_llc.py` under
`streamlit run` and drove them with Playwright: `page_structure()` (the
`by_id` removal) renders the full structural tree with no exception;
`page_norm()` (the f-string fix) renders "Tier 3 · LLC Law — the stage
that specialises it" correctly for stage 1. One test-only wrinkle, not a
real bug: running both apps concurrently against the same `corpus.duckdb`
in this sandbox hit `app_hierarchy.py`'s own documented read-write/read-only
fallback in a way that briefly locked `app_llc.py` out
(`_duckdb.IOException: Could not set lock`) — resolved by not running both
against the same file at the same instant, not a code change; the two apps
were never designed to be launched simultaneously against one file from a
single test harness, only used one-at-a-time in this session. `python3
verify_transfer.py` — all checks green, same as before any edit.

**Decision: this closes today's Cleanup session with a concrete, measured
artifact** (a repeatable `pyflakes *.py` check, now 0 issues) rather than
"nothing found" — Cleanup's last two sessions (09-07, 09-10) were genuine
re-confirms of an already-drained backlog; this one found real, if minor,
new material by widening what "cleanup" means (static analysis, not just
manual re-reading of the same execute-f-string pattern). Worth running
`pyflakes *.py` again after any future session that adds new files or
touches these — cheap, fast, and just found 9 real issues on a repo that
had already had two "nothing left" cleanup passes.

### 2026-09-18 — found and fixed a whole-act/partial-repeal conflation and a silent join fan-out in `v_act_currency`; brought act-level currency badges to the General Part explorer

Rotation: 09-17 Extractor (its third of the last four sessions). Standing
note said next should prefer Data currency or Cleanup; Cleanup had nothing
new since 09-07/09-10's re-confirms, so picked Data currency. Also first had
to fast-forward and push a fully-verified but unpushed commit
(`3e61579`) left behind from 09-17's session — its local `main` branch was
detached and never reached `origin/main`; confirmed it was sound (`git lfs
pull` had to run first, since the raw parquet's LFS pointer hadn't resolved
in this fresh container either) before pushing. Worth flagging in case it
recurs: something about how a prior session ends can leave the branch
pointer behind the last commit even though the commit itself is already on
`origin` — not investigated further today since the actual risk (an
unpushed commit silently lost) didn't materialize, but a future session
should double-check `git fetch && git log origin/main` before assuming
local state reflects what shipped.

Picked up the open half of "Propagate currency into the LLC dossier's
implementing-acts list" (closed 2026-09-16) — the General Part explorer,
`app_hierarchy.py`, never got the same act-level currency badge the LLC
dossier has, despite covering 386 articles vs. the LLC's single slice.
Before writing any UI code, measured the underlying numbers directly against
`corpus.duckdb` rather than trusting the standing "357 acts provably
superseded" / "1115 stale realization edges" INFO stat from
`verify_transfer.py` — and building the join for the new feature
(`LEFT JOIN v_act_currency`) immediately threw `InvalidInputException: More
than one row returned by a subquery`, which is what actually surfaced the
first bug: `v_act_currency.doc_id` isn't unique. 483/24,750 rows are
duplicates, some doc_ids appearing up to 35 times.

Root-caused by reading raw text, not by staring at the SQL. The worst
offender, doc -5388561 (an omnibus 2021 law, OʻRQ-683), had 35 different
later acts each listed as "repealing" it. Pulling the actual clause text
(not the view) showed why: each item reads "...gi OʻRQ-683-sonli
Qonunining (Oʻzbekiston Respublikasi Oliy Majlisi ... Axborotnomasi,
2021-yil, 4-songa ilova) 132-moddasi ... kuchini yoʻqotgan deb topilsin" —
i.e. only Article 132 of OʻRQ-683 lost force, not the whole act; 34 other
later acts each separately voided one other article of the same 2021
omnibus law over the following years. `repeal_clause`'s extraction only
ever matched act-level (date, title), with no check for a trailing article
qualifier, so every one of these got recorded identically to a genuine
whole-act repeal. Measured corpus-wide with a standalone regex (matching
`repeal_clause`'s own `re_item`, then checking the text right after each
resolved title/number for `\d+-(?:modda|qism|band|bob|paragraf)`, skipping
over the intervening bibliographic gazette-citation parenthetical which
itself often contains an unrelated "N-modda" that would otherwise produce
false positives): **398/885 (45%)** of all repeal-list items are actually
partial, article-level repeals, not whole-act ones. Confirmed the extractor
side is sound by reading every item inside one real host row's own list end
to end (doc -8151376, the LLC Law's own final repeal clause): items 1-2 are
genuine whole-act repeals of the two old LLC laws (no trailing qualifier),
items 3-21 (19 of them) each void exactly one unrelated act's single
article (all with the qualifier) — a clean, unambiguous split, not a
borderline judgment call. Random-sampled 8 more hits from elsewhere in the
corpus (seed 42): all 8 confirmed the same "Act X's article N loses force"
reading, no false positives from the qualifier regex.

Second bug, found while designing the fix for the first: even restricting
to whole-act-only repeal items, 96/185 resolved `dst_doc_id`s still had more
than one repeal_clause row (max 4) — a handful of old Soviet-era acts
(e.g. a 1992 sports law, doc -10860) are redundantly re-declared repealed by
more than one later cleanup act. So `v_act_currency`'s `LEFT JOIN
repeal_clause` was always going to fan out even after fixing bug 1, just
less severely — meaning any downstream `JOIN v_act_currency ON doc_id`
(both apps do this) was silently multiplying whatever it counted. Confirmed
this was live, not just theoretical, in `app_llc.py`'s `page_currency()`
"Superseded acts still feeding the realization graph" table (`GROUP BY
act, count(*) AS edges` through that same join) — checked one row directly
(-55558, the housing-policy act, 52 raw `link_edge` rows) and confirmed
`v_act_currency` had exactly 1 row for it post-fix, so the displayed count
now equals the raw count instead of some join-inflated multiple.

Fixed both at the source in `build_links.py`. (1) `repeal_clause` gained a
`target_locator` column (NULL = whole act; else the matched "N-moddasi"/
"N-bandi" text) computed via a new regex during the same extraction loop
that already builds each clause — additive schema change, `INSERT` count
bumped from 9 to 10 placeholders. (2) `v_act_currency`'s view now joins a
`whole_repeal` CTE that filters to `target_locator IS NULL` and dedupes
with `QUALIFY row_number() OVER (PARTITION BY dst_doc_id ORDER BY
cited_date) = 1` (earliest repeal wins for the rare redundant-repeal case).
Verified the view is now genuinely 1-row-per-`doc_id`: `24267` rows, `24267`
distinct `doc_id`, `0` duplicates (was 483 duplicate rows across 24,750
total).

Reran `build_links.py`: `repeal_clause` unchanged at 885 items/840 resolved
(scope classification doesn't touch resolution), now logs "487/885 void the
whole cited act; 398 name a specific article/part of it". Reran
`build_llc.py`: `cites_cc_foundation` route's superseded count dropped
15 -> 13/74 (2 acts were false positives from the partial-repeal bug); the
2001 LLC Law itself (doc -22525, the load-bearing `verify_transfer.py`
check) is still correctly `superseded` — it's a genuine whole-act repeal,
confirmed by hand in the same doc -8151376 list read above (item 1, no
qualifier). Corpus-wide: "acts provably superseded" 357 -> **248** (-31%,
109 fewer), "stale realization edges" 1115 -> **494** (-56%, 621 fewer) —
both numbers were substantially overstated before today, not just off by a
rounding error.

With the data fixed, built the originally-scoped feature: `page_article()`
in `app_hierarchy.py`'s "Realization pyramid" now joins `v_act_currency`,
shows a 🔴 badge + a `st.error("Superseded by: ...")` inside the expander for
each superseded realizing act, a per-tier "(N acts · M superseded)" count,
and a "Hide superseded acts" toggle. Chose **off** by default — the
opposite of `app_llc.py`'s `value=True` — because this measurement also
found **4** General Part articles (21, 62, 290, 291) whose realizing acts
are *exclusively* superseded; defaulting to hidden would silently show
"nothing cites this" for those 4 instead of "everything that once cited
this is now dead law". Article 62 is exactly the LLC's own Civil Code
anchor that 2026-09-16 already flagged as having zero surviving
`cites_cc_foundation` evidence in the LLC slice — this confirms the same
fact holds at the whole-corpus level, not just within the LLC's narrower
foundation-article set. Added a warning banner (mirroring `app_llc.py`'s
existing "every citation was filtered out" pattern) for the case where the
toggle empties a tier.

Verified live with Playwright against a running `streamlit run
app_hierarchy.py`: screenshotted the 🔴 badge and its `st.error` on Article
48's Tier 3 list (a real superseded railway-transport act among 6 live
ones), the toggle correctly dropping the tier's act count when flipped, and
Article 62 showing 2/2 superseded acts with the "all realizing acts are
superseded" warning once hidden. Also re-verified `app_llc.py` still loads
and its `page_currency()` table now shows correct, non-inflated edge counts
(spot-checked -55558 by hand: 52 raw `link_edge` rows, 52 shown, 1
`v_act_currency` row — was silently able to be wrong before, though this
specific act happened not to be one of the fanned-out ones).
`verify_transfer.py` stays green; the `sup`/`stale` INFO lines recompute
from the same query against the corrected view, so no check needed
touching. This closes today's thread — `repeal_clause.target_locator` is
captured but not yet surfaced in either app (see Backlog).

### 2026-09-17 — two real corpus-wide extractor bugs fixed via a fresh gold-sample round; one false alarm rejected; one new backlog item captured

Rotation: 09-15 Extractor, 09-16 Data currency (closed). Standing note said
next should prefer Extractor or Cleanup (Data currency had run three of the
last four sessions); Cleanup was re-confirmed empty as recently as 09-16
with nothing new to drain, so picked Extractor — continued the "read a
fresh sample, hypothesize, measure" loop via `build_gold_sample.py` rather
than building the still-open scoring-layer backlog item (see Backlog
"Build the gold set"): that item is real and worth doing, but sampling
alone had paid off in 8/8 prior sessions, so tried it once more before
switching approaches.

**Environment**: same drill as every prior session — `apt-get install
git-lfs`, `git lfs install --local && git lfs pull` (materializes the real
163MB parquet from its LFS pointer stub; `corpus.duckdb` was already a real
DuckDB file, no stub issue this time), `pip install duckdb pyarrow numpy
streamlit playwright pytest`. Baseline `verify_transfer.py` was green
before any change.

**Drew a fresh 50-window sample** (`--seed 20260917`, disjoint from every
prior seed used) and read all 50 by hand (25 "hit" windows for precision,
25 "empty" windows for recall, per the tool's own stratification). Two
candidate bugs stood out and were both confirmed genuine after independent
corpus-wide measurement against the raw parquet; one more candidate was
investigated and correctly rejected as a false alarm; one more was measured
and logged as a new backlog item rather than fixed.

**Bug 1 — a doubled en-dash range collapses to its own trailing endpoint.**
Window (gold_id 16, row 29535): "Fuqarolik kodeksining 744 –– 748-moddalari"
— two literal U+2013 en-dash characters back to back with no space between
them (confirmed at the codepoint level; a LexUZ export artifact, not a
different separator). `RE_CLAUSE`'s inner list/range separator and
`RE_RANGE_PAIR` both used `[-–—]` — exactly one dash character. Hitting the
second dash where a digit was expected silently failed the whole match
attempt starting at "744", so the regex engine backtracked to match "748"
alone as an unrelated single citation: 744-747 vanished with no edge at
all, not even a dangling one. Searched the whole corpus for
`\d+\s*[–—]{2,}\s*\d+` (84 raw hits across all three source fields) and
manually classified every one by whether it sits inside a genuine Civil
Code anchor (`Fuqarolik kodeksi`/`FK`/`self_reference` inside doc -111189
or -180552) versus some other code's own range (Labor Code, Criminal Code,
Administrative Liability Code, a Customs Code's *own* "mazkur Kodeksning"
self-reference, etc. — all correctly out of scope for this extractor) or a
non-citation number run (years, percentages, gazette table positions):
**16 clauses corpus-wide** are genuine Civil Code range citations hitting
this bug. Fixed by widening both regexes' dash class from `[-–—]` to
`[-–—]+`. Verified each of the 16 individually by running `extract()` on
the full field text before/after the fix: every one now expands to its
full range instead of collapsing to one endpoint (e.g. row 29535's
744→748 now yields all 5 articles instead of just 748; row 25211's
437→456 now yields 20 articles instead of 1).

**Bug 2 — "Fuqarolik Kodeksning" (missing the "-i-" thematic vowel) never
anchors at all.** While corpus-scanning for Bug 1, row 7437 stood out:
"Oʻzbekiston Respublikasi Fuqarolik Kodeksning 260 –– 263-moddalari"
produced **zero** citations from `extract()` — not even a bare act-level
one. `RE_ANCHOR_CC` required the literal substring "kodeksi"
(`Fuqarolik\s+kodeksi\w*`); "Kodeksning" is "kodeks"+"ning" with no "i", so
the anchor regex never matched at all — the whole clause was invisible,
not merely coarser. This is the *anchor*-side twin of the "kodeksning"
*stop-word* gap already fixed 2026-09-15 (that one was about some OTHER
code naming itself "...kodeksning" and wrongly attracting a nearby Code
citation into itself — same missing-vowel surface form, opposite failure
mode: there it was a false attribution to guard against, here it's a
missing anchor to add). Measured corpus-wide
(`Fuqarolik\s+[Kk]odeksning\b`): exactly **3 rows / 4 raw occurrences**,
all genuine, all previously producing zero citations (row 7437: articles
260-263, doubly affected since it's also a doubled-dash range needing
Bug 1's fix; rows 32791/32792: articles 54 and 50). Fixed by extending
`RE_ANCHOR_CC` to `Fuqarolik\s+kodeks(?:i\w*|ning)`. Confirmed this doesn't
reopen the existing "kodeksning naming another code" stop-word self-test
(still passes unchanged): that case requires "Ma'muriy javobgarlik
to'g'risidagi kodeksning", not "Fuqarolik" immediately before "kodeks", so
the two patterns don't collide.

**False alarm investigated and rejected.** Gold_id 27 (row 5291) looked
like a third bug at first glance: "Fuqarolik kodeksi (bundan buyon matnda
Fuqarolik kodeksi deb yuritiladi) 549-moddasi" sampled as a bare act-level
citation with no article number — suggesting the alias-definition
parenthetical breaks the lookahead to the real article, a plausible bug
given "FK" alias definitions are a documented, handled pattern elsewhere.
Reran `extract()` on the row's *full* text (not the gold-sample's
per-anchor display slice) and found article 549 (with "birinchi qism")
correctly present. Root cause of the false alarm: the phrase "Fuqarolik
kodeksi" appears *twice* in this sentence — once at the very start, once
again inside its own alias definition — so `RE_ANCHOR_CC.finditer` finds
two separate anchor matches, and the real article citation attaches to the
*second* one. `build_gold_sample.py`'s display window cuts each sampled
anchor's shown slice at the *next* anchor's start position (for
readability), so the first anchor's sampled record correctly shows nothing
attached to *it* — but `build_links.py` calls `extract()` once on the whole
row and doesn't care which anchor index produced a citation, so this was
never a real recall gap. Recorded here (and in the Backlog "Build the gold
set" item) as a concrete methodology note: always verify a sampled "empty"
against the full-text `extract()` output before concluding it's a miss.

**Measured corpus-wide impact.** Added 2 new self-test cases (one per
fix) to `citation_extractor.py`: **47/47 self-tests passed** (was 45).
Reran `build_links.py`: `link_edge` 9402 -> **9531 (+129 edges)** — matches
the hand-computed expected total from the 16+3 confirmed rows closely
(≈126 from Bug 1's range expansions, ≈3 from Bug 2's previously-zero
rows). Reran `build_llc.py` next per the pipeline order, since `link_edge`
changed underneath it: the `FOUNDATION` dict itself is untouched (curated,
off-limits by design), but the *acts* citing it are more complete — two
acts citing the range "49 –– 57" (all 9 articles land inside LLC stage 8's
own foundation set, 39-59) now produce 9 `link_edge` rows each (articles
49-57) instead of 1 (article 57 only): "Kreativ iqtisodiyot toʻgʻrisida"
(2024, in-force) and the 2016 Customs Code. Confirmed directly in
`llc_implementing_act`: the Creative Economy Act's `n_hits` for the
`cites_cc_foundation` route now reads **9**, up from what would have been
1 before today's fix. Verified live, not just from the diff: booted
`app_llc.py` (`streamlit run --server.headless`) and drove it with
Playwright — "Follow a norm down" -> Stage 8 -> CC article 49 renders
"Implementing acts: 32" without error; booted `app_hierarchy.py`'s article
explorer the same way and confirmed it still renders citation counts
correctly (General Part only, per the existing M0 scope decision — the
744-748 and 260-263 fixes are Special Part articles, outside
`norm_unit`'s populated scope, so not independently spot-checkable in that
app, which is expected and unrelated to today's fix). `py_compile` clean
on `app_llc.py`, `app_hierarchy.py`, `build_links.py`, `build_llc.py`,
`citation_extractor.py`. Reran `measure_extractor_recall.py`: still 0 real
misses on article/chapter recall; qism/band residual unchanged at 7/630
(untouched by today's fixes, as expected — different bug class). Reran
`test_transfer_e2e.py`: 14/14 passed (independent markdown-parser
implementation, unaffected as expected).

**Full re-verification.** `python verify_transfer.py`: **VERIFICATION
PASSED — all checks green**, same reconciliation detail as every prior
session (10 pre-existing `db_only`/`md_only`/`structure_missing_articles`
gaps, 1 ambiguous-key superscript article, 1 documented version-drift
case — nothing new introduced). Checked `git diff --stat corpus.duckdb`:
binary-only diff, no schema change (only row counts grew in `link_edge`
and the `llc_implementing_act`/`v_llc_realization` tables derived from
it), so no need to touch either app's queries.

**Decision: ship both extractor fixes; log the false alarm and the new
backlog item rather than act on them.** Both fixes are minimal, targeted
regex widenings with a documented root cause, a measured corpus-wide
scope, and a verified before/after at both the extractor and the
downstream-table level; the false alarm is recorded so a future session
doesn't re-investigate the same alias-parenthetical pattern from scratch;
the new "boʻlim" (Part-level citation) gap is recorded with its measured
count (6 occurrences) so a future session can decide with data whether
that ever justifies a new structural grain, rather than guessing.

### 2026-09-16 — closed the LLC currency-default backlog item; found and fixed two real fan-out bugs it exposed

Rotation: Extractor ran 09-15, note said next should prefer Data currency or
Cleanup. Picked the one open half of the "Propagate currency into the LLC
dossier" backlog item: article-level currency was already wired into both
apps 2026-09-14, but whether `page_acts`/`llc_implementing_act` should gate
"implements" by currency *at the data layer* by default (instead of today's
opt-in `hide_dead` UI toggle) was explicitly left as "deserves its own
measurement pass" rather than decided either way.

**Environment**: local `main` was again a stale detached-HEAD pointer 1
commit behind `origin/main` (same pattern as 09-13/09-15) — `git fetch
origin main && git checkout -B main origin/main` fixed it, zero data loss,
confirmed by comparing `git log origin/main` against the detached HEAD
before touching anything. `git-lfs`/the real 163MB parquet and
`corpus.duckdb` were both already materialized correctly in this container
(no LFS-pointer-stub issue this time). Installed `duckdb`, `pyarrow`,
`numpy`, `streamlit`, and `playwright` (python bindings only — the browser
itself was pre-installed) via pip. Baseline `verify_transfer.py` was green
before any change.

**Measured the actual question first.** Queried `llc_implementing_act`
directly: for the `cites_cc_foundation` route, 74 acts total, 15 (20.3%)
`superseded`; weighting by the table's own `n_hits` gave a much higher
41.6% (153/368) of "evidence weight" from dead law — a big enough gap
between the act-count and hit-count percentages to be suspicious on its
own, so before drawing any conclusion from it, checked *why* they diverged
rather than reporting the raw number.

**Bug found while checking that divergence: `build_llc.py`'s `n_hits`
was inflated by a join fan-out, not a real reflection of citation count.**
Two Civil Code foundation articles, 45 and 62, each anchor *two* different
LLC-Law stages (confirmed via `llc_norm`: article 45 founds stages 1 and 4,
article 62 founds stages 1 and 3 — both legitimate, curated `FOUNDATION`
dict entries, not a data error). `llc_implementing_act`'s INSERT joins
`link_edge` to `llc_norm` on `article_number` and groups by
`(doc_id, tier, title, date, status)` — not by article or stage — so for
any act citing article 45 or 62, the join produces one row per (edge,
stage) pair, and `count(*)` counted every duplicate. Measured the real
scope by rewriting the same join with `count(DISTINCT e.edge_id)` (the
table's true unique-citation key) instead of `count(*)`: **9 acts had
inflated `n_hits`** (e.g. one act's badge read "34 hit(s)" when the real
count was 16), total `cites_cc_foundation` `n_hits` 368 -> 307 (-16.6%).
Fixed by changing `count(*)` to `count(DISTINCT e.edge_id)` in
`build_llc.py`'s INSERT query, with a comment recording why (the fan-out
is a real, intentional multi-stage mapping, not something to "fix" at the
`llc_norm` level). Re-ran `build_llc.py`: `llc_implementing_act` totals for
`cites_cc_foundation` now read `59 no-repeal + 15 superseded = 74 acts`,
`213 + 94 = 307 n_hits` — confirmed against the independent
`count(DISTINCT edge_id)` measurement query, exact match, not just a
plausible-looking number.

**Second bug, same root cause, in `app_llc.py`.** `page_norm`'s "Below ·
acts implementing this Code article" section reads `v_llc_realization`
`WHERE cc_article = ?` with no stage filter and no `DISTINCT` — since that
view's own `SELECT DISTINCT` includes `stage_no`, the same citation to
article 45 or 62 produces two physically distinct rows (identical except
for `stage_no`, which this particular query doesn't even select), so every
citation to those two articles was silently rendered *twice*: once in the
"Normative citations" metric (not deduped by act, so double-counted for
real when both duplicate rows were normative-kind — confirmed article 45's
own metric read 2 when the true count was 1) and once as a literal
duplicate expander in the citation list below (confirmed live: article
62's page showed 6 raw rows collapsing to 3 real citations from 2 acts).
Fixed by adding `SELECT DISTINCT` to that one query (safe because it
doesn't select `stage_no`, so nothing downstream depends on preserving the
per-stage duplicate). Checked every other `llc_norm`-foundation join in
both apps and `verify_transfer.py` for the same fan-out risk before calling
this done: seven other call sites either filter by a single `stage_no`
already (`page_skeleton`, `page_norm`'s own special-law list) or already
wrap the foundation-article list in `SELECT DISTINCT article_number,
article_title` before joining `v_article_currency` (`page_currency`'s
amendment-activity table) — only these two were actually affected.

**Verified live, not just via SQL.** Booted `app_llc.py` with `streamlit
run --server.headless` and drove it with Playwright: on "Follow a norm
down" -> stage 1 -> article 62, confirmed "Implementing acts: 2,
Superseded acts: 2" and, with the default `hide_dead=True` toggle, the
"every citation was filtered out" warning (correct — both are dead);
toggled "Hide superseded acts" off and confirmed exactly 3 expanders
render (not 6) with two distinct acts named. On "Implementing acts" ->
`cites_cc_foundation`, confirmed the visible per-act "N hit(s)" badges no
longer reflect the pre-fix inflated counts. `py_compile` clean on
`app_llc.py`, `app_hierarchy.py`, `build_llc.py`.

**Answered the original question with the corrected numbers.** Post-fix,
`cites_cc_foundation`: 74 acts (15 superseded, 20.3% — unchanged, this was
never wrong at the act level) but now 94/307 hits (30.6%) from superseded
acts, not the pre-fix 41.6% — a real number, not the artifact the bug had
been producing. More decisive than the aggregate, though: **article 62
itself** — `Masʼuliyati cheklangan jamiyat`, the Civil Code's own
definition of the institution this entire dossier is about — has **zero**
non-superseded implementing evidence (2/2 acts, all 3 real citations,
100% superseded); article 41 is the same (1/1, 100%). **Decision: do not
gate "implements" by currency at the data layer by default.** If
`llc_implementing_act`/`v_llc_realization` excluded superseded evidence at
the source instead of leaving it to an opt-in toggle, the dossier's single
most central article would show no implementing acts at all, with no way
for a reader to recover the (real, informative) evidence that used to
exist — worse than today's design, where the toggle already defaults to
hiding it but a reader can flip it back on. This closes the backlog item's
open question with a measured decision instead of leaving it pending
indefinitely.

**Also, opportunistic cleanup**: found `demo_llc.py` while grepping for
`v_llc_realization` consumers — a standalone walkthrough script hardcoding
a Windows path (`C:\uzbek-legal-corpus\corpus.duckdb`) that doesn't exist
in this or any Linux environment, same unrunnable-dead-script pattern as
the four scripts removed 2026-09-07. Confirmed zero references anywhere in
the repo before deleting.

**Full re-verification.** Rebuilt only `build_llc.py` (no full
`build_corpus_db.py` rebuild — nothing upstream of it changed); `git diff
--stat corpus.duckdb` shows the expected binary-only diff, same byte size.
`python verify_transfer.py`: **VERIFICATION PASSED — all checks green**,
same reconciliation detail as every prior session (the 10 pre-existing
`db_only`/`md_only`/`structure_missing_articles` gaps, the 1 ambiguous-key
superscript article, the 1 documented version-drift case — nothing new).
Grepped for `n_hits` corpus-wide first: only `build_llc.py` (the fix) and
`app_llc.py`'s `page_acts` (reads the now-correct value, no code change
needed there) reference it.

**Decision: ship both fixes plus the demo_llc.py deletion.** Each
measured before/after against an independent reimplementation of the
query, not just accepted from an aggregate count; the citation-list fix
verified live in the browser, not just read from the diff.

### 2026-09-15 — three real extractor bugs found via a new reusable gold-sample tool, plus a confidence-hierarchy fix the third one exposed

Rotation: three Data-currency sessions in a row (09-11 through 09-14, the
amendment-chains thread), so rotated to Extractor per the standing note.
Environment needed the usual `apt-get install git-lfs && git lfs install
--local && git lfs pull` before the parquet was real data, plus `pip install
duckdb pyarrow`. Also found (and immediately fixed) that this container's
local `main` branch was a stale ref pointing at 6176a15 (2026-09-08) — a
detached-HEAD `git log` showed six *more* commits (09-09 through 09-14)
sitting on top of that as unreachable-looking history, which looked at first
like six days of unpushed work about to be lost. `git fetch origin main`
showed origin/main was already at 3e98727 (09-14) — the local branch pointer
had just never been fast-forwarded after some earlier checkout in this
container. `git merge --ff-only origin/main` fixed it with zero data loss;
recorded here because it cost real time to rule out before touching anything.

**Built `build_gold_sample.py` instead of another one-off unsaved query.**
Every prior "read real corpus text and hypothesize" session (09-04, 09-05,
09-08, 09-10, 09-12) wrote a throwaway script and discarded it. This one is
a small, seeded, stratified sampler over real anchor windows — the same
windows `citation_extractor.extract()` and `build_links.py` themselves
scan — split half "hit" (extractor produced a citation: checks precision)
and half "empty" (produced nothing: checks recall), reusable by any future
session with a fresh `--seed`. Drew a 50-window sample (seed 20260915, 25+25)
from 2579 hit-candidates and 668 empty-candidates corpus-wide, dumped to a
reviewable text file, and read every one by hand. Three windows surfaced
real, confirmable bugs; details below. This is the 8th session running where
reading a real sample this way has found at least one genuine, fixable gap
(qism/band 09-04, Qonun 09-05, doc_id 09-08, chapter+paragraph comma 09-10,
qonunning 09-12, and all three below) — see Backlog for what the tool still
doesn't do (no persisted hand-labeled verdicts, no fixed regression score).

**Bug 1 — "kodeksning" (genitive without the "-i-" thematic vowel) missing
from `RE_STOP`, same class of gap as "qonunning" (09-12) but for "kodeks".**
Gold-sample window (row 29029): "Fuqarolik kodeksining 166-moddasi,
... Maʼmuriy javobgarlik toʻgʻrisidagi **kodeksning** 60, 61-moddalari" — the
extractor was attributing articles 60 and 61 (Administrative Liability Code)
to the Civil Code, because `RE_STOP` had "kodeksi" and "kodeksining" but not
the genitive-without-"-i-" form. A second window (row 21715, doc -3517337,
`is_the_code=False`) showed the more common trigger: **"mazkur Kodeksning"
inside some other code's own text**, meaning that code, not the Civil Code —
`RE_ANCHOR_SELF` only treats that phrase as a Civil-Code self-reference when
the citing act genuinely *is* the Code, so everywhere else it needs to stop
the scan like any other act name, and didn't. Fixed by adding "kodeksning"
to `RE_STOP`'s case-insensitive group. **Measured corpus-wide by replicating
`build_links.py`'s own extraction loop with a monkey-patched `RE_STOP`
before writing the fix**: 32 clauses misattributed to the Civil Code across
21 rows, all read and confirmed genuine (one Administrative-Liability-Code
citation by name, twenty rows of another code's own "mazkur Kodeksning"
self-reference). **Zero collateral loss verified directly**: inside the
Civil Code's own text, every "ushbu/mazkur/shu Kodeksning" occurrence is
itself the `self_reference` anchor match (consuming the whole word including
"-ning"), so the new stop-word can never fire there — confirmed by checking
that none of the 21 affected rows have `doc_id` in `CC_DOCS`. Added 3 new
self-tests (another code named by role, `mazkur Kodeksning` inside a
different code's text, and a control confirming real self-reference still
works when `is_the_code=True`). **Rebuilt `build_links.py` and diffed the
full edge set against a snapshot of the pre-fix build** (not just the
aggregate count): 48 edges removed, 1 added. 47 removed are clean genuine
misattributions; 1 (row 19636, "Fuqarolik kodeksi Kodeksning 53-moddasi") is
a single, corpus-wide-unique garbled phrasing — read the full text and
couldn't tell whether "Kodeksning" there is a duplicate-typo of
"kodeksining" (making 53 a real hit this fix wrongly drops) or an
orphaned reference to some unnamed other code (making the drop correct);
logged as an honest, unresolved ambiguity rather than claimed as clean. The
1 added edge is the same documented "weaker act-level fallback when no
provision is left to pin" pattern used elsewhere (this session's own row
19636, once its specific article was excluded). `link_edge`: 6667 -> 6620.

**Bug 2 — a bare space instead of a hyphen before modda/bob/paragraf,
never matched at all.** Same gold sample, row 15444: "Fuqarolik
kodeksining 49 moddasi" (no hyphen). `RE_CLAUSE`'s separator before the unit
word was a mandatory `[-–—]`; LexUZ sometimes just leaves a space. Fixed by
accepting either a dash (unchanged) or bare whitespace with no dash at all
(never zero-width, so this can't start matching some unrelated digit run
glued onto another word). **Measured corpus-wide with a naive reimplementation
of the anchor/stop-word scan**: 21 real citations used only the space form,
confirmed genuine by reading 3 of them in full raw context (rows 10087,
15444, 24219 — plain "Fuqarolik kodeksining N moddasi", no ambiguity).
Added 3 self-tests. Rebuilt and diffed again: 62 edges added, 15 removed
(the same act-level-fallback-replaced-by-real-citation pattern as always,
confirmed by inspecting all 15). `link_edge`: 6620 -> 6667 (coincidentally
the same number as before Bug 1's fix, but a different, more correct set of
edges — verified via the diff, not assumed from the count matching).

**Bug 3 — a list with an embedded "N-M" sub-range never expanded, and
(found while fixing it) neither did one with an embedded "N — M" sub-range
once a third list item was present.** Same gold sample, row 45116: "ushbu
Kodeksning 393-395, 399, 402, 408, 412-moddalarida" — `_expand`'s range
detection only ever fired for a whole clause containing *exactly* two
numbers joined by an en/em dash; a list with more than 2 total values (any
mix of plain numbers and dash-joined pairs) fell through to keep only the
literal numbers actually present as separate list items, silently dropping
everything a sub-range implied. This turned out to affect **both** an
ASCII hyphen ("393-395") and, surprisingly, the en/em dash already used
for whole-clause ranges — e.g. row 46882's "mazkur Kodeksning 14, 236 — 258,
325 — 339-moddalari" (a real, common cross_references pattern in the Civil
Code's own text) was extracting only `[14, 236, 258, 325, 339]`, silently
losing all 34 in-between articles, purely because a *third* item ("14") sat
in the list alongside the two ranges. Rewrote `_expand()`: split into
top-level comma/va-separated items first, then expand each item that is
itself a dash-joined pair (ASCII or en/em dash, same 200-wide malformed-range
guard as before) independently, rather than trying to classify the whole
clause as one shape. Preserves every existing case exactly (verified via
self-tests: plain single "14", whole-clause range "299 — 310", plain lists,
and the malformed too-wide 173-1737 case, which still correctly degrades to
its two literal endpoints). Added 2 more self-tests. **Measured the narrow
ASCII-hyphen case corpus-wide first** (11 clauses) before writing the fix,
then **measured the actual fix's full impact by diffing the rebuilt edge
set**: 2783 edges added, 48 removed, across 242 distinct clauses — far more
than the 11 originally found, because of the em-dash discovery above.
Spot-checked the largest-impact clauses directly in raw text (row 46911's
"ushbu Kodeksning 234-352-moddalari", a clean 119-article self-reference
range; row 38838's several distinct multi-range citations to different
contract-law chapters, up to a 39-article span, all comfortably inside the
200-wide guard) — every one read as a genuine citation, not corpus noise.
`link_edge`: 6667 -> 9402.

**Found by Bug 3, not itself a citation-extraction bug: a confidence-hierarchy
violation in `build_links.py`.** Article 234-352's range includes 261, the
one article number in the whole corpus already flagged
`review_ambiguous_key` (261 collides textually with 26-1's concatenated
superscript form). This was the *first* article_text-sourced (normative)
edge ever to hit the ambiguous/dangling downgrade — every prior one came
from cross_references (editorial) — which broke `verify_transfer.py`'s AC7
check "normative evidence always outranks editorial for the same target
kind": the ambiguous downgrade capped this normative edge's confidence at a
flat 0.60, below cross_references' plain 0.80 `article` baseline, inverting
`BASE_CONFIDENCE`'s own documented design ("the act's own words outrank an
editorial pointer"). This is exactly what the task brief asks for — a
verify_transfer.py failure caused by today's own change, to be understood
and fixed (or reverted) before committing, not routed around. Diagnosed by
querying `link_edge` directly for the violating pair rather than guessing;
confirmed the fixed caps (0.60 ambiguous / 0.70 dangling) had simply never
been checked against cross_references' baseline before, because no
normative edge had ever needed them. **Fixed by making the caps field-aware**:
`article_text` (normative) ambiguous/dangling now cap at 0.85/0.88 —
comfortably above cross_references' un-downgraded 0.80 `article` ceiling —
while `cross_references`/`amendment_note` keep the original 0.60/0.70
(unaffected; those were never the side of the inequality that mattered).
Considered instead loosening the check to compare same-target-article rather
than same-`dst_kind`, but that would weaken a real, documented invariant
("the act's own words outrank an editorial pointer") to route around one
data point, rather than fixing the actual gap in the formula — kept the
check as-is and fixed the confidence formula instead. Reran `build_links.py`,
`verify_transfer.py`: **PASSED** on the first rerun after the fix.

**Full re-verification after all three fixes plus the confidence fix**:
`citation_extractor.py` self-tests 37 -> 45 (11 new, all passing).
`measure_extractor_recall.py`: still 0 real misses on article/chapter
recall across all three anchor kinds; qism/band attachment residual
unchanged at 7 (this session's fixes are orthogonal to that gap). Reran
`build_llc.py`: `cites_cc_foundation` tier-3 acts 59 -> 60 net (dipped to 58
after Bug 1 alone, since one previously-miscounted act's "kodeksning"
citation was correctly excluded, then recovered and grew via Bugs 2-3's
genuine new citations); repealed-company-form-article citations shifted
consistently with the same edges (63: 4->3, 65: 2->1, 66: 3->1, 70: 5->4,
71: 2->3, 72 unchanged at 3) — every shift traced to a specific added/removed
edge, not just accepted from the aggregate. `repeal_clause` (885/840
resolved) and `article_amendment` (594 clauses -> 612 rows) both completely
unchanged, confirming today's fixes don't touch those code paths. Grepped
both apps for `confidence`/`dst_ambiguous`/`dst_dangling` usage before
trusting the confidence-formula change: both only ever `ORDER BY
(evidence_kind <> 'normative'), confidence DESC` — normative rows already
sort first regardless of the exact confidence value, so the fix changes
data, not display behavior. `py_compile` clean on both apps and every
pipeline script. `verify_transfer.py`: **VERIFICATION PASSED — all checks
green.** Final `link_edge`: 6667 -> 9402 (+2735 net); by evidence kind,
normative 1484 -> 2505, editorial 1406 -> 6896 (both against the true
day-start baseline, reconfirmed via `git stash` immediately before writing
this entry, not assumed from an intermediate build) — the editorial jump is
mostly Bug 3's em-dash-list discovery, since `mazkur/ushbu Kodeksning N, M —
P-moddalari`-style multi-range citations are far more common in
`cross_references` (the Civil Code's own cross-reference apparatus) than in
`article_text`.

**Decision:** ship all three extraction fixes plus the confidence fix —
each measured before and after, self-tested, diffed edge-by-edge (not just
by count) against a snapshot of the prior build, and independently verified
against `measure_extractor_recall.py`, `build_llc.py`, and
`verify_transfer.py`. The one open ambiguity (row 19636) is logged, not
hidden. Did not chase the three smaller residuals found along the way
("hamda" as a list conjunction, the chapter+paragraph lookahead's own
space-separator gap, qism-range collapse) — each is either single-occurrence
today or, for qism, not yet consumed downstream; recorded in Backlog with
enough detail to pick up directly.

### 2026-09-14 — wired `article_amendment`/`v_article_currency` into both Streamlit apps, closing the amendment-chains thread

Continued the mid-flight amendment-chains thread rather than rotating: its
Active-threads entry named one explicit remaining step ("that UI wiring is
the one open step"), which is exactly the kind of concrete, scoped
continuation this file's process asks for.

**Environment note first, unrelated to the actual work**: this fresh clone's
`articles/train-00000-of-00001.parquet` was a bare git-lfs pointer stub (134
bytes, `git-lfs.github.com/spec/v1`, ASCII), not the real 163MB parquet —
`git-lfs` wasn't installed in the container, so the smudge filter never ran
on checkout. `verify_transfer.py`'s AC3 failed immediately on a fresh clone,
before touching any code, with `No magic bytes found at end of file`. Fixed
by `apt-get install -y git-lfs && git lfs install --local && git lfs pull`
— the real parquet materialized (163,356,047 bytes, matches the LFS oid's
recorded size exactly) and every AC3 check then passed. Flagging this in
case tomorrow's fresh clone hits the same thing: it's an environment-image
gap, not a repo or data problem, and the fix is those three commands before
anything else.

**What was built.** `page_article()` in `app_hierarchy.py`: a "Legislative
history" line under the OKOZ caption showing amendment count, last
change-type/date, and a ⚠️ when `has_removed_or_voided_part` is true, plus an
expander with the full dated history (locator, act number, effective date,
raw evidence text) pulled straight from `article_amendment`. `app_llc.py`
got three additions: (1) `page_skeleton()` — each foundation-article bullet
now carries an inline amendment badge (e.g. "📝 9 amendments, last
2025-02-07"), computed once per stage list via a single batched
`v_article_currency` query rather than one query per article; (2)
`page_norm()` — the same full summary + expander as `app_hierarchy.py`,
under the Tier-2 Civil Code article; (3) `page_currency()` ("Is this still
law?") — a new dataframe table across all 27 distinct LLC foundation
articles, explicitly captioned as a *different* currency signal from the
page's existing two (which are about whole acts being repealed via
`v_act_currency`/`repeal_clause` — this is about parts of a still-live
article being rewritten in place via `article_amendment`). All new SQL is
parameterized (`?` placeholders, only `DOC_GENERAL`/article-number values
bound) — no f-string SQL added anywhere, keeping the project's one known
offender (already-deleted `hierarchy_engine.py`) the only historical case.

**Measured, not assumed.** Queried live against `corpus.duckdb`: of the 27
distinct Civil Code articles founding the LLC's 8 stages, **22 (81.5%) have
recorded amendment history** — article 55 alone has been amended **9
times** between 2006 and 2025 (four separate `restated` events on its parts
plus a `supplemented` insertion), several others (39, 40, 42, 43, 46, 48,
50, 58) were restated as recently as 2025-02-07. This is a genuine,
previously-invisible signal: before today, neither app told a reader that
80%+ of the LLC's own legal foundation has been substantively rewritten
since the Code was enacted — `page_currency()`'s existing act-level view
would have shown the *2001 LLC Law itself* as repealed-and-replaced, but
said nothing about churn inside the Code articles the *current* 2026 LLC
Law still rests on.

**Verified live, not just read from the diff.** `python3 -m py_compile` on
both files, then actually booted each app with `streamlit run
--server.headless` and drove them with Playwright (pre-installed Chromium)
rather than trusting the SQL alone: confirmed the "Legislative history"
line and its expander render with real content on `app_hierarchy.py`'s
default article (49), expanded the history panel and read four real dated
entries with correct badges; on `app_llc.py`, confirmed the skeleton's
inline badges render, clicked into "Follow a norm down" for article 39 and
saw the same summary+expander pattern, and clicked into "Is this still
law?" and confirmed the new dataframe section renders with its caption and
no traceback. Caught along the way (not a bug, a test artifact): running
both apps against `corpus.duckdb` simultaneously in this sandbox raises
DuckDB's expected single-writer lock conflict — pre-existing, documented in
`app_hierarchy.py`'s own `_connect()` docstring, not something today's
change touched; tested each app alone instead, which is also how they're
meant to run in production (one writer max per the docstring's own
reasoning).

**Scope check against the hard constraints.** No pipeline script touched,
so no rebuild of `corpus.duckdb` was needed or done — `git status` shows
only `app_hierarchy.py`/`app_llc.py` modified. Grepped both apps beforehand
for the table/column names touched (`v_article_currency`,
`article_amendment`) to confirm nothing else already used them (a fresh
grep, not trusting yesterday's — matched yesterday's finding of zero
references). `verify_transfer.py`: **all checks green**, same
`m0-20260813T110129Z` run, no new INFO/FAIL lines beyond the pre-existing
documented ones (26¹ version drift, the two ambiguous-key superscript
articles, the 9 `structure_missing_articles`/`md_only` gaps — all
pre-existing and already explained in past Log entries).

**Decision: amendment-chains thread closed.** The Active-threads entry
tracked this since 2026-09-11 across three sessions (built → list-swallowing
fix → UI wiring); today's step was the one explicitly flagged as remaining,
and there's nothing else scoped to `article_amendment` left to do — the
amending-act-resolution residual (33/594, `act.doc_number` empty
corpus-wide) is a documented data-acquisition gap, not pipeline or UI work.
Rotation-wise this was technically a third straight Data-currency session
(09-11 built it, 09-13 fixed the list-swallowing bug, 09-14 wired the UI) —
justified because "mid-flight thread" takes priority over rotation per this
file's own process, but it does mean next session should prefer Extractor
or Cleanup rather than a fourth Data-currency day, absent a new item that
clearly outweighs rotating.

### 2026-09-13 — fixed amendment-chain list-swallowing bug: 18 dropped target articles recovered by reusing the extractor's own list/range grammar

Continued the rotation onto Data currency (Extractor ran 09-10 and 09-12,
Data currency 09-11; see Active threads for the running tally). Fresh clone
needed the same setup hiccups as recent sessions: local `main` was a stale
detached-HEAD pointer 3 commits behind `origin/main` (`git checkout -B main
origin/main` fixed it, no lost work — matches the pattern flagged 09-04 and
09-12), `git-lfs` wasn't installed (`apt-get install -y git-lfs && git lfs
install --local && git lfs pull` restored the real 163MB parquet from its
pointer file), and `duckdb`/`pyarrow`/`numpy` needed `pip install`. Baseline
`verify_transfer.py` was green before touching anything.

Picked up the amendment-chain list-swallowing residual flagged in Active
threads/Backlog from 2026-09-11: `build_links.py`'s `article_amendment`
parser used `re_target_article = re.compile(r"(\d{1,5})\s*-?\s*modda")` and
took the *first* regex match in a clause's scope text to find the target
article. For a list like "65 va 66-moddalar", "65" is never adjacent to
"modda" (it's followed by " va 66-moddalar"), so the bare-digit-then-modda
pattern only ever matches "66" — the list's last member. The daily review
had only spotted this on one occurrence (article 65).

**Measured the real scope first, before fixing anything**: wrote a
standalone script replicating both the old regex and a candidate fix
(`citation_extractor.RE_CLAUSE` + `_expand`, the same list/range grammar the
extractor itself already uses for citations, backed by 32+ self-tests) over
all 594 amendment clauses in `CC_DOCS`. Result: **10 of 594 clauses (1.7%)
are genuinely multi-member lists or ranges**, not 1 — covering **28 target
articles total**, of which only 10 (one per clause, always the last member)
were ever captured. 18 target articles were silently dropped corpus-wide,
including a full 7-member superscript range ("1731 — 1737-moddalar", i.e.
articles 173-1 through 173-7 — the same superscript-numbering family fixed
in the 2026-09-08 `doc_id` bug, though this one already worked correctly
here because `_expand`'s integer range naturally lines up with consecutive
superscript children when the endpoints are 6 apart, unlike the 09-08 bug's
1564-wide malformed-range case).

**Fix**: replaced the single-match regex with a small `target_articles()`
helper that finds a clause's modda-unit match via `cx.RE_CLAUSE` and expands
it with `cx._expand()` — reusing the extractor's own tested list/range
grammar instead of maintaining a second, narrower one. The per-clause loop
now iterates over every expanded target article (previously just one),
emitting one `article_amendment` row per target while keeping the event's
other fields (locator, change_type, dates, evidence) identical across the
list's members — the same "one row per list member, shared event context"
shape `build_links.py` already uses elsewhere for citation edges. Chapter/
paragraph-level clauses (no modda unit at all) still correctly produce no
target article, unaffected.

Also cleaned up the log line while in there: it previously called
`len(amend_rows)` "amendment events", which was accurate when clause==row
but became misleading once one clause could produce multiple rows. Now logs
both counts explicitly: "594 amendment clauses -> 612 rows".

**Re-ran `build_links.py`**: `article_amendment` count 594 -> 612 rows
(+18, exactly the predicted gap), clause-level distributions
(`by change_type`, `by match_method`) unchanged since those are still
counted once per clause, not per row. `repeal_clause` and `link_edge`
counts unchanged (this fix only touches `article_amendment`, confirmed by
diffing the full pipeline log against the pre-change baseline). Verified
directly: article 65's own `voided`/2014-05-14 amendment event now exists
in `v_article_currency` (previously invisible, only article 66's event was
recorded); the 7-member superscript range resolves all 7
`norm_id`s (`-111189-a1731` .. `a1737`) against real `norm_unit` rows,
confirmed present by direct lookup, not just the endpoint article 1737
that used to be the only one captured.

**Reran `build_okoz.py` and `build_llc.py`**: zero numbers changed in
either (OKOZ coverage stayed 386/386, LLC foundation/implementing-act
counts identical) — neither table reads `article_amendment` (grepped both
scripts and both apps first, confirmed no references, same as the
2026-09-11 amendment-chains session found). `citation_extractor.py`
self-tests: 37/37 (unchanged — this fix lives entirely in `build_links.py`,
not the extractor itself, though it reuses the extractor's regex/expand
functions as library code). `verify_transfer.py`: all checks green,
identical reconciliation-detail output to the pre-change baseline (this
change doesn't touch any AC1-AC7 check's inputs).

**Decision**: fixed rather than deferred, unlike the single-occurrence range
gaps left open elsewhere in Backlog (e.g. the "173 – 1737" citation-range
gap from 2026-09-08) — the difference is scope: measuring first showed this
was 10 occurrences /28 articles, not 1, clearing the bar for a real fix
rather than a documented, deferred edge case. The remaining two
amendment-chain residuals (chapter/paragraph-level clauses correctly having
no target article; the 5.6% amending-act-resolution cap from empty
`act.doc_number`) are unaffected by this fix and stay as documented,
not-worth-chasing residuals — see Active threads and Backlog.

### 2026-09-12 — found "qonunning" missing from RE_STOP entirely: 131 misattributions fixed, biggest precision gap closed since "Qonun" itself

Continued the Extractor rotation (last ran 09-10; Data currency ran 09-11 in
between, so this keeps rotation alternating rather than draining one area —
see Active threads). Fresh clone needed the usual `apt-get install -y
git-lfs && git lfs install --local && git lfs pull` plus `pip install
duckdb pyarrow numpy`; `git fetch origin main` also had to run once before
`main` matched `origin/main` — the container's initial checkout was a
detached HEAD 3 commits ahead of the local `main` ref (both already equal to
`origin/main` once fetched; not a lost-push, just a stale local branch
pointer, same category of hiccup 2026-09-04 flagged).

**Four hypotheses tried before the one that paid off — all measured, not
guessed, per this thread's own methodology:**

1. **ORDINALS list caps at "oʻn ikkinchi" (12th); does a 13th+ qism/band
   ordinal ever get missed?** Corpus has 255 raw occurrences of "oʻn
   uchinchi/toʻrtinchi/.../yigirmanchi qism/band" combined. Monkeypatched
   `citation_extractor.ORDINALS`+`RE_QISM` with an extended set (13th
   through 22nd) and diffed `Citation.qism` across all 10,348 candidate
   rows: **0 citations gained a qism/band.** Only 5 rows in the whole corpus
   even have a higher ordinal co-occurring with the word "kodeks" at all —
   falsified, no live bug.
2. **"Modda A dan modda B gacha" (from...to) as an alternative range syntax
   to the dash `_expand` already handles.** Zero occurrences anywhere in the
   54,173-row corpus of `\d+-modda\w*dan\s+.{0,20}gacha` (or the `bob`
   equivalent) — this construction simply isn't used; falsified before
   writing any extraction code.
3. **Does the FK-alias definition pattern (`bundan buyon matnda FK deb`)
   miss any of the 26 alias-defining acts' actual "FK ..." citations?**
   Traced every standalone "FK" token in all 26 alias docs against
   `RE_ANCHOR_FK`; every one that precedes a modda/bob clause was already
   correctly recognized. (An early false alarm — apparently 6 missed
   anchors — was my own test-harness bug: I'd truncated sample strings for
   readability and cut off the leading "Fu" of "Fuqarolik", which is not
   what the real corpus text looks like. Re-ran against full, untruncated
   row text and the "misses" vanished.) Falsified.
4. **Does `RE_STOP`'s `break` (not `continue`) on a stop-word cause hidden
   recall loss** — i.e., once a window hits a stop-word, does it silently
   drop *later, genuine* Civil-Code clauses that would have followed in the
   same window? Reimplemented the exact clause loop to find every window
   where a stop triggers with `RE_CLAUSE` matches still remaining
   afterward: 552 such windows exist, but reading every remaining clause by
   hand (not just counting them) showed all of them correctly belong to
   whatever act *triggered* the stop (an act's own gazette record numbers,
   another code's own article, etc.) — the conservative "abandon the rest of
   this window once contaminated" design is safe for the current stop-word
   set. Falsified as a *current* bug, but flagged as a design tension worth
   remembering: it depends on stop-words never appearing *before* a
   genuinely-Code-bound clause in a densely-packed window, which is exactly
   what tripped up hypothesis 5 below during measurement (not in
   production — see the false-alarm note there).

**5. The one that paid off: `RE_STOP` has `qonuni`, `qonuniga`,
`qonunining`, and (case-sensitive) bare `Qonun\b` — but never `qonunning`
(qonun+ning, the genitive *without* the "-i-" thematic vowel that
`qonunining` has). Distinct surface form, not a substring of any existing
alternative, and very common**: corpus-wide, capitalized "Qonunning"
precedes a modda/bob/paragraf clause 1504 times, lowercase "qonunning" 28
more. Measured actual impact the same way the 2026-09-05 "Qonun" fix did —
reimplementing `_anchors()`+`RE_CLAUSE`+`RE_STOP` directly and diffing
`extract()`'s output before/after adding the candidate word, keyed by
**textual span**, not list index (first pass wrongly showed ~240
"removed"+125 "added" because removing an early citation shifts every later
list index — a measurement bug, not a real one; re-keyed by
`(row, field, start, end, kind, article)` and the real signal was much
cleaner). Result:

    case-sensitive "Qonunning" alone:            118 real misattributions removed, 3 'act' fallback edges added, 0 collateral, 0 changed-in-place
    + case-insensitive "qonunning" (lowercase):   13 more removed, 0 added, 0 collateral
    total:                                       131 removed, 3 added

Read every one of the 131 by hand (not a sample — the full list): every
single one is a real named act's own article hiding behind "X toʻgʻrisida"gi
Qonunning N-moddasi" or a self-referencing "mazkur/ushbu Qonunning
N-moddasi" (a *different* act referring to itself), sitting inside a
Civil-Code anchor's scan window. None were a genuine Civil-Code citation
lost as collateral damage — confirmed at both the citation level (the diff
above) and, after shipping, at the `link_edge` level (see below, exact
match). Unlike bare "Qonun", made this one case-**insensitive**: bare lower
"qonun" is the ambiguous generic noun ("legislation"), but "qonunning" only
ever means "of a specific, already-named law" — the Civil Code is never
itself called "qonun" in this corpus, so there's no generic-phrase collision
to guard against, and the lowercase-vs-capitalized split for this
genitive form turned out to be inconsistent in the source text (LexUZ often
leaves it lowercase even under a quoted, unambiguous act title).

**Shipped**: extended `RE_STOP`'s existing case-insensitive group with
`qonunning`, documented the "why case-insensitive here but not for bare
Qonun" reasoning inline. Added 5 new self-tests (capitalized and lowercase
"qonunning" both stopping correctly; a real Code citation earlier in the
same window surviving the stop). `citation_extractor.py`: **37/37 self-tests
pass** (was 32).

**Reran `build_links.py`.** `link_edge`: 6795 -> 6667 (**-128**). Diffed the
two databases directly by `(src_row_id, source_field, ev_start, ev_end,
dst_kind, dst_article_number, dst_struct_node_id)`: **131 edges removed, 3
added** — exact match to the pre-ship citation-level measurement, from 44
distinct citing rows (mostly Plenum/court-explanation acts that cite many
different laws in one breath — exactly the dense-citation context that
hypothesis 4 above worried about, confirmed here to resolve correctly).
`dst_qism` population: 665 -> 657 (-8, qism/band tails that were attached to
now-removed false edges). Reran `measure_extractor_recall.py`: still **0
real misses**; anchor-window count 2340 -> 2331 (-9, the newly-scoped-out
"qonunning" windows, same lockstep-with-the-fix pattern the original Qonun
fix showed). Reran `build_llc.py`: **`llc_implementing_act` 132 -> 131
(-1)** — traced the one dropped act (doc `-1063359`): its *only*
`cites_cc_foundation` evidence was article "45", which turned out to come
entirely from a now-removed false edge (a "mazkur Qonunning 40 — 53-moddalari"
list wrongly attributed to the Civil Code — article 45 is a real LLC
foundation article, 44 others in that same false list weren't, which is why
this was the only LLC-slice number to move). This is a genuine precision
improvement to the LLC dossier, not just the general corpus: one fewer act
was being shown to the project owner as "implements the LLC Law's
foundation" on the strength of a citation that was never really there.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green.** 37/37
extractor self-tests; 6667 edges; AC7's "realization edges from superseded
acts" 1007 -> 1002 (-5, consistent with the removed edges' distribution);
39 OKOZ mappings still awaiting the owner's validation (untouched); same
reconciliation-detail list as prior sessions, byte-for-byte.

**Decision:** ship the "qonunning" fix — measured before/during/after,
edge-level diff matches the citation-level prediction exactly, every one of
131 removed edges hand-verified as a real bug, zero collateral loss. Did
NOT add `Farmonning`/`farmonning` despite 15+1 raw corpus occurrences
preceding a clause — measured actual anchor-window impact the same way and
got **0** (falsified as a live bug, same story as bare Qaror/Farmon on
2026-09-05): this is now the second time this exact false-alarm shape has
shown up for the decree-type nouns specifically, worth remembering as "this
family of nouns keeps *looking* risky by raw count but isn't, in this
corpus" rather than re-deriving it from scratch next time. The RE_STOP
`break`-vs-`continue` design tension (hypothesis 4) is not a bug today, but
is now written down as a specific thing to re-check if a future corpus
update introduces denser multi-act citation clusters.

### 2026-09-11 — Amendment chains: mined `amendment_note` instead of parsing "kiritilsin" clauses, 594 events, 8 of verify_transfer's 9 "missing article" mysteries solved

Rotation: Extractor ran last two sessions running (09-08 doc_id recall,
09-10 chapter+paragraph precision); Data currency last ran 09-09 (closed the
repeal-resolution thread). Picked Data currency's open backlog item,
"Amendment chains, not just repeals," to keep rotation honest rather than a
third Extractor session in a row.

**Environment**: fresh clone, same two-step setup prior sessions have
needed: `apt-get install -y git-lfs && git lfs install --local && git lfs
pull` for the parquet (it's an LFS pointer until pulled), then `pip install
duckdb pyarrow numpy`. `main` was already at `origin/main`'s tip this time —
no stale-ref issue to flag.

**Rejected the backlog item's own proposed approach before writing any
code.** It suggested detecting "kiritilsin"/"oʻzgartirish kiritilsin" style
clauses *inside amending acts' own text* — the same shape as `repeal_clause`'s
existing numbered-list parse, one grammar up. Checked how noisy that would
be first: `grep`-style counts on raw `article_text` for those phrases return
thousands of hits (8395 for "kiritilsin" alone) across ordinary decrees that
have nothing to do with the Civil Code — sampling 3 of the top matches
confirmed they're unrelated Cabinet resolutions that happen to contain the
word. Building a second repeal_clause-style extractor on top of that noise
floor looked like a lot of fragile work for a shakier signal than the
existing repeal detector has.

**Found a better source already in the corpus: the `amendment_note`
field.** Every article row carries its *own* structured legislative history
— e.g. `(8-modda birinchi qismining oltinchi xatboshisi Oʻzbekiston
Respublikasining 2025-yil 30-dekabrdagi OʻRQ-1109-sonli Qonuni tahririda —
Qonunchilik maʼlumotlari milliy bazasi, ...)` — one parenthetical clause per
amendment event, already isolated from surrounding prose. `build_links.py`
already scans this field as a citation source (`SOURCE_FIELDS`) but nothing
parsed its *structure* before. This is the receiving-article's side of the
exact relationship the backlog item wanted (amending act -> affected
article), and far cleaner to parse than scanning amending acts' free text
for the same thing from the other direction.

**Measured coverage before committing to the approach**: 174/386 (45%)
General Part articles and 239/811 (29.5%) Special Part articles have a
non-empty `amendment_note` — substantial enough to be worth building. Wrote
a single clause regex (date + OʻRQ-number-or-legacy-number + law-type +
verb phrase + optional em-dash source citation) and iterated against the
594 raw clauses until every single one parsed: the main gaps found and
fixed were (1) the genitive suffix "-ning" is sometimes dropped
("Respublikasi 2006-yil..." vs "Respublikasining"), (2) the date's "-dagi"
suffix is sometimes dropped too ("20-avgust" vs "20-avgustdagi"), (3) older
(pre-2007) acts use a legacy "832-I-sonli"/"405-II-son" numbering instead of
"OʻRQ-N-sonli" — widened the number alternative to catch both, (4) the
source-citation separator regex used a bare hyphen class `[—\-]`, which
collided with ordinary in-word hyphens like "70-moddaning" and truncated the
verb capture to a couple of words — narrowed it to the em-dash `—` only,
which is what LexUZ actually uses before a source citation. **Verb-phrase
classification** (restated/supplemented/removed/inserted/replaced/voided)
needed two stemming fixes of the same shape: "kuchini yoʻqotgan" (voided,
past participle) also appears as "kuchini yoʻqotish sanasi" (voided,
nominalized, in a *reversed* clause order — "Qonuniga asosan N-moddaning
oʻz kuchini yoʻqotish sanasi — DATE" puts the law citation first and the
effect second) and "chiqarilgan" similarly appears as "chiqarilish sanasi";
widened both to stem matches. Result: **594/594 (100%) of Civil Code
clauses parse**, 0 left in an "other" bucket. Sanity-checked generalization
beyond scope: the same regex parses **23307/23919 (97.4%)** of clauses
corpus-wide across all 12,166 rows with an `amendment_note` — strong
evidence the grammar is real, not overfit to the Civil Code, though the
built table stays scoped to the Civil Code (CC_DOCS) since that's what
`norm_unit`/`struct_node` can anchor an article to today.

**A second regex, scoped to the clause's own text (locator+verb, explicitly
excluding the source-citation tail), extracts which article the clause is
*actually* about** — not assumed to be the host row's own `article_number`.
This mattered: 13/594 clauses (2.2%) target a *different* article than the
row carrying the note, e.g. row 62's note includes "(...Qonuniga asosan
63-moddaning oʻz kuchini yoʻqotish sanasi...)" — article 63 itself has no
row in the corpus at all (it was voided outright), so its only trace is a
clause parked on its still-living neighbor, article 62. This is exactly
**8 of the 9** `structure_missing_articles`/`md_only` entries
`verify_transfer.py`'s own reconciliation has carried for a while as
unexplained gaps (63, 70, 71, 72, 176, 177, 179 from this table, plus 66 —
see below): each now resolves to an exact voiding law and date (mostly
OʻRQ-1025, 2025-02-07). **The 9th, article 65, is a known, narrow miss**:
its clause is "(65 va 66-moddalar ... kiritilgan)" — a 2-item list — and the
target-article regex only catches the *last* member directly adjacent to
"-moddalar" (66), the same list-swallowing shape as the qism/band and
chapter+paragraph-list bugs found on the Extractor thread on other days.
Left as a documented residual (1 occurrence) rather than special-cased.

**Shipped**: `article_amendment` table (event_id, doc_id,
host_article_number, target_article_number, norm_id, locator, change_type,
amend_date, amend_act_number, effective_date, amending_doc_id,
match_method, evidence) and `v_article_currency` view (per-article
n_amendments, last_amend_date, last_change_type, has_removed_or_voided_part)
in `build_links.py`, right after the `repeal_clause` section it parallels.
One bug caught before shipping: the `norm_id` lookup originally fell back to
the *host* article's norm_id whenever the target article had none — correct
for a chapter-level clause with no target at all, wrong for the
voided-neighbor case (it would have mislabeled article 63's event with
article 62's norm_id). Fixed to only fall back when `target_article_number`
is `None` outright.

**Final numbers** (`article_amendment`, Civil Code only): 594 events on
425/1197 articles (35.5%) — 304 Special Part, 290 General Part. By
change_type: restated 529, supplemented 29, removed 17, inserted 10, voided
8, replaced 1. Date range 1997-08-30 to 2025-12-30 (the Code's full life).
74 distinct amending law numbers. 65/594 (10.9%) carry a distinct
`effective_date` separate from the amending law's own adoption date
(delayed entry into force). **Amending-act resolution: 33/594 (5.6%)** —
matched when exactly one act exists on the clause's date whose own title
names "Fuqarolik kodeksi" (e.g. article 477's "2012-04-20 / OʻRQ-325" event
resolves to doc `-2003602`, titled exactly "Fuqarolik kodeksining
477-moddasiga oʻzgartish kiritish toʻgʻrisida" — hand-verified correct).
The other 94.4% stay unresolved for the *same* reason `repeal_clause`
already has an 18-item unresolved tail for: `act.doc_number` is empty for
every one of the corpus's 24,267 acts, so there's no number to match against
— only date, and most amending acts here are omnibus bills ("ayrim qonun
hujjatlariga oʻzgartirish...") whose own title never names the Civil Code,
so date-only matching is hopelessly ambiguous (median 10 acts share a date).
Not chased further; this is a corpus-data limitation, not a parsing gap —
recorded in Backlog.

Re-ran `build_okoz.py` (unchanged OKOZ mapping output, as expected — it
doesn't touch `amendment_note`) and `build_llc.py`: its own independent,
pre-existing "repealed company-form articles still cited" check already
listed 63/65/66/70/71/72 by article number with no date attached — today's
work gives that same finding a when-and-by-which-law answer rather than
introducing a new one, good cross-validation that both signals agree.
Grepped both apps for `article_amendment`/`v_article_currency` first: no
references yet (new tables, not wired into either app's UI today — a real
next step, not done this session given the time budget). `verify_transfer.py`:
all checks still green, unchanged from baseline (this is a pure addition,
no existing table's content changed — `link_edge` edge count identical at
6795 before and after).

### 2026-09-10 — Cleanup re-audit (nothing found), three precision hypotheses falsified, one real chapter+paragraph attachment gap found and fixed

Rotation: Data currency ran last (09-09), Extractor before that (09-08);
Cleanup had run once (09-07) and its own Active-threads note said it was
"fully drained." Rather than skip Cleanup on the note's word, re-audited it
first — cheap to check, and the note is a year-old claim by 09-10's clock.
Found nothing new (see below), so fell through to the "Precision, more
broadly" thread's own explicit instruction: invent another falsifiable
misattribution hypothesis by sampling extractor output against raw text.
Fresh clone needed the usual `apt-get install git-lfs && git lfs install
--local && git lfs pull` plus `pip install duckdb pyarrow`. One environment
note: this session's local `main` ref started one commit *behind* origin
(HEAD was detached at 09-09's `a822891`, `main` still pointed at 08's
`6176a15`) — the same stale-ref shape 09-04's log flagged as something to
watch for, this time the other direction. `git fetch origin main` confirmed
origin already had `a822891`; fast-forwarded local `main` to it before
starting, no work was at risk.

**Re-audited Cleanup before rotating away from it.** Listed every
`execute(f"...")` call left in the repo (grepped all `.py` files) and read
what each interpolates: every single one is the same `raw = f"read_parquet('
{PARQUET.as_posix()}', ...)"` module-level constant used identically across
`build_corpus_db.py`, `build_links.py`, `build_llc.py`,
`measure_extractor_recall.py`, and `verify_transfer.py` — a hardcoded path
literal, not a runtime or data-derived value, so it doesn't violate this
project's "no string-interpolated SQL with a non-constant value" rule (that
rule is about exactly what `hierarchy_engine.py` did differently: an
instance-level `self.parquet_path` that could vary). No new dead code, no
new one-off scripts, no new f-string-SQL offender. Cleanup stays fully
drained — see updated Active threads note.

**Tried three new falsifiable precision hypotheses, all measured
corpus-wide, all resulted in zero real impact:**

1. *Does the FK-alias mechanism ever fire for a non-Civil-Code meaning of
   "FK"?* `RE_FK_ALIAS_DEF` only checks that an act defines *some*
   abbreviation as "FK" (`bundan buyon matnda FK deb`) — it never verifies
   the abbreviation is for "Fuqarolik kodeksi" specifically, so any act
   using "FK" as shorthand for something else would get every "FK
   N-moddasi" in the whole document wrongly attributed to the Civil Code.
   Pulled all 26 acts (all 26 distinct `doc_id`s) matching the definition
   regex and read the defining sentence in each: **all 26 define FK
   immediately after "Fuqarolik kodeksi"** — zero counter-examples.
   Falsified.
2. *Does `RE_STOP_ABBR` (any 2-4 uppercase letters + "K") ever truncate a
   real Civil Code citation by falsely matching a non-code acronym (e.g.
   "BANK" fits the character class)?* Replicated the extractor's own
   scan loop, collected every token that actually triggered a stop inside a
   real anchor window, corpus-wide. Result: exactly 6 distinct tokens fired
   (`IPK`/`IPKning`, `FPK`/`FPKning`, `XPK`/`XPKning`), all genuine other
   codes (Iqtisodiy/Fuqarolik-protsessual/Xoʻjalik protsessual kodeksi) —
   zero false stops. Falsified.
3. *Does a list of chapters ("N, M-bobi") followed by a single paragraf tag
   get the paragraf wrongly applied to every chapter in the list, not just
   the one it belongs to?* (The same class of bug the qism/band fix found
   in 2026-09-04, one level up the grammar.) Ran `extract()` corpus-wide and
   filtered for `target_kind == "section"` with `listing != "single"`.
   Result: **zero** such citations exist in the corpus today — the
   construct the bug would need never occurs. Falsified as a live bug
   (the code path itself was never exercised, so nothing to fix).

**Found a real one on the fourth pass, from the same code path (2)'s replica
touched.** While replicating the scan loop, noticed `unit == "paragraf"`
matches (bare paragraf, normally just an echo of a bob+paragraf pair
already captured by the bob branch's own lookahead) that weren't actually
covered by any section citation. Traced one down (row 25634's evidence,
seen while investigating) and found the real pattern: LexUZ sometimes
punctuates chapter+paragraph citations with a comma — "Fuqarolik kodeksi
57-bobi, 4-paragrafi" — instead of the genitive "57-bobining
4-paragrafi" the existing lookahead (`re.match(r"\s*(\d+)\s*-\s*paragraf",
...)`) expects right after the bob match. A comma there makes the lookahead
fail, so the citation falls through to a bare chapter citation (57), losing
the paragraph pin — not dropped, just coarser than what the text actually
says. Measured corpus-wide with a direct regex for
`\d+-bob\w*\s*,\s*\d+-paragraf` inside real anchor windows: **exactly 3
occurrences** (rows 6070, 25511, 25512).

**Fix:** widened the lookahead to `re.match(r"\s*,?\s*(\d+)\s*-\s*paragraf",
...)` — the optional comma is followed only by `\s*`, never a wildcard skip,
so if a *second* chapter number sits between the comma and "paragraf" (a
genuine list, e.g. "57-bobi, 60-bobi, 4-paragrafi") the match fails here and
the paragraf instead attaches to *that* later bob on its own iteration,
never misattributed backwards — same non-ambiguity property the qism/band
fix's list guard relies on. No such list case exists in the corpus today to
test against real text, so added a constructed one as a self-test guard
alongside the two real comma cases. `citation_extractor.py`: 35/35
self-tests pass (was 32).

**Rerunning `build_links.py` surfaced a second, smaller bug in the same
code path, caught before shipping rather than after.** One of the 3 comma
cases (row 25511, "2-bob, 2-paragrafi") now correctly extracts a *section*
citation (chapter 2, paragraph 2) — but chapter 2 in the current corpus
structure has no sub-paragraphs at all (`struct_node` has no `C2.S*` rows;
likely a stale reference to a pre-restructuring numbering, the same kind of
edition drift `verify_transfer.py`'s reconciliation list already documents
elsewhere). `build_links.py`'s chapter/section resolution did `if node not
in struct_doc: continue` — silently dropping the *entire* edge when the
precise node doesn't exist, with no fallback. Before today's regex fix this
row was captured only as a bare chapter citation (which *does* resolve,
since C2 exists) — so widening the regex alone would have been a **net
regression** for this one row: trading a real, if coarse, edge for no edge
at all. Caught this by re-querying `link_edge` for all 3 target rows right
after the rebuild rather than trusting the edge-count delta alone (which
was `6795 -> 6794`, off by exactly one — the silent drop).

**Fixed by falling back to the chapter node when the section node doesn't
exist** (`build_links.py`, same block): if `C{n}.S{m}` isn't in
`struct_doc`, try `C{n}` alone, and only `continue` if even that's missing.
When the fallback fires, store `dst_kind = 'chapter'` (not `'section'`) and
price the edge at the chapter-level base confidence — the paragraph pin
genuinely isn't defensible, so the edge shouldn't claim more precision than
it has. This is the same principle 2026-09-08's article-level dangling
fallback established (don't drop an edge outright just because the finest
grain isn't available) applied one level up, at chapter/section instead of
article/norm.

**Reran the full pipeline.** `citation_extractor.py`: 35/35 self-tests.
`build_links.py`: `link_edge` **6795 -> 6795** (net zero — one row moved
`chapter` to `chapter`-via-fallback and stayed an edge throughout, two rows
moved `chapter` to `section`; total citation count is unaffected, this
thread only changes grain/labels): `chapter same` 58 -> 59, and the three
target rows individually confirmed by direct query — 6070 and 25512 now
carry precise `section` edges (`C57.S4`, `C22.S2`), 25511 correctly falls
back to `chapter` (`C2`) instead of vanishing. Reran
`measure_extractor_recall.py`: still 0 real misses on article and
chapter/section recall; qism/band residual unchanged at 7/640 (this fix is
orthogonal — different unit entirely). Reran `build_llc.py`: no LLC-slice
numbers changed (none of the 3 touched rows cite the LLC Law or its
foundation articles). Grepped `app_hierarchy.py`/`app_llc.py` for
`dst_kind`/`v_realization_struct`/`struct_number` first: neither app reads
`link_edge.dst_kind` directly or depends on which of `chapter`/`section` a
given edge is labelled — `v_realization_struct` joins on
`dst_struct_node_id` and reads the target's own `kind` from `struct_node`,
unaffected by this change — so no app change needed; both apps
`py_compile` clean.

**Found, measured, and deliberately left one more residual from the same
sampling pass.** Row 25634's "4-bobining 1 (“Umumiy qoidalar”) va
2-paragraflari" is a *list* of two paragraphs for one chapter, with a
parenthetical section title sitting between the first number and the "va"
before the second — the lookahead only ever tries one `\d+-paragraf`
immediately after the bob match, so this still produces a bare chapter-4
citation (correctly non-dropped by today's fallback, just missing both
paragraph pins). Confirmed single-occurrence corpus-wide; recorded in
Backlog with the concrete shape rather than rushed into the same fix,
since handling the parenthetical-skip and "va"-list correctly would need
its own guard the way the comma case got one, not a quick bolt-on.

**Decision:** ship the comma-attachment fix and its fallback companion
together — they were found and fixed in the same session because the first
literally exposed the second on rebuild, and shipping the regex fix without
the fallback would have been worse than not fixing anything (a net edge
loss on real data). Do not chase the parenthetical-list residual today:
it's a single occurrence, and the three falsified hypotheses plus this
two-part fix is a full session's worth of measured, verified work already.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green.** 6795
edges (unchanged in total, as expected — see above); AC7's "acts provably
superseded" / "realization edges from superseded acts" unchanged at
357/1007 (expected — this thread never touches repeal resolution); 38 OKOZ
mappings still awaiting the owner's validation (untouched); identical
reconciliation-detail list to every prior session. `py_compile` clean on
both apps and every pipeline script.

### 2026-09-09 — closed the repeal-resolution thread: the 45-item residual is corpus coverage, not a bug

Rotation: Extractor ran last (09-08); Data currency had only run once before
(09-06) against four Extractor sessions and one Cleanup, so rotated to Data
currency and picked up its own named Active thread rather than inventing a
fresh angle — the repeal-resolution thread had an explicit, concrete next
step recorded (read the 32 fuzzy-rejected full titles by hand, not the
60-char preview used in the original triage). Fresh clone needed the usual
`apt-get install git-lfs && git lfs install --local && git lfs pull` plus
`pip install duckdb pyarrow`.

**Rebuilt the exact 09-06 pipeline logic standalone** (not imported —
`build_links.py`'s repeal resolution lives inline in `main()`) to dump full
raw context for all 45 unresolved items instead of the truncated preview,
split by the documented 13 `no_date_match` / 32 `fuzzy_no_clear_winner`
kinds — reproduced that exact 13/32 split first, confirming the replica
logic matches the live pipeline before trusting anything read from it.

**Read all 45 in full, and a pattern was obvious almost immediately**: the
overwhelming majority quote a *Qaror* (a Supreme Council/Oliy Majlis
resolution — approving a statute, an enactment-procedure decision, a
personnel list) or a *Farmon* (a Presidium/presidential decree), not a
*Qonun* (a law). Measured this as a corpus-wide hypothesis rather than
trusting the sample: classified all 885 repeal_clause items by the word
immediately following the closing quote mark (`Qonun`/`Qaror`/`Farmon`/
`Nizom`, via a small regex) and cross-tabulated against exact-tier
resolution. Result: **709/856 (82.8%) of `Qonuni` citations resolve; 0/24
`Qarori` and 0/3 `Farmon` do — zero, not "mostly."**

**Verified this isn't an artifact of the classifier or a coincidence of
titles**, by searching the `act` table directly for the single most common
missing pattern seen in the sample — a Code's own "...ni amalga kiritish
tartibi toʻgʻrisida" (procedure-for-enactment) resolution, issued alongside
the Code itself but as a separate document. `SELECT * FROM act WHERE
doc_title LIKE '%amalga kiritish tartib%'` returns **exactly one row in the
whole 24,267-act corpus** — the 1992 Constitution's own enactment
resolution — and none for the Labor Code, Urban-Planning Code, Housing
Code, Civil-Procedure Code, or Economic-Procedure Code, even though repeal
clauses cite all five by name and date. This is a real, corpus-wide
document-type gap, not a title-phrasing mismatch the fuzzy tier could ever
close.

**The second cluster (13 of the 45) is entirely one citing act (row
16788), citing Qoraqalpogʻiston Respublikasi's (Karakalpakstan's) own
"ayrim qonunlariga oʻzgartishlar va qoʻshimchalar kiritish toʻgʻrisida"
(amendments to certain laws) template law, by the same title, on 8
different dates spanning 1998-2018.** Queried the `act` table directly for
each of those 8 dates: **zero acts exist at all** on 6 of them, and the 2
dates that do have same-day acts have no title anywhere near a match
(best fuzzy ratio 0.10-0.65, nowhere close to the 0.80 floor). Also
confirmed the corpus does carry *some* Qoraqalpogʻiston-titled acts (168
of them, by a separate `LIKE '%qoraqalpo%'` query) — so this isn't "the
corpus excludes Karakalpakstan entirely," it's specifically that this
national-level LexUZ-sourced corpus doesn't carry Karakalpakstan's own
sub-national statute-amendment acts. The remaining 4 items (row 44011,
row 17741) are pre-1991 Soviet-era Presidium/Cabinet decrees with zero
acts at all on their cited date — same root cause (document/era not in
this corpus), just too early rather than the wrong type.

**Every one of the 45 is now accounted for** — 24 Qarori + 3 Farmon + 1
Qarori misclassified by a nested-quote artifact in the manual read (row
181's citation embeds one quoted title inside another; both are actually
one Qaror, "...Qonunini amalga kiritish tartibi haqida"gi 311-II-sonli
Qarori", the regex's own quote-matching just captures the inner phrase) =
28 Qaror/Farmon-type, + 13 Qoraqalpogʻiston + 4 pre-1991 = 45. Zero
residual left unexplained, and zero found to be an extraction or matching
bug — every single one traces to a document that plain doesn't exist as a
row in this corpus's `act` table.

**Shipped one small, additive fix**: in `build_links.py`, when a clause
clears no resolution tier, check the word right after the quoted title —
if it's `Qaror`/`Farmon` (not `Qonun`), tag `match_method =
'unresolved:non-statute'` instead of a bare `'unresolved'`. Cheap
(one regex, only runs on already-unresolved rows), unambiguous by
construction (matches exactly the same word-after-quote signal the
corpus-wide measurement above used), and purely descriptive — `dst_doc_id`
stays `NULL`, no target is invented. Chose not to also tag the
Qoraqalpogʻiston/pre-1991 cluster: there's no comparably cheap, reliable
detector for "this specific title template belongs to a sub-national
jurisdiction" the way there is for "the word after the quote is Qaror,"
and inventing one for 13 items sharing one citing act felt like overfit
machinery for a single-source finding — documented here in full instead,
which is enough for a future session (or the project owner) to recognize
these on sight if they show up again.

**Reran `build_links.py`.** `repeal_clause`: 885 items, still 840/885
resolved (94.9%, unchanged — this is a label-only change, no new target
was invented or dropped). `by match_method`: `{'date+title': 710,
'date+substring': 81, 'date+fuzzy:*': 48 (five sub-buckets, unchanged from
09-06), 'unresolved:non-statute': 27, 'unresolved': 18}`. `link_edge`
count unchanged at 6795 (expected — this thread never touches citation
extraction). Reran `build_llc.py`: no LLC-slice numbers changed (expected
— none of the 45 items touch the LLC Law or its foundation articles).
Grepped `app_hierarchy.py`/`app_llc.py` for `match_method` first: neither
app filters on its value, only reads `dst_doc_id`/`evidence`/counts, so
the new label needed no app change; both apps `py_compile` clean.

**Decision: close this thread rather than leave it "diminishing returns,
revisit later"** as the 09-06 note left it. There is nothing left for
`build_links.py` or `citation_extractor.py` to do here — the gap is that
LexUZ's national act index, which this corpus is built from, doesn't
carry Qaror/Farmon-type resolutions or Karakalpakstan's own sub-national
lawmaking at meaningful coverage. That's a data-acquisition question (does
a corpus update ever add these document types), not a pipeline bug, and
solving it would mean sourcing new raw data, out of scope for this
project's build scripts. Recorded the exact reopening signal for whoever
does source more data: `unresolved:non-statute`'s count is the fastest way
to check whether a corpus update actually added Qaror/Farmon coverage — a
re-run should push it toward zero on its own, no code change needed.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green.** 32/32
extractor self-tests (unchanged — no extractor code touched today); 6795
edges unchanged; AC7's "acts provably superseded" / "realization edges
from superseded acts" unchanged at 357/1007 (expected — no new repeal was
resolved, only relabeled); 38 OKOZ mappings still awaiting the owner's
validation (untouched); same reconciliation-detail list as every prior
session. `py_compile` clean on both apps and every pipeline script.

### 2026-09-08 — found and fixed a silent recall drop in superscript-article resolution

Rotation: Data currency (09-06) then Cleanup (09-07) had run most recently, so
rotated back to Extractor per the Active-threads note. Picked up the
"Precision, more broadly" thread's own named-but-unsearched hypothesis —
"wrong doc_id resolution" — rather than inventing a fresh one from scratch,
since it was already sitting there unexamined. Fresh clone needed the usual
`apt-get install git-lfs && git lfs install --local && git lfs pull` plus
`pip install duckdb pyarrow` before any data was visible.

**Read `Citation.doc_id` looking for exactly this class of bug, then verified
by reading `norm_unit` before touching code.** The property classifies a
cited article as General or Special Part by comparing its integer value
against `GENERAL_PART_LAST_ARTICLE` (385) and `CODE_LAST_ARTICLE` (1199). But
`norm_unit.article_number` encodes superscript articles by concatenating the
suffix digit onto the base ("173-7" -> "1731".."1737", confirmed directly:
`SELECT norm_id, article_number, article_base, superscript FROM norm_unit
WHERE superscript IS NOT NULL` returns exactly 9 rows, all under this
scheme). Any such citation whose concatenated value exceeds 1199 was
therefore misclassified as "outside the Code entirely" (`doc_id = None`), and
`build_links.py`'s resolution loop does `if dst_doc is None: continue` right
before the norm lookup — not an unresolved or dangling edge, just silently no
edge at all.

**Also found, while checking the fix's safety, that Special Part coverage is
narrower than the doc_id constants imply.** `SELECT DISTINCT doc_id FROM
norm_unit` returns only `-111189` (the General Part) — the Special Part
(`DOC_SPECIAL = -180552`, articles 386-1199) has zero norm_unit rows. This
isn't a bug: `build_corpus_db.py`'s own M0 docstring says its scope is "the
Civil Code General Part" and the markdown source lives under a directory
literally named `Civil code of Uzbekistan_general part`. It does mean a
Special Part citation can never resolve to a `dst_norm_id` (no norm exists to
point at) — a fact the pipeline already handles correctly for plain Special
Part citations (they get an edge with `dst_norm_id = NULL`, not dropped, not
flagged dangling). This is the bar the fix needed to clear for the two
Special Part superscript hits: not "resolve them to a norm" (impossible by
design) but "don't drop the edge outright, same as every other Special Part
citation."

**Measured the actual impact before writing the fix**, by replicating
`build_links.py`'s exact extraction loop (same candidate-row filter, same
`alias_docs`, same `is_the_code` gating) and collecting every `article`-kind
citation with `c.doc_id is None`. Exactly **4** in the whole corpus:
- row 1390 (Suv kodeksi, `cross_references`): "Fuqarolik kodeksining 173 –
  1737-moddalari" -> citation "1737" (173-7, General Part)
- row 41737 (a Garov/Pledge Law amendment, `cross_references`): "Fuqarolik
  kodeksining 2591-moddasi" -> citation "2591" (259-1, General Part)
- row 6071 (a court explainer, `article_text`, via the FK alias): "FKning
  11071-moddasiga asosan" -> citation "11071" (1107-1, Special Part)
- row 49322 (Maʼmuriy javobgarlik kodeksi, `cross_references`): "Fuqarolik
  kodeksining 539, 6261-moddalari" -> citation "6261" (626-1, Special Part)

All 4 manually confirmed genuine: each sits inside a real `Fuqarolik
kodeksi`/FK-alias anchor, correctly scoped by the existing anchor logic — the
bug is purely in the post-extraction classification, not in what gets
anchored or matched.

**Fix:** reclassify by the base article when the concatenated value exceeds
`CODE_LAST_ARTICLE` (`n //= 10` before the General/Special comparison) —
sound because no plain article number in this Code exceeds 1199, so anything
past it can only be this concatenation scheme, never a genuine larger article
number. Added 4 self-tests: the two General Part hits, the Special Part hit,
and a control (plain "700" must stay classified `DOC_SPECIAL`, confirming the
fix doesn't touch ordinary citations). `citation_extractor.py`: 32/32
self-tests pass (was 28).

**Reran `build_links.py`.** `link_edge`: 6791 -> 6795 (+4, exactly the 4
found). Inspected each new edge directly rather than trusting the count: the
two General Part ones resolved `dst_norm_id` correctly (`-111189-a1737`,
`-111189-a2591`, matching `norm_unit` exactly); the two Special Part ones
landed as `dst_norm_id = NULL`, `dst_dangling = false` — consistent with how
every other Special Part citation already behaves, not a new kind of gap.
Reran `measure_extractor_recall.py`: still 0 real misses on article and
chapter/section recall; qism/band residual unchanged at 7/640 (this fix is
orthogonal to qism attachment). Reran `build_llc.py`: no LLC-slice numbers
changed (expected — none of the 4 new edges touch the LLC Law or its
foundation articles, all of which are small General Part numbers well under
this bug's threshold).

**Found one residual while checking whether the fix generalized, decided not
to fix it today.** Row 1390's citation is actually a *range* — "173 –
1737-moddalari" means "173 through its 7 superscript children" (8
provisions), but `_expand`'s malformed-range guard (rejects a span over 200,
meant to reject garbled text) sees `1737 - 173 = 1564` and falls back to a
2-item list of just the endpoints, so today's fix rescues "1737" but 173-1
through 173-6 (6 provisions) are still never cited. Checked whether this
generalizes: scanned the whole corpus for range citations exceeding the
200-guard (49 found) — 48 of the 49 are in other codes (Criminal Code,
Criminal Procedure Code, etc.) citing their own superscript ranges, and never
sit inside a Civil Code anchor, so the extractor correctly ignores them
already; row 1390 is the only one that lands inside a real `Fuqarolik
kodeksi` anchor. A single-occurrence gap (6 missing edges) — recorded in
Backlog with a concrete fix sketch (detect matching base articles via
integer-divide-by-10 on both range endpoints) rather than special-cased into
`_expand` for one instance today.

**Decision:** ship the `doc_id` fix — small, unambiguous, measured before and
after, self-tested, zero regression on recall or the LLC slice. Do not chase
the range-collapse residual in the same session; it is genuinely one
occurrence today, and a rushed generalized fix to `_expand` risks new failure
surface for less benefit than the properly-scoped fix already shipped.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green.** Same
reconciliation-detail list as every prior session (this thread never touches
`norm_unit`/`struct_node`, only `link_edge`); AC7's "acts provably
superseded" / "realization edges from superseded acts" unchanged at 357/1007
(expected — none of the 4 new edges originate from an act already flagged
superseded). `py_compile` clean on both apps and every pipeline script;
grepped `app_hierarchy.py`/`app_llc.py` for `dst_article_number`/`doc_id`
usage first — neither app filters on the specific numeric value, only joins
through `dst_norm_id`/`dst_doc_id`, so the newly-added edges are additive and
need no app change.

### 2026-09-07 — Cleanup rotation: retired dead prototypes, right-sized test_transfer_e2e.py

Extractor threads had run three of the last four sessions (09-03, 09-04,
09-05) and Data currency one (09-06); Cleanup had zero. Picked the whole
Cleanup backlog section rather than one item, since each item was small and
independently verifiable, and did real work on all four rather than
"looked into" any of them.

**Confirmed dead code before deleting anything, not assumed it.** Grepped
the entire repo (`.py`, `.md`, and any config/entrypoint files) for
references to `hierarchy_engine`, `app_deep`, `app.py`, and the four
`analyze_*`/`find_civil_code.py` scripts. Found exactly one internal
reference (`app_deep.py` importing `hierarchy_engine.py`) and nothing
external — no README mention, no Streamlit config, no other script
importing them. Read each file's header to sanity-check the grep:
`hierarchy_engine.py` confirmed as the backlog described (f-string SQL via
`conn.execute(f"...{self.parquet_path}...")`, and its `okoz_to_fk_map`
dict literally empty with a "User will fill this later" comment — genuinely
superseded by `build_okoz.py`'s real classification). The four
`analyze_*`/`find_civil_code.py` scripts all hardcode
`P = 'c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet'` — a
Windows path that doesn't exist in this or any prior Linux session, so none
of these have been runnable since at least the first 2026-09-03 session;
confirmed genuinely dead rather than "unused but working." Deleted all 7
files (`git rm`): 851 lines removed.

**Diffed `test_transfer_e2e.py` against `verify_transfer.py` instead of
assuming the backlog's "probably redundant" framing.** Read every test in
its 4 tiers and traced what each actually checks:
- Tier 1 (R1-R4) and Tier 2 (edge cases: duplicate article 26¹/261,
  superscript sub-articles, titleless headings, mislabeled Section/§
  headings, repealed articles, the article-168 gap) all run through the
  file's own `parse_markdown_articles()` — a from-scratch regex re-parse of
  the raw markdown, written independently of `structure_parser.py` and the
  frozen `parsed_articles.json` the real pipeline loads at build time
  (`build_corpus_db.load_markdown_articles` just reads that JSON, it never
  re-parses). This is the same "naive independent detector" role
  `measure_extractor_recall.py` plays for citation extraction, applied to
  markdown parsing instead — genuinely non-duplicate coverage.
- Tier 3 checks the raw parquet against hardcoded literals (54173 rows, 386
  Civil Code rows, zero null/empty Uzbek text) rather than against a hash
  captured at the pipeline's own last build — a meaningfully different
  guarantee from `verify_transfer.py`'s AC3 sha256-vs-build-time check
  (which would not catch a parquet that was tampered with and then
  legitimately rebuilt).
- Tier 4 (its own AC1-AC3) was the one genuinely redundant part, and worse
  than redundant: its "post-M2" branches (`if "article_text_en" in
  cols_query`) test a schema — English text added as a column on the raw
  parquet — that the actual pipeline never built (English text lands in
  `norm_unit.article_text_en` inside `corpus.duckdb`, per the immutable-raw-
  parquet constraint this project has always followed). Confirmed by
  reading `build_corpus_db.py` and `verify_transfer.py`'s own AC1-AC3 (lines
  75-191): those check the *live* corpus.duckdb exhaustively — every landed
  article byte-compared against a fresh markdown re-extraction, not
  sampled — a strict superset of what Tier 4's sampled `test_ac2` did, and
  Tier 4's `test_ac1`/`test_ac3` pre-M2 branches just re-checked counts
  already covered by Tier 1's `test_r1` and Tier 3's
  `test_integrity_uzbek_text_intact`.

**Decision: removed only Tier 4** (134 lines, 3 tests) rather than the
whole file. Rewrote the module docstring to record this reasoning
explicitly, so a future session (or a future me) doesn't re-open the same
question from scratch or delete the genuinely-independent parts by
over-applying the backlog's original framing. Reran: 14/14 tests pass (was
17/17 — exactly the 3 removed, nothing else moved).

**Verified nothing else broke.** `py_compile` on both apps
(`app_hierarchy.py`, `app_llc.py`) and all pipeline scripts: clean.
Re-grepped for the 7 deleted files' names across all `.py` files: zero
hits. No pipeline script touched today (no `build_*.py` changes), so
`corpus.duckdb` is untouched — no rebuild needed. `verify_transfer.py`:
**VERIFICATION PASSED — all checks green**, exit 0, identical
reconciliation-detail list and INFO counts to 2026-09-06 (357 acts
superseded, 1007 realization edges, 38 OKOZ mappings awaiting validation) —
expected, since nothing in today's change touches extraction, links, OKOZ,
or the LLC slice.

**Net:** 8 files touched, 993 lines deleted / 27 added. All four Cleanup
backlog items resolved (three fully, `test_transfer_e2e.py` right-sized
rather than deleted outright — see updated Backlog entry).

### 2026-09-06 — repeal resolution: tiered date+substring/date+fuzzy fallback, 80.2% -> 94.9%

Rotated out of Extractor precision (per 2026-09-05's own note) into Data
currency, the backlog's highest-value unaddressed item: 175/885
`repeal_clause` items unresolved by the existing exact `(date, title)`
match. Fresh clone needed the same setup as every prior session
(`pip install duckdb pyarrow`, `apt-get install git-lfs`, `git lfs install
--local && git lfs pull`) — still not worth automating for a single daily
run, per 2026-09-05's assessment.

**Diagnosed the actual failure mode by reading raw text, not by guessing.**
Sampled 25 of the 175 unresolved items directly from the parquet's
`article_text`, matched against `repeal_clause.item_no` (not just
`src_row_id` — a first pass that ignored `item_no` misattributed which
regex match belonged to which clause and gave nonsense continuations).
Root cause: the existing extractor's `re_item` captures only the quoted
title inside "`{date} qabul qilingan "{title}"gi ... -sonli`" — but a large
share of repeal-list items don't name the repealed act directly; they name
an *amending* act by describing what it amends: "...2000-yil 26-mayda
qabul qilingan "Jismoniy tarbiya va sport toʻgʻrisida"gi Oʻzbekiston
Respublikasi Qonuniga oʻzgartishlar va qoʻshimchalar kiritish haqida"gi
76-II-sonli Qonuni" — the quoted phrase is the *original* law's title, and
the actual target act (`-63106`, dated exactly 2000-05-26) is titled
"'Jismoniy tarbiya va sport toʻgʻrisida'gi ... Qonuniga oʻzgartishlar va
qoʻshimchalar kiritish haqida" — i.e. the quoted title is a normalized
*substring* of the true target's title, not equal to it, and both always
share the item's own cited date (verified this holds, not assumed it).
Classified all 175 by the text immediately following the quote: 37 fit a
clean "Qonuniga ... kiritish" template, but many more had middle phrases
("...ga qaratilgan oʻzgartirishlar...", "...ning N-moddasiga
oʻzgartirish...") that made template-matching itself fragile — so instead
of growing the regex to cover each phrasing, tested substring/fuzzy
matching directly against the already-correct quoted title, scoped by date.

**Measured the fix before writing it into the pipeline.** Built
`by_date`: every act's `(doc_id, norm_title)` grouped by `doc_date`, then
for each of the 175 unresolved items checked whether the normalized quoted
title is a substring of exactly one same-date act's title. Result: **81
resolved, zero ambiguous** (never more than one same-date substring match
across all 175 — no arbitrary tie-breaking needed). Of the remaining 94,
tried `difflib.SequenceMatcher` ratio against same-date candidates,
accepting a match only when the best ratio is >=0.80 *and* beats the
second-best by >=0.15 (both thresholds chosen from the actual score
distribution: every accepted case scored >=0.87 with the next candidate
at least 0.27 lower, so the bar has real margin, not a knife-edge). Result:
**49 more resolved**, mostly near-1.0 spelling variants
(oʻzgartish/oʻzgartirish, tashkilotlarning/tashkilotlarining — LexUZ's own
transcription is inconsistent across documents citing the same act).
Manually read the full source text and target act title for the 3
lowest-confidence accepts (ratios 0.87, 0.88, 0.93 — cids 557, 62, 745):
all three confirmed correct on inspection — one is the well-known
"propiska" -> "yashash joyi boʻyicha roʻyxatga olinishi" terminology
rename Uzbekistan made to its residency-registration law, one is a 2-item
vs 3-item enumeration paraphrase of the same compulsory-treatment law, one
is a grammatical paraphrase of the same "in connection with improving
justice-body activity" act. No wrong match found in either fallback tier
at any confidence level checked.

**Shipped as two new tiers in `build_links.py`, each tagged with its own
`match_method`** (`date+substring`, `date+fuzzy:{ratio:.2f}`) so a weak
match stays visibly weak rather than silently indistinguishable from the
original exact match — exactly what the backlog item asked for. The
existing exact-match tier and its `by_date_title` lookup are unchanged; the
fallback only runs when that lookup misses and a `doc_date` was parsed.
Left the true-ambiguous branch (>1 same-date substring match) returning
`unresolved` rather than guessing, even though it never fired on this
corpus — a future corpus update could hit it.

**Reran `build_links.py`.** `repeal_clause`: 885 items, resolved 710 -> 840
(94.9%, was 80.2%) — `{'date+title': 710, 'date+substring': 81,
'date+fuzzy:0.99': 31, 'date+fuzzy:1.00': 8, 'date+fuzzy:0.98': 5,
'date+fuzzy:0.97': 2, 'date+fuzzy:0.93': 1, 'date+fuzzy:0.88': 1,
'date+fuzzy:0.87': 1, 'unresolved': 45}`. `link_edge` count unchanged at
6791 (expected — this only touches repeal detection, not citation
extraction). Reran `build_llc.py`: no LLC-slice numbers changed (expected —
none of the newly-resolved repeals touch the LLC Law or its foundation
articles). The 45 still unresolved split cleanly into 13 `no_date_match`
(no act at all on the cited date) and 32 `fuzzy_no_clear_winner` (a date
match exists but no candidate clears the acceptance bar) — recorded as the
new Active thread with a concrete next step rather than closed as done.

**Decision:** ship both fallback tiers — the substring tier is
zero-ambiguity by construction, and the fuzzy tier's precision was checked
by hand at every distinct confidence level down to its acceptance floor,
not just spot-checked at the top. Did not attempt to also parse the
amending-act continuation grammar into the regex itself (the originally
imagined "reconstruct the full title" approach) — the substring/fuzzy
approach on the existing quoted-title capture got the same acts resolved
with far less regex complexity and no new failure surface in
`citation_extractor.py`.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green.** AC7's
"acts provably superseded" moved from 278 to 357 (+79, now correctly
detecting supersession through the newly-resolved amending-act repeals);
"realization edges from superseded acts" moved from 948 to 1007 (+59).
Same reconciliation-detail list as prior sessions (no article-hierarchy
changes — this thread never touches `norm_unit`/`struct_node`). Grepped
`app_hierarchy.py`/`app_llc.py` for `repeal_clause`/`match_method`/
`v_act_currency` first: neither app filters on `match_method`'s value, only
selects `dst_doc_id`/`evidence`/`derived_status`, so the new method labels
are additive and don't need any app change; confirmed both apps still
byte-compile clean.

### 2026-09-05 — closed the "Qonun" precision thread; falsified the qaror/farmon/nizom generalization

Continued the Active thread from 2026-09-04. Fresh clone again needed
`pip install duckdb pyarrow`, `apt-get install git-lfs`, `git lfs install
--local && git lfs pull` before any data was visible — same as every prior
session; worth eventually baking into a setup script if this cadence
continues, but not done today (out of scope for this thread).

**Measured the capitalization heuristic across the corpus before writing
any fix.** For each of qonun/qaror/farmon/nizom, counted every bare-word
occurrence (capitalized vs lowercase) and how often it's immediately
followed by an "N-modda"/"N-bob" clause:

| noun | capitalized, total | capitalized + clause | lowercase, total | lowercase + clause |
|---|---|---|---|---|
| qonun | 12387 | 1006 | 49484 | 3 |
| qaror | 1631 | 0 | 43314 | 1 |
| farmon | 1087 | 1 | 150 | 0 |
| nizom | 14146 | 10 | 10451 | 1 |

Manually read samples from every non-zero cell. Capitalized+clause samples
are, without exception, a specific named Act ("ushbu Qonun 4-moddasi",
"mazkur Nizom 4-bobining 6-paragrafida") — the capital letter marks a proper
reference the same way it does in English. Lowercase+clause samples are the
opposite: "Konstitutsiyaviy qonun 4-moddasi" (a different multi-word proper
name that happens to lowercase its second word), one stray "qaror
1-bob."/"Vaqtincha nizom 10-bobining" — rare, and not fixable by a
single-word capitalization rule anyway. This confirms the capitalization
heuristic from 2026-09-04's hypothesis: it's a strong, corpus-supported
signal, not a guess.

**Then measured actual impact inside Civil-Code anchor windows specifically**
(the number that matters — a bare "Qonun" anywhere in the corpus is not a bug
unless it sits inside a window `extract()` is actively scanning for the
Code). Wrote a throwaway script re-using `citation_extractor._anchors()` and
`RE_CLAUSE`/`RE_STOP` directly: for each anchor window, does a bare
capitalized noun sit immediately before a modda/bob clause that RE_STOP
currently fails to stop at, and does the extractor actually emit a
citation there? Result:

    Qonun:  25 misattributed citations found (matches the manual estimate from 2026-09-04)
    Qaror:   0
    Farmon:  0
    Nizom:   0

Nizom's zero is explained, not surprising: bare "nizom" (case-insensitive)
was already in `RE_STOP` before today — it's on the same line as
"konstitutsiya", added at some earlier point for a different reason. Qaror
and Farmon's zero is a genuine corpus fact, not a detection failure: their
bare capitalized forms exist (1631 and 1087 times respectively) but never
happen to land immediately before an unstopped modda/bob clause inside a
Civil-Code anchor's scan window in the current 54,173-row corpus. So the
2026-09-04 hypothesis ("this generalizes to qaror/farmon/nizom") is
falsified as a *live* bug, even though the underlying gap in RE_STOP's
design (suffixed forms only) genuinely exists for those two — it just isn't
firing today.

**Fix: added case-sensitive bare `Qonun` to `RE_STOP` only.** Restructured
the regex from a single `re.IGNORECASE`-flagged pattern into a scoped
`(?i:...)` group (the existing case-insensitive alternatives, unchanged)
plus one new case-sensitive alternative, `Qonun\b`, so a bare *lowercase*
"qonun" (the generic word, 49484 occurrences) still doesn't stop a scan,
but bare *capitalized* "Qonun" (a named Act) now does. Added 2 new
self-tests: the exact misattribution sample from 2026-09-04's log now
resolves to `("act", None, "single")` instead of falsely pinning article
19, and a generic "qonun hujjatlarida" phrase still leaves a real Civil
Code citation intact. `citation_extractor.py`: 28/28 self-tests pass (was
26).

**Reran `build_links.py`.** Edge count: 6827 -> 6791 (-36). Diffed the two
databases directly (by `src_row_id, source_field, ev_start, ev_end`): 38
raw edges removed (19 from `article_text`, 19 from `cross_references` —
symmetric because both fields get scanned separately and most of the
affected acts cite the same "Qonun N-moddasi" phrase in both places), from
15 distinct citing rows; 2 new edges added back, both `dst_kind='act'` —
the weaker "Code named, no provision pinned" signal, correctly emitted now
that the false article attribution is gone from those 2 windows. Net -36
matches exactly. `dst_qism` population: 689 -> 665 (-24) — most of the
removed edges had a qism/band tail attached (e.g. "Qonun 19-moddasining
toʻrtinchi qismi"), which is why yesterday's qism/band-attachment miss
sample (row 2767) is no longer in that residual list either (see Active
threads) — it was never a qism-truncation bug, it was this same
misattribution. Reran `measure_extractor_recall.py`: still **0 real misses**
on article and chapter/section recall (2337 windows now, down 3 from 2340 —
those 3 are exactly the newly-scoped-out "Qonun" windows, confirming the
naive checker's own RE_STOP-based scoping moved in lockstep with the real
fix rather than disagreeing with it). Reran `build_llc.py`: no LLC-slice
numbers changed (expected — none of the removed edges touch the LLC Law or
its foundation articles).

**Decision:** ship the "Qonun" fix (measured before, during, and after;
28/28 self-tests; 0 recall regression; exact edge-diff accounted for) and
explicitly do NOT add qaror/farmon/nizom to RE_STOP — there is no measured
bug to fix there today, and adding untested stop words "just in case" is
exactly the kind of unmeasured change this project's methodology exists to
avoid. If a future corpus update introduces the gap for those nouns, the
same throwaway measurement script (not committed — trivially
reproducible from `citation_extractor._anchors()` plus `RE_CLAUSE`) will
catch it.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green.** 28/28
extractor self-tests; 6791 edges (down from 6827, all accounted for above);
AC7's "realization edges from superseded acts" count moved from 983 to 948
(-35, consistent with the edge removal — most of the removed citations
happened to be in acts already flagged superseded); 38 OKOZ mappings still
awaiting the owner's validation (untouched); same reconciliation-detail
list as prior sessions.

### 2026-09-04 — closed the recall thread, fixed a real qism/band gap, opened a precision thread

Continued the Active thread from 2026-09-03. First: this fresh clone's git
history was missing yesterday's commit locally on `main` (only reachable
from a detached HEAD state matching the working tree), even though `git
fetch origin main` showed origin already had it — a stale local
remote-tracking ref, not a real lost-push. Fast-forwarded `main` to it
before starting; `git push` correctly reported "Everything up-to-date". No
data was actually at risk, but worth recording in case it recurs: if a
future session sees a detached HEAD with local commits main doesn't have,
fast-forward first and confirm against a fresh `git fetch` before assuming
work is lost.

**Extended `measure_extractor_recall.py` to all three anchor kinds.**
Previously the recall check only opened windows at literal "Fuqarolik
kodeksi" occurrences (`cx.RE_ANCHOR_CC`), so FK-alias-only and
self-reference-only text never got checked at all, and even where a
"Fuqarolik kodeksi" anchor existed nearby, the naive check's window
boundary was computed independently of the OTHER anchor kinds, so it could
disagree with the window `extract()` itself actually used. Rewrote it to
use `citation_extractor._anchors()` directly — the exact anchor list and
ordering `extract()` uses — so windows are now identical between the naive
checker and the real extractor for all three kinds. Result: **2340 anchor
windows checked (up from 1559), 0 real misses** for both article-level and
chapter/section-level forms, broken down as `{'fuqarolik_kodeksi': 1321,
'fk_alias': 351, 'self_reference': 668}` (article) and `{'fuqarolik_kodeksi':
238, 'fk_alias': 8, 'self_reference': 27}` (chapter/section). One apparent
miss during development (article "11071" found by the extractor but the
naive regex's `\d{1,4}` cap truncated it to "1071") was a naive-detector
artifact, not a real gap — fixed by widening the cap to `\d{1,5}` (superscript
articles like this one can run to 5 digits). This closes the "does recall
hold beyond the core forms" question from 2026-09-03's Active Threads entry:
it does, everywhere measured.

**Found and fixed a real recall gap: qism/band attachment.** Distinct from
"was the article found" (clean, above) is "when article text has a
qism/band clause right after it, does the extractor capture it into
`Citation.qism`". It didn't, for most of the corpus: `extract()`'s qism/band
attachment only fired when the modda word's suffix was exactly "sining"
(genitive, "moddasining") — but a frequency count over ~48k
"N-moddaSUFFIX" occurrences showed "sining" is only 7017 of them, while
"si" (bare "moddasi") alone is 8399, plus thousands more suffix variants
(sida, siga, ning, ...). Measured the gap directly: of 764 single-article
citations with an (extractor's own `RE_QISM`, applied unconditionally)
qism/band-looking tail, **249 (32.6%) had `qism=None` anyway** — 216 of
those on the bare "si" suffix alone. Manually inspected 15 samples; all
were genuine "part N of article M" constructions the "sining"-only gate
was silently dropping (e.g. "212-moddasi uchinchi qismiga muvofiq",
"281-moddasi oltinchi qismining 4-bandida").

Broadening the gate isn't free, though: comma-separated lists like
"185-moddasi, 186-moddasi toʻqqizinchi qismi" would misattribute the ninth
part to 185 instead of 186 if the tail search ignored list structure.
Tested a guard (reject if a comma or another modda/bob number intervenes
between the citation and the qism/band match) against the actual 249 misses
before writing any code: 184 accept / 65 correctly reject, and manual
inspection of both buckets confirmed the split is right (accepts are all
genuinely this citation's own qism; rejects are all list continuations or
citations belonging to a different, unstopped act). Implemented as
`RE_QISM_BLOCK` in `citation_extractor.py`, gating attachment for any
non-"sining" suffix; kept the "sining" path untouched. Added 4 new
self-tests targeting exactly this (accept-adjacent, accept-with-band,
reject-list-continuation, reject-different-act) — 26/26 extractor
self-tests pass.

Reran `build_links.py` (the only script that runs the extractor) against
the existing `corpus.duckdb`: **edge count unchanged at 6827** (confirms the
fix only enriches metadata, doesn't change what's cited or how it resolves)
and **`dst_qism` population rose from 522 to 689 edges (+32%)**. Reran
`build_llc.py` since it reads `link_edge` (no LLC-slice numbers changed).
`verify_transfer.py`: all checks green, same INFO-level findings as
2026-09-03 — see summary below.

Added a permanent qism/band attachment regression check to
`measure_extractor_recall.py` (using the same `RE_QISM_BLOCK` gate as the
real fix) so a future change that narrows the gate again gets caught. It
found 10 residual misses out of 667 checked (1.5%) — traced to a *different*,
smaller bug: the extractor's internal tail lookup is
`window[m.end():m.end()+60]`, and when a citation lands close to its
anchor's own window limit, that tail is truncated to a few characters,
missing a qism/band clause that's well within 60 raw characters of text.
Sampled 3, confirmed truncation (4-14 chars of slack vs. the 60 needed) as
the cause for 2; the 3rd is unexplained. Documented as a new, lower-priority
Active thread rather than fixed today — small (1.5%), and a rushed fix risked
being wrong in a way today's careful, sample-verified qism fix wasn't.

**Went looking for precision bugs and found one, by accident.** One of the
qism-attachment miss samples (row 2767) turned out to not be a Civil Code
citation at all: `'"Davlat boji toʻgʻrisida"gi Qonun 19-moddasining
toʻrtinchi qismi'` — a citation to the *State Duty Law*'s article 19,
wrongly captured as if it were Civil Code article 19, because `RE_STOP`
only recognizes suffixed forms of "qonun" (qonuni/qonuniga/qonunining) and
this uses the bare nominative "Qonun". Measured the scope: 365 raw
occurrences of `Qonun N-modda` (bare) in the corpus, 159 distinct
row/field locations; cross-checked which of those actually got captured
as a false Civil Code citation by the live extractor (matching citation
position against the bare-Qonun match position, not just presence) —
**25 confirmed misattributed edges**. Did not attempt a fix today: a
blanket `qonun\b` addition to `RE_STOP` would also catch the very common
generic phrase "qonun hujjatlarida" ("in legislation"), which has nothing
to do with naming another act, and would silently suppress real Civil Code
citations near it. Recorded as the new Active thread — a capitalization
heuristic (named acts are capitalized, "Qonun"; the generic word isn't,
"qonun") looks promising from the samples but isn't measured yet, and the
same bare-nominative gap plausibly extends to qaror/farmon/nizom.

**Decision:** ship the qism/band fix (measured, sample-verified, self-tested,
verify_transfer.py green) since it's unambiguous and already validated; do
NOT attempt the "Qonun" precision fix in the same session, since getting the
guard right needs its own measurement pass the way the qism fix got one —
rushing it risks trading a real, well-understood fix for a half-measured one
in the same commit. This is now the standing thread for the next session.

`verify_transfer.py`: **VERIFICATION PASSED — all checks green** (26/26
extractor self-tests, 6827 edges unchanged, same INFO-level findings as
2026-09-03's run: 278 acts superseded/983 realization edges, 38 OKOZ
mappings awaiting validation, the same reconciliation-detail list).

### 2026-09-03 — first session: extractor recall, measured corpus-wide

Picked the highest-value Extractor recall/precision item: no gold set exists,
and the backlog's proposed shortcut (compare `article_text` vs
`cross_references` extractions on the same row) looked cheap to try before
committing to hand-annotation. Also had to `pip install duckdb pyarrow` and
`apt-get install git-lfs` + `git lfs pull` first — the parquet ships as a
163MB LFS object and neither LFS nor the Python deps were present in this
fresh clone; without pulling it, `articles/train-00000-of-00001.parquet` is
just a 134-byte pointer file, invisible to any read against the raw layer.

**Tried the cross_references-vs-article_text idea, measured it, and it
failed.** Built the comparison directly from the already-computed
`link_edge` table (build_links.py already runs the extractor separately over
both fields, tagged by `source_field` — no new extraction needed). Result:
4249/4272 (99.5%) of cross_references-sourced Civil Code article citations
have no matching article_text citation on the same row. Manually inspected
4 of these (rows 1073, 1390, 1759, 1764) by reading the raw parquet text: in
every case cross_references correctly points at a real, unrelated provision
in another law (a defense-procurement act's LexUZ footnote pointing at Civil
Code arts 457-458 on contracts; a Water Code article pointing at a Land Code
article) that the citing article's own body text never mentions. This is
LexUZ editorial commentary adding related-reading pointers, not restating
what the act says — so "article_text missed it" is the wrong description;
the two fields are structurally independent, and their disagreement rate
says nothing about extractor recall. Recorded as a falsified hypothesis in
the backlog rather than silently dropped, since another day (or another
resumed session) could otherwise re-try the same dead end.

**Built a working recall check instead, and it passed clean.** Wrote
`measure_extractor_recall.py`: an independent, deliberately dumber "naive"
detector (`\d+-modda`, `\d+-bob`, both scoped by the extractor's own
RE_STOP/RE_STOP_ABBR boundaries so a same-window "FPK 75-moddasi" doesn't
get flagged) run against every "Fuqarolik kodeksi" anchor occurrence across
the full 54,173-row raw corpus (10,348 candidate rows contain "kodeks" or
"FK"), then checked that every naive hit is accounted for by some citation
the real extractor returned in the same window. Result: **0 real misses**,
both for article-level citations (1321 anchor windows, 1469 naive numbers vs
3147 extracted — extractor finds more because it correctly expands lists
and ranges the naive regex can't) and chapter/section-level citations (238
windows, 243 naive vs 256 extracted). Two apparent misses during
development turned out to be bugs in the naive checker itself (not
excluding "IPK 107-moddasi" / "FPK 274-275-moddalari" — other codes'
abbreviations — and not counting the extractor's `section` target kind
alongside `chapter`), both fixed before the final run; the script's
docstring records why. This is a real, corpus-scale validation that the
22 self-tests didn't provide before.

**Decision:** don't build the ~50-article gold set yet — recall on the two
most common surface forms (article and chapter/section citations, which
together are the overwhelming majority of the 6827 edges) is empirically
excellent, so hand-annotation effort is better spent on precision
(misattribution: wrong target doc/article for a correctly-found number) once
the remaining surface forms (qism, band, FK-alias, self-reference) are
checked the same way — see Active threads. No pipeline code changed; this
was pure measurement, so `verify_transfer.py` was not expected to move and
stayed green (45+ checks pass, same INFO-level findings as before).

*(earlier entries go here, newest first, once more sessions run)*
