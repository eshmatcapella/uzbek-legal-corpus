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

- **Amendment chains: built and measured 2026-09-11, closed with two small
  documented residuals.** New `article_amendment` table + `v_article_currency`
  view, mined from the per-article `amendment_note` field rather than the
  backlog's originally-proposed "kiritilsin"-clause detector (see Log for why
  that approach was rejected first). 594 events on 425/1197 Civil Code
  articles; 8 of `verify_transfer.py`'s 9 long-standing unexplained
  `structure_missing_articles`/`md_only` gaps now resolve to an exact voiding
  law + date. Two residuals, both in Backlog, neither worth interrupting this
  thread for: (1) a 2-item list clause ("65 va 66-moddalar") only registers
  its last member — 1 known occurrence (article 65); (2) amending-act
  resolution caps at 5.6% (33/594) because `act.doc_number` is empty
  corpus-wide, same root cause as `repeal_clause`'s own unresolved tail — not
  a parsing gap, a data-acquisition one. **Not done this session**: wiring
  either new table into `app_hierarchy.py`/`app_llc.py`'s UI (grepped both
  first — zero references today, so nothing to break, but also nothing
  surfaced to a user yet). If picked up again: either is a reasonable next
  step, but neither blocks closing this thread.

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
  fallback, same principle as the article-level dangling fallback). "wrong
  qism attachment beyond what's already checked" and "other stop-word gaps
  not yet hypothesized" remain unsearched. Next session: invent another
  falsifiable hypothesis the same way (by sampling extractor output and
  reading the raw text — this has now found a real, fixable gap four
  sessions running: qism/band 09-04, Qonun 09-05, doc_id 09-08,
  chapter+paragraph comma-attachment 09-10). The repeal-resolution thread
  this note used to point to is now closed (see Active threads, 2026-09-09)
  — its 45-item residual turned out to be corpus coverage, not extractor
  precision, so it's not a substitute rotation target here. Cleanup was
  fully drained 2026-09-07 and re-confirmed empty 2026-09-10. Data currency
  ran 2026-09-11 (amendment chains, see Active threads/Log) — rotation
  should land back on Extractor next (another falsifiable-hypothesis pass,
  per above) unless a new Cleanup item surfaces first.

- **Cleanup: fully drained 2026-09-07, re-confirmed empty 2026-09-10.** All
  four backlog items (dead prototypes, `test_transfer_e2e.py` redundancy,
  one-off exploration scripts, `hierarchy_engine.py`'s f-string SQL) were
  resolved in one session — see Log. 2026-09-10 re-audited every remaining
  `execute(f"...")` call in the repo before picking a different rotation
  target: all of them interpolate only the same hardcoded `PARQUET` path
  constant (the established, safe pattern this project's f-string-SQL rule
  is actually about), none interpolate a runtime/data-derived value. Nothing
  left open here unless a future session finds something new to add to the
  Backlog's Cleanup section.

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
- **Build the gold set.** ~50 articles, hand-verified ground truth for
  citation extraction (which acts realize them, at what confidence). No gold
  set exists yet — `citation_extractor.py`'s 32 self-tests (see Log) check
  surface-form parsing, not corpus-wide recall/precision. Recall is measured
  clean across all anchor kinds; the "Qonun" precision bug and the
  superscript-`doc_id` recall bug are both fixed and measured (see Log
  2026-09-05, 2026-09-08). Still no gold set and no systematic search for
  OTHER misattribution patterns beyond the ones found so far by sampling —
  revisit whether hand-annotation is now the highest-value next step or
  whether more hypothesis-driven sampling keeps finding gaps faster (it's 3
  for 3 so far).
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
  Active threads and Log.
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
- **Article-amendment residuals from 2026-09-11** (see Log for full detail):
  (1) a multi-article list clause ("65 va 66-moddalar ... kiritilgan")
  only registers its *last* member — same class of list-swallowing gap as
  the qism/band and chapter+paragraph list bugs found on other threads;
  article 65 is the one known miss. (2) 5/594 clauses are chapter/paragraph-
  level (no article number at all, e.g. "42-bobning nomi ... tahririda") and
  get no `target_article_number` — correct behavior, just worth knowing if
  a future session wants chapter-level currency too. (3) amending-act
  resolution (33/594) only fires when the amending act's own title names
  "Fuqarolik kodeks" — most amendment acts are omnibus bills ("ayrim qonun
  hujjatlariga oʻzgartirish...") that don't, and without `doc_number` there's
  no safe way to disambiguate same-day candidates by number; not worth
  chasing further without a corpus update that populates `doc_number`.
- **Propagate currency into the LLC dossier's implementing-acts list** (and
  eventually the general explorer) as a first-class filter rather than a
  toggle buried in an expander — currency should probably gate what counts as
  "implements" by default.

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

---

## Log

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
