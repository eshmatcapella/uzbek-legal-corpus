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

**Convention change, 2026-10-19 (see Log for the full measurement/reasoning):
this section now holds only the current state of each rotation area, not a
growing day-by-day narrative.** Before today, every closed thread's full
write-up was appended here and never trimmed, even though this section's
own stated purpose ("read Active threads, continue one if mid-flight") only
needs the *current* state. `DAILY_REVIEW.md` had grown to 534KB/8014 lines
(the Read tool's own 256KB cap can no longer load it in one call) — Active
threads alone was 1998 lines/140KB, almost entirely closed-thread detail
that already exists, verbatim, in the Log section below (organized by
date) and in git history. Rewrote this section down to one current-state
bullet per focus area; moved the two genuinely-still-open residuals this
section held that Backlog didn't yet have into Backlog (qism/band tail
truncation; see Backlog > Extractor recall/precision), confirmed every
other residual mentioned in the old text was already present in Backlog,
and dropped the ~117-line rotation-order diary (each area's own
current-state bullet already states its own last-touched date and the
other two areas', which is all the rotation rule needs). Nothing is lost:
every dropped paragraph's full text is still in this file's own git
history and in the dated Log entry it summarized. Going forward, when a
thread closes, fold its outcome into Backlog (if a residual remains) or
just let the Log entry be the permanent record — don't also keep growing a
paragraph here.

- **Extractor rotation — current state: gold set at 500 records (twelfth
  signature-stratified batch), precision 2122/2135 (99.4%), recall
  2122/2158 (98.3%), 456/3251 window signatures covered. Last touched
  2026-10-21** (fixed the qism/band dash-RANGE sub-form — the one
  remaining piece of the 2026-10-18 list-collapse bug, 7 in-scope
  citations corpus-wide; see Backlog > Extractor recall/precision
  "Qism-level grain", now fully closed). **Thread stays open — next
  Extractor rotation should draw gold batch 13** via
  `build_gold_sample_novel.py` (`--seed`/`--n` fresh each time),
  hand-annotate, merge into `gold_citations.json` — deferred two rotations
  running now in favor of two precisely-scoped fixes found while
  annotating/measuring, both good value but neither growing the gold set's
  signature coverage (still 456/3251, unchanged since 2026-10-18). Full
  detail: Log, 2026-10-21.

- **Data currency rotation — current state: fixed a real Roman-numeral
  target_locator gap in `build_links.py`'s repeal-clause parser (113/885
  repeal items corpus-wide, 14 acts' false 'superseded' badge corrected,
  one live in the LLC dossier). Last touched 2026-10-20** (found via a new
  angle — cross-checking internal consistency of the repeal/currency
  signals against each other, rather than re-measuring the already-dry
  snapshot-age thread). `lex.uz` egress re-checked, still 403-blocked, no
  change since 2026-10-17. No thread currently mid-flight; next Data
  currency rotation should pull from Backlog > Data currency — the
  internal-consistency angle used today (checking whether independent
  derived signals agree with each other) worked well and is worth
  applying to other parts of the pipeline (e.g. `article_amendment` vs.
  `repeal_clause` for the same doc_id) if nothing more specific is
  waiting. Full detail: Log, 2026-10-20.

- **Cleanup rotation — current state: eight repeatable checks now exist
  (`pyflakes`, `vulture --min-confidence 60`, `bandit`, `check_sql_bindings.py`,
  `check_code_clones.py`, `check_fstring_interp.py`, plus the folded-in
  f-string grep and its own eighth-check widening). Last touched
  2026-10-16** (closed a structural blind spot in `check_fstring_interp.py`
  itself — found 0 live bugs, but a real class of indirected-f-string call
  sites the tool had never been able to see). One deliberately-deferred,
  single-call-site residual remains in `check_sql_bindings.py` (doesn't
  trace plain-literal indirection; zero injection risk, left alone — see
  Backlog > Cleanup). Next Cleanup rotation should re-run all eight checks
  as a baseline before deciding whether a ninth is worth adding. Full
  detail: Log, 2026-10-16.

---

## Backlog

### Extractor recall/precision
- ~~**Build the gold set.**~~ **Scoring layer built 2026-09-20, grown to 100
  records 2026-09-22, to 140 via signature-stratified sampling 2026-09-25,
  to 220 via two more signature-stratified batches 2026-09-28, to 260 via
  a third 2026-09-29, to 300 via a fourth 2026-10-02, to 340 via a fifth
  2026-10-04, to 380 via a sixth 2026-10-10, to 420 via a seventh
  2026-10-13, to 460 via an eighth 2026-10-15, to 500 via a ninth
  2026-10-18** — see Active threads and Log for the full detail.
  `gold_citations.json` (500 hand-verified anchor occurrences, twelve
  batches — two uniform-random, ten signature-stratified) + `score_gold.py`
  (the scorer) + `build_gold_sample.py`/`build_gold_sample_novel.py` (the
  two samplers) now exist; current score **precision 2120/2133 (99.4%),
  recall 2120/2156 (98.3%)** — the mismatches are the documented "paragrif"
  spelling gap, the 2026-09-25 Roman-chapter+paragraf gap, the 2026-09-28
  "hamda" list-separator gap, the 2026-09-28 chapter+paragraph-list-with-
  parenthetical gap, the 2026-09-28/2026-10-10 "bare article number before
  an interposed different act name" gap (4 rows, now all 4 consistently
  recorded as `known_gap` — see 2026-10-15 log entry for a gold-set
  bookkeeping fix), the 2026-10-04 "§ N" section-mark-notation gap, the
  2026-10-10 chapter+paragraph space-separator gap, and the 2026-10-10
  "moddsi" typo gap (see below), each recorded with its true expected
  output rather than silently marked correct. Not closed outright — 500
  windows is still a small fraction of the 3251 real candidate windows
  corpus-wide (456 distinct window *signatures* covered as of 2026-10-18,
  up from 417/451 after 2026-10-15's batch — signature-stratified
  sampling's own novelty guarantee means every one of batch 12's 40
  windows added a signature the gold set had never seen, the biggest
  single-batch novelty drop yet; 115/3251 candidate windows remain in
  never-annotated territory, down from 737/3251 — see Active threads).
  **Next step, whenever Extractor rotation comes up again**: run
  `build_gold_sample_novel.py`
  again (not `build_gold_sample.py` — see below for why) with a fresh
  `--n`/`--seed`, hand-annotate the batch, and merge into
  `gold_citations.json` — or add a targeted record for any new bug a
  hypothesis-driven session finds, so fixes become permanent regression
  checks instead of one-time. What changed getting here: `build_gold_sample.py` (2026-09-15) built the
  reusable, seeded, stratified sampler over real anchor windows (half
  `extract()`-produced-a-citation, half empty); 2026-09-17's sample found a
  false alarm — a citation that looked like a recall miss in one anchor's
  *display* window but was actually caught by `extract()` via a different,
  nearby anchor occurrence — which is why `score_gold.py` scores recall
  against the whole field's `extract()` output rather than each anchor's
  own local bucket (see Active threads for the full reasoning).
  Hypothesis-driven sampling had found a real, fixable bug in every one of
  9 sessions running before 2026-09-20 (qism/band 09-04, Qonun 09-05, doc_id
  09-08, chapter+paragraph comma-attachment 09-10, qonunning 09-12, three on
  09-15, two more on 09-17); 2026-09-20's batch was the first to come back
  clean (100/100); 2026-09-22's batch found one small real gap (see below).
  **2026-09-25**: with two of the last three batches coming back clean or
  near-clean, built `build_gold_sample_novel.py` instead of drawing a fourth
  uniform batch — it signatures each candidate window's raw-text shape
  (separator type, unit words, qism form, parens, roman numerals, anchor
  kind, etc.) and samples from signatures the gold set has never annotated,
  rather than uniform-random. Measured first: only 58/451 distinct
  signatures were covered by the 100-record set, leaving 1456/3251 (44.8%)
  of all candidate windows in never-annotated territory — this directly
  explains why uniform sampling was running dry. The resulting 40-window
  batch found 1 real bug (see below) + 1 known_gap, a higher yield than the
  two most recent uniform batches — see Active threads and Log for the full
  measurement and the decision to keep using this sampler going forward.
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
- **Roman-numeral chapter citations never get the paragraf/section
  lookahead.** Found 2026-09-25 via the new signature-stratified gold
  sample (see Active threads): "Fuqarolik kodeksi IV bobining 2 paragrafi"
  (row 15441) should produce `target_kind=section` (chapter 4, section 2)
  the same way the Arabic-numeral "37-bobining 3-paragrafi" already does,
  but `extract()`'s Roman-chapter fallback branch (only reached when the
  main `RE_CLAUSE` loop finds nothing) never runs the paragraf lookahead the
  `bob` branch has — it always emits a bare `chapter` citation, silently
  losing the section grain. `dst_kind` is a real `link_edge` column (same
  class of gap as the "paragrif" item above), so this is recorded as a
  `known_gap` gold record (`gold_id` 123) with its true expected output
  rather than scored as correct. Measured corpus-wide: exactly 1 occurrence
  (checked every `RE_ROMAN_CHAPTER` match's 30-char tail for an immediately
  following paragraf reference). Not fixed today, same single-occurrence
  precedent as several items on this list — if ever picked up, port the
  same `sec = re.match(r"\s*,?\s*(\d+)\s*-\s*paragraf", ...)` lookahead the
  `bob` branch already uses into the Roman-chapter branch in `extract()`.
- **Chapter+section citations written with a "§ N" section-mark symbol,
  not the word "paragraf", lose the section grain.** Found 2026-10-04 via
  the eighth signature-stratified gold batch (see Active threads and Log):
  row 41858 reads "Fuqarolik kodeksining 9-bobi § 2" — same semantic
  content as "9-bobining 2-paragrafi" elsewhere in the corpus, but the
  chapter+section lookahead's `sec = re.match(r"\s*,?\s*(\d+)\s*-\s*paragraf", ...)`
  only recognizes the literal word, not "§", so this resolves as a bare
  chapter-9 citation, losing the section-2 grain (same `dst_kind`-affecting
  failure class as the "paragrif" and Roman-chapter-lookahead items above).
  Measured corpus-wide: exactly 2 raw `bob\w*\s*§\s*\d+` occurrences, only 1
  in scope — row 35993's "ushbu Qoidalarning XXI bobiga § 84" is a
  different document's own internal Rules, not a Civil Code citation, and
  never sits inside a Civil Code anchor window. Not fixed given the
  single-occurrence scope, same precedent as the two items above; recorded
  as a permanent `gold_citations.json` known_gap record (`gold_id` 324)
  instead. If ever picked up, accept `§\s*(\d+)` as an alternate spelling
  alongside `\d+\s*-\s*paragraf` in the chapter+section lookahead.
- **LexUZ typo drops an article entirely: "moddsi" instead of "moddasi".**
  Found 2026-10-10 via the ninth signature-stratified gold batch (see Log):
  row 38339 reads "Fuqarolik kodeksining 43-moddsi." — a source-data typo
  (missing the 'a' in "moddasi") that `RE_CLAUSE`'s unit-word match doesn't
  recognize at all, so the whole clause falls through to the bare-act
  fallback and Civil Code Article 43 is dropped entirely — a genuine recall
  miss, not a grain loss. Measured corpus-wide: this exact typo string also
  appears 3 more times in the corpus, but always against a different act
  (Mehnat kodeksi, "mazkur Qonun") entirely out of this extractor's anchor
  scope — so the real in-scope footprint is exactly 1 occurrence. Not
  fixed given the single-occurrence scope, same precedent as the
  "paragrif" misspelling gap; recorded as a permanent `gold_citations.json`
  known_gap record instead (`gold_id` 370). If ever picked up broadly:
  tolerate a missing vowel in "modda"'s suffix the same way "paragraf"/
  "paragrif" could be unified, e.g. `modd a?si|moddalari` or a small
  edit-distance check — but given it's the same 1-occurrence-of-a-typo
  shape as "paragrif", probably not worth the risk of over-matching until
  more instances appear.
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
- **Qism-level (article-part) grain.** `dst_qism` on `link_edge` is
  displayed to users (`app_hierarchy.py::page_article()`, `· part:
  {qism}`), so it IS load-bearing, not just stored — the "not consumed
  downstream" framing this item carried since 2026-09-04 turned out to be
  stale, not current, when re-checked 2026-10-18 (see Log and Active
  threads). **The comma/"va"-separated LIST sub-form is fixed as of
  2026-10-18** — "11-moddasining 1, 4-bandlari" and "377-moddasining
  ikkinchi, toʻrtinchi, oltinchi qismlari" (measured at 68 ordinal-list +
  14 digit-list regex-shape occurrences by 2026-09-25, 63 real in-scope
  citations by the precise 2026-10-18 recount) now correctly emit one
  `Citation` per listed qism/band instead of collapsing to the single
  ordinal nearest the unit word (or to nothing, when a comma triggered
  `RE_QISM_BLOCK`'s unrelated different-article gate). `link_edge` now
  carries 755 `dst_qism` values (was 660) across 9620 edges (was 9535).
  ~~**Still open — the dash-RANGE sub-form...**~~ **Fixed 2026-10-21**:
  "ikkinchi — toʻrtinchi qismlarida" (parts two through four) now expands
  to all three parts instead of collapsing to just the last ordinal —
  `RE_QISM_RANGE`/`_qism_range` added alongside the list-form's
  `RE_QISM_MULTI`/`_qism_list`, resolving each ordinal's position via a
  new canonical-spelling table (`_ORDINAL_CANON`/`_ordinal_index`, since
  `ORDINALS` itself carries two spellings per ordinal and can't be indexed
  directly) and expanding the range the same way `_expand()` expands a
  numeric article range. Confirmed exactly 7 in-scope citations
  corpus-wide, exactly matching the 2026-10-18 scoping (rows 21303, 25801,
  26169, 41003, 43296, 46794, 46898); `link_edge` now carries 769
  `dst_qism` values across 9634 edges. See Log, 2026-10-21.
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
  a future corpus update introduces more of these. **Formalized 2026-09-28**:
  the signature-stratified sampler independently re-drew this exact row
  (`gold_id` 148) — merged as a permanent `gold_citations.json` known_gap
  record with the true two-section expected output instead of leaving it as
  a bare backlog line with no regression check.
- **Bare article number before an interposed different code's own name
  loses its unit word entirely.** Found 2026-09-28 via the second
  signature-stratified gold batch of the day (see Log): row 37948 (an
  amending Oliy sud Plenumi resolution) contains, three separate times,
  "Fuqarolik kodeksining 38, Oila kodeksining 228, 233-moddalari" — "38" is
  a genuine elliptical citation to Civil Code Article 38 (the parallel
  structure with "Oila kodeksining 228, 233-moddalari" makes this
  unambiguous to a human reader), but no unit word (`modda`/`bob`/`paragraf`)
  ever touches "38" directly — the immediately-following different code's
  own name breaks `RE_CLAUSE`'s contiguous digit run before any unit word is
  reached, and the citation falls all the way through to the bare-act
  fallback, dropping article 38 entirely rather than just losing a grain.
  Unlike the comma/va-list gaps on this list, this isn't a missing
  separator — the shared unit word actually lives in a *different* code's
  own clause later in the sentence, which would need real cross-clause
  inference to generalize safely (a materially bigger, riskier change than
  adding "hamda" to a separator alternation). Measured corpus-wide (regex:
  `Fuqarolik\s+kodeksi(?:ning|)\s+(\d+)\s*,\s*` not immediately followed by
  a unit word, then another code's own "...kodeks...ning"): exactly 5 raw
  occurrences across 3 distinct rows (26159, 37948 ×3, 53186) — all five
  name the identical target, Civil Code Article 38, a civil-registry
  cross-reference that recurs verbatim across several related Oliy sud
  Plenumi resolutions on establishing vital-record facts, not a general
  grammar pattern. Not fixed today given the narrow, single-target,
  cross-clause-inference scope; formalized as three permanent
  `gold_citations.json` known_gap records instead (`gold_id` 194-196, one
  per anchor occurrence in row 37948). **Corrected 2026-10-10**: that
  corpus-wide count was itself incomplete — the regex only looked for an
  interposing *kodeks* (code), missing the *Qonun* (law) variant. A wider
  measurement (any CC anchor whose `extract()` falls back to a bare
  act/chapter despite a genuine 2+-digit list sitting right after the
  anchor with no modda/bob/paragraf/qism/band/boʻlim word ever attaching to
  it) found exactly 1 more occurrence: row 42229, "Fuqarolik kodeksining 14,
  15, 324 — 339, 985, 989 va 990, Oʻzbekiston Respublikasining
  "Tadbirkorlik..."gi Qonunining 38-moddasiga..." — the SAME failure
  mechanism, but losing 21 articles in one shot (not 1), immediately before
  a Qonun rather than a kodeks. True corpus-wide count for this failure
  class: 6 occurrences / 4 rows, not 5/3. Formalized as a fourth
  `gold_citations.json` known_gap record (`gold_id` 379). Still not fixed —
  same cross-clause-inference risk as before — but if this is ever picked
  up, the fix needs to treat "a different act's own name" generically
  (kodeks/Qonun/Nizom/Farmon/Qaror), not just kodeks.
- **"hamda" not recognized as a list conjunction, only "va".** Found
  2026-09-15 while fixing the space-separator gap (see Log): row 24219 reads
  "Fuqarolik kodeksining 11-12 hamda 14 moddalari" — `_expand`'s top-level
  split only recognizes "," and "va" between numbers, so "hamda" ("as well
  as") breaks the list there; today's fix already recovers "11-12" as an
  embedded sub-range independently, but a bare number joined only by "hamda"
  (like the "14" here) still comes through fine only because it's the last
  item before the unit word, not because "hamda" is understood — a case
  shaped like "14 hamda 20-moddasi" (hamda-joined, nothing after) would
  still lose "14". **Correction, 2026-09-28**: re-verified this description
  directly (`citation_extractor.extract()` on the exact row 24219 text, plus
  the module's own self-test at the "hamda" case) and it's wrong about
  "11-12" — nothing recovers it. `RE_CLAUSE`'s `nums` group stops extending
  the moment it hits "hamda" (only `,`/`va`/a dash continue it), so the
  whole match backtracks past "11-12" entirely and only re-matches at the
  bare "14" that directly touches "moddalari" — **both "11" and "12" are
  silently dropped, not just "14" degraded to a weaker listing tag**. The
  session that wrote this apparently reasoned about what the 2026-09-15
  sub-range fix *would* do if "hamda" reached `_expand` at all, not what
  actually happens today. Formalized as a permanent `gold_citations.json`
  known_gap record today (`gold_id` 140) with the true three-article
  expected output, so this won't silently drift back into "described but
  unverified" — see Log. **Measured corpus-wide 2026-09-22** (regex search
  for `\d+(?:\s*[-–—]\s*\d+)?\s+hamda\s+\d+\s*[-–—]?\s*(modda|bob|paragraf)`
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
  corpus update adds more. **Formalized 2026-10-10**: the signature-
  stratified sampler independently re-drew this exact row (`gold_id` 341) —
  merged as a permanent `gold_citations.json` known_gap record (this
  backlog note alone was never a regression check until now). Re-confirmed
  still exactly 1 occurrence corpus-wide.
- ~~**Qism range collapses to its last ordinal only.**~~ Found 2026-09-15,
  precisely measured and merged into the "Qism-level (article-part) grain"
  item above on 2026-10-18 (same dash-range sub-form — see that item for
  the current, precise 7-citation count and the fix sketch). Duplicate
  bullet removed 2026-10-19 rather than left to drift from the merged item.
- **Qism/band tail-window truncation.** Found 2026-09-04 while building the
  qism/band attachment check (see Log): the qism/band tail lookup inside
  `extract()` is `window[m.end():m.end()+60]`, and `window` itself is
  capped by the anchor's own limit (the next anchor's start, or `+WINDOW`)
  — when a citation lands close to that limit, the available tail is
  shorter than 60 chars and a qism/band clause just past it is never seen,
  even though it would be well within a raw 60-char slice of the
  underlying text. Measured: 10/667 residual misses (1.5%) when first
  found; re-measured after later fixes, now **7/640 (1.1%)**, unchanged by
  the 2026-10-18 list/range qism work (that fix touches which *ordinals*
  attach to a match already found, not the tail-window's reach). Sampled 3
  by hand: 2 had a confirmed 4-14 char window-slack shortfall vs. the 60
  needed; the third's cause wasn't fully pinned down (ample 249-char slack
  yet still missed). Not fixed — small enough (1.1%) to not be worth
  interrupting other work for, but a real, precisely-measured bug, not a
  vague note. If picked up: either widen the window when a modda-with-tail
  match is the last thing found before the anchor's limit, or search the
  raw text directly (bounded by the *next* anchor, not by `+60` past an
  already-truncated window) instead of re-slicing a pre-cut window.
- ~~**"boʻlim" (Part, the structural level above chapter) is never a
  recognized citation unit.**~~ **Built and closed 2026-10-02.** Found
  2026-09-17 while reading a gold sample (see Log): "Fuqarolik kodeksining
  IV-boʻlimi" cites Part IV of the Code by roman numeral, but `RE_CLAUSE`
  only recognizes `modda`/`bob`/`paragraf` as unit words, so a bare
  Part-level citation (no chapter/article alongside it) falls all the way
  back to a coarse act-level citation, losing the Part distinction
  entirely. Measured corpus-wide at the time
  (`Fuqarolik\s+kodeks\w*\s+[IVXLC]+\s*-\s*boʻlim\w*`): 6 occurrences, all
  genuine. Not fixed then — adding a real Part-level grain means a new
  `target_kind`, roman-numeral parsing, and touching `build_links.py`,
  which wasn't justified by a 6-occurrence count alone. Re-confirmed
  2026-09-28 (still exactly 6 via that same hyphen-only regex). **Built
  2026-10-02** (Extractor rotation, continuing the open gold-set thread):
  the regex itself was undercounting — LexUZ writes the unit word with a
  bare space far more often than with a hyphen, same space-vs-hyphen
  variability already handled for modda/bob/paragraf. Re-measured with the
  hyphen made optional: 20 corpus-wide (14 more via the space form), and
  running the fixed extractor itself (rather than a hand regex) found 5
  *more* real occurrences the literal-text regex structurally couldn't see
  at all — 2 via the `self_reference` anchor ("ushbu/mazkur Kodeksning")
  rather than literal "Fuqarolik kodeksi", and 3 where the part citation
  sits in the same anchor window as an already-matched modda/bob clause
  (e.g. row 38614's "23-bobi ... hamda V boʻlimiga") that the old `if not
  produced` Roman-chapter-fallback-style gating would have skipped. Added
  `RE_ROMAN_PART` to `citation_extractor.py` and a new `target_kind='part'`,
  scanned independently of the modda/bob loop (not gated on `produced`) so
  it can't be silently skipped by an earlier clause in the same window;
  resolved in `build_links.py` via a new `_int_to_roman()` helper to the
  real `struct_node` Part rows (`PI`..`PVI`, already present in the corpus
  from `structure_parser.py` — no new struct data needed). Caught and fixed
  one real false positive the new unconditional scan introduced before
  shipping: row 42566's own "...yoʻriqnoma"ning (roʻyxat raqami 697,
  08.04.1999-y.) IV boʻlimi" (a *different* document's Part IV) was being
  misattributed to the Civil Code, because `RE_STOP` had no entry for
  "yoʻriqnoma" (instruction/guideline) as a named-other-act signal.
  Measured corpus-wide before adding it: 11 anchor windows mention
  "yoʻriqnoma" at all, and row 42566 is the *only* one where a modda/bob/
  paragraf/boʻlim clause of any kind follows it within the window — zero
  collateral loss elsewhere. **Net new/corrected `link_edge` rows**: 24
  real `dst_kind='part'` edges after dropping that false positive (22 via
  the `fuqarolik_kodeksi` anchor, 2 via `self_reference`); total edge count
  9530 -> 9535. Updated 5 pre-existing `gold_citations.json`
  records (gold_id 134/170/186/193/200, rows 21686/32449/35586/37887/38614)
  whose correct expected output changed from a bare `act` (or no part field
  at all) to include the new part citation — these were previously scored
  `correct` only because the schema had no field to express the gap
  against, same treatment this backlog item always got; now scored correct
  against real, resolved output. Added 6 self-test cases (57/57 passing, up
  from 51/51 at the session's start). `pyflakes`/`vulture
  --min-confidence 60`/`bandit` clean on both changed files (`bandit`'s 14
  pre-existing `B608` hits unchanged); `unittest test_transfer_e2e.py`
  14/14; `verify_transfer.py` green, same General-Part-coverage INFO
  numbers as before (372/386 cited, 285/386 below) — this feature adds a
  coarser-than-chapter target kind, it doesn't change which articles are
  cited. Both apps smoke-tested live (HTTP 200, no exceptions); confirmed
  `app_hierarchy.py`'s existing "citations to this article's chapter/
  section as a whole" query (already written generically against
  `v_realization_struct`, no code change needed there) correctly surfaces a
  real part-level citation for an article under Part II. See Log.

### Data currency
- **New angle worth repeating: cross-check independent currency/evidence
  signals against each other, not just against external ground truth.**
  Found 2026-10-20 (see Log): every prior Data currency rotation either
  measured a signal's precision/recall against a known cause, or tried to
  compare against an external source (`lex.uz`, blocked). Today's fix
  (Roman-numeral `target_locator` gap, below) was found instead by asking
  whether `repeal_clause` was internally self-consistent — do multiple
  whole-act repeal candidates for the same `dst_doc_id` make sense
  together? That question surfaced a real, 113-occurrence, 14-act-impact
  bug the other two framings hadn't touched. Worth trying again on other
  pairs of independent signals this project computes — e.g. does
  `article_amendment` (mined from `amendment_note`) ever disagree with
  `repeal_clause` (mined from free-text "kuchini yoʻqotgan" lists) about
  the same act/date/target? Not measured yet — just the methodology note.
- ~~**Repeal-clause `target_locator` misses Roman-numeral qualifiers
  ("XIV boʻlimi", "XX moddasi").**~~ **Fixed 2026-10-20** (see Log for the
  full trace): `build_links.py`'s `re_target_locator` only recognized
  Arabic-digit-plus-hyphen locators; 113/885 repeal-list items use a
  Roman numeral instead (112 "boʻlim"/Part, 1 bare "modda"), silently
  defaulting to "whole act repealed". 14 acts flipped from
  `v_act_currency.derived_status = 'superseded'` to `'no repeal found'`
  once fixed, including one (doc -42953) that was showing a false 🔴
  whole-act badge on a live amendment in the LLC dossier today. Re-ran
  `build_links.py` + `build_llc.py`; `verify_transfer.py` green
  throughout (248 -> 234 provably-superseded acts). No known residual in
  this regex — re-measured with the broadened fix before shipping.
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
  session wants chapter-level currency too. (2) ~~amending-act resolution
  (33/594 clauses) only fires when the amending act's own title names
  "Fuqarolik kodeks"~~ — **fixed 2026-09-24**: a new `date+cc-clause-match`
  tier joins on the target article number appearing in a same-date
  candidate's own Civil-Code-amending block instead of its title, taking
  resolution from 43/612 (7.0%) to 454/612 (74.2%) without needing
  `doc_number` at all. See Active threads and Log for the false-positive risk
  that had to be ruled out first and the exact measurement. **Residual
  158/612 diagnosed and mostly fixed 2026-09-27**: root cause was
  `text_by_doc` sourcing an amending act's full text through
  `src_provision` (which only holds rows that themselves produced a
  `link_edge`), so a long omnibus act's OTHER pagination chunks — same
  corpus_id, different raw rows — were invisible to the block-match. Reading
  every raw row for the doc_id directly instead of routing through
  `src_provision` fixed it with zero regressions: resolution
  454/612 (74.2%) -> **521/612 (85.1%)**. See Active threads and Log for the
  full measurement and the worked example (doc -6809366's Article 26¹
  insertion clause, invisible in the one src_provision chunk kept, present in
  a different one of its 9 raw pagination rows). **Residual 91/612 (14.9%)
  mostly closed 2026-09-30**: root-caused the bigger half (57, "CC mentioned
  elsewhere, not in the target's own block") down to its real cause for the
  biggest cluster within it — not a smarter block heuristic, but a genuine
  scrape-completeness gap (the amending act's own raw text is missing the
  portion that would contain both the Civil-Code-naming header and the
  target articles, for the acts affected). Built a new
  `date+sole-law-cc-mention` tier that doesn't need the missing text at all:
  when exactly one same-date `doc_type='law'` act's captured text mentions
  the Civil Code anywhere, use it (safe because the citing grammar already
  guarantees the true amending act is always a `Qonun`). Resolution
  521/612 (85.1%) -> **573/612 (93.6%)**, 52 newly resolved, zero
  regressions. See Active threads and Log for the full measurement, the
  four hand-verified worked examples, and the one (non-colliding) 62-pair
  retroactive-agreement check. **New residual: 39/612 (6.4%)** — most of the
  remaining dates have 2+ `law`-type candidates that are either genuinely
  ambiguous (both/all mention the Civil Code) or where neither candidate's
  captured text mentions it at all (the 2025-04-17 cluster, 19 events,
  checked both its law-type candidates directly — same scrape-completeness
  class as the newly-fixed cluster, not a solvable ambiguity). Diminishing
  returns past this point, same conclusion the repeal-resolution thread
  reached for its own non-statute residual 2026-09-09 — not worth
  re-opening without a new angle (most plausibly, a more complete source
  scrape of the specific affected acts, which is outside `build_links.py`'s
  reach).
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
- **`date+cc-clause-match`'s same-block check degrades to a whole-document
  search for 13/58 distinct amending acts.** Found and fully investigated
  2026-10-08 (see Log, 2026-10-08, for the full trace): `cc_blocks()` finds
  zero top-level `"N-modda."` markers in 13 of the 58 documents this tier
  resolves to (older Roman-numeral-structured omnibus acts, and modern
  standalone laws whose own articles are referenced as "ushbu Qonunning
  N-moddasi" rather than headed "N-modda."), so the whole document (up to
  161KB) becomes one block. **Not a live bug today**: verified
  `host_article_number == target_article_number` for all 478
  `date+cc-clause-match` rows, so this tier never actually has to pick the
  right ARTICLE out of a block — only the right ACT, which held up on
  inspection for every candidate case checked. Only worth revisiting if
  `target_articles()` in `build_links.py` is ever extended to parse a
  genuine multi-article list/range for `article_amendment` (it can't
  today) — at that point the same-block check would need real
  article-level discrimination and these 13 documents would become a
  measurable risk. Do not re-open this without that trigger; a regex fix
  was prototyped, tested, and deliberately reverted today for lack of a
  confirmed bug to justify it.
- **`act.version_date` (LexUZ's scrape date) surfaced as a snapshot-age
  signal, 2026-10-11 — shipped, not just measured** (see Log for the full
  trace): 78/245 (31.8%) of acts realizing a General Part article, and
  33/135 (24.4%) of LLC implementing acts, are >3 years past their own
  scrape date AND carry no positive repeal signal from this project's own
  text-based detector — their "current law" status rests entirely on an
  unrefreshed scrape. Tried to check this against the live lex.uz source
  directly first; blocked by this environment's egress policy (`lex.uz` is
  not in the allowed domains). Shipped the honest fallback instead: both
  apps now show "LexUZ snapshot: DATE (~Ny old — verify at lex.uz)" on a
  realizing act's citation card once it passes 3 years old. **If ever
  picked up again**: (1) re-run the live comparison if `lex.uz` is ever
  added to this environment's allowed domains — turns "how old" into "is
  it actually stale"; (2) the 3-year threshold is round-number legible,
  not tuned against any labeled staleness data (none exists corpus-wide);
  (3) ~~the same signal isn't yet wired into `v_act_currency`/
  `v_act_partial_repeal`'s own whole-act 🔴/⚠️ badges in the General Part
  explorer, only the two realization-citation panels touched today.~~
  **Done 2026-10-14**: wired into the LLC dossier's two remaining whole-act
  badge spots, `app_llc.py::page_acts()` and `page_currency()`'s
  governing-law chip (see Active threads/Log) — 43/135 LLC implementing
  acts now show the note. ~~(2) the 3-year threshold is round-number
  legible, not tuned against any labeled staleness data (none exists
  corpus-wide).~~ **Tested 2026-10-17, resolved as "no tunable signal
  exists"**: `repeal_clause`'s 357 confirmed-repealed acts ARE labeled
  staleness data (the claim "none exists" was itself wrong); tested
  scrape age against them and found no positive correlation with
  repeal risk — if anything, a measured *negative* one (confirmed-
  repealed acts average 6.86y scrape age vs. 9.98y for unflagged acts,
  bootstrap 95% CI [-4.14, -2.08], after controlling for a real
  crawl-batch-clustering confound in `version_date`). See Active
  threads/Log for the full measurement. Decision: keep 3.0 as a
  legible round number (there's no data-driven alternative to tune to),
  but stopped implying a risk verdict in the UI copy — "verify at
  lex.uz" became "since last scrape" in both apps'
  `snapshot_age_note()`. (1) the live lex.uz comparison remains open,
  still blocked on this environment's egress policy as of 2026-10-17 —
  re-check only occasionally, not every rotation, since this is an
  environment-policy question, not something more measurement against
  `corpus.duckdb` can resolve. (4) Open, minor: whether `snapshot_age_note()`'s
  copy should go further and drop the number entirely in favor of a neutral
  "last scraped" framing with no implied age judgment at all — not done
  2026-10-17 since the current copy no longer makes an unsupported claim,
  just worth a second look if a future session wants to push further.

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
- ~~**f-string SQL beyond the known `hierarchy_engine.py` offender.**~~
  **Audited and fixed 2026-09-26**: swept all 29 `execute(f"...")` call
  sites across the codebase (the `hierarchy_engine.py` deletion on
  2026-09-07 closed the one *known* offender but nothing had checked for
  others since). Found 3 real violations of the project's own rule —
  `build_gold_sample_novel.py:169-172`, `score_gold.py:90-93`,
  `build_llc.py:253-257`, all interpolating a runtime-computed int list into
  an `IN (...)` clause instead of binding it — fixed with DuckDB's
  `IN (SELECT * FROM UNNEST(?))` idiom. Confirmed `app_hierarchy.py`/
  `app_llc.py` (the actual user input surface) already have zero f-string
  SQL. See Active threads and Log for the full audit and the
  byte-identical-output verification (`build_llc.py`: 132/132
  `llc_implementing_act` rows unchanged between pre-fix and post-fix runs).
  A repeatable third Cleanup check now exists alongside `pyflakes`/
  `vulture`: `grep -n 'execute(f"' *.py` and re-classify anything new
  against "hardcoded constant vs. runtime value" — cheap enough to re-run
  every time this rotation comes up again, not just once.
- **New, small paper cut found while fixing the above (not itself a
  violation)**: the git-lfs-pointer-stub cold-start failure
  (`verify_transfer.py`'s AC3 previously surfaced it as a bare DuckDB "no
  magic bytes found" error, costing a diagnostic detour in roughly 15 prior
  sessions per the Log) is now fixed too — `_check_parquet_pulled()` at the
  top of `verify_transfer.py::main()` gives an immediate, actionable
  `SystemExit` instead. This doesn't remove the actual cold-start step
  (`git lfs pull` still has to run every session until the container image
  preinstalls `git-lfs`, which is outside this project's control) — just
  the diagnostic cost of that step failing silently-wrong instead of
  loudly-right. Nothing left to do here; recorded for context only, in case
  a future session wonders why this guard exists.
- ~~**A fourth static-analysis tool class beyond pyflakes/vulture/f-string
  grep.**~~ **Added 2026-10-01**: `bandit` (security-pattern linter) found 3
  issue classes — 57 `B608` (re-discovery of already-audited f-string SQL,
  not new), 3 `B311` (non-cryptographic-random false positives in
  `verify_transfer.py`'s sampling, reviewed and left alone), and 1 `B110`
  (`except Exception: pass`) that led to finding a real bug: one assertion
  in `test_transfer_e2e.py`'s `test_r1_markdown_extraction` claimed to test
  `parser.py`'s real output but was structurally incapable of doing so since
  the project's first commit (a dict-vs-list shape mismatch), silently
  re-testing the internal reimplementation under a misleading label instead.
  Fixed and proved with a before/after regression (393-vs-394 count,
  undetected before the fix, correctly caught after). See Active threads and
  Log for the full trace. `bandit -r . -x ./articles,./documents,./okoz,./structure`
  is now a fourth repeatable Cleanup check; next rotation should re-run all
  four (pyflakes/vulture/f-string grep/bandit) before deciding whether a
  fifth is worth adding.
- ~~**A fifth check: something beyond pyflakes/vulture/f-string grep/bandit,
  none of which understand SQL semantics.**~~ **Added 2026-10-03**:
  `check_sql_bindings.py` — AST-extracts every plain-literal SQL query passed
  to `q()`/`qdf()`/`execute()` in the read-only app/analysis layer
  (`app_hierarchy.py`, `app_llc.py`, `verify_transfer.py`, `score_gold.py`,
  `measure_extractor_recall.py`, `build_gold_sample.py`,
  `build_gold_sample_novel.py` — deliberately *not* the `build_*.py`
  pipeline scripts, whose `CREATE TABLE`/`CREATE VIEW`/temp-table-dependent
  statements aren't validatable this way and already self-validate on every
  successful run) and validates each one against the live `corpus.duckdb`
  schema via DuckDB's `PREPARE` statement, which resolves every table/column
  name without needing bound parameter values. 106/119 call sites in scope
  are checked today (the other 13: 4 are the `q`/`qdf` helper definitions, 8
  are f-strings already covered by the grep audit, 1 is a single
  variable-indirected literal, not resolved); all 106 bind cleanly. Proved
  with a mutation test (a scratch copy of `app_llc.py` with one column
  renamed) that it catches exactly the class of drift none of the other four
  tools can see — a schema-breaking typo that's still valid Python, still a
  "used" string, with no injection shape. See Active threads and Log for the
  full measurement and the build-script-exclusion reasoning. Now a fifth
  repeatable Cleanup check; next rotation should re-run all five.
- ~~**A sixth check: something that catches drift between hand-duplicated
  copies of the same helper logic.**~~ **Added 2026-10-09**:
  `check_code_clones.py` — AST-diffs every function (>=4 body lines) across
  every `*.py` file pairwise with `difflib.SequenceMatcher`, flagging
  cross-file pairs at similarity >= 0.55. 91 functions, 4 flagged pairs, 0
  live bugs (all 4 hand-verified as either byte-identical-and-consistent or
  intentionally-different-by-design — see Active threads/Log for the full
  trace). A SQL-block-level variant was tried first and rejected as too
  noisy (54 false-positive-heavy pairs from shared SQL vocabulary). Now a
  sixth repeatable Cleanup check; next rotation should re-run all six.
- ~~**A seventh check / a fix to the third: the `execute(f"` grep (added
  2026-09-26) is a single-line literal match and can't see a call whose
  f-string sits on a different source line than `execute(`.**~~ **Added
  2026-10-12**: `check_fstring_interp.py` — AST-walks every f-string
  `execute()` call regardless of line layout, recursively resolving each
  interpolated expression to a hardcoded constant via intra-function
  dataflow rather than trusting a variable's name. Found 20 call sites in
  `test_transfer_e2e.py` the grep had never once seen, one of which was a
  real violation (`query_db_article_text_en()` interpolating a runtime
  `norm_id` into SQL) — fixed by parameterizing it. Proved with a mutation
  test against the pre-fix file; a first, name-based-allowlist draft of
  the checker failed that same test, which is why the shipped version
  resolves structurally instead. See Active threads/Log for the full
  trace. Now a seventh repeatable Cleanup check, and it subsumes the third
  (`execute(f"` grep) going forward — next rotation should re-run all
  seven, which in practice means the six scripted checks plus this one;
  the plain grep itself doesn't need a separate re-run anymore.
- ~~**An eighth check / a fix to the seventh: `check_fstring_interp.py`'s
  own `find_calls()` only matches `execute()` calls whose f-string is the
  *direct* argument, so `query = f"..."` then `execute(query)` on a later
  line was invisible to it entirely (not even counted), not merely
  unresolved.**~~ **Fixed 2026-10-16**: added `_contains_joinedstr()` and
  widened `find_calls()` to trace a bare-name argument back to an f-string
  via the same intra-function `Assign` chase `_is_safe()` already does,
  reusing that existing resolver unchanged for the safety verdict itself.
  Proved the gap with a mutation test first (a runtime value spliced into
  a scratch copy of `test_transfer_e2e.py` in exactly this indirected
  shape passed the pre-fix script clean, with the call count unchanged).
  Measured the real population: exactly 6 `execute(<bare name>)` sites
  codebase-wide — 4 are the `q()`/`qdf()` helper definitions (out of
  scope), 1 is a fully literal string with no interpolation
  (`measure_extractor_recall.py`), 1 is a real indirected f-string
  (`test_transfer_e2e.py::test_r3_alignment_key_matching`, safe today via
  the `PARQUET_PATH` constant but reached by luck of the blind spot, not
  by design). Zero live bugs found, but the structural gap was real — same
  precedent as `check_sql_bindings.py`'s own 106/106-clean debut. See
  Active threads and Log for the full trace. Now an eighth repeatable
  Cleanup check (folded into the existing script, not a new file); next
  rotation should re-run all eight. One deliberately-deferred residual:
  `check_sql_bindings.py` still doesn't trace *plain-literal* indirection
  (the `measure_extractor_recall.py` site above) — zero injection risk
  since it has no interpolation, so left alone for a single call site, same
  single-occurrence-scope precedent as several Extractor items above.

---

## Log

### 2026-10-21 — Extractor rotation: closed the qism/band dash-RANGE sub-form left open 2026-10-18 — 7 in-scope citations fixed, `link_edge` 9620 -> 9634 edges, one stale gold record corrected

Picked up the one item the 2026-10-18 entry explicitly scoped and deferred
rather than drawing gold batch 13 this time (see rationale at the end):
`citation_extractor.py`'s qism/band attachment still collapsed a dash
RANGE of ordinals ("216-moddasining birinchi — uchinchi qismlari" = parts
one through three) down to just the one ordinal immediately before the
unit word, even though the sibling comma/"va"-separated LIST shape got
fixed two rotations ago. Measuring this precisely matters because the
naive approach — grep the whole corpus for `ORD[-–—]ORD\s*qism|band` —
overcounts by two orders of magnitude: "qism"/"band" are ordinary Uzbek
words well outside any Civil Code citation ("harbiy qism" = military
unit, a government resolution's own numbered "band" list items,
hyphenated compounds like "oʻzini-oʻzi band"), so a first pass of that
regex found 1657 "ordinal-ish" and 2684 digit matches corpus-wide — almost
all noise. Rewrote the measurement to mirror `extract()`'s own anchor+
clause scan exactly (reusing `_anchors`, `RE_CLAUSE`, `RE_LEADING_PUB_PAREN`
and the real per-row FK-alias table build_links.py itself computes) and
got exactly 7 in-scope hits, landing on precisely the 7 rows the
2026-10-18 entry had already named (21303, 25801, 26169, 41003, 43296,
46794, 46898) — first pass only found 5 of the 7 until the FK-alias table
was wired in correctly (two of the seven, rows 25801/26169, only resolve
once "FK" is recognized as an alias for "Fuqarolik kodeksi" in those
specific acts, same subtlety `build_links.py` itself has to handle).

Fix: added `RE_QISM_RANGE` alongside the existing `RE_QISM_MULTI` (list
form), anchored the same way at the start of the post-modda tail through
one optional leading comma so it can never fire on the different-article
list shape `RE_QISM_BLOCK` guards against. Expanding an ordinal range
needed a lookup `ORDINALS` itself can't give directly — that tuple
carries two spellings per ordinal (the apostrophe-letter `ʻ` vs plain
ASCII `'` for "toʻrtinchi"/"toʻqqizinchi"/"oʻninchi"/"oʻn birinchi"/"oʻn
ikkinchi"), so indexing into it directly would misorder or double-count.
Added `_ORDINAL_CANON` (one canonical spelling per ordinal, 12 entries)
and `_ordinal_index()` (normalizes `ʼ`/`'` to `ʻ` before lookup), then
`_qism_range()` expands `range(lo_index, hi_index + 1)` into
`_ORDINAL_CANON` the same way `_expand()` already expands a numeric
article range — a lookup, not a new numbering scheme, per the 2026-10-18
entry's own plan. A reversed range (hi before lo, or either endpoint not
a recognized ordinal) returns `None` and falls through to the pre-existing
single-match behavior unchanged — regression-tested explicitly (see
below). Wired into both call sites that already tried `_qism_list(tail)`
first (the `-sining` genitive path and the bare-`moddasi` single-article
path): `_qism_list(tail) or _qism_range(tail)`, list form still tried
first since it is more specific. No digit-range form ("3 — 5-qismlari")
exists in-scope anywhere in the corpus (confirmed by the same scoped
measurement), so none was built — would be pure speculation otherwise.

Added 4 self-tests to `citation_extractor.py`'s own suite (61 -> 65,
all passing): the three real dash spellings observed in the corpus
(plain hyphen, en dash, em dash) each expanding to the right 3-part run,
plus a reversed-range regression guard confirming the old single-match
fallback still fires unchanged when the range isn't a valid range.
Re-ran `build_links.py` against the existing `corpus.duckdb` (not a full
`build_corpus_db.py` rebuild — only the extractor changed): `link_edge`
9620 -> 9634 edges (+14, exactly the expected 7 citations × 2 extra parts
each — every one of the 7 ranges is 3 ordinals wide), `dst_qism`
non-null count 755 -> 769 (+14, matching exactly). Spot-checked all 7
target rows' real `extract()` output directly: every one now lists all
ordinals in its range (e.g. row 46794's article 476: uchinchi/toʻrtinchi/
beshinchi qism; row 26169's article 154: birinchi through toʻrtinchi
qism).

Running `score_gold.py` after the fix surfaced a real, expected
consequence rather than a regression: precision dropped from 2120/2133
(99.4%) to 2120/2135 (99.3%, +2 FP) because `gold_citations.json`'s own
`gold_id` 289 (row 46898) had been hand-annotated against the *old,
buggy* collapsed output — its `expected` list recorded only `{"article":
"382", "qism": "toʻrtinchi qism"}` for the window's "382-moddasi ikkinchi
— toʻrtinchi qismlari", not the full three-part range. Same precedent as
the 2026-10-18 fix's own stale-annotation cleanup (gold_id 224 et al.):
corrected the record to the true expected output (ikkinchi/uchinchi/
toʻrtinchi qism, all three) with a dated note explaining why, rather than
leaving a now-incorrect record silently degrading the score. Final:
precision 2122/2135 (99.4%, back to the pre-fix rate — the 2 extra
correct predictions and the 2 corrected expected entries cancel out
exactly), recall 2122/2158 (98.3%, unchanged ratio, denominator grew by
the same 2 newly-correct entries). `citation_extractor.py`'s own 65
self-tests, `test_transfer_e2e.py`'s 14 tests, and `verify_transfer.py`
all pass clean.

Why this over gold batch 13 (the thread's stated "next step" two
rotations running now): with this fix, the "Qism-level grain" backlog
item (open since 2026-09-04, partially fixed 2026-10-18) is now fully
closed rather than carrying one small, precisely-scoped, already-
documented residual — finishing a scoped, already-measured fix over
starting new annotation work seemed like the higher-value use of today's
rotation, especially since the fix itself doubled as a second real-world
test of the gold set's own annotation-staleness failure mode (same
mechanism as 2026-10-18, confirms it's a repeatable thing to watch for,
not a one-off). Gold batch 13 remains the clear next step whenever
Extractor rotation comes up again — signature coverage is unchanged
today (456/3251) since nothing here touched the sampler or the gold set's
breadth, only one existing record's correctness.

### 2026-10-20 — Data currency rotation: found and fixed a real Roman-numeral target_locator gap in `build_links.py`'s repeal-clause parser — 14 acts' false 'superseded' badge corrected, including one live in the LLC dossier today

Rotated to Data currency per the rotation rule — oldest of the three
(last touched 2026-10-17; Extractor 10-18, Cleanup 10-19). Environment:
`git lfs install && git lfs pull` (parquet was a 134-byte LFS pointer
stub), `python3 -m pip install duckdb pytest pyflakes vulture bandit`
(`python3` is 3.11, bare `pip`/`pip3` target a separate 3.13 dist —
same recurring mismatch earlier sessions documented). Baseline
`verify_transfer.py` green before touching anything.

Quick re-check first (per Backlog's "re-check occasionally" note):
`lex.uz` is still blocked by this environment's egress policy (403 on
the CONNECT tunnel, confirmed via the agent-proxy status endpoint) —
no change since 2026-10-17, not worth another look for a while.

New angle for this rotation: rather than re-running the snapshot-age
thread (already measured dry on 2026-10-17 — no tunable signal), cross-
checked the *internal* consistency of the repeal/currency machinery
itself — do the independent signals (`repeal_clause` whole-act vs.
partial, `v_act_currency`, `v_act_partial_repeal`) agree with each
other, something no prior rotation had tested. Found it by querying
which acts have *multiple* distinct whole-act repeal candidates
(`target_locator IS NULL`) in `repeal_clause`: 108 acts do, all sharing
one surface shape — many different later acts, all citing the exact
same historical date+title, with `cited_date` identical across every
row for a given `dst_doc_id`. Read the raw text for one (`dst_doc_id`
-44853, itself the 1999-08-20 "832-I" omnibus amending law): 9 later
acts (2007-2022) each void one numbered item in 832-I's own list, not
832-I as a whole — but `repeal_clause.target_locator` recorded `NULL`
(whole-act) for every one of them.

Root cause: `build_links.py`'s `re_target_locator` only recognizes a
locator written as Arabic digits + hyphen + `modda|qism|band|bob|
paragraf` (e.g. "9-moddasi"). The actual text uses Roman numerals with
no hyphen: "XIV boʻlimi" (Part 14) and, in one case, "XX moddasi"
(article 20). Neither the unit word ("boʻlim", Part — the structural
tier above chapter) nor the numeral system was recognized, so every
such item silently fell through to the "no qualifier found = whole act
repealed" default. `citation_extractor.py` already solved the boʻlim
half of this for its own, independent CC-citation grammar
(`RE_ROMAN_PART`, 2026-10-02) — it was never ported to this module's
separate repeal-locator regex, and this module never had a
Roman-numeral-modda case at all.

Measured the true corpus-wide scope by re-implementing the exact
match-and-window logic standalone (so it could be tested against
variant regexes before touching the real pipeline): of 885 total
repeal-list items, 487 fell back to "whole act" under the old regex.
113 of those (23%) are this gap — 112 boʻlim, 1 modda (found by
noticing one act, -205727, still showed a single remaining whole-act
row after the first boʻlim-only version of the fix — its raw text
turned out to be the "XX moddasi" case, which is what prompted folding
Roman-numeral-modda into the same branch rather than shipping a
narrower boʻlim-only fix and leaving modda as a known_gap). Traced
real downstream effect, not just a classification nicety: resolving
each rescued item's `dst_doc_id` and checking whether it had any OTHER
genuine whole-act evidence left, **14 acts corpus-wide currently show
`v_act_currency.derived_status = 'superseded'` with zero remaining
whole-act evidence once the gap is fixed** — every one of their
"whole-act" `repeal_clause` rows was this same misparsed qualifier.
3 of the 14 are realizing acts in `link_edge` (visible in the General
Part explorer), and one, doc -42953 (a 1998 omnibus amending act), is
an `llc_implementing_act` row **literally showing the LLC dossier's 🔴
whole-act badge today** on a still-genuinely-live amendment to Civil
Code article 53 — a real, user-visible false positive, not a
theoretical one.

Fixed in `build_links.py`: added a Roman-numeral branch to
`re_target_locator` covering all five existing units plus boʻlim
(`[IVXL]{1,6}(?:\s*-\s*|\s+)(?:modda|qism|band|bob|paragraf|
bo[ʻʼ']?lim)\w*`), same bare-space-instead-of-hyphen and
apostrophe-letter tolerance the digit branch and
`citation_extractor.py`'s own `RE_ROMAN_PART` already use. Re-ran
`build_links.py` (repeal_clause: whole-act count 487 -> 374, i.e. 113
items correctly reclassified as partial) then `build_llc.py` (its
`llc_implementing_act.derived_status` is a materialized join against
`v_act_currency`, so it goes stale otherwise) — did not re-run
`build_okoz.py` (no dependency on repeal/currency data) or
`build_corpus_db.py` (raw-text extraction untouched). Verified all 14
predicted doc_ids flipped from `superseded` to `no repeal found`
exactly as measured, confirmed -42953's dossier badge specifically.

`verify_transfer.py`: **all checks green** (248 -> 234 "provably
superseded" acts, 495 -> 492 realization edges from them — the AC7
checks that depend on repeal direction/evidence all still pass).
`citation_extractor.py` self-tests 61/61 unaffected (different
module). `test_transfer_e2e.py`: 14/14 pass. `pyflakes`,
`check_sql_bindings.py` (106 queries, 7 files), `check_fstring_interp.py`
(55 calls, 18 files) all clean on the touched file. Both apps' affected
queries (`app_llc.py`'s `v_act_currency`/`derived_status` joins,
`app_hierarchy.py`'s `v_realization`/`v_act_currency` join) smoke-tested
directly against the rebuilt db — same schema, corrected values, no
query errors. No schema change anywhere, so no second sanity pass
needed beyond that.

Decision: this is a plain correctness fix to an already-documented
regex (same file, same design decision, no new column or table), not a
case needing the "single-occurrence, not worth the risk" deferral this
project applies elsewhere — 113 corpus-wide occurrences with measured,
concrete, user-visible impact clears that bar easily. Closed, not
reopened: no known residual in this specific regex today (re-measured
with a broadened regex before shipping, found exactly the 1 "XX
moddasi" case and folded it in rather than leaving a second known_gap
next to a freshly-fixed first one).

### 2026-10-19 — Cleanup rotation: paid down `DAILY_REVIEW.md`'s own unbounded growth — Active threads 1998 lines/140KB -> 61 lines/~4.3KB, whole file 534KB -> 399KB, zero code/data touched

Rotated to Cleanup per the rotation rule — oldest of the three (last
touched 2026-10-16; Data currency 10-17, Extractor 10-18). Environment:
`git lfs install && git lfs pull` (parquet and `corpus.duckdb` were both
already real files, not pointer stubs, for once — no cold-start detour),
`python3 -m pip install duckdb pandas streamlit pyflakes vulture bandit`.
Local `main` was one push behind `origin/main` on container start (HEAD
detached 4 commits ahead of the stale local ref, at 2026-10-18's own
`a790aee`) — same recurring stale-local-pointer pattern earlier sessions
have documented (2026-09-09, 2026-10-09, 2026-10-12, 2026-10-18), this
time inverted the same way 10-18 found it; `git checkout main && git
reset --hard origin/main` resynced, no data at risk (`origin/main` is
always the real source of truth here).

Started by re-running the eight repeatable Cleanup checks as the backlog's
own "next rotation" instruction says: `pyflakes`/`vulture
--min-confidence 60` clean; `bandit` 61 issues (4 Low/57 Medium, same
57 B608/3 B311/1 B110 breakdown as every prior baseline); `check_sql_bindings.py`
106/106; `check_code_clones.py` 5 cross-file pairs (same as every prior
baseline — no new clone); `check_fstring_interp.py` 55/55. No drift since
2026-10-16; all eight confirmed healthy before doing anything else.

Then, rather than stopping there (there was no ninth static-analysis gap
suggesting itself), turned Cleanup's lens on this project's own operating
document. Tried to read `DAILY_REVIEW.md` whole, the way a fresh session
does on cold start, and hit a hard wall: the Read tool refused — file was
534,487 bytes, over its 256KB single-read cap. That's not a hypothetical
problem; it's the literal first thing this session's own harness hit
today, and it would hit every session from here on, worse each day.
Diagnosed why: "Active threads" is documented as holding only *current*
state ("read Active threads, continue one if mid-flight") but in practice
every closed thread's full write-up had been appended there and never
trimmed since the file's creation — 1998 lines / 140,601 bytes (26% of
the whole file), almost entirely narrative that already exists verbatim
in the dated "Log" section below and in git history. One single bullet
(`"Precision, more broadly: still open beyond 'Qonun'"`) had become a
117-line day-by-day rotation diary, appended to on nearly every session
since 2026-09-10, that existed purely to track which focus area ran last
— information each day's own current-state bullet already restates for
all three areas in one sentence.

Audited every one of the ~31 bullets in the old "Active threads" before
touching anything, to make sure nothing would be lost (see the bullet-by-
bullet classification done live this session — not reproduced here, but
every decision below followed directly from it): (1) 3 bullets are
genuinely current state (Extractor's 12th-batch result, Data currency's
snapshot-age test, Cleanup's 8th-check close) — kept, compressed to one
paragraph each with a "full detail: Log, YYYY-MM-DD" pointer. (2) ~25
bullets are fully superseded by one of those 3, or closed with zero
residual (amendment chains, repeal resolution's 45-item residual, the
"Qonun" fix, the LLC currency-default decision, etc.) — every one of
their residuals was cross-checked against "Backlog" by name and confirmed
already present there (most of Backlog's own entries use in-place
strikethrough edits rather than appending, which is exactly the
discipline Active threads was missing) — dropped, with the Log's own
dated entry remaining the permanent record, same role git history already
plays. (3) Exactly 2 residuals were genuinely still open and NOT yet in
Backlog: the qism/band 60-char tail-window truncation (7/640, 1.1%,
root-caused but unfixed since 2026-09-04) and a stale, pre-10-18 duplicate
of the dash-range qism item that Backlog's own "Qism-level grain" entry
had already superseded with the precise 2026-10-18 count — moved the
former into Backlog as a new bullet with its full measurement, replaced
the latter with a one-line "merged, see above" pointer rather than letting
it drift from the entry that actually tracks the live state. Also added
one small addendum to Backlog's snapshot-age item (the "should the copy
drop the number entirely?" open question Data currency's 2026-10-17 entry
raised but never filed) so it isn't silently lost along with the diary
bullet that used to carry it.

Result: "Active threads" is now a ~60-line convention note plus one
current-state paragraph per focus area (each stating its own last-touched
date, which is all the rotation rule needs — the standalone diary bullet
is gone). Whole file: 534,487 -> ~399,000 bytes (-25%), 8014 -> ~6095
lines (-24%); "Active threads" alone: 140,601 -> ~4,300 bytes (-97%).
Verified nothing is lost, not just asserted it: every dropped paragraph's
full text remains recoverable via `git log -p -- DAILY_REVIEW.md` and
via the dated Log entry it summarized (Log itself untouched — it's
designed to grow forever, the same role git commit history already
plays, and isn't what a fresh session needs to read to get oriented); the
two genuinely open residuals were relocated, not deleted; nothing in
Backlog changed except the two additions above. This is purely a
documentation change — no `.py` file, `corpus.duckdb`, or the raw
parquet was touched, so there was nothing to rebuild and no behavior to
regression-test; ran the full existing verification suite anyway as due
diligence rather than assuming a text-only change is automatically safe:
`python3 citation_extractor.py` 61/61; `python -m unittest
test_transfer_e2e.py` 14/14; `verify_transfer.py` green, same INFO/PASS
counts as 2026-10-18 (9620 edges, 372/386 General Part articles cited,
248 superseded acts, etc. — nothing moved); both apps started live via
`streamlit run --server.headless true` (HTTP 200, clean logs, no
exceptions) and torn down after.

**Decision, per the hard constraint** ("if you think a documented
decision is wrong, say so and propose the change rather than quietly
reverting it"): this project's own instructions (top of this file) never
said to let Active threads grow forever — they say it exists so a fresh
session can "read Active threads, continue one if mid-flight," which only
ever needed current state. The append-forever pattern was an emergent
habit, not a documented decision, so this isn't overriding anything the
owner deliberately chose — but flagging the going-forward convention
explicitly anyway, in the note now at the top of Active threads, so it's
a visible norm rather than something a future session has to re-infer
from this one entry: when a thread closes, fold any residual into
Backlog and let the Log entry be the permanent record; don't also keep
extending a paragraph in Active threads. If this pattern recurs (Log
itself will keep growing by design — ~7KB/entry, so roughly 2.5MB/year at
the current one-entry-per-day cadence), the next load-bearing fix is
likely splitting Log by month/quarter into separate files once a fresh
session's *targeted* reads (not a whole-file read, which nothing in the
brief actually asks for) start getting expensive too — not yet justified
by anything measured today, just the obvious next pressure point if this
cadence continues for another few hundred sessions.

Thread: no new backlog work started today (this was Cleanup's own
process-hygiene pass, not a code change) — next Cleanup rotation should
resume at "re-run all eight checks, decide on a ninth" since that step
is still unaddressed (today's checks came back clean, same as 2026-10-16,
with no new gap-class found); next Extractor rotation should draw gold
batch 13; next Data currency rotation should pick from Backlog > Data
currency (no thread currently mid-flight there).

### 2026-10-18 — Extractor rotation: twelfth gold batch (460 -> 500), found and fixed a real 63-citation qism/band grain bug, corrected 9 pre-existing gold records it exposed, rebuilt link_edge

Rotated to Extractor per the rotation rule — oldest of the three (last
touched 2026-10-15; Cleanup 10-16, Data currency 10-17). Environment:
`git lfs install && git lfs pull`, `python3 -m pip install duckdb pandas
streamlit pyflakes vulture bandit` (`python3` is 3.11, `pip3` targets a
separate 3.13 — same recurring mismatch). Container started with its
local `main` ref 3 commits *behind* `origin/main` (the inverse of the
usual "ahead" stale-pointer pattern earlier sessions documented) — `git
fetch origin main` then `git checkout main && git reset --hard
origin/main` fixed it; no data at risk, `origin/main` is always correct.

Drew batch 12 (`build_gold_sample_novel.py --seed 20261018 --n 40`,
417/451 signatures covered before drawing). Hand-read all 40 against the
raw text. 37/40 immediately correct; 3/40 shared one surface shape: a
single modda citation naming 2+ qism/band ordinals at once ("497-moddasi
birinchi, ikkinchi qismlari"; "377-moddasining oltinchi va yettinchi
qismlarida"). `RE_QISM` only ever grabbed the ordinal adjacent to the
unit word, and the comma form was actively zeroed out by
`RE_QISM_BLOCK` — a gate correctly built for "185-moddasi, 186-moddasi
toʻqqizinchi qismi" (comma separates two DIFFERENT articles) firing on
the same shape for the wrong reason when the comma instead separates two
qisms of the SAME article.

This is the exact gap the "Qism-level (article-part) grain" backlog item
measured on 2026-09-25 (a regex-shape upper bound: "14 digit-list + 68
ordinal-list occurrences") and deliberately deferred, reasoning "qism
isn't consumed downstream" every time it came up since. Re-checked that
premise today instead of taking it on faith: it's false.
`build_links.py` has written `Citation.qism` into `link_edge.dst_qism`
since 2026-09-04 (689/9535 edges already carried a value), and
`app_hierarchy.py::page_article()` has rendered it to users as `· part:
{qism}` since before this session. Per the hard constraint ("if you
think a documented decision is wrong, say so and propose the change
rather than quietly reverting it"): fixed the extraction-layer bug today
(self-contained, low-risk, independently correct regardless of later
schema decisions) while leaving the separate, bigger question — whether
to expand `link_edge`'s schema further around qism — untouched for the
owner.

Measured the TRUE count against `extract()`'s real output rather than a
regex-shape estimate: **63 real in-scope article citations** carry 2+
qism/band ordinals this way. Fixed via `RE_QISM_MULTI`/`_qism_list()` in
`citation_extractor.py`: matches an unbroken ordinal/digit run
immediately before qism/band (a bare digit excluded via lookahead
whenever it starts a different "N-modda/bob" citation, so the
different-article shape still falls through to the untouched old
single-match/gate path), only engaging when 2+ tokens are found so a
single-ordinal match defers entirely to the old logic, unchanged. Emits
one `Citation` per qism/band found. Added 4 self-test cases (comma list,
"va" list, a 5-way list, the different-article regression guard) —
`61/61` extractor self-tests pass.

Post-fix: 62/63 locations resolve completely. The 63rd (row 46795's own
"564-moddasi birinchi, ikkinchi qismlari", later in the same long list
gold_id 23 sampled) still reads `qism=None` — traced to the anchor's
`WINDOW=260` cutoff simply running out before reaching that modda at all;
identical before and after this fix, an unrelated pre-existing
truncation limit not worth widening for one row.

`score_gold.py` against the fix surfaced 9 PRE-EXISTING records (gold_id
6, 131, 224, 242, 244, 259, 329, 348, 349, dated 2026-09-04 through
2026-10-04) that flipped from `correct` to a spurious false positive —
each one's original hand-annotation had verified the article number but
not that every qism/band was captured, so each `expected` silently
carried the same under-measurement. Re-read all 9 against the raw text
and the fixed extractor's window-bounded output, corrected each
`expected` to the true multi-entry list, documented inline in each
record's `notes`. **Final score: precision 2120/2133 (99.4%), recall
2120/2156 (98.3%) on 500 windows** (up from 460) — unchanged in
percentage (qism isn't part of the scoring signature); diffed the full
mismatch list against the pre-fix run and confirmed the only remaining
mismatches are the same 13 pre-existing documented records, zero new
noise from today's 9 corrections. **New signature coverage: 456 covered,
115/3251 windows remain never-annotated** (down from 737) — the biggest
single-batch novelty drop yet.

While measuring, found a second, DIFFERENT qism sub-form still open: a
dash-RANGE ("uchinchi — beshinchi qismlari" = parts three through five,
not a list) — the sub-form 2026-09-15 flagged but never measured
precisely. Measured against the fixed extractor: exactly 7 in-scope
citations corpus-wide. Not fixed today (genuinely different
implementation, needs range-expansion like `_expand()` already does for
article numbers; much smaller footprint than the 63 just fixed) — left
as a precisely-scoped Backlog item instead of folding it into today's
claim or silently leaving it undocumented.

Re-ran `build_links.py` (not `build_corpus_db.py` — only the extractor
changed) to carry the fix into the actual database: `link_edge` 9535 ->
9620 edges (+85), `dst_qism` populated on 660 -> 755 edges (+95). Re-ran
`build_llc.py` too since it joins `link_edge` (output unchanged, as
expected — the fix changes which qism attaches to an edge, not which
edges exist at the article-number grain `build_llc.py` keys on);
`build_okoz.py` doesn't touch `link_edge` at all (confirmed via grep), so
left alone, and `okoz_assignment`'s `validated_by`/`validated_at` was
never touched. Confirmed the fix is actually visible: queried
`app_hierarchy.py`'s own `v_realization` article-panel query directly
against the rebuilt `corpus.duckdb` for Article 377 — now returns both
`'oltinchi qism'` and `'yettinchi qism'` self-reference rows where only
the latter existed before. `llc_norm`'s foundation mappings have no
`validated_by`/`validated_at` column at all (checked `build_llc.py`'s own
`CREATE TABLE` — that validation lives in the curated `FOUNDATION` dict
in source, not a runtime flag), so re-running it touched no human
validation state.

Verified: `61/61` extractor self-tests; `python -m unittest
test_transfer_e2e.py` 14/14; `verify_transfer.py` green (AC5's "9620
edges carry evidence" and AC7 all PASS); `pyflakes`/`vulture
--min-confidence 60` clean on every touched file; `bandit` unchanged (61
issues, same 57 B608/3 B311/1 B110 breakdown); `check_sql_bindings.py`
106/106; `check_fstring_interp.py` 55/55; `check_code_clones.py` still
exactly the same 5 cross-file pairs (no new clone); both apps started
live (HTTP 200, clean logs, no exceptions) and torn down after. Raw
parquet untouched throughout (sha256 unchanged per `verify_transfer.py`'s
own AC3 check) — only `corpus.duckdb` (via `build_links.py`/
`build_llc.py`, both `CREATE OR REPLACE`, no wholesale rebuild),
`citation_extractor.py`, and `gold_citations.json` changed. Thread stays
open — next Extractor rotation should draw batch 13; the dash-range qism
sub-form is now a precisely-measured, ready-to-pick-up Backlog item.

### 2026-10-17 — Data currency rotation: tested the snapshot-age threshold against real ground truth for the first time, found it has no predictive signal, softened the UI copy to match

Rotated to Data currency per the rotation rule — oldest of the three
(last touched 2026-10-14; Extractor 10-15, Cleanup 10-16). Environment
setup: `git lfs install && git lfs pull` (parquet starts as a 134-byte
pointer stub); `python3` resolves to 3.11 but the pre-wired `pip3`
targets a separate 3.13 install, so `python3 -m pip install duckdb
pandas numpy streamlit pyflakes vulture bandit` (not bare `pip3
install`) — same interpreter mismatch 2026-10-15 already documented.

Re-checked backlog item (1) (the live lex.uz comparison) first, since
it's a one-line check: `curl -sS https://lex.uz/` still fails
(`CONNECT tunnel failed, response 403`), and
`$HTTPS_PROXY/__agentproxy/status`'s `recentRelayFailures` confirms it
as a policy denial, `lex.uz:443` — unchanged since 2026-10-11, nothing
new to report.

Picked up item (2): "the 3-year threshold is round-number legible, not
tuned against any labeled staleness data (none exists corpus-wide)."
Questioned that last clause — `repeal_clause` already records 357
distinct acts (`dst_doc_id`) this project's own text detector has
positively confirmed were repealed by a later act, each carrying its
own `act.version_date` (LexUZ's scrape date for that act). That's
exactly the labeled ground truth the backlog note said didn't exist:
for these 357 acts we KNOW the staleness-detector's answer is "yes,
actually changed," independent of scrape age. The open question
`snapshot_age_note()` is implicitly answering is "does an old
`version_date` predict that an act is more likely to be in this
confirmed-changed state" — directly testable.

**Confound found first**: `act.version_date` is heavily batch-
clustered, not a smooth per-act timeline. 24,267 acts carry a
`version_date`, but only 4850 distinct date values — the single
busiest date, 2021-02-22, alone accounts for 1228 acts (5.1% of the
whole corpus with a date), and the top 10 dates range from 104 to 1228
acts each. These are clearly bulk LexUZ re-crawl sweeps (an entire
batch of unrelated acts scraped the same calendar day), not
individually-triggered "someone flagged this page" events. Confirmed
this confound actually matters by bucketing every dated act by how
many other acts share its exact `version_date`: acts in a >=100/day
mass-crawl bucket (3485 acts) show a **0.00%** repeal-signal rate,
vs. 2.33% (medium batch, 10-99/day, 9585 acts), 1.27% (small batch,
2-9/day, 9279 acts), 0.83% (unique day, 1918 acts) — a mass-crawl
`version_date` carries essentially zero information about an
individual act's real status, since it's a scheduling artifact, not a
content-triggered check.

**Controlling for the confound**: restricted to the "clean" population
(batch size <10, so each `version_date` was shared by at most 9 other
acts — far more likely to be an individually-relevant re-check), n =
11,197, overall repeal rate 1.20%. Binned scrape age into 1-year
buckets (0-1, 1-2, 2-3, 3-4, 4-5, 5-7, 7-10, 10-15, 15+): repeal rate
by bucket is 0.59%, 3.04%, 0.94%, 1.65%, 1.70%, 2.14%, 0.44%, 1.08%,
0.61% — flat and noisy, no rising trend with age and no inflection
point anywhere near 3 years (or anywhere else). Pearson
r(age, has_repeal) = -0.04. Comparing the two groups' mean scrape age
directly: acts WITH a confirmed repeal signal average **6.86 years**
old (n=134), acts with NO repeal signal average **9.98 years** old
(n=11,063) — the *opposite* direction from "an older scrape means
higher staleness risk." A 5000-resample bootstrap on that 3.13-year
difference gives a 95% CI of [-4.14, -2.08], clearly excluding zero —
this isn't noise, the effect (such as it is) runs backward from the
threshold's premise. Plausible reading: LexUZ's crawler seems to
revisit a page somewhat preferentially around when something about it
changes, so an old, never-refreshed `version_date` is weak evidence
the page's content hasn't needed attention — not evidence it's
drifted out of date unnoticed.

**Decision**: this falsifies "scrape age predicts staleness risk" for
the one ground truth available, so there is no empirical basis for
picking a different, "tuned" number — fitting a threshold to a signal
with no measured correlation would just be fitting noise, and 3.0
remains exactly as legible a round number as any other choice would
be. Per the hard constraint on documented design decisions ("if you
think one is wrong, say so and propose the change rather than quietly
reverting it"): did not remove the feature — the scrape date is still
genuine, useful provenance information, and 2026-10-11's own docstring
already took care to disclaim it as "not a verdict, just how old the
snapshot is." What *had* drifted from that stated intent was the
shipped copy: `snapshot_age_note()` in both apps rendered "LexUZ
snapshot: DATE (~Ny old — **verify at lex.uz**)" — an imperative that
reads as a risk alarm, which today's measurement shows isn't earned.
Changed the return string in both apps' identical `snapshot_age_note()`
copies (same deliberate-duplicate function `check_code_clones.py`
already tracks) to "LexUZ snapshot: DATE (~Ny since last scrape)" —
keeps every fact (date, computed age), drops the unsupported
imperative — and added a comment above each copy recording today's
numbers so a future session doesn't have to re-run this measurement to
know why 3.0 is unvalidated-but-not-worth-re-tuning.

Verified: `pyflakes app_hierarchy.py app_llc.py` and
`vulture --min-confidence 60 app_hierarchy.py app_llc.py` both clean;
`bandit -r . -x ./articles,./documents,./okoz,./structure` unchanged
at 61 issues (4 low/57 medium/0 high, same 57 B608/3 B311/1 B110
breakdown as every prior session back to 2026-10-01); `check_sql_bindings.py`
106/106; `check_fstring_interp.py` 55/55 call sites clean (no new
f-string call introduced); `check_code_clones.py` 100 functions, same
exactly 5 cross-file pairs as baseline, `snapshot_age_note()`'s pair
still `[IDENTICAL 1.000]` (both copies' return strings changed in
lockstep, so it's a true duplicate still, not drift);
`python -m unittest test_transfer_e2e.py` 14/14;
`python verify_transfer.py` — all AC1-AC7 checks green ("VERIFICATION
PASSED — all checks green"); both apps started live via
`streamlit run ... --server.headless true` on throwaway ports (8601,
8602), both HTTP 200 with clean logs (only the normal Streamlit/
Uvicorn startup banner, no exceptions), torn down after. `corpus.duckdb`
and `articles/train-00000-of-00001.parquet` both untouched — this
entire session only ever read them; no rebuild was needed since this
was an app-layer copy/comment change, not a schema or view change.

`git diff --stat`: `app_hierarchy.py` +15/-1, `app_llc.py` +6/-2 — the
scoped comment-and-copy change only, confirmed via `git status
--short` before staging.

### 2026-10-16 — Cleanup rotation: closed a structural blind spot in `check_fstring_interp.py` itself (eighth repeatable check), zero live bugs

Container started detached from `refs/heads/main`, one commit *ahead* of
the local `main` ref (local `main` was stuck at `9834165`, `HEAD` and
`origin/main` both already at `00a5935` — 2026-10-15's eleventh-gold-batch
commit). Same recovery as every prior session that's hit this: `git fetch
origin main` confirmed `origin/main` already matched `HEAD` exactly, then
`git checkout -B main origin/main`. Toolchain gap, same shape as recent
sessions: `duckdb`/`pandas`/`pyflakes`/`vulture`/`bandit`/`streamlit` all
missing from this fresh container; `python3 -m pip install -U ...` fixed
it (this time a plain `pip install` without `-U` landed in the right
3.11 interpreter already — the 3.11-vs-3.13 split some prior sessions hit
didn't reproduce today, so that one may be container-image-revision-
dependent rather than permanent; worth a one-line note in case it recurs).
`articles/train-00000-of-00001.parquet` was already the real 163MB file,
not a pointer stub, so no `git lfs pull` was needed this time either.

Rotation: Cleanup last touched 2026-10-12, older than Data currency
(10-14) and Extractor (10-15) — clear next pull per the rotation rule.
Baselined all seven existing checks before looking for anything new:
`pyflakes`/`vulture --min-confidence 60` clean; `bandit -r . -x
./articles,./documents,./okoz,./structure` 61 issues (4 Low/57 Medium by
severity, same 57 B608/3 B311/1 B110 breakdown as every prior session);
`check_sql_bindings.py` 106/106 bind cleanly; `check_code_clones.py` 99
functions parsed, the same 5 cross-file pairs as 2026-10-09 (2 identical,
1 near-dup, 2 similar — all previously hand-verified, nothing new);
`check_fstring_interp.py` 54/54 clean. All seven unchanged from their
last-recorded baselines — no drift since 2026-10-12.

Looked for an eighth gap-class rather than re-running the same seven
blind. First tried the obvious extension of the project's own rule —
grepped the whole codebase for SQL assembled via `.format()` or
`+`-string-concatenation involving a non-literal — zero hits either way;
dead end, but cheap to rule out and now ruled out. Then asked a sharper
question specifically of `check_fstring_interp.py`, the newest and most
structurally sophisticated of the seven: its own `find_calls()` requires
`node.args[0]` to be *literally* `ast.JoinedStr` before it even tries to
resolve anything, so `query = f"...{x}..."` followed by `conn.execute
(query)` on a later line never enters its result set at all — the same
shape of blind spot the 2026-09-26 `execute(f"` grep (single-line literal
match) and the 2026-10-12 AST rewrite that replaced it each found in
their own predecessor, one level deeper this time: not "wrong line
layout" but "one assignment away from the call entirely".

Proved it with a mutation test before fixing anything, same methodology
every prior check-script addition in this project has used: copied
`test_transfer_e2e.py` to scratch, spliced a runtime-derived value
(`runtime_doc_id = str(-111189)` — a function call result, not a
hardcoded constant) into `test_r3_alignment_key_matching`'s existing
`query = f"...{PARQUET_PATH}..."` / `self.conn.execute(query)` shape. Ran
the pre-fix script against the mutated file: `checked 19 f-string
execute() calls` — identical count to the unmutated original, meaning the
mutated call site was never even seen, not merely misjudged safe. That's
the sharpest possible confirmation the gap is structural.

Measured the real population across the whole codebase before fixing —
every `*.execute(<bare name>)` call site, regardless of what the name
resolves to: exactly 6, corpus-wide.
  - 4 are the `q()`/`qdf()` helper definitions in `app_hierarchy.py`
    (`:113`,`:117`) and `app_llc.py` (`:48`,`:52`) — `check_sql_bindings.py`
    already treats these as out of its own scope by name; they're the
    generic plumbing every other query in those two files calls through,
    not a SQL string to audit in themselves.
  - 1 is `measure_extractor_recall.py::check_cross_reference_disagreement()`'s
    `q = """...multi-line literal..."""` then `con.execute(q)` — a fully
    literal triple-quoted string with zero interpolation anywhere in it;
    zero injection risk regardless of indirection.
  - 1 is the real case: `test_transfer_e2e.py::test_r3_alignment_key_matching`'s
    `query = f"SELECT ... FROM read_parquet('{PARQUET_PATH}') WHERE doc_id
    = -111189"` then `self.conn.execute(query)`. Safe today only because
    `PARQUET_PATH` is a SCREAMING_CASE module-level constant (verified at
    its definition, line 47) — but safe by luck of what currently happens
    to be assigned there, not because the tool meant to check it. This is
    structurally the same family as the `query_db_article_text_en()` bug
    `check_fstring_interp.py` was built to catch on 2026-10-12; it simply
    hadn't been written one assignment away from its `execute(` call at
    the time.

Fixed by adding `_contains_joinedstr()` — a small sibling to the existing
`_is_safe()` that asks "does resolving this pass through an f-string at
all" (chasing `Name` -> `Assign` the same way `_is_safe()` already does)
rather than "is it safe" — and widening `find_calls()`'s match condition
to accept a bare `ast.Name` first argument when `_contains_joinedstr()`
says yes, in which case the whole argument (not a sub-expression) becomes
the one thing `main()` asks `_is_safe()` to verify. No new resolution
logic was needed for the safety verdict itself: `_is_safe()`'s existing
`ast.Name` branch (chase every `Assign` to that name within the same
function, recurse) already handled exactly this shape — it just never
used to be *reached* from a top-level call argument, only from inside an
f-string's own interpolations.

Re-ran the mutation test post-fix: now correctly flagged — `checked 20
f-string execute() calls` / `1 interpolated expression(s) that don't
resolve to a hardcoded constant: ...mut_test.py:436 {query}`. Ran the
fixed script against the real, unmutated `test_transfer_e2e.py`: 20/20
clean (one more in-scope call than the pre-fix 19, the
`PARQUET_PATH`-indirected one, resolved safe exactly as expected).
Corpus-wide: `check_fstring_interp.py` now checks 55 f-string execute()
calls (54 -> 55), all clean — no new bug, but a closed blind spot that
could have hidden one.

Re-verified nothing else moved after the fix: `pyflakes`/`vulture
--min-confidence 60` clean on the changed file; `check_code_clones.py` 100
functions parsed (99 -> 100, the new `_contains_joinedstr()` helper),
still the same 5 cross-file pairs, no new clone introduced; `bandit`
unchanged (61 issues, same breakdown); `check_sql_bindings.py` 106/106
unaffected (disjoint scope); `verify_transfer.py` green end to end;
`python -m unittest test_transfer_e2e.py` 14/14; both `app_hierarchy.py`
and `app_llc.py` started live (HTTP 200, clean logs, no exceptions) and
torn down after — unaffected by this change but checked per the project's
own standing constraint. `corpus.duckdb` and
`articles/train-00000-of-00001.parquet` both untouched — this entire
session only ever read the database, never wrote it. Deleted all scratch
mutation-test files before committing.

**Decided and why**: eight repeatable Cleanup checks now exist
(`pyflakes`, `vulture`, `bandit`, `check_sql_bindings.py`,
`check_code_clones.py`, `check_fstring_interp.py` plus its own newly-fixed
indirection handling — the `execute(f"` grep is still fully subsumed, not
revived). One residual gap noted but deliberately not fixed today, same
single-occurrence-scope precedent this project already applies elsewhere
(the "paragrif"/Roman-chapter/"§ N" Extractor gaps, all left unfixed at
exactly 1-2 occurrences): `check_sql_bindings.py` still never traces
*plain-literal* indirection, so `measure_extractor_recall.py`'s
`execute(q)` stays unchecked for schema drift specifically (not for
injection — it has no interpolation at all, so there's nothing to inject).
Fixing that would mean teaching `check_sql_bindings.py` the same
Name-chasing `check_fstring_interp.py` already has, for exactly one call
site with zero security relevance — not worth it today; worth revisiting
only if a second such site ever appears. Next Cleanup rotation should
re-run all eight checks before deciding whether a ninth gap-class exists;
candidates not yet tried: whether any `CREATE VIEW` built by the
`build_*.py` pipeline scripts has gone unqueried by both apps and all
analysis scripts (a SQL-object-level `vulture`), or whether any numeric
threshold (e.g. the 3-year snapshot-age cutoff, still on the Data-currency
backlog as "untuned") is duplicated as a second hardcoded literal
somewhere instead of a single named constant.

### 2026-10-15 — Extractor rotation: eleventh gold batch, 420 -> 460 records; broke the clean-batch streak not with a new bug but a fixed gold-set inconsistency

Container toolchain gap, same shape as recent sessions: `duckdb`, `pandas`,
`streamlit`, `pyflakes`, `vulture`, `bandit` all absent from this fresh
container. `pip3 install duckdb` appeared to succeed but installed into the
wrong interpreter — `python3` resolves to `/usr/bin/python3.11` (3.11.17)
but `pip3` is wired to a separate Python 3.13 (`pip 24.0 from
/usr/lib/python3/dist-packages/pip (python 3.13)`), so `import duckdb`
still failed after a "successful" install. Fixed with `python3 -m pip
install duckdb pandas` (and later `pyflakes vulture bandit streamlit` the
same way) — same fix pattern 2026-10-14's entry already documented, worth
restating since it keeps recurring across fresh containers.
`articles/train-00000-of-00001.parquet` was a 134-byte git-lfs pointer
stub, not the real 163MB file; `git lfs install && git lfs pull` fetched
the real file before `verify_transfer.py` would even import successfully.

Rotation: the Extractor thread (last closed-batch touch 2026-10-13) was
mid-flight per its own closing note ("next Extractor rotation should draw
batch 11"), so continued it directly rather than re-deriving rotation order
from the other two areas' dates (Cleanup 10-12, Data currency 10-14).
Re-verified the baseline first: `verify_transfer.py` green, `score_gold.py`
on the as-is 420-record set reproduced the exact numbers the last log entry
claimed (precision 1895/1906, recall 1895/1929) before touching anything.

Drew batch 11: `python build_gold_sample_novel.py --seed 20261015 --n 40`.
Pre-draw stats matched the 2026-10-13 entry exactly (3251 candidate windows,
451 distinct signatures, 377 already covered, 958 windows/91 signatures
novel) — a good cross-session consistency check that nothing about the
corpus or the signature function had silently drifted. Hand-read all 40
windows against the raw parquet text and `citation_extractor.py`'s live
`extract()` output, checking every list/range expansion, every RE_STOP
boundary against an interposed different act or code name, and every
chapter/section/part grain. **39/40 verdict `correct`** — list expansions
("va"/comma/dash/doubled-en-dash ranges, including a 13-article range and
a 21-item-wide one), Roman-numeral chapters and parts, chapter+paragraf
sections, bare-act fallbacks for true act-level mentions (including two
cases where "Fuqarolik kodeksi" appears only inside the quoted *title* of
an unrelated Plenum resolution — correctly still falls back to the weak
`act` signal per the project's existing by-design behavior, not a bug),
and multiple different-act/different-code stop boundaries all matched
hand-verification exactly.

The 1 exception, gold_id 451 (row 26159): "Tushuntirilsinki, Fuqarolik
kodeksining 38, Oila kodeksining 228, Fuqarolik protsessual kodeksining
274-moddalari..." — Article 38 of the Civil Code is named but the suffix
"-moddalari" that would pin it is captured by the *third* code's own
number instead, so `extract()` falls through to the bare-`act` fallback
and silently drops Article 38. This is not a new bug: it is the identical
failure class gold_id 194-196 documented on 2026-09-28 ("bare article
number before an interposed different code's own name"), and that
session's own corpus-wide measurement already named this exact row
(regex-matched 5 raw occurrences across 3 distinct rows: 26159, 37948 x3,
53186) — it just never got its own `gold_citations.json` record until
today, the same kind of five-week prose-only backlog gap gold_id 341
formalized on 2026-10-10. Recorded it as `known_gap` with the honest
`expected: [article 38]` rather than counting it as a fresh finding.

Formalizing gold_id 451 meant re-reading the other two rows gold_id 194's
measurement named, to confirm they're each represented correctly. Row
37948 already has its 3 `known_gap` records (gold_id 194-196). **Row
53186 did not**: `gold_citations.json` already contained two records for
this row (gold_id 295, 331), and gold_id 295 — the exact same
"Fuqarolik kodeksining 38, Oila kodeksining 228, 233-moddalari" phrase,
same anchor pattern — was recorded `verdict: correct` with
`expected: [{"target_kind": "act", ...}]`. Ran `citation_extractor.py`
directly against row 53186's actual `article_text` to double check this
wasn't a subtly different, genuinely-`act`-only occurrence: it produces
the identical bare-`act` fallback citation_extractor.py always does for
this failure class, at the exact anchor position gold_id 295 recorded.
This was a real gold-set inconsistency, not a code bug — gold_id 295 pre-
dates the 2026-09-28 discovery of this failure class entirely (it reads
like an earlier, less-informed annotation pass that hadn't yet learned to
recognize the pattern), and no session since had revisited it even though
2026-09-28's own measurement already named row 53186 by number. Corrected
gold_id 295 to `known_gap` with `expected: [article 38]`, matching its
siblings. All 3 rows gold_id 194 originally counted (26159, 37948, 53186)
are now consistently `known_gap` in the gold set for the first time; the
corpus-wide count for this failure class is unchanged at 6 occurrences /
4 rows (the 4th row, 42229, is the separate *Qonun*-interposing variant
gold_id 379 found on 2026-10-10) — today's work only fixed how faithfully
the gold set represents a count that was already correct, it didn't
change the count itself.

Merged batch 11 into `gold_citations.json` (420 -> 460 records) via a
one-off script (not committed — scratch merge logic, same pattern every
prior batch-merge session has used) and fixed gold_id 295 in the same
pass; appended the new `_meta.batches[]` entry and extended
`_meta.description`. **Score after merging**: precision 1988/2001
(99.4%), recall 1988/2024 (98.2%) on 460 windows — both percentages
essentially unchanged from 420 (1895/1906 = 99.4% / 1895/1929 = 98.2%),
because gaining one `known_gap` record (451) and converting a second
existing record to `known_gap` (295) is a 2-citation swing against 39
fully-clean windows' worth of new citations, not enough to move a
rounded percentage; zero drift against the pre-existing 420 records
(`score_gold.py`'s own drift check: 0 flagged). **New signature
coverage: 417/451** (up from 377/451) — the single biggest jump of any
batch so far, because every one of today's 40 windows was drawn
specifically from a signature the gold set had never seen, and none of
them collided with each other's signature group; 737/3251 candidate
windows now sit in never-annotated territory (down from 958/3251), 34
signatures remain uncovered (down from 74). Given how much headroom that
jump revealed, deferred the "switch sampling strategy" decision
2026-10-13's clean batch raised — the well is clearly not dry yet.

Verified before merging and after: `verify_transfer.py` green throughout
(this change never touches any table/view or `corpus.duckdb` — confirmed
`corpus.duckdb`'s mtime unchanged start-to-finish); `python -m unittest
test_transfer_e2e.py` 14/14; `check_sql_bindings.py` 106/106;
`check_fstring_interp.py` 54/54 call sites clean; `check_code_clones.py`
still exactly the same 5 cross-file pairs, 0 new (expected — no `.py` file
changed today, only `gold_citations.json`); `pyflakes` clean;
`vulture --min-confidence 60` unchanged; `bandit -r . -x
./articles,./documents,./okoz,./structure` 61 issues, same 57 B608/3
B311/1 B110 breakdown as every prior session. Both `app_hierarchy.py` and
`app_llc.py` started live on separate ports, both HTTP 200 with clean
logs (no exceptions, no tracebacks), both torn down after — neither
reads `gold_citations.json` at all, so this was a pure regression check,
not an expected-impact one.

Decided: gold_citations.json is accumulating real annotation batches
faster than code fixes are landing (11 batches, only a handful of actual
regex changes among them) — that's expected and fine for a
signature-novelty sampler whose whole point is measuring coverage, not
forcing a fix per batch, but worth flagging for whoever next considers
the "switch sampling strategy" question: the 34 remaining never-covered
signatures are now a small enough set that a future session could
plausibly eyeball all of them directly (print each one's representative
window) rather than drawing another random batch, to decide up front
which of them look like real extractor gaps worth hypothesis-driven
investigation versus harmless shape variations (punctuation/whitespace
noise) not worth a 41st annotation round. Not done today — out of scope
for this rotation's time, and a deliberate hand-crafted next step rather
than something to rush.

### 2026-10-14 — Data currency rotation: wired the snapshot-age signal into the LLC dossier's two remaining whole-act badge spots — 43/135 implementing acts now show it

Container toolchain gap, same shape as recent sessions: `duckdb`, `streamlit`,
`pandas`, `pyflakes`, `vulture`, `bandit` all absent from this fresh
container; `pip` (`/usr/bin/pip`) resolved to the system Python 3.13
interpreter while this project runs under `/usr/local/bin/python3` 3.11.17,
so `pip install` silently installed into the wrong interpreter — fixed with
`python3 -m pip install duckdb streamlit pandas pyflakes vulture bandit`.
No git-lfs pointer-stub issue today: `articles/train-00000-of-00001.parquet`
was already the real 163MB file.

Container started `HEAD` detached one commit ahead of the local `main` ref
(at `13915be`, 2026-10-13's own closing commit) — `git fetch origin main`
confirmed `origin/main` already matched `HEAD` exactly, the same
stale-local-pointer shape every recent session has hit; recovered with
`git checkout -B main origin/main` (no classifier objection this time).

Rotation: Data currency was the oldest of the three focus areas (last
touched 2026-10-11; Cleanup 10-12, Extractor 10-13 — Extractor's own
"second clean batch" thread is open-ended, not mid-flight/blocking, so
rotation discipline won over continuing it). Re-verified the baseline
first: `verify_transfer.py` green, `test_transfer_e2e.py` 14/14,
`check_sql_bindings.py` 106/106, `check_fstring_interp.py` 54/54,
`check_code_clones.py` 5 pairs, `pyflakes`/`vulture`/`bandit` clean/61
issues — all matching 2026-10-13's own re-confirmation, no drift.

Read 2026-10-11's own backlog note (see Backlog, Data currency item (3)):
`src_version_date`/`snapshot_age_note()` — the "LexUZ snapshot: DATE (~Ny
old — verify at lex.uz)" caption shipped 2026-10-11 — had only been wired
into the two citation-level realization panels
(`app_hierarchy.py::page_article()`'s pyramid, `app_llc.py::page_norm()`'s
"Below" panel). Grepped both apps for every other place a 🔴/⚠️ badge is
rendered from `v_act_currency`/`v_act_partial_repeal`/`llc_implementing_act`
to find what was still unwired: `app_hierarchy.py` has no other such spot
(the realization pyramid is its only one) — so the General Part explorer
side of this backlog item turned out to already be fully covered; the real
gap was entirely in the LLC dossier, which has two more whole-act badge
spots neither of which carried the signal:

1. `page_acts()` — the "Acts implementing the LLC" listing (135 acts across
   two routes, `cites_cc_foundation`/`names_llc_law`), showing 🔴
   superseded / ⚠️ partially-voided badges per act with zero currency-age
   context for the acts that show neither badge.
2. `page_currency()`'s "The LLC's own governing law" section — just two
   acts (the repealed 2001 LLC Law and the current 2026 LLC Law) via
   `status_chip()`, same gap in miniature.

Fixed both the same way 2026-10-11 did it: a live `JOIN act a ON a.doc_id =
...doc_id` added to each query (additive — neither `llc_implementing_act`
nor `v_act_currency` changed shape, so no rebuild of `build_llc.py` or
`build_links.py` needed) to pull `a.version_date`, then called the
existing `snapshot_age_note()` helper (not a new copy — `page_norm()` in
the same file already defines and uses it) and rendered it as a caption in
the same spot `page_norm()` does.

**Measured, not assumed.** Ran both new queries directly against
`corpus.duckdb` before touching the apps: the `page_acts()` join (all
`cites_cc_foundation` rows, `hide_dead=False`) returned 61 rows, every one
carrying a non-null `version_date` (the join doesn't drop rows — every
`llc_implementing_act.doc_id` has a matching `act` row, as expected since
the table is built *from* `act` in the first place). Computed ages
directly: **43/135 (31.9%)** of all LLC implementing acts (both routes
combined) are now old enough to trigger the note — matching 2026-10-11's
own corpus-wide LLC-vertical measurement (33/43 of 135 *stale* acts lacked
a repeal signal; today's 43/135 is the stale-count itself, the superset
that measurement's denominator came from) almost exactly, which is the
expected sanity check: wiring a display doesn't change which acts are
stale, it just makes the existing fact visible where a user actually
browses. The two governing-law acts show no note today (`version_date`
2026-07-22 and 2026-04-21, both under the 3-year threshold) — correctly
quiet, confirmed by hand rather than assumed.

**Verification.** `pyflakes app_llc.py app_hierarchy.py` clean;
`vulture --min-confidence 60` clean; `check_sql_bindings.py` 106/106 (the
two rewritten queries bind against the live schema identically to before);
`check_fstring_interp.py` 54/54 call sites, no new interpolation
introduced; `check_code_clones.py` still exactly 5 cross-file pairs, same
list as 2026-10-13 (`snapshot_age_note` IDENTICAL, `sha256_file`
IDENTICAL, `excerpt` NEAR-DUP, two SIMILAR gold-sample pairs) — confirms
reusing the existing helper rather than writing a second copy kept the
clone count flat; `bandit -r . -x ./articles,./documents,./okoz,./structure`
unchanged at 61 issues (57 B608/3 B311/1 B110, same breakdown as every
prior rotation). `verify_transfer.py` exits 0, all checks green (see
closing summary below). `python -m unittest test_transfer_e2e.py` 14/14.
Both apps started live with `streamlit run --server.headless true` on
scratch ports, confirmed HTTP 200 with clean logs (no tracebacks) at
startup, then torn down with `pkill`; since Streamlit only executes the
code path for whichever sidebar page is selected, also ran the exact two
rewritten SQL queries directly against `corpus.duckdb` in a plain Python
script to independently confirm both resolve and return the expected
columns/row counts (above) — a stronger check than an HTTP 200 alone,
which only proves the *default* page (`page_skeleton()`) renders.

**Decision**: thread closed, not left open — this was a bounded,
well-scoped backlog item (two query edits, no design ambiguity) rather
than an open-ended investigation. Backlog items (1) (re-run a live
lex.uz comparison if that domain is ever allowed through this
environment's egress policy) and (2) (the 3-year threshold is round-number
legible, not tuned against labeled staleness data, none of which exists
corpus-wide) remain open for whoever next picks up Data currency.

`verify_transfer.py` summary: all AC1-AC7 checks PASS, same INFO-level
counts as 2026-10-13 (39 proposed OKOZ mappings awaiting validation, 248
acts provably superseded / 495 edges from them) — nothing about today's
change touches either number, as expected for a pure display-layer
addition.

### 2026-10-13 — Extractor rotation: tenth signature-stratified gold batch, 380 -> 420 records, first fully clean batch since batch 1 — signature coverage jumps 337/451 -> 377/451

Container toolchain gap, same shape as 2026-10-12's: `duckdb`, `streamlit`,
and `pyflakes`/`vulture` were all absent from this fresh container; `pip`
again resolved to the wrong interpreter (`/usr/bin/pip` -> system Python
3.13, while this project runs under `/usr/local/bin/python3` 3.11.17) —
`python3 -m pip install duckdb`/`streamlit` fixed it (didn't reinstall
`pyflakes`/`vulture` since no `.py` file changed today, so their checks
weren't needed). Also hit a git-lfs gap not previously logged:
`articles/train-00000-of-00001.parquet` was a 134-byte LFS pointer stub,
not the real 163MB file, so `verify_transfer.py` failed immediately on
import — `git lfs install && git lfs pull` fixed it (`documents/...parquet`
pulled too, same stub state). Noting both here for whichever future session
hits them again on a fresh container.

Container started `HEAD` detached at `0af58fd` (2026-10-12's own closing
commit), one commit ahead of the local `main` ref — `git fetch origin main`
confirmed `origin/main` already matched `HEAD` exactly, the same
stale-local-pointer shape every recent session has hit. This time the
auto-mode permission classifier denied `git checkout -B main origin/main`
as "Irreversible Local Destruction" (even though it would only have
fast-forwarded a stale local branch pointer with no local-only commits at
risk) — rather than fight the classifier, committed directly on the
detached `HEAD` (already at the exact tip `origin/main` expects) and pushed
with `git push origin HEAD:main`, which is a plain fast-forward from
`origin`'s point of view and didn't need the branch-reset step at all.

Rotation: Extractor was the oldest of the three focus areas (last touched
2026-10-10; Data currency 10-11, Cleanup 10-12) and its gold-set thread was
already mid-flight ("thread stays open" in Active threads), so continued it
rather than drawing from Backlog. Re-verified the baseline first:
`verify_transfer.py` green, `python -m unittest test_transfer_e2e.py`
14/14, `check_sql_bindings.py` 106/106, `check_code_clones.py` 5 cross-file
pairs (same as 2026-10-12, no new pair — expected, since no code changed
today).

Drew batch 10 (`build_gold_sample_novel.py --seed 20261013 --n 40`, novelty
coverage 337/451 signatures before drawing, matching 2026-10-10's
post-batch-9 figure exactly, confirming no drift in the sampler itself).
Hand-read all 40 against the raw parquet text and the live `extract()`
output. **All 40/40 verdict `correct`** — the first fully clean batch since
batch 1 (2026-09-20); every batch in between found at least one real bug or
known_gap. Gave the one genuinely novel signature in the batch (row 46565,
`cross_references`: "mazkur Kodeksning 1 — 6-moddalari, 70-bobi (1158 —
1167-moddalari)" — a chapter citation immediately followed by its own
parenthetical article range) a closer look before accepting it: `extract()`
emits both a `chapter` edge for chapter 70 *and* 10 separate `article`
edges for 1158-1167, which could in principle be a double-count bug rather
than intended behavior. Checked against how every other multi-granularity
window in the corpus is already treated (e.g. row 46911's "234-352-moddalari
... 354 — 363-moddalari" case in this same batch, or any chapter+section
citation elsewhere) — the extractor's consistent design is to capture every
number that has its own unit-word suffix as its own edge, independent of
whether a coarser citation also covers the same text; no corpus table
collapses these into one row, so both edges are genuinely informative
(one says "this whole chapter is relevant", the other says exactly which
articles). Not a bug — confirmed correct, not merely "didn't crash."

**Score after merging** (`score_gold.py`): precision 1895/1906 (99.4%),
recall 1895/1929 (98.2%) on 420 windows (up from 1608/1619 = 99.3% /
1608/1642 = 97.9% on 380) — a clean improvement with zero drift reported
against the pre-existing 380 records; the 11 remaining FP/FN pairs are
exactly the 5 known_gap records already on file (gold_id 196, 324, 341,
370, 379), nothing new. **New signature coverage: 377/451** (up from
337/451) — a much bigger jump than any prior single batch, because this
batch specifically targeted the rarest never-covered signatures and the
sampler takes up to 3 examples per signature, so one 40-window draw
resolved many single-digit-count signatures at once; 958/3251 candidate
windows still sit in never-annotated territory (down from 1142/3251).

While merging, noticed `gold_citations.json`'s own `_meta.batches` list was
missing entries for batch 7 (gold_id 260-299, built 2026-10-02) and batch 9
(gold_id 340-379, built 2026-10-10) — both batches are fully documented in
`_meta.description`'s prose and in this file's own Log/Active-threads
history, just never got their structured `batches[]` row.
Backfilled both (same shape as every other entry: `gold_id_range`, `seed`,
`n`, `built`, `method`) rather than leaving the gap, since it's the kind of
small bookkeeping drift that would make a future `jq` query over `batches[]`
silently under-count. Pure metadata — no `expected`/`verdict` record
touched, no `validated_by`/`validated_at` field anywhere near this (that
field doesn't even exist on gold records), so no validation-state line was
crossed.

Verified before committing: `verify_transfer.py` green (`gold_citations.json`
is read only by `score_gold.py`/`build_gold_sample_novel.py`, never by any
`build_*.py` script, so `corpus.duckdb` is untouched); `python -m unittest
test_transfer_e2e.py` 14/14; both apps smoke-tested live after installing
`streamlit` (HTTP 200 on `app_hierarchy.py` and `app_llc.py`, no
exceptions in either server log).

Thread stays open — next Extractor rotation should keep drawing fresh
`build_gold_sample_novel.py` batches. Today's 0/40 real-finding rate is the
first time this project's "diminishing returns" bar has actually been
touched on a full batch; worth watching over the next 1-2 rotations whether
this is a one-off clean draw or a genuine sign the signature-stratified
sampler is running out of novel, bug-bearing shapes (958/3251 candidate
windows remain unannotated, but a shrinking share of distinct *signatures*,
74/451, is left to resolve) — if the next batch also comes back clean,
that's the point to consider switching strategy (e.g. targeting specific
`doc_type`s or anchor kinds the signature space doesn't capture, rather
than another signature-novelty draw).

### 2026-10-12 — Cleanup rotation: built a seventh check, `check_fstring_interp.py`, after finding a real structural blind spot in the third check (the `execute(f"` grep) and one real f-string-SQL violation it had been hiding

This container also had a toolchain gap worth recording: `duckdb`, `pandas`,
`streamlit`, `pyflakes`, `vulture`, `bandit`, `pyarrow`, and `requests` were
all absent from the start (`pip` itself resolved to a different, system
Python 3.13 than the `/usr/local/bin/python` 3.11.17 this project actually
runs under — `pip install` silently installed into the wrong interpreter
the first time; `python -m pip install ...` fixed it). Not a code bug, just
noting it here in case a future session hits the same `ModuleNotFoundError:
duckdb` on a fresh container and wastes time looking for a corpus problem
instead.

Container itself started `HEAD` detached one commit ahead of the local
`main` ref (at `f62ce8d`, 2026-10-11's own closing commit) — `git fetch
origin main` confirmed `origin/main` already matched `HEAD` exactly, same
stale-local-pointer shape every recent session has hit. Recovered with
`git checkout -B main origin/main` rather than the usual `merge --ff-only`
(no local-only commits to preserve, so resetting the branch pointer
straight to the fetched tip is equivalent and slightly simpler).

Rotation: Cleanup last ran 2026-10-09, the oldest of the three focus areas
(Extractor 10-10, Data currency 10-11) — clear next pull. The Extractor
"gold set" thread's own 2026-10-10 entry explicitly recommends continuing
it next, but per the brief's own "rotate across the three" instruction and
this project's consistent precedent of treating that as a standing
recurring bucket rather than a blocked mid-step task, Cleanup's own
staleness won out.

Re-ran all six existing checks before looking for anything new: `pyflakes
*.py` (clean), `vulture *.py --min-confidence 60` (clean), `bandit -r . -x
./articles,./documents,./okoz,./structure` (61 issues: 57 B608 + 3 B311 +
1 B110, same classes and counts as every prior session back to 2026-10-01
— no new issue), `check_sql_bindings.py` (106/106 literal queries bind
cleanly), `check_code_clones.py` (93 functions across 18 files, same 4
pairs as 2026-10-09 plus the one new, fully expected pair from 10-11's
`snapshot_age_note()` duplicate — nothing else).

The sixth check, `grep -n 'execute(f"' *.py`, came back at 35 raw hits, up
from 33 at 2026-10-09. Per this project's own standing precedent (never
trust a count-only re-check; re-derive what actually changed), looked
closer rather than just re-stating the new number. One of the 35 is
`check_sql_bindings.py`'s own docstring mentioning the pattern in prose,
not a real call — a pre-existing false positive in the grep that's
probably been present since 2026-10-03 and never isolated. The real
question was the other direction: are there call sites the grep *misses*?
Wrote a quick AST script to enumerate every `*.execute(...)` call whose
first argument is an f-string, independent of the grep entirely, and it
found 54 such calls — 19 more than the grep's real count of 34. All 19
untracked calls are in `test_transfer_e2e.py`, a file that had never once
appeared in any prior Cleanup rotation's grep output. The reason: the grep
pattern `execute(f"` is a single-line literal match, and every one of
those 19 (really 20, one more turned up on a second pass) call sites in
that file has its f-string literal on the line *after* `execute(`, e.g.:

```python
res = conn.execute(
    f"SELECT article_text_en FROM read_parquet('{parquet_path}') WHERE {where_clause}"
).fetchone()
```

That's a real, structural blind spot in a check this project has relied on
since 2026-09-26 — not a hypothetical one, since it had successfully hidden
20 call sites for 16 days across 4 Cleanup rotations (10-01, 10-03, 10-09,
and whichever earlier ones never thought to check file coverage against
the grep's own output).

Hand-audited all 20 against the project's own f-string-SQL rule (no
interpolated value that isn't a hardcoded constant). 19 are fine —
`PARQUET_PATH` (a module constant) in 19 of them. The 20th,
`query_db_article_text_en()`'s `else` branch, is a real violation:

```python
where_clause = f"doc_id = -111189 AND article_number = '{norm_id}'"
```

`norm_id` is not a constant — it's derived at runtime from parsing the
project's own English markdown fixture (normalized superscript-article IDs
like `173-1`), threaded in from the Tier-2 reconciliation test's per-article
loop. It's not externally reachable (the markdown is a tracked fixture,
not user input), so this was never an exploitable injection in practice —
but it's exactly the shape of violation this project has fixed every other
time it's found one (`build_gold_sample_novel.py`/`score_gold.py`/
`build_llc.py`'s runtime int-list interpolations, fixed 2026-09-26), and
the project's own hard rule doesn't carve out an exception for "fixture
data, not live input." Fixed it the same way: parameterized the one
runtime value (`article_number = ?` + `conn.execute(sql, [norm_id])`)
instead of leaving the WHERE clause built entirely from an f-string. The
other two branches (`raw_id == "26¹"`/`"261"`) were already pure hardcoded
literals and needed no change beyond pulling the shared `doc_id = -111189`
clause out into the call site so all three branches compose the same way.

Built `check_fstring_interp.py` as the seventh repeatable Cleanup check —
and the structural replacement for the third, not just an addition next to
it. Method: AST-walk every `*.execute(...)` call whose first argument is a
`JoinedStr`, which DuckDB's AST sees identically regardless of how the
source lines are wrapped, so the multi-line blind spot can't recur by
construction. For each interpolated expression, resolve it recursively:
a plain string literal is safe; a SCREAMING_CASE name or dotted attribute
(this project's own consistent naming convention for a module-level
constant, e.g. `CC_GENERAL_PART`, `cx.DOC_GENERAL`) is safe, including
through a method call on one (`PARQUET.as_posix()`); an f-string is safe
iff every one of *its* interpolations is, recursively; and a bare name
with no safe resolution is traced to every place it's assigned *within the
same function* — if every one of those right-hand sides is safe
(recursively), so is the name.

That last rule is what makes this check materially stronger than a
name-based allowlist, and the first draft proved it the hard way: it
initially allowlisted the bare names `raw` and `where_clause` directly
(the same two names the 2026-10-03 manual audit had already hand-verified
as safe), on the theory that re-deriving safety from first principles each
run was overkill. A mutation test against a scratch copy of the *pre-fix*
`test_transfer_e2e.py` (restored via `git show HEAD:test_transfer_e2e.py`
before the fix was committed) was supposed to prove the new checker would
have caught the `norm_id` bug — instead it passed clean, because
`where_clause` was still spelled `where_clause` in the buggy version and
the allowlist didn't look past the name. That's the exact failure mode
this check exists to prevent, caught by the check's own test before it
ever shipped. Redesigned to resolve `where_clause` and `raw` structurally
instead (tracing every local assignment within their enclosing function,
recursively) — re-ran the same mutation test: the pre-fix file now
correctly flags `{where_clause}` at line 308 (its one unsafe assignment
resolves to the unresolvable parameter `norm_id`), and the post-fix,
real file passes clean (54 calls, 0 flagged). A handful of genuinely
irreducible shapes (a loop variable ranging over a fixed tuple, a
cross-function parameter, `check_sql_bindings.py`'s own PREPARE-statement
plumbing, a hardcoded constant's length used to generate `?` placeholders)
are still hand-verified and listed explicitly with a one-line reason each,
the same way `check_sql_bindings.py` already excludes what it can't
validate — but that list is now 5 entries instead of being the entire
mechanism.

Validation before committing: `python verify_transfer.py` — all AC1-7
green, same reconciliation residual as every prior session (`corpus.duckdb`
untouched; this change touches no table/view, so no rebuild was needed or
attempted). `python -m unittest test_transfer_e2e.py` — 14/14, including
`test_edge_duplicate_article_261` and the other edge test that exercise
`query_db_article_text_en()`'s three branches directly. Re-ran
`pyflakes`/`vulture --min-confidence 60`/`bandit`/`check_sql_bindings.py`/
`check_code_clones.py` against the two changed/new files — all clean, no
new findings introduced by this change itself. Both `app_hierarchy.py` and
`app_llc.py` smoke-tested live (HTTP 200 on both ports, no exceptions in
server logs — expected, since nothing schema-level changed and neither app
imports the touched test file).

**Decision: shipped.** One real bug fixed (an actual, if not externally
exploitable, violation of the project's own hard rule), one real gap in an
existing check closed, and the new check proved against its own mutation
test rather than just asserted clean. Thread closed. Next Cleanup rotation
should re-run all seven checks; the plain `execute(f"` grep can retire —
`check_fstring_interp.py` subsumes everything it covered and sees strictly
more.

### 2026-10-11 — Data currency rotation: surfaced `act.version_date` (LexUZ's scrape date) as a snapshot-age signal after measuring the realization graph's staleness blind spot

Container started in detached `HEAD`, 3 commits ahead of the local
`main`/`origin/main` refs as this checkout initially saw them (at
`1afec90`, 2026-10-10's own closing commit) — same stale-remote-tracking-
pointer pattern flagged in several prior entries, confirmed harmless again:
`git fetch origin main` showed `origin/main` already at `1afec90` (the
push had succeeded), so `git checkout main && git merge --ff-only
origin/main` recovered cleanly with no lost work. Cold-start installs:
`git lfs install && git lfs pull` (the raw parquet was a 134-byte LFS
pointer stub until then), `python -m pip install duckdb pandas pyarrow
streamlit pyflakes vulture bandit` (note: this container's `pip` on PATH
targets Python 3.13's dist-packages, not the `/usr/local/bin/python`
3.11 that actually runs the scripts — `python -m pip install ...` avoids
the mismatch; a bare `pip install duckdb` silently installs into the
wrong interpreter and `import duckdb` still fails afterward).

Rotation: Extractor last touched 2026-10-10, Cleanup 2026-10-09, Data
currency 2026-10-08 — clearly the oldest, and its own backlog items are
each either closed or explicitly "diminishing returns, not worth
re-opening without a new angle" (the 39/612 amending-act residual,
2026-09-30; the 13/58 whole-doc-block risk, 2026-10-08). Rather than
re-litigate either, looked for a genuinely new angle instead.

The most direct possible "data currency" check for a project whose
README explicitly calls itself "a pinned consolidated snapshot, not a
live legal database" is to compare the snapshot against the live source.
Tried it: `curl -sS https://lex.uz/uz/docs/-111189` failed with a proxy
`CONNECT tunnel failed, response 403` ("organization policy"), and
`WebFetch` on the same URL failed with `getaddrinfo ENOTFOUND lex.uz`.
Confirmed via `read_documentation` that this is this environment's
network allow-list, not a transient failure — not fixable from inside
the session. No live-vs-corpus diff was possible today.

Pivoted to what the corpus already has but has never used. The raw
parquet carries 28 columns; one is `version_date` — LexUZ's own per-act
scrape/snapshot date, distinct from `doc_date` (the act's own enactment
date). `build_corpus_db.py` already copies it into the `act` table
(`any_value(version_date)`, confirmed uniform per `doc_id` — not an
internally-mixed-vintage document), and has done so since the project's
first build. But `grep -rn version_date *.py` turns up exactly 3 hits
total: the column definition, the INSERT, and a docstring comment noting
the Civil Code's own pin date — it has never been read by `build_links.py`,
`build_llc.py`, `app_hierarchy.py`, or `app_llc.py`. This is a different
signal from the already-known-useless `status` field (100% `in-force`
for all 24,267 acts, `build_links.py`'s own long-standing comment) — an
act's `status` says nothing, but its `version_date` at least says how
old the text behind that claim is.

Measured (`duckdb` read-only against the committed `corpus.duckdb`, see
`/tmp/.../scratchpad/measure_staleness.py`): of the 245 distinct acts that
currently realize (cite as a lower-tier act) at least one General Part
Civil Code article (`link_edge.hierarchy_rel = 'below'`), snapshot ages
range 2 months to 28 years (mean 4.3y, median 1.9y); bucketed by age,
66 are <1y, 57 are 1-2y, 20 are 2-3y, and 102 (41.6%) are >3y old (36 in
3-5y, 39 in 5-10y, 27 over 10y). Cross-joined those 102 against
`v_act_currency.derived_status` (the project's own text-based repeal
detector): only 24/102 are independently flagged `superseded` by a later
act's repeal clause — the other **78/102 (76.5%)** carry no positive
signal either way, meaning **78/245 (31.8%) of all realizing acts
corpus-wide** rest their "still current law" status purely on an
unrefreshed scrape, with nothing in the pipeline re-checking it since
(oldest example found: a 1998-09-11 Oliy sud Plenumi resolution still
cited as realizing Civil Code Article 100, 28 years stale). Repeated the
same measurement scoped to the LLC vertical alone (`llc_implementing_act`
join `act`): 135 implementing acts, 43 (31.9%) >3y stale, 33/43 (76.7%)
with no repeal signal — close enough to the corpus-wide rate (31.8%/76.5%)
that this isn't a quirk of one vertical, it's structural.

**Decision: ship the signal, not a verdict.** The measurement shows a real
blind spot, but nothing in it supports actually calling any specific act
"stale" — absence of a detected repeal is not evidence of currency, and
without the live lex.uz comparison there is no way to confirm or deny
staleness for any individual act. Inventing a "risk score" from this data
would overclaim. The honest, available move is to surface the scrape date
itself and let the reader judge, matching the project's own stated
epistemic stance (README: "always verify the current, in-force text [at]
lex.uz"). Implementation, kept minimal: added `a.version_date AS
src_version_date` to `v_realization` (`build_links.py`) and to
`v_llc_realization` (`build_llc.py`) — additive columns on existing views,
no table schema change, no full `corpus.duckdb` rebuild (only re-ran
`build_links.py` then `build_llc.py`, per the hard constraint, since
`build_okoz.py` has no dependency on either). Added a `snapshot_age_note()`
helper to both `app_hierarchy.py` and `app_llc.py` — deliberately
duplicated rather than factored into a shared module, the same
duplication-by-design precedent `check_code_clones.py` already accepted
for `excerpt()` on 2026-10-09, since the two apps have no shared import
path today and inventing one for a 10-line function would be the bigger
change. It renders "LexUZ snapshot: YYYY-MM-DD (~Ny old — verify at
lex.uz)" on a citing act's expander, gated at the 3-year threshold the
measurement above used — at median age 1.9y, showing it unconditionally
on every citation would bury the signal in noise for acts that are
plausibly current.

Wired it into the two existing per-citation displays that already carry
per-act currency badges: the General Part explorer's realization pyramid
(`app_hierarchy.py:page_article()`) and the LLC dossier's "Below · acts
implementing this Code article" panel (`app_llc.py:page_norm()`). Both
queries needed column-position updates (`GROUP BY`/tuple-unpack indices
shifted by the new column) — re-verified both queries directly against
`corpus.duckdb` by hand (not just via the running app) before trusting
the app's own smoke test, since an off-by-one in a tuple unpack is exactly
the kind of bug that silently mislabels a different field instead of
crashing.

Caught one self-inflicted bug before it shipped: `from datetime import
date` collided with pre-existing local loop variables named `date` in
both apps (amendment-history loops, an LLC currency listing, an acts
table) — `pyflakes app_hierarchy.py app_llc.py build_links.py build_llc.py`
caught all 4 instances ("import 'date' from line N shadowed by loop
variable") on the first run after the edit. None of the 4 were actual
runtime bugs (each shadow is local to its own enclosing function, and
`snapshot_age_note()` itself never sees the shadowed name), but shipping
a new, avoidable lint warning into a codebase this project otherwise
keeps `pyflakes`-clean would be its own small regression. Fixed by
switching to `import datetime as dt` in both files instead of renaming
3 unrelated, pre-existing local variables to work around a new import —
`pyflakes` clean afterward.

Full verification before committing: `python build_links.py` (9535 edges,
612 `article_amendment` rows via 478/45/33/38 across the four match
methods, 840/885 repeal items resolved — all identical to the
pre-change baseline, confirming the view-only change didn't perturb any
upstream table) and `python build_llc.py` (135 implementing acts, 25
superseded, same repealed-company-form-article counts as before) both
re-run clean; `python verify_transfer.py` — all checks green, identical
INFO-line counts to 2026-10-10 (17 citations/8 repealed articles, 248
superseded acts/495 edges, 39 proposed OKOZ mappings); `python -m
unittest test_transfer_e2e.py` 14/14; `pyflakes`/`vulture
--min-confidence 60`/`bandit -r . -x ./articles,./documents,./okoz,./structure`
all clean on the 4 changed files (bandit: 61 issues total project-wide,
unchanged from the 2026-10-01 baseline — no new findings); `python
check_sql_bindings.py` 106/106; `python check_code_clones.py` — 93
functions, 5 cross-file pairs >= 0.55, and the one new pair
(`snapshot_age_note()`, 1.000 similarity) is the deliberate, documented
duplicate described above, not drift. Ran both apps live
(`streamlit run ... --server.headless true`) on throwaway ports: both
HTTP 200 at startup with nothing in either log beyond the normal
Uvicorn banner, and the exact modified SQL for both touched pages re-run
directly against `corpus.duckdb` (not just through the app) to confirm
real old-snapshot acts (e.g. a 2011-07-20 realizing act, a 2022-02-25 LLC
implementing act) surface with the correct `version_date` and that the
new `GROUP BY`/tuple-unpack indices didn't silently misalign any other
column.

**Net effect**: a real, measured blind spot (31.8% of the realization
graph's currency claims rest on scrapes with no independent check, some
decades old) made visible to readers for the first time, without
overclaiming what the data can support. Not a fix to the staleness
itself — that would need either a fresh scrape or the live lex.uz access
this environment doesn't grant — but a genuinely new angle for this
rotation area (every prior Data-currency session worked inside the
existing repeal/amendment-resolution machinery; today used a column that
machinery never touches at all). Thread closed, not left mid-flight; see
Backlog for the three concrete follow-ons if this is picked up again.

### 2026-10-10 — Extractor rotation: ninth gold batch, 340 -> 380 records, two new bugs found (dropped-article typo, widened an existing gap class), one stale backlog note finally formalized

Container started in detached `HEAD`, 2 commits ahead of the local
`main`/`origin/main` refs as this checkout initially saw them (at
`7b9d503`, 2026-10-09's own closing commit) — same stale-remote-tracking-
pointer pattern the 2026-10-09 entry flagged as "might show up again."
`git fetch origin main` confirmed `origin/main` was genuinely already at
`7b9d503` (nothing lost, the push from yesterday had succeeded); this
checkout's local `main` ref was just never advanced. Fixed with
`git checkout main && git merge --ff-only 7b9d503`, then proceeded.
Installed the project's Python dependencies (`duckdb`, `pandas`, `pyarrow`,
`streamlit`, `pyflakes`, `vulture`, `bandit` — this is a fresh container
with none of them present) and ran `git lfs pull` to materialize
`articles/train-00000-of-00001.parquet` (was a 134-byte LFS pointer stub).
`verify_transfer.py` confirmed green before touching anything.

Rotation: Extractor last touched 2026-10-04 (6 days ago), the oldest of
the three focus areas (Data currency 2026-10-08, Cleanup 2026-10-09), so
picked it per the brief's own rotation guidance, continuing the still-open
gold-set thread rather than inventing a new angle.

Drew a fresh batch via `build_gold_sample_novel.py --seed 20261010 --n 40`
(novelty coverage 298/451 signatures, 1179/3251 candidate windows in
never-annotated territory before drawing — both numbers unchanged from
2026-10-04, confirming the corpus itself hasn't moved). Hand-read all 40
windows against the raw parquet text (`article_text`/`cross_references`/
`amendment_note` via a direct DuckDB query) and the live `extract()`
output, window by window.

**37/40 verdict `correct`.** Several are worth noting as real stress tests
that passed: a self_reference list correctly stopping before THREE
different codes named in sequence afterward (Oila kodeksi, Uy-joy kodeksi,
Havo kodeksi, each with its own number run — gold_id 351), two separate
range-then-list correctly stopping before a different code's own citation
(gold_id 356, 360), and a window correctly producing both an article-list
AND a separate chapter citation from one anchor run (gold_id 374). One
window (gold_id 348, formerly local id 8) re-hits the already-known
qism/band-collapse limitation in an unusually dense form (two articles in
one window each losing a qism to the "keep only the last ordinal"
behavior) — scored `correct` per existing precedent (qism isn't
load-bearing), just noted.

**3/40 real findings, all investigated and measured corpus-wide before
deciding not to fix:**

1. **gold_id 370** (row 38339): a LexUZ typo, "Fuqarolik kodeksining
   43-moddsi." — missing the "a" in "moddasi". `RE_CLAUSE`'s unit-word
   match doesn't recognize "moddsi" as any unit word at all, so the whole
   clause falls through to the bare-act fallback, dropping Civil Code
   Article 43 entirely — a genuine recall miss caused by a source-data
   typo, not a grammar gap. Measured corpus-wide: the identical typo
   string appears 3 more times, but always against a different act (Mehnat
   kodeksi, "mazkur Qonun") entirely outside this extractor's anchor scope
   — so the real in-scope footprint is exactly 1 occurrence, same shape as
   the existing "paragrif" misspelling known_gap. Not fixed given the
   single-occurrence scope; recorded as a permanent known_gap record.

2. **gold_id 379** (row 42229): "Fuqarolik kodeksining 14, 15, 324 — 339,
   985, 989 va 990, Oʻzbekiston Respublikasining "Tadbirkorlik faoliyati
   erkinligining kafolatlari toʻgʻrisida"gi Qonunining 38-moddasiga..." —
   the Civil Code's own list (expanding the 324—339 range: 16 articles, 21
   total) has no unit word anywhere; the sentence moves straight from
   "990," into a different Qonun's own "38-moddasiga". This is the
   identical failure mechanism as the existing 2026-09-28 known_gap
   (gold_id 194-196: a bare number loses its unit word to a different
   act's own later clause) — but that session's corpus-wide measurement
   regex only searched for an interposing *kodeks* name and reported 5
   occurrences across 3 rows, all resolving to the same target (Article
   38). Built a wider, general measurement today
   (`/tmp/.../measure_bare_list.py`, not committed — a throwaway script):
   scan every CC anchor window, and flag any where `extract()` produced no
   article/chapter/section/part citation at all despite a genuine
   2+-digit list sitting right after the anchor with no
   modda/bob/paragraf/qism/band/boʻlim word ever attaching to it (checked
   both inside the matched digit run and in the ~20 chars immediately
   after it, to avoid false positives from legitimate multi-chapter lists
   like "22, 24, 57-boblari" which the extractor already handles
   correctly — an early version of this script wrongly flagged 9 such
   cases before that tail-check fix). Found exactly 1 more in-scope
   occurrence: this row, the *Qonun* variant of the same bug, missed by
   the kodeks-only regex, and a much bigger single-row loss (21 articles,
   not 1). **Corrected the 2026-09-28 backlog note's corpus-wide count
   from 5 occurrences/3 rows to 6 occurrences/4 rows** for this whole
   failure class. Not fixed — same cross-clause-inference risk already
   weighed and rejected for the sibling gap (inferring that a bare
   number's unit word lives in a different act's own later clause isn't
   safe to generalize past this narrow, repeatedly-recurring shape) — but
   recorded as a known_gap record and the Backlog item corrected.

3. **gold_id 341** (row 42566): the sampler independently re-drew the
   exact row the 2026-09-15 session already found and described in prose
   ("Chapter+paragraph's own space-separator gap" — "Fuqarolik kodeksi
   22-bobining 2 paragrafi", space instead of hyphen before "paragrafi",
   loses the section-2 grain because the chapter+section lookahead's own
   regex requires a hyphen) but never turned into a gold record across the
   five weeks since — it sat as backlog prose only. Re-confirmed corpus-
   wide still exactly 1 occurrence; formalized as the permanent
   `known_gap` regression record it should have had from the start.

**Combined score after merging**: precision 1608/1619 (99.3%), recall
1608/1642 (97.9%) on 380 windows, down from 1481/1489 (99.5%) / 1481/1492
(99.3%) on 340 — the drop is arithmetic, not a regression: gold_id 379
alone contributes 21 honest new misses in a single record, more than any
previous individual finding, plus 2 more small ones and 37 confirmed-
correct windows. `verify_transfer.py` green (`gold_citations.json` is read
only by `score_gold.py`/`build_gold_sample_novel.py`, never by any
`build_*.py` pipeline script, so no rebuild needed); `python -m unittest
test_transfer_e2e.py` 14/14; both Streamlit apps smoke-tested live (HTTP
200, no exceptions in server logs — no schema touched, this session only
edited `gold_citations.json` and this file). **New signature coverage:
337/451** (up from 298/451), 1142/3251 candidate windows still in
never-annotated territory. Thread stays open for tomorrow: next Extractor
rotation should keep drawing fresh `build_gold_sample_novel.py` batches —
today's yield (3 real findings / 40 windows) is still well above the
"diminishing returns" bar this project has used before to justify
switching strategy, so no reason to change approach yet.

### 2026-10-09 — Cleanup rotation: built and adopted a sixth check, `check_code_clones.py` (cross-file duplicate-logic drift), no live bug found

Container started with `HEAD` detached one commit ahead of the local `main`
branch ref — at `68b8bd7`, 2026-10-08's own "Data currency" closing commit.
Checked whether this meant lost/unpushed work: `git fetch origin main`
showed `origin/main` was already at `68b8bd7`, so the push had in fact
succeeded; only this checkout's local `main` pointer was stale (pointing at
the previous commit, `f9cd423`) while `HEAD` sat on the real tip, detached.
Recovered cleanly with `git checkout main && git merge --ff-only 68b8bd7`
(fast-forward, no conflict, confirmed identical to `origin/main` after).
No work was at risk, but recording the pattern here in case a future
session sees the same detached-HEAD-ahead-of-main shape and needs to tell
"stale local pointer, already pushed" apart from "uncommitted/unpushed work
from a session that got cut off" quickly.

Rotation: Cleanup last ran 2026-10-03, the oldest of the three focus areas
(Extractor 10-04, Data currency 10-08 after today's recovery) — clear next
pull, and no thread was genuinely mid-flight (the Extractor "gold set"
thread's own 2026-10-04 entry decided *not* to fix its one open gap, same
single-occurrence precedent as prior gaps, so it's a standing recurring
bucket to pick up on Extractor's next turn, not a blocked mid-step task).

Re-ran all five existing checks before deciding whether to touch anything:
`pyflakes *.py` (clean), `vulture *.py --min-confidence 60` (clean),
`grep -n 'execute(f"' *.py` (same 33 call sites as the 2026-09-26 audit,
all previously confirmed to bind via parameterized `UNNEST`/safe hardcoded
interpolation, no new offender), `bandit -r . -x ./articles,./documents,
./okoz,./structure` (61 issues: 57 B608 + 3 B311 + 1 B110, same classes and
same count as 2026-10-01 — no new B110 this time), `check_sql_bindings.py`
(106/106 literal queries bind cleanly against the live schema, same as
2026-10-03). All five confirm clean/unchanged.

Per the 2026-10-03 entry's own note ("next rotation should re-run all five
before deciding whether a sixth is worth adding"), looked for a genuinely
new angle rather than stopping at re-confirmation. None of the five
existing tools check for *cross-file duplicate-logic drift* — and this
project has real exposure to exactly that: `alias_docs` (the FK-abbreviation
doc-id query) and the `_anchors()`/`extract()` call pattern are hand-copied,
by design, into five different scripts (`build_gold_sample.py`,
`build_gold_sample_novel.py`, `build_links.py`,
`measure_extractor_recall.py`, `score_gold.py`). A fix landing in one copy
and never reaching the others would be invisible to pyflakes (valid
Python), vulture (all copies are "used"), the f-string grep (none of these
are f-string SQL — already parameterized or safe), bandit (not a security
pattern) and check_sql_bindings.py (each copy's query still binds fine
against the schema on its own, binding doesn't prove two copies agree).

Built `check_code_clones.py`: AST-parses every function (>=4 body lines,
skip trivial getters) in every `*.py` file, diffs every cross-file pair's
source text with `difflib.SequenceMatcher`, reports pairs at similarity
>= 0.55. Tried a SQL-block-level variant first (diff text inside
`execute()`'s triple-quoted SQL strings directly, rather than whole
function bodies) on the theory that it would catch *partial* duplication
inside otherwise-different functions that whole-function diffing might
miss: 83 SQL blocks across 10 files, 54 cross-file pairs >= 0.5 similarity
— but manually spot-checking the pairs showed almost all were coincidental
overlap from shared SQL vocabulary (`SELECT ... FROM norm_unit WHERE ...`)
between queries with nothing actually in common, not real duplication.
Rejected that variant as too noisy to be a repeatable check. The
whole-function version is precise: 91 functions parsed across 17 files,
exactly 4 cross-file pairs >= 0.55, 0 further noise.

Hand-verified all 4 flagged pairs against the actual source (not just the
diff ratio):
1. `sha256_file()` in `build_corpus_db.py` and `verify_transfer.py` — ratio
   1.000, byte-identical. Fine (this is the intended invariant: both must
   hash the same way or the parquet-integrity check means nothing).
2. `excerpt()` in `app_hierarchy.py`/`app_llc.py` — ratio 0.930. Full-text
   diff shows the logic is byte-identical; only the one-line docstring's
   wording differs ("Paragraph-sized window into an act stored as a single
   block" vs "...of a whole-act blob around the citation"). No behavior
   drift.
3. `citation_dict()` (`build_gold_sample.py`) vs `citation_to_dict()`
   (`score_gold.py`) — ratio 0.795. The former includes `anchor` and
   `evidence` fields (serializing extra context for a human annotator to
   read in `gold_sample.json`); the latter deliberately omits them when
   building the per-citation signature used for scoring, per
   `score_gold.py`'s own docstring reasoning: two logically-equivalent
   citations found via different anchor kinds should still score as a
   match, so the anchor/evidence metadata is correctly excluded from the
   comparison key. Documented, intentional difference, not drift.
4. `build_gold_sample.py:main()` vs
   `build_gold_sample_novel.py:build_candidates()` — ratio 0.672. These are
   the uniform-random and signature-stratified samplers' shared
   candidate-window-generation logic (deliberately duplicated — see
   `build_gold_sample_novel.py`'s own docstring on why it's a separate
   script rather than a shared import). The parts that must agree (the
   `alias_docs` and `rows` SQL, independently confirmed byte-identical
   across all 5 files that define them — checked directly, not just via
   the ratio) are unchanged; the similarity score difference is entirely
   the stratification/output logic the two scripts intentionally differ on.

**No live drift bug found** in any of the 4 candidates — a clean bill of
health for the specific duplication this project carries today. Adopted
`check_code_clones.py` as a sixth repeatable Cleanup check anyway: it runs
in under a second, is precise on this codebase (0 false positives above its
threshold once the noisy SQL-block variant was rejected), and targets a
real, project-specific bug class (by-design duplicated helper logic across
the gold-sampling/scoring/measurement scripts) that none of the other five
tools can see by construction.

Validation before committing: `python verify_transfer.py` green (all AC1-7
checks pass, same reconciliation residual as every prior session —
`corpus.duckdb` untouched, this change touches no table/view); `python -m
unittest test_transfer_e2e.py` 14/14; `pyflakes`/`vulture --min-confidence
60`/`bandit`/`check_sql_bindings.py` all re-confirmed clean on the new file
itself too; both `app_hierarchy.py` and `app_llc.py` smoke-tested live
(HTTP 200 on both ports, no exceptions in server logs — expected, since
nothing schema-level changed). Net effect: a clean, well-scoped new
cleanup tool added to the toolchain, no regression, no bug to fix today —
closing this rotation's thread rather than leaving it open; next Cleanup
rotation should re-run all six checks before deciding whether a seventh is
worth adding.

### 2026-10-08 — Data currency rotation: exhaustive independent precision audit of `date+cc-clause-match`, no bug found, one real invariant documented

Container started with local `main` at `f9cd423` (2026-10-04's own commit,
matching `origin/main` exactly — no stale-ref gap this time, unlike most
prior sessions). Environment cold-start: `apt-get`-installed `git-lfs`,
`git lfs pull` for the real parquet (confirmed 163,356,047 bytes, not the
10KB LFS-pointer stub), `pip install duckdb pandas pyarrow streamlit
pyflakes vulture bandit`.

Rotation: Extractor had run 10-02 and 10-04 (two of the last three real
sessions), Cleanup ran 10-03, Data currency last ran 09-30 — the clear
next pull. Data currency's own backlog is in diminishing-returns
territory on every open item per 09-30's own note, so today's work
invented a new angle rather than re-running the same checks: instead of
spot-checking a handful of `article_amendment` resolutions by hand (the
pattern every prior Data-currency session used, typically 4-10 examples
per new tier), built a throwaway, from-scratch re-implementation of
`cc_blocks()`/`cc_clause_candidates()` and ran it against **all 478**
`date+cc-clause-match` rows — the project's single largest, most-relied-
upon amendment-resolution tier, never before audited at full scale for
precision rather than recall.

Two measurements: (1) every resolution is mechanically reproducible
(478/478, 0 mismatches re-deriving the same logic independently) — the
pipeline is deterministic, no reproducibility bug. (2) 13/58 distinct
amending documents have zero top-level `"N-modda."` markers (older
Roman-numeral-structured omnibus acts from the late 1990s/early 2000s,
plus modern standalone laws — e.g. a bank-sanitation law, an agricultural-
cooperative law — whose own articles are referenced internally as "ushbu
Qonunning N-moddasi" rather than headed "N-modda."), so `cc_blocks()`'s
fallback (`if not marks: blocks_by_doc[doc_id] = [text]`) treats the
*entire* document, up to 161,011 characters, as one block. That looked
like a live regression toward the naive whole-document search this
project explicitly measured and rejected on 2026-09-24 (where an omnibus
act's own sequential numbering coincidentally matched low target article
numbers).

Found 6 candidate rows (event_id 6, 52, 53, 54, 86, 247, spanning 3 of the
13 whole-doc-block documents) where the matched "Fuqarolik kodeks" mention
read as a passing substantive reference rather than a real citation —
e.g. event 6's "Bajarilishi Oʻzbekiston Respublikasi Fuqarolik kodeksining
259-moddasida nazarda tutilgan usullarda taʼminlanadigan majburiyatlar..."
sits deep inside a bank-sanitation law discussing what secures an
obligation, nowhere near a real "the Civil Code is hereby amended" clause.
Wrote and tested a stricter regex, `re_civil_citation = re.compile(r"(?:
qabul qilingan|tasdiqlangan).{0,130}?fuqarolik kodeks", ...)` — the two
bibliographic shapes every genuine Civil Code citation in this corpus
actually uses ("...1995/1996 **qabul qilingan** ... Fuqarolik kodeksi
(gazette locators)..." or "...-dagi ... Qonunlari bilan **tasdiqlangan**
... Fuqarolik kodeksi...") — and swapped it into `cc_clause_candidates`'s
guard in `build_links.py`. Tested against a throwaway copy of
`corpus.duckdb` (never the committed one) before deciding anything:
4/478 rows (52, 53, 54, 247) moved from `date+cc-clause-match` to
`date+sole-law-cc-mention`, landing on the *same* `amending_doc_id` in
every case (-7367697); events 6 and 86 didn't move at all, because the
same giant block also contains a second, separate, legitimate Civil Code
citation elsewhere that still satisfies the stricter check. Zero rows
became unresolved; `score_gold.py` unaffected (this tier doesn't touch
`citation_extractor.py`).

That near-zero effect is what led to the real finding: before shipping a
fix whose only measurable effect is relabeling 4 rows, checked *why* it
could only ever do that much — and found that **every single one of the
478 `date+cc-clause-match` rows has `host_article_number ==
target_article_number`** (verified directly against the live
`article_amendment` table: 478/478, 0 exceptions). This tier is only ever
asked to parse the Civil Code's *own* per-article `amendment_note` field —
`target_article_number` is always just the host article itself, LexUZ's
own authoritative annotation, never something this pipeline infers from a
list or range (`target_articles()`'s list/range-expansion machinery,
built 2026-09-13, has simply never had a case to apply inside this
specific tier). So the failure mode a weak same-block check could
theoretically cause — crediting an act with amending the *wrong article*
— is structurally impossible here today: the article is never in doubt,
only the identity of the cited act, which is a much narrower and already
better-defended question. Re-read the 6 candidate rows with that framing
and all 6 hold up: 4 resolve to -7367697/OʻRQ-1025, already independently
corroborated in the 2026-09-30 entry via its own genuine superscript-
article insertions (articles 181, 358-1, 962-1); event 6's restated text
for Article 2 ("...shuningdek banklarni sanatsiya qilish va tugatish
bilan bogʻliq munosabatlarga nisbatan fuqarolik qonunchiligi...") reads
as exactly the conforming scope-extension a bank-sanitation law would add
to the Civil Code's own scope article, not a coincidence; event 86's
Article 69 addition (a joint agricultural-cooperative organizational form)
is equally plausible as a real amendment from an agricultural-cooperative
law.

**Decision: reverted the regex change** (`git checkout -- build_links.py`,
confirmed clean via `git status`) rather than ship it. It has no
confirmed bug to justify it — the premise (risk of misattributing the
target article) doesn't hold given the `host==target` invariant — and
shipping an unvalidated stricter pattern carries real downside: the first
draft (`qabul qilingan` only) already had to be widened once after it
false-flagged two genuinely correct resolutions that use the "-dagi ...
tasdiqlangan" phrasing instead, and there is no guarantee a third,
unseen phrasing isn't still out there waiting to cause a real false
negative on some future gold batch or corpus update. `corpus.duckdb` is
therefore byte-identical to yesterday; no rebuild of any kind was done or
needed. `verify_transfer.py`: all checks green, identical INFO-line
numbers to 10-04. `pyflakes *.py` / `vulture *.py --min-confidence 60`
both clean (nothing shipped, so nothing new to check, but re-ran both to
confirm the revert left no stray residue). Did not re-run
`check_sql_bindings.py`/`bandit`/`test_transfer_e2e.py` — no file in
their scope changed from the committed state.

**This is a deliberate negative result, not a non-finding**: the project
now has direct, exhaustive (not sampled) confirmation that its largest
amendment-resolution tier's core mechanism — one article number is never
in competition with another inside this tier's block-matching, ever — is
sound, reached by building new, reusable-in-spirit verification logic
rather than repeating the existing spot-check pattern. See Backlog for
the one real condition (an extension to `target_articles()`) that would
make the 13 whole-doc-block documents worth measuring again.

### 2026-10-04 — Extractor rotation: eighth gold batch, found and formalized a new "§ N" section-mark gap, 300 -> 340 records

Same stale-local-ref pattern as 2026-09-04 and 2026-10-03 at session start:
this container's `main` sat at `209c62f` (three days behind) with HEAD
detached at `4d7f5ce` (10-03's own commit). `git fetch` confirmed
`origin/main` was already at `4d7f5ce`, so nothing was actually unpushed —
fast-forwarded local `main` to it (`git checkout main && git merge --ff-only
origin/main`) before starting. Recorded again since this is now the third
occurrence; if a fourth session hits it, worth asking whether something
about how these containers are provisioned reliably leaves `main` stale
rather than treating it as a one-off each time.

Continued the Extractor thread (last touched 2026-10-02; 10-03 rotated to
Cleanup, and that session's own log explicitly flagged Data currency as
diminishing-returns on every open item — so with Cleanup now also closed
for this rotation, the Extractor thread was the clear next pull, not a
forced rotation-order pick). Drew an eighth signature-stratified batch:
`python build_gold_sample_novel.py --seed 20261004 --n 40` (258/451
signatures covered going in, matching the 10-02 log's own number exactly —
confirms the sampler's coverage tracking is stable across sessions/containers).

Hand-read all 40 windows against the raw parquet text and the live
`extract()` output. 39/40 are correct. The 40th (row 41858, doc -104720, a
code's own cross-reference) reads "Fuqarolik kodeksining 9-bobi § 2" — the
same semantic content as the many "N-bobining M-paragrafi" citations
elsewhere in the corpus, but using a "§ N" section-mark symbol instead of
the word "paragraf". `citation_extractor.py`'s chapter+section lookahead
(`sec = re.match(r"\s*,?\s*(\d+)\s*-\s*paragraf", ...)`, run right after a
bob match) only recognizes the literal word, so this citation resolves as a
bare chapter-9 citation — correct at the chapter level, but silently
dropping the section-2 grain. This is the same failure class as two
already-documented backlog items (the 2026-09-22 "paragrafi"->"paragrifi"
misspelling gap, and the 2026-09-25 Roman-numeral-chapter-never-gets-the-
lookahead gap): a real citation, with `dst_kind` landing one level coarser
than it should (`chapter` instead of `section`), not a dropped citation.

Measured corpus-wide before deciding whether to invest in a fix: a regex
scan for `bob\w*\s*§\s*\d+` across every Civil-Code-anchor candidate row
(the same row set `build_gold_sample_novel.py` scans) found exactly 2 raw
occurrences. Checked both by hand: row 41858 (this one, in scope) and row
35993 ("ushbu Qoidalarning XXI bobiga § 84" — "this [set of internal] Rules'
Chapter XXI, § 84" — a different document's own internal numbering, not a
Civil Code citation at all, and not inside any Civil Code anchor window).
So the real, in-scope footprint is exactly 1 occurrence corpus-wide.

**Decision: did not fix.** This project has applied the same
single-occurrence-scope reasoning consistently to the paragrif gap, the
Roman-chapter-lookahead gap, and the chapter+paragraph space-separator gap
— a 1-occurrence count doesn't justify touching a regex that 106+ other
call sites and dozens of self-tests already depend on being conservative.
Formalized instead as a new `known_gap` gold record (`gold_id` 324, in
`gold_citations.json`) carrying the true `section 9/2` expected output, so
the score reflects an honest, permanent regression check rather than either
silently marking it correct or leaving it as an un-tracked backlog line.
Added the same reasoning to the Backlog (new item, same family as the two
existing section-lookahead gaps) in case a future corpus update introduces
more "§"-style citations and tips the scope calculus.

Merged the batch: **gold set 300 -> 340 records.** Re-scored:
**precision 1481/1489 (99.5%), recall 1481/1492 (99.3%)** (up from
1189/1196 = 99.4% / 1189/1199 = 99.2% at 300 records) — the movement is
exactly one new honest miss (`gold_id` 324's FP/FN pair) plus 39 newly
confirmed-correct windows, verified by diffing `score_gold.py`'s mismatch
list before and after the merge rather than just reading the headline
percentages. **New signature coverage: 298/451** (up from 258/451),
1179/3251 candidate windows still never-annotated.

No pipeline code changed today (`citation_extractor.py`, `build_links.py`
untouched) — only `gold_citations.json` and this file — so
`corpus.duckdb` is byte-identical to yesterday and no rebuild was needed or
attempted. `verify_transfer.py`: all checks green, identical INFO-line
numbers to 10-03 (372/386 General Part articles cited, 248 acts
superseded/495 realization edges, 39 OKOZ mappings awaiting validation).
`pyflakes *.py` / `vulture *.py --min-confidence 60` / `check_sql_bindings.py`
all clean (106/119 call sites checked, all bind). `python -m unittest
test_transfer_e2e.py`: 14/14. Both apps smoke-tested live (fresh
`streamlit run` on :8601/:8602, HTTP 200, server logs free of
errors/exceptions).

**Decision on today's rotation choice**: didn't invent a brand-new angle
this session — the signature-stratified gold sampler is still finding a
real, previously-uncharacterized gap roughly every other batch (7 of 8
batches so far have found something; this is the second batch in a row to
find exactly one), so it's still the highest-measured-yield use of an
Extractor session, not yet a checklist-running exercise. Worth revisiting
that judgment once a batch comes back fully clean (0/40) for the first
time — at that point diversifying into a genuinely new method (e.g.
model-assisted window classification, or targeting the specific 153
not-yet-covered-at-all signatures directly rather than sampling from them)
would be the better next invention, not another uniform draw from the same
sampler.

### 2026-10-03 — Cleanup rotation: re-confirmed pyflakes/vulture/f-string grep/bandit clean, invented a fifth check (SQL-schema-binding validation via DuckDB PREPARE), proved it with a mutation test, adopted it

Also fixed a stale-container git issue found at session start: this
container's clone had `main` sitting at `209c62f` (one day behind) with HEAD
detached at `7c40bed` (10-02's own commit, two ahead) — `git fetch` showed
`origin/main` was already at `7c40bed`, so 10-02's work *had* made it to the
remote; this container's local branch ref was just stale from before that
push. `git branch -f main 7c40bed && git checkout main` fixed the local ref
to track `origin/main` correctly; nothing was unpushed or at risk, and no
push was needed to resolve it. Recorded here only so a future session
doesn't mistake a stale local ref for a real problem.

Data currency's backlog (see Backlog) is now diminishing-returns on every
open item — the 39/612 amending-act residual and the OKOZ-granularity item
both explicitly say "not worth re-opening without a new angle"/"not scoped
by today's finding alone." Cleanup's own backlog, by contrast, had a
concrete, explicit next step: 10-01's entry asked "next rotation should
re-run all four before deciding whether a fifth is worth adding." Re-ran all
four first: `pyflakes *.py` (0 issues), `vulture *.py --min-confidence 60`
(0 issues), `bandit -r . -x ./articles,./documents,./okoz,./structure` (61
findings — same 57 `B608`/3 `B311`/1 `B110` breakdown as 10-01, no new
issue), and the `execute(f"...")` grep (**32 call sites**, up from 31 at
10-01). Re-verified all 32 programmatically rather than eyeballing: wrote a
quick AST-based extraction of every f-string's `{...}` interpolated
expressions and listed the distinct identifiers per file —
`build_corpus_db.py`: `CC_GENERAL_PART`, `raw`; `build_gold_sample.py`/
`build_gold_sample_novel.py`/`measure_extractor_recall.py`/`score_gold.py`:
`raw` only; `build_links.py`: `cx.DOC_GENERAL`, `doc_id`, `raw`;
`build_llc.py`: `CC_GENERAL`, `LLC_LAW_CURRENT`, `LLC_LAW_PRIOR`, `raw`, and
`','.join('?' * len(REPEALED_COMPANY_ARTICLES))`; `verify_transfer.py`:
`CC_GENERAL_PART`, `raw`. Checked the one that looked most suspicious at a
glance — `build_links.py`'s `doc_id` (a loop variable, not an obvious
constant) — by hand: it's `for doc_id in CC_DOCS:` where `CC_DOCS =
(cx.DOC_GENERAL, cx.DOC_SPECIAL)` (`build_links.py:30`), a fixed 2-tuple of
module-level constants, not a runtime/user value, so it's fine under the
project's own rule. All 32 sites interpolate only hardcoded constants —
zero violations. (Didn't chase why the count moved 29→31→32 across 09-26/
10-01/10-03 when each day's note names only one new site; neither 7c40bed
nor 8b7b808 touch any `execute(f` call site, so today's +1 isn't explained
by yesterday's commits either — most likely earlier bookkeeping drift, not
a new site. Not worth forensically re-auditing every prior count when
today's direct re-check is itself clean.)

**The actual question — is a fifth tool worth adding — needed a real
answer, not just "re-run the greps again."** Looked at what the four
existing tools structurally cannot see: none of them understand SQL at all.
`pyflakes` and `vulture` operate on Python syntax/symbol-reachability — a
SQL string with a typo'd column name is just a string literal to both,
syntactically valid and "used." The f-string grep governs interpolation
safety (constant vs. runtime value), not query correctness. `bandit`
pattern-matches known-risky *constructs* (string-built SQL, weak random),
not whether a query actually binds against a schema. And the project's own
verification step for the apps is "smoke-tested live (HTTP 200)" — which
only proves the *default* page of each app loads, not that every widget's
query on every page actually resolves. That's a real, previously-unmeasured
gap: a column rename or typo inside, say, `app_llc.py`'s dossier-detail
query would sit silently broken until a person happened to click into that
specific page.

**Built `check_sql_bindings.py`.** Confirmed first that DuckDB's `PREPARE
<name> AS <query>` is exactly the right primitive: it resolves every
table/column reference in a query against the connected schema and raises
`BinderException`/`CatalogException` on a bad one, *without* needing actual
parameter values bound — so a query full of `?` placeholders validates
cleanly with no dummy inputs required (confirmed interactively: `PREPARE t1
AS SELECT * FROM norm_unit WHERE article_number = ?` succeeds unbound;
`PREPARE t2 AS SELECT * FROM norm_unit WHERE nonexistent_col = ?` raises
immediately with the real "not found in FROM clause" error and candidate-
column suggestions). The script walks each target file's AST (not a regex —
multi-line triple-quoted strings and the project's own `q(sql, params)` /
`qdf(sql, params)` calling convention would be fragile to approximate any
other way) for every call to `q`/`qdf`/`execute` whose first argument is a
plain string literal (or a `+`-chain of literals), then runs
`PREPARE`/`DEALLOCATE` for each one against a fresh `read_only=True`
connection to `corpus.duckdb`.

**Scope decision, made by testing both ways rather than assuming**: first
ran it against every `*.py` file in the repo (156 queries found, 17
"failures"). All 17 turned out to be the wrong kind of failure for this
tool: every `CREATE TABLE`/`CREATE VIEW` statement in `build_corpus_db.py`/
`build_links.py`/`build_okoz.py`/`build_llc.py` fails outright because DDL
isn't a `PREPARE`-able statement at all, and one `INSERT`
(`build_corpus_db.py:254`) fails with "table uz does not exist" because
`uz` is a `CREATE OR REPLACE TEMP TABLE` created by the immediately
preceding statement in that same pipeline run (`build_corpus_db.py:248-253`)
— this tool's one-statement-per-fresh-connection model has no way to see
session state a multi-statement script builds as it runs, and that's not a
real bug to chase: those four scripts already self-validate every single
time `python build_*.py` completes without crashing, which every green
`verify_transfer.py` run already proves happened. So the default scope is
deliberately just the read-only layer: `app_hierarchy.py`, `app_llc.py`,
`verify_transfer.py`, `score_gold.py`, `measure_extractor_recall.py`,
`build_gold_sample.py`, `build_gold_sample_novel.py` (the last two have no
`CREATE` statements at all — checked with a plain grep before including
them). Against that 7-file scope: **106 literal SQL queries checked, all
bind cleanly**; the gap to the file set's 119 total `q`/`qdf`/`execute` call
sites breaks down as 4 (the `q()`/`qdf()` helper *definitions* in
`app_hierarchy.py`/`app_llc.py` themselves, not call sites), 8 (f-strings,
already covered by the grep audit above — `verify_transfer.py` ×4,
`score_gold.py` ×2, `measure_extractor_recall.py` ×2), and 1
(`measure_extractor_recall.py:172` — a literal assigned to a local `q`
variable a few lines earlier and passed by name, which the AST walk
doesn't resolve; a real but single-occurrence coverage gap, left as a
documented limitation in the script's own docstring rather than building
variable data-flow tracking for one site — same precedent several Extractor
backlog items already set).

**Proved the check actually catches something, not just "nothing's broken
today."** A clean run on day one of a tool proves nothing about its
sensitivity — ran a mutation test instead: copied `app_llc.py` to a
scratch file, changed one column reference inside a real, currently-correct
query from `article_title` to `article_title_TYPO` (line 89, the LLC
foundation-mapping query), and ran the checker against the mutant. Caught
immediately: `BinderException: Referenced column "article_title_TYPO" not
found in FROM clause!`, with the exact line number and the full query text
printed. This is precisely the failure mode none of the other four tools
can see — valid Python, a "used" string literal, no SQL-injection shape —
so it's a genuinely new class of coverage, not a re-discovery. Discarded
the mutant and scratch checker copy afterward; `corpus.duckdb` was opened
`read_only=True` throughout, so nothing was ever at risk.

**Decision: adopted.** `check_sql_bindings.py` is now a fifth repeatable
Cleanup check, same escalation pattern as `vulture` (09-23) and `bandit`
(10-01) — each added only once the existing set stayed clean on a fresh
re-run and a real, measured, distinct-from-the-others gap was identified
first. Zero new runtime dependency (reuses `duckdb`, already required by
everything in this project); every connection it opens is read-only.
Verified: `pyflakes`/`vulture --min-confidence 60` clean on the new file
itself; `python verify_transfer.py` all green, same INFO-line numbers as
10-02 (this change touches nothing in the pipeline or `corpus.duckdb` —
every query run today, by the new script and by me directly, used a
read-only connection); `python -m unittest test_transfer_e2e.py` 14/14.
Both apps smoke-tested live: fresh `streamlit run app_hierarchy.py
--server.port 8601`/`app_llc.py --server.port 8602`, both returned HTTP 200.

**Next Cleanup rotation**: re-run all five (`pyflakes`/`vulture`/f-string
grep/`bandit`/`check_sql_bindings.py`) before deciding whether a sixth is
worth adding. The `measure_extractor_recall.py:172` single-occurrence
coverage gap is worth closing only if `check_sql_bindings.py` is being
touched anyway for some other reason — not a standalone justification.

### 2026-10-02 — Extractor rotation: gold set 260 -> 300 (batch 7), built and closed the "boʻlim"/Part-level citation backlog item, caught and fixed a false positive the new feature introduced

Picked up the open Extractor gold-set thread (09-29's own note: "next
Extractor rotation should keep drawing fresh batches"; 09-30 and 10-01 had
rotated to Data currency and Cleanup, so this was Extractor's turn back).

**Drew batch 7**: `build_gold_sample_novel.py --seed 20261002 --n 40`
(novelty coverage 218/451 signatures before drawing). Hand-read all 40
windows against the raw Uzbek text and the extractor's own stop-word/anchor
rules. 38/40 were already-correct instances of well-covered shapes
(self-reference/fuqarolik_kodeksi anchors, list/range modda citations,
roman-numeral chapter citations, act-level fallbacks for Plenum-resolution
citations where the specific clause numbers belong to the resolution, not
the Code). 2/40 (rows 46656, 48850) are occurrences of the existing
"'boʻlim' is never a recognized citation unit" backlog item (open since
2026-09-17, measured then at 6 corpus-wide occurrences, re-confirmed
unchanged at 09-28).

**Re-measured the backlog item's own methodology before building anything**:
the 09-17/09-28 corpus-wide count used a hyphen-only regex
(`[IVXLC]+\s*-\s*boʻlim`). Making the hyphen optional (LexUZ writes the unit
word with a bare space far more often than a hyphen — the same variability
already handled for modda/bob/paragraf) found 14 *more* real occurrences:
20 corpus-wide via literal "Fuqarolik kodeksi(ning) <roman> boʻlim" text
alone, all confirmed genuine by hand (none are a different document's own
Part reference at this stage of the check).

**Built Part-level citation support**: added `RE_ROMAN_PART` to
`citation_extractor.py` (matches a roman numeral + "boʻlim", hyphen or
space, either apostrophe-like spelling LexUZ uses) and a new
`target_kind='part'`. Scanned *independently* of the main modda/bob/paragraf
loop (not gated on `produced` the way the existing Roman-chapter fallback
is) because a part citation can sit either before an already-matched clause
in the same window ("Fuqarolik kodeksi III-boʻlimining ... va
927-moddasi", row 32449) or after one ("23-bobi ... hamda V boʻlimiga",
row 38614) — a `not produced` gate would have silently kept dropping those.
Resolved in `build_links.py` via a new `_int_to_roman()` helper to the
corpus's existing `struct_node` Part rows (`PI`..`PVI` — real data already
present from `structure_parser.py`, nothing new to build there). Running the
fixed extractor itself (not a hand regex) corpus-wide found **5 more real
occurrences** the literal-text regex structurally could never see: 2 via the
`self_reference` anchor ("ushbu/mazkur Kodeksning", rows 46656/46741 — the
first is literally one of today's batch-7 windows) and the `anchor`-window
mechanism reaching past an already-matched clause, which a plain text regex
has no equivalent of (rows 38614, 32449, plus one more). **Real corpus-wide
total: 25 occurrences, not 6 or even 20.**

**Caught and fixed one real false positive before shipping**: the
unconditional, whole-window scan initially mis-caught row 42566's "...
"Bojxona toʻlovlarini toʻlash muddatlarini uzaytirish ... boʻyicha
yoʻriqnoma"ning (roʻyxat raqami 697, 08.04.1999-y.) IV boʻlimi" — a
different document's own Part IV, not the Civil Code's — because `RE_STOP`
had no entry for "yoʻriqnoma" (instruction/guideline) as a named-other-act
signal, and the real Civil Code citation in that window is a separate,
earlier "22-bobining 5 paragrafi" clause the new part-scan ran straight
past. Measured corpus-wide before adding "yoʻriqnoma" to `RE_STOP`: 11
anchor windows mention it at all, and row 42566 is the *only* one where any
modda/bob/paragraf/boʻlim clause follows it within the window (the other 10
only ever reach an "ilova"/annex or "band"/point, units this extractor
never matches anyway) — zero collateral loss elsewhere, confirmed by
re-running `score_gold.py` before and after.

**Numbers**: `build_links.py` 9530 -> 9535 edges (24 real `dst_kind='part'`
edges after dropping the false positive: 22 via the `fuqarolik_kodeksi`
anchor + 2 via `self_reference`). Updated 5 pre-existing `gold_citations.json`
records (gold_id 134/170/186/193/200, rows 21686/32449/35586/37887/38614)
whose expected output changed from a bare `act` citation (or no part field
at all) to include the new part citation — these were scored `correct`
before only because the schema had no field to express the gap against,
same treatment the backlog item always got; now scored correct against
real, resolved output, not a vacuous pass. Merged batch 7 as gold_id
260-299 (all `verdict: correct` against the current, fixed extractor).
**Combined score: precision 1189/1196 (99.4%), recall 1189/1199 (99.2%)**
on 300 windows, up from 926/933 (99.2%) / 926/936 (98.9%) on 260 — a real
improvement (24 previously-wrong-or-missing edges now resolving correctly),
not just a larger denominator. New signature coverage: 258/451 (up from
218/451), 1257/3251 candidate windows still never-annotated.

Added 6 self-test cases to `citation_extractor.py` (57/57 passing, up from
51/51). `pyflakes`/`vulture --min-confidence 60` clean on both changed
files; `bandit` re-run on both (14 pre-existing `B608` hits, unchanged —
no new finding from this session's code). `python -m unittest
test_transfer_e2e.py`: 14/14. `verify_transfer.py`: all checks green, same
General-Part-coverage INFO numbers as before (372/386 cited, 285/386 below)
— this feature adds a coarser-than-chapter target kind without changing
which articles are cited, so that metric correctly didn't move. Both apps
smoke-tested live (HTTP 200, no exceptions in logs); additionally verified
by hand that `app_hierarchy.py`'s existing "citations to this article's
chapter/section as a whole" query — already written generically against
`v_realization_struct`, so it needed no code change — correctly surfaces a
real part-level citation (Part II, "Right of Ownership and Other Property
Rights") when viewing General Part article 206.

This closes the "boʻlim" backlog item. The gold-set thread stays open —
see Active threads for next steps (keep drawing `build_gold_sample_novel.py`
batches; the "2-kichik boʻlim" subsection grain one level finer than Part,
visible in rows 32449/46741, is a new small thing worth a look given the
Part-grain machinery now exists).

### 2026-10-01 — Cleanup rotation: re-confirmed pyflakes/vulture/f-string grep clean, added `bandit`, found and fixed a real test-suite blind spot in `test_transfer_e2e.py`

Cleanup's turn (09-30's own note: prefer Cleanup next, repeatable checks not
re-run since 09-26). Cold-start: `apt-get install -y git-lfs` was already
present; `git lfs pull` (parquet was the 134-byte pointer stub, confirmed by
`verify_transfer.py`'s own `_check_parquet_pulled()` guard — it's been there
since 09-26 for exactly this); `pip install duckdb pandas pyarrow streamlit
pyflakes vulture`. `git status`/`git log` showed local `main` already
up to date with `origin/main` at `209c62f` (no detached-HEAD gotcha this
time).

**Re-ran the three existing repeatable checks first**, before deciding
whether to widen the toolchain:
- `python3 -m pyflakes *.py` — 0 issues.
- `python3 -m vulture *.py --min-confidence 60` — 0 issues.
- `grep -c 'execute(f"' *.py` — 31 call sites total (was 29 at 09-26's
  audit). Diffed against `git show 74b4574:build_links.py` (the 09-26
  commit) to find exactly what changed: one new site at `build_links.py:669`
  (`text_by_doc`'s dict comprehension, added by 09-27's fix for the
  `src_provision`-pagination-chunk bug — see Active threads). Classified it
  the same way the 09-26 audit classified every other site: it interpolates
  `{raw}`, which is `f"read_parquet('{PARQUET.as_posix()}', ...)"` —
  the same hardcoded `PARQUET`-path constant every other call site in the
  file already uses, not a runtime value. Not a violation.

All three clean — third time in a row (09-19 pyflakes, 09-23 vulture, 09-26
f-string grep each stayed clean on re-run before that session widened the
toolchain). Followed the same established pattern: **installed `bandit`**
(a security-pattern linter — genuinely different analysis from the other
three: `pyflakes` does per-scope import/variable-usage analysis, `vulture`
does whole-repo symbol-reachability, the f-string grep is a single targeted
regex; `bandit` pattern-matches known-risky constructs like string-built SQL,
weak randomness, bare excepts). Ran `bandit -r . -x
./articles,./documents,./okoz,./structure` (excluded the four data
directories — not code).

**61 findings across 3 rule IDs**:
- **`B608` (hardcoded SQL expression), 57 hits.** Every single one is a
  `execute(f"...")` call site the 09-26 manual audit already individually
  classified. `bandit` has no type information, so it flags every f-string
  inside an `execute()` call regardless of whether the interpolated value is
  a hardcoded constant or a runtime one — strictly blunter than the manual
  audit, not a new finding. Confirmed by spot-checking several against the
  09-26 classification: all hardcoded-constant, all already judged safe.
- **`B311` (non-cryptographic `random.sample`), 3 hits**, all in
  `verify_transfer.py`'s AC3 spot-check sampling. Standard bandit
  false-positive class — this is drawing a verification sample, not
  generating a secret, so cryptographic strength is irrelevant. Reviewed,
  left alone.
- **`B110` (`except Exception: pass`), 1 hit**, in
  `test_transfer_e2e.py:290`, inside `parse_markdown_articles()`'s loop over
  candidate `parser.py` function names:
  ```python
  try:
      res = fn(file_path)
      if isinstance(res, list) and len(res) > 0:
          return res
  except Exception:
      pass
  ```
  This one looked worth tracing rather than dismissing outright, since a
  silently-swallowed exception in a fallback path is exactly the shape of
  bug this project's other Cleanup sessions have found real issues in
  (dead code, dangling constants) — the question was whether this except
  ever actually fires, and if so, whether it's hiding something.

  **Traced it by instrumentation, not just reading**: loaded the real
  `parser.py` via the same `importlib.util` mechanism
  `load_external_parser()` uses, wrapped its `parse_markdown()` to print
  when called and what it returns, and ran `parse_markdown_articles()`
  against the real markdown file. Result: `parser.py`'s `parse_markdown()`
  **is** called every time (the `except` branch is reachable code, not
  literally dead) — but it returns `{"metadata": {...9 keys...}, "articles":
  [...394 items...]}`, a `dict`, never a bare `list`. `isinstance(res, list)`
  is `False`, so the function falls through to
  `parse_internal_markdown_articles()` every time, without ever raising —
  the `except Exception: pass` has never actually fired in this file's
  history; it's a defensive no-op, not a bug by itself.

  **But tracing it surfaced something else.** `parsed_articles.json` (the
  file `build_corpus_db.load_markdown_articles()` actually reads, via
  `data["articles"]`) is exactly this same `{"metadata", "articles"}` shape
  — confirming `parser.py`'s `parse_markdown()` is a real, substantial,
  independently-maintained parser (its own docstring: "FSM line-by-line
  streaming parser... 15-field output schema... Built-in `--verify` and
  `--summary` CLI suite with 10 automated verification checks"), not a stub.
  Running `python3 parser.py --verify` directly confirms: "Parsed 394
  articles... All 10 verification checks PASSED." So `parser.py` is a real,
  working, independently-verified tool — but nothing in the automated test
  suite ever actually calls it meaningfully, because `parse_markdown_articles()`'s
  `isinstance(res, list)` check can never be satisfied by its real return
  shape.

  That's by design for `self.extracted_articles` (Tier 1's own module
  docstring: `parse_markdown_articles()` is supposed to be "a from-scratch
  re-parse... independent of structure_parser.py and the frozen
  `parsed_articles.json` the real pipeline loads" — so never preferring
  `parser.py`'s own output here is actually correct, not a bug, since using
  it would make Tier 1 tautological). But `test_r1_markdown_extraction`
  (`test_transfer_e2e.py:324`) does something different: after checking
  `self.extracted_articles` (the independent count), it *separately* calls
  `parse_markdown_articles(MARKDOWN_PATH)` again and asserts on it with the
  message `f"External parser.py extracted {len(external_result)} articles
  instead of {EXPECTED_TOTAL_ARTICLES}"` — i.e. it explicitly claims to be
  testing `parser.py`'s own output. Since `parse_markdown_articles()` always
  falls through to the internal reimplementation (as just traced), **this
  assertion has always silently re-tested the internal parser a second time
  under a label claiming it tested `parser.py`**, for the entire life of
  this file (confirmed via `git log --diff-filter=A` — present since the
  very first commit, `e96fb5c`).

  **Verified this is a real, consequential blind spot, not a cosmetic
  mislabeling**: monkeypatched `parser.py`'s own `parse_markdown()` to drop
  one article (`res['articles'] = res['articles'][:-1]`, simulating a real
  394->393 regression) and ran `test_r1_markdown_extraction` against both
  the pre-fix and post-fix code with that monkeypatch injected via
  `t.load_external_parser = lambda: mod`. **Pre-fix: test still passes,
  completely blind to the simulated regression** (since the assertion was
  really checking the untouched internal reimplementation, not the
  monkeypatched module). **Post-fix: test fails correctly** —
  `AssertionError: 393 != 394 : External parser.py extracted 393 articles
  instead of 394`, with the right count. This is exactly the proof this
  project's "measure before claiming done" pattern calls for, applied to a
  test-suite bug rather than a pipeline one.

  Fixed by making `test_r1_markdown_extraction`'s assertion call `parser.py`'s
  function directly and unwrap its `"articles"` key (handling both the
  dict-wrapped shape `parser.py` actually returns and a bare-list shape for
  robustness, in case a future `parser.py` refactor changes it), instead of
  routing through `parse_markdown_articles()`. `self.extracted_articles` and
  every other test in the file are untouched — `parse_markdown_articles()`
  itself still behaves exactly as before (same independence property for
  Tier 1), only this one previously-inert assertion changed.

  **Why this matters beyond a lint fix**: `parser.py --verify` is the only
  thing that currently exhaustively checks `parser.py`'s own output (10/10
  checks, including the exact article count), but it's a standalone CLI a
  human has to remember to run separately — it isn't wired into
  `verify_transfer.py`'s AC1-AC7 or invoked by `python -m unittest
  test_transfer_e2e.py`, the two automated checks every session in this log
  already runs before committing. `test_r1_markdown_extraction` looked like
  the one place this was automated, and wasn't. Now it genuinely is: a
  future regression in `parser.py`'s own article-extraction logic (which
  feeds `parsed_articles.json`, which `build_corpus_db.py` actually loads
  into the pipeline) will now be caught by the routine `unittest` run this
  project already does every session, not just by a `--verify` flag nobody
  is required to pass.

**Full verification after the fix**: `python3 -m pyflakes test_transfer_e2e.py`
and `python3 -m vulture test_transfer_e2e.py --min-confidence 60` both clean;
`python3 -m py_compile test_transfer_e2e.py` clean; `python -m unittest
test_transfer_e2e.py` — 14/14 pass (including the fixed test, now actually
exercising `parser.py`). Re-ran `bandit` after the fix: `B110` count
unchanged at 1 — the *other* `except Exception: pass`, inside
`load_external_parser()` itself (catches a failed dynamic import of
`parser.py` and returns `None`), deliberately left alone: that one guards
the whole mechanism's intended graceful-degradation behavior (if `parser.py`
is missing or fails to import, skip the external-parser section of the test
entirely rather than crashing), reviewed and judged correct, not a second
instance of the same bug. `python3 verify_transfer.py` — all checks green,
same INFO-line numbers as 2026-09-30 (248 superseded acts, 494 stale edges,
372/386 General Part articles cited, 39 OKOZ mappings awaiting validation —
this change has zero pipeline or `corpus.duckdb` surface; `test_transfer_e2e.py`
isn't part of the build pipeline and writes nothing). `score_gold.py`:
unchanged at 926/933 (99.2%) precision, 926/936 (98.9%) recall, 0 drift
(doesn't touch `citation_extractor.py`). Both apps smoke-tested live:
started `app_llc.py` on :8501 and `app_hierarchy.py` on :8502, `curl` HTTP
200 on both, no exceptions in either's server log — no schema change, so a
load check is sufficient per the project's own established rule. `git
status`/`git diff` confirm the only change is the ~20-line patch inside
`test_r1_markdown_extraction` in `test_transfer_e2e.py` — no other file
touched, `corpus.duckdb` untouched and not re-committed.

**Decision**: closing this thread, not leaving it active. The `B608`/`B311`
classes needed review but no fix (re-discoveries and a standard false
positive respectively); the `B110` class needed tracing, which paid off with
one real, verified, previously-invisible bug, now fixed and proven with a
reproduced-before/confirmed-after regression test. `bandit` joins
`pyflakes`/`vulture`/the f-string grep as a fourth repeatable Cleanup check
— next time this rotation comes up, re-run all four before considering a
fifth.

### 2026-09-30 — Data currency rotation: root-caused the amending-act-resolution residual to a genuine source-scrape gap, built a new fallback tier around it, 85.1% -> 93.6%

Rotated to Data currency rather than continuing the Extractor thread a
fourth session running (Extractor had 09-25/09-28/09-29 of the last five
sessions; Cleanup's own backlog is fully drained and its repeatable checks
were last re-run 09-26, so between the two non-Extractor areas, Data
currency's still-open 91/612 amending-act-resolution residual (left by
2026-09-27) was the more concrete, measurable target). Cold-start steps:
`apt-get install -y git-lfs && git lfs install && git lfs pull` (parquet
was the 134-byte pointer stub), `pip install duckdb pandas pyarrow
streamlit pyflakes vulture`. Also found the local `main` ref stale again
(detached HEAD 6 commits ahead) — same recurring gotcha as most sessions
since 09-04 — `git fetch origin main` confirmed origin already had all 6
commits, so `git checkout -B main origin/main` only, no push needed.

2026-09-27's own entry had already split the 91-row residual into two
clusters and flagged the bigger one (57, "a same-date candidate act
mentions the Civil Code somewhere but not inside the target article's own
block") as the more promising half, suggesting a smarter same-block
heuristic as the next step. Reproduced `build_links.py`'s exact
`by_date`/`text_by_doc`/`cc_blocks` logic in a standalone script against
the real `article_amendment` table and confirmed the split exactly: 57 CC-
mentioned-elsewhere, 34 no-CC-anywhere, matching 2026-09-27's numbers
precisely. Picked the single largest cluster inside the 57 (36 rows, all
one omnibus act on one date: OʻRQ-1025, 2025-02-07, doc -7367697) and read
its raw parquet rows directly rather than guessing at a better heuristic.
Finding: this act has only 8 raw rows in the whole corpus, and the very
first one already opens mid-list at item 18 of what must be a much longer
numbered clause list (confirmed each row's text flows seamlessly into the
next — file_row_number order does preserve true document order here, it's
not a re-ordering bug). Items 1-17, and with them the top-level clause that
would name "Fuqarolik kodeksi" and the 8 target articles this cluster's
events need (39, 40, 42, 43, 46, 48, 55, 58), were simply never captured by
LexUZ's scrape for this act at all. This is a genuine source-completeness
gap, not a matching-logic one — no amount of smarter same-block matching
can find text that isn't in the raw parquet. Searched the whole corpus for
"Fuqarolik kodeksiga...kiritilsin"-shaped text under this doc_id to rule
out the header living under a different doc_id or row: confirmed absent.

The insight that unblocked this: the act is still safely identifiable
without needing the missing text, because `re_amend_event` (the regex that
extracts `amend_date`/`act_number` from each `amendment_note` clause in the
first place) only ever matches a citation naming a "Qonun" (Law) — so
every amending act this pipeline looks for is *guaranteed* by the source
citation's own grammar to be `doc_type='law'` in the `act` table. Built
`sole_law_cc_mention(iso)`: among same-date candidates restricted to
`doc_type='law'`, if exactly one's full captured text mentions "Fuqarolik
kodeks" anywhere (not restricted to any one block), resolve to it. Wired in
as a third fallback tier, `date+sole-law-cc-mention`, only reached after
`date+civil-code-title` and `date+cc-clause-match` both fail.

**Measured before touching the real database.** Retroactively checked the
new tier's own logic against all 62 distinct (date, doc) pairs the two
existing tiers already resolve: agrees on 53, silent (ambiguous or no
CC-mentioning law candidate) on 8, disagrees on exactly 1 — 2022-03-29,
where the true amending act is itself titled "...Fuqarolik kodeksiga...",
but LexUZ's own source `doc_type` field (copied straight into the `act`
table, not derived from title by this project — checked
`build_corpus_db.py`'s `act` INSERT to be sure before writing a wrong
comment) tags it `'code'`, not `'law'`. Not a real collision: that date
resolves via `date+civil-code-title` before the new tier would ever run.
Ran the fixed `build_links.py` against a throwaway copy of `corpus.duckdb`
first: diffed `article_amendment` row-for-row by `event_id` against the
pre-fix copy — 0 previously-resolved rows changed which act they resolved
to, 52 purely-additive new resolutions, `link_edge` (9530) and
`repeal_clause` (885) byte-identical. Hand-verified all 4 newly-resolved
dates against the raw text, not just structurally: **-55080** (2002-12-13)
contains exact "587-moddasining"/"589-moddasining"/"595-moddasi"/
"597-moddasining" matches for all 4 of that date's target articles;
**-2388207** (2014-05-14, OʻRQ-372) contains "65 va 66-moddalar chiqarib
tashlansin" verbatim — the exact voiding of Articles 65/66 that
`verify_transfer.py`'s reconciliation output has listed as an unexplained
`md_only`/`structure_missing_articles` gap since this project's very first
session (2026-09-03) — now finally traced to its voiding law and date;
**-6643526** (2023-10-23, OʻRQ-871) is a land-legislation omnibus act
plausibly touching the 173-1..173-7 superscript range its events cite;
**-7367697** (2025-02-07, OʻRQ-1025) is independently corroborated by
three of its own 8 raw rows being full quoted insertions of new Civil Code
articles 181, 358-1 and 962-1 — real corpus superscript articles this
exact reform created, confirming the act's identity even though its own
target-39-through-58 items are unrecoverable.

Applied to the real `corpus.duckdb`: `article_amendment` `by match_method`
now `{'date+cc-clause-match': 478, 'date+sole-law-cc-mention': 52,
'date+civil-code-title': 43, 'unresolved': 39}` — **521/612 (85.1%) ->
573/612 (93.6%)**. Re-ran `build_okoz.py`/`build_llc.py` against a
throwaway copy only (grepped both first to confirm neither reads
`article_amendment`; `build_llc.py` only reads `link_edge`, which this
change never touches, so re-running for real against the committed db
would only add non-deterministic serialization churn for zero content
change — same reasoning several prior Cleanup entries already established):
`llc_implementing_act` 135/135, `llc_norm` 100/100, `okoz_assignment`
39/39, all unchanged as expected. `verify_transfer.py`: all checks green,
same reconciliation output as before (no check is scoped to
`article_amendment`'s resolution rate, so nothing was expected to move).
`pyflakes build_links.py`/`vulture build_links.py --min-confidence 60`:
both clean. `python -m unittest test_transfer_e2e.py`: 14/14. 51/51
extractor self-tests. `score_gold.py`: unchanged at 926/933 (99.2%)
precision, 926/936 (98.9%) recall — expected, this change never touches
`citation_extractor.py`.

Smoke-tested both apps live via Playwright, and hit one unrelated
DuckDB startup race while doing it: `app_hierarchy.py`'s `_connect()`
opportunistically opens the file read-write (for its validation page) and
only falls back to read-only if that fails — a design tradeoff its own
docstring already documents for the *other* startup order (app_llc.py
first), but nothing mitigates the reverse order, so starting
`app_hierarchy.py` first starved `app_llc.py`'s read-only connection with a
real `_duckdb.IOException`. Not caused by today's change (confirmed by the
traceback: pure DuckDB single-writer/many-reader contention, no code path
touched today involved) — restarting with `app_llc.py` first cleared it
immediately; recorded here in case a future session hits the same
confusing-looking exception and wonders if their own change caused it.
With that resolved, both apps returned HTTP 200 with no exceptions, and
`app_hierarchy.py`'s Article 39 amendment-history expander now visibly
shows "Amending act: *Korporativ munosabatlarning huquqiy asoslari yanada
takomillashtirilishi...*" where it was blank before today (confirmed via
Playwright's rendered page content, not just a load check, since the
resolved-act name is exactly the new, directly-observable effect of this
session's change).

**Closed, not left active**: characterized the new 39-row residual instead
of stopping at a bare count. Most of the 11 remaining distinct dates have
2+ `law`-type same-date candidates that are genuinely ambiguous (multiple
mention the Civil Code, or none do) — correctly left alone by the new
tier's own conservative "exactly one" requirement. Checked the single
largest remaining cluster by hand (2025-04-17, 19 events, exactly 2
`law`-type candidates): neither candidate's captured text mentions
"Fuqarolik kodeks" anywhere at all — the same scrape-completeness class as
the newly-fixed OʻRQ-1025 cluster, not a solvable ambiguity. Diminishing
returns from here, matching the conclusion the repeal-resolution thread
reached for its own non-statute residual 2026-09-09 — not reopening
without a genuinely new angle (most plausibly sourcing a more complete
scrape of the handful of affected acts, which is a data-acquisition
question outside `build_links.py`'s reach, not a pipeline bug).

### 2026-09-29 — Extractor thread continued: gold set 220 -> 260, real "axborotnoma" recall bug found+fixed (9 rows, +3 LLC implementing acts), verify_transfer.py's own gazette check tightened

Continued yesterday's still-open Extractor thread (the brief's priority
order: finish a mid-flight thread before rotating to a fresh backlog item)
rather than picking Data currency or Cleanup next. Also spent real time at
the start of the session on an environment check inherited from prior
days' pattern: `git status` showed HEAD detached 5 commits ahead of the
local `main` ref; `git fetch origin main` showed origin/main was actually
already at that same commit (962a84d) — a stale local ref only, not lost
work — so this was just `git checkout main && git merge --ff-only`, no
push needed. Also re-ran the by-now-standard cold-start steps: `apt-get
install -y git-lfs && git lfs install && git lfs pull` (parquet was still
the 134-byte LFS pointer stub) and `pip install duckdb pandas pyarrow
streamlit pyflakes vulture`.

Drew batch 6 with `build_gold_sample_novel.py --seed 20260929 --n 40`
(signature coverage 178/451 before drawing) and hand-read all 40 windows
against the raw Uzbek text. Two of them (row 43534, row 44469) exposed the
same real bug: `extract()` returned a bare `act` fallback where the text
plainly names a specific article and part — e.g. row 43534's "Fuqarolik
kodeksi (Oʻzbekiston Respublikasi Oliy Majlisining Axborotnomasi,
1996-yil, № 11-12) 775-moddasining ikkinchi qismidagi ... soʻzlar chiqarib
tashlansin" should resolve to Article 775, part 2, not to a bare act
citation. Root-caused it to `RE_STOP`'s `axborotnoma` branch: that branch
exists on purpose, to stop the scan on the Code's own gazette
*publication-record* parenthetical (e.g. "(...Axborotnomasi, 1997-yil, №
2, 56-modda)"), so a gazette item locator like "56-modda" is never
mistaken for a Code article — a measured, deliberate design from the
pipeline's original build. But the stop is a whole-window `break` (the
pre-existing "break-vs-continue" backlog item's subject), and when a real
article citation legitimately follows the closing paren, the very first
`RE_CLAUSE` candidate *inside* the parenthetical (one of the gazette's own
locators) trips the break before the real citation downstream is ever
reached — discarding it too, not just the false one.

**Measured corpus-wide before fixing**: reimplemented the anchor+window
walk standalone to find every anchor window that starts with a balanced,
signal-bearing (`axborotnoma`/`vedomosti`/`toʻplam`/`№`) parenthetical: 25
such windows exist. Of those, 9 are immediately followed by a real
modda/bob/paragraf clause once the parenthetical closes, and *all 9* were
losing their citation entirely under the then-current code (articles 15,
38, 43, 48, 53, 292, 775, 788, 1015 — hand-confirmed each against the raw
text, all genuine Civil Code citations, several inside long omnibus
amending acts that also touch the Criminal Code, the Administrative
Liability Code, etc. earlier in the same very long row). This directly
contradicts the 2026-09-12 backlog note's claim that all 552
`break`-triggering windows with clauses remaining afterward were checked
and found safe — that measurement evidently didn't include (or predates)
these 9 `axborotnoma`-triggered rows; flagging the discrepancy here per
the project's own rule about not silently overriding a documented
decision, rather than re-asserting the old "not a live bug" claim.

**Fixed** in `citation_extractor.py`: added `RE_LEADING_PUB_PAREN`, a
regex matching a balanced parenthetical (no nested parens — confirmed none
of the 25 have any) starting right at the anchor and containing one of the
publication-record signal words. When it matches, the parenthetical is
blanked out in place (replaced with spaces of the same length, so every
downstream character offset into the untouched original `text` stays
correct) before the clause-scanning loop starts. Deliberately scoped to
only the parenthetical sitting *immediately* at the anchor, mirroring
exactly the measured shape — an `axborotnoma` mention anywhere else in the
window (after some other citation was already found) still triggers the
full, conservative break, unchanged; that's different, unmeasured
territory, noted as a fresh sub-item on the "break-vs-continue" backlog
entry rather than touched today. Checked for collateral risk before
committing to the fix: 58 anchor windows corpus-wide start with *some*
leading parenthetical; 33 of those are the unrelated "(bundan buyon matnda
FK deb yuritiladi)" FK-alias declaration (no publication-record signal
word, so `RE_LEADING_PUB_PAREN` correctly never touches them — added as an
explicit self-test guard) — only the 25 signal-bearing ones are affected.
Added 3 new self-test cases (`citation_extractor.py`, now 51/51 passing,
up from 48/48): the two-locator case, the single-locator case, and the
FK-alias-declaration non-match guard.

**Verified corpus-wide after fixing**: re-ran the same standalone
measurement — all 9 rows now resolve to their correct article, and
`ev_start`/`ev_end` on each new edge points precisely at the real citation
text ("775-moddasining", "53-moddasi", etc.), never at one of the
gazette's own locators. Re-ran the pipeline: `build_links.py` — 9530
edges total (unchanged; the 9 useless bare-`act` edges were converted in
place to real, resolved `article` edges, one of which duplicates an edge
already present at that row from a second, separate occurrence of the
same citation, hence the total count not moving by the full +9 even
though 9 real citations were recovered — confirmed by diffing `link_edge`
row-for-row between a pre-fix copy of `corpus.duckdb` and the fixed
rebuild); `build_okoz.py` unchanged (386/386 classified, same mappings,
expected — no citation-extraction logic feeds OKOZ); `build_llc.py` —
**`llc_implementing_act` grew 132 -> 135**, three new, real implementing
acts found (doc -36953, -42953, -44853, each an omnibus amending act
citing Civil Code articles 48, 53, and 43 respectively, all newly visible
to the LLC foundation-citation scan now that the underlying `link_edge`
carries the real article instead of a bare `act` fallback) — hand-checked
each: all three genuinely cite one of the LLC foundation articles.
`llc_norm` unchanged at 100/100 (no foundation-mapping logic touched, as
expected). Merged batch 6 into `gold_citations.json` as gold_id 220-259
(all "correct" — including the 2 that only score correct because of
today's fix, regenerated against the fixed extractor before merging, not
the pre-fix snapshot). `score_gold.py`: 260 records, 0 drift, **precision
926/933 (99.2%), recall 926/936 (98.9%)** — same 5 pre-existing known_gap
mismatches as 2026-09-28, 0 new ones.

**`verify_transfer.py` initially FAILED** after the fix, on its own AC5
"no article edge mined from an act's publication record" check — a
permanent regression guard, present since the pipeline's original build,
for exactly this false-positive class. Its heuristic checks whether an
edge's 90-char-padded evidence *text* mentions "Axborotnomasi, YYYY-yil"
and "№" *anywhere nearby*, which is too blunt now that real citations
legitimately sit close enough to a closed gazette parenthetical for the
padding to still catch both signal words even though the matched digits
themselves are provably outside it (2 of the 9 recovered edges, articles
53 and 775, both have a short enough gazette record for this to happen).
This is the check's own imprecision surfacing, not a reason to revert a
fix that's zero-regression on every other measure — refined the check in
`verify_transfer.py` instead: strip every *balanced* publication-record
parenthetical out of the evidence text first, then only flag an edge if
its `dst_article_number` + "modda" citation does *not* survive outside
that stripped text (i.e. it only ever existed inside the parenthetical).
Tested the refined logic standalone against both a synthetic true-positive
(article number only inside the paren — still correctly flagged) and the
2 real false positives (now correctly cleared) before trusting it.
`verify_transfer.py` green again, same INFO-line numbers elsewhere.
`pyflakes` clean on both changed files; `vulture --min-confidence 60`:
same pre-existing warnings only (2 dataclass-field ones in
`citation_extractor.py`, 2 `art_no` ones in `verify_transfer.py` —
confirmed via `git stash` that neither is new). `python -m unittest
test_transfer_e2e.py`: 14/14. Both apps smoke-tested live (`streamlit run`
+ `curl`: HTTP 200 from both, no errors/tracebacks in either log; no
schema change, so a load check is sufficient per the project's own rule).

The other 38/40 batch-6 windows all read correct against the raw text —
no other new gaps found this round (spot-checked the ones with the most
unusual shapes: multi-range-plus-list clauses like "236 — 258 va
784-moddalari" correctly expand all 24 values, though worth noting for
future reference that `_expand()`'s single `listing` tag covers the whole
clause, not per-value, so a range combined with a plain list via "va" is
tagged "list" throughout rather than "range" for the range portion — this
matches `_expand()`'s own documented, deliberate whole-clause granularity,
not a bug). **New signature coverage: 218/451 (up from 178/451)**,
1299/3251 candidate windows still sit in never-annotated territory. See
Active threads for the full detail and the specific next steps.

### 2026-09-28 — Extractor rotation: two more signature-stratified gold batches, gold set 140 -> 220, one new bug found, one existing backlog claim corrected

Rotation: of the last five sessions (09-23..09-27), Cleanup had two,
Extractor one, Data currency two — Extractor hadn't run since 09-25, so
today is Extractor's turn. Followed the established next-step
(`build_gold_sample_novel.py` with a fresh seed) rather than inventing a
new angle, since that thread is explicitly still open.

**Batch 4** (`--seed 20260928 --n 40`): novelty coverage was 98/451
signatures (up from 58/451 on 09-25, since batches 3 grew the set since
then). Read all 40 windows by hand against the raw text. Result: 38/40
correct, 2/40 known_gap — but **both known_gaps were re-discoveries of
already-documented backlog items that had never actually been formalized
into `gold_citations.json`** (the "hamda" list-separator gap, row 24219;
the chapter+paragraph-list-with-parenthetical gap, row 25634) plus one more
"correct" re-hit of the already-known "boʻlim" gap (row 32449). Zero new
bugs. While formalizing the "hamda" record, **found the 2026-09-15 log
entry's own description of that gap was factually wrong**: it claims "the
fix already recovers '11-12' as an embedded sub-range independently," but
directly re-running `citation_extractor.extract()` on the exact row 24219
text shows only "14" is produced — "11" and "12" are dropped entirely, not
degraded. Confirmed against the module's own self-test comment ("hamda
isn't a recognized list separator") too. Corrected the Backlog wording
rather than leaving a false claim standing (see Backlog, "hamda" item) —
this is exactly the "say so, don't silently revert" case the brief asks
for, though here there was nothing to revert, just a description to fix.
Formalized the true three-article expected output (`gold_id` 140) so this
won't drift back into "described but unverified."

**Batch 5** (`--seed 20260928002 --n 40`, drawn after batch 4 found nothing
new, specifically to get a second independent read before concluding the
day was a dry run): novelty coverage 138/451 after batch 4's merge. Result:
37/40 correct, 3/40 known_gap. Two are more "boʻlim" re-hits (rows 35586,
38614 — corpus-wide count re-measured, still exactly 6, same 6 as
2026-09-17, not growth). **One is a genuinely new finding**: row 37948 (an
Oliy sud Plenumi resolution amending several older resolutions) contains,
three times, "Fuqarolik kodeksining 38, Oila kodeksining 228,
233-moddalari" — the bare number "38" is unambiguously Civil Code Article
38 by the parallel structure with the Family Code citation right after it,
but no unit word (`modda`/`bob`/`paragraf`) ever touches "38" directly (the
interposed different code's own name breaks `RE_CLAUSE`'s digit run before
any unit word is reached), so it falls through to the bare-act fallback and
is silently dropped rather than just losing grain. Measured corpus-wide
(regex for the shape, checked against all three source fields): exactly 5
raw occurrences across 3 distinct rows (26159, 37948 ×3, 53186), all naming
the identical target article — a recurring civil-registry cross-reference
idiom in these Plenum resolutions, not a general list-grammar gap. Not
fixed today: fixing it properly would mean inferring that a bare number's
unit word lives in a *different* code's own clause later in the sentence —
a materially harder and riskier generalization than the comma/va/hamda
separator gaps already on this list, for a pattern that (so far) always
resolves to the same single target number. Formalized as three known_gap
records (`gold_id` 194-196, one per anchor occurrence in the row) and a new
Backlog item instead.

**Net for the day**: `gold_citations.json` grown from 140 to 220 records
across two disjoint batches; score moved from precision 297/299 (99.3%) /
recall 297/299 (99.3%) to **precision 693/700 (99.0%) / recall 693/703
(98.6%)** — the drop is entirely the newly-formalized known_gaps becoming
countable, not a regression (0 drift, confirmed by `score_gold.py`
re-running clean against the exact windows recorded). Did not touch
`citation_extractor.py`, `build_links.py`, or any other pipeline file —
`gold_citations.json` isn't consumed by the build pipeline or either app
(confirmed by grep), so no `corpus.duckdb` rebuild or app-schema check was
needed; ran `pyflakes *.py`/`vulture *.py --min-confidence 60`/
`python -m unittest test_transfer_e2e.py`/`citation_extractor._selftest()`
anyway as a baseline sanity check (all clean/48-48/14-14/0) and smoke-tested
both `app_hierarchy.py`/`app_llc.py` live (HTTP 200, no exceptions in
either log). `verify_transfer.py`: all checks green, same INFO-line numbers
as 2026-09-27 (nothing touched here feeds any of its checks).

Thread stays open (220/3251 candidate windows, 138/451 signatures is still
partial coverage) — next Extractor rotation should keep using
`build_gold_sample_novel.py` with a fresh seed. Today's two-batches-in-one-
day pattern (draw again immediately if the first batch comes back clean,
rather than concluding "no bug today" after one batch) seemed to pay off —
worth repeating if a future Extractor session's first batch is also clean,
though this is anecdotal (n=1) rather than a settled policy.

### 2026-09-27 — Data currency rotation: diagnosed the amending-act-resolution residual's real root cause, fixed it, resolution 74.2% -> 85.1%

Rotation: 09-25 was Extractor, 09-26 was Cleanup, so today is Data currency
(last five sessions 09-23..09-27 before today would have been Cleanup/Data
currency/Extractor/Cleanup — Data currency had only one). Picked the
highest-value open Data currency backlog item rather than inventing a new
angle: 2026-09-24's `date+cc-clause-match` tier took amending-act resolution
from 7.0% to 74.2%, but left 158/612 (25.8%) unresolved with an explicit
note that "the rest are same-date candidates whose body doesn't block-match
for a reason not yet diagnosed" — an open, named question, not a closed
thread.

**Environment**: same as every session since 09-19 — `apt-get install -y
git-lfs && git lfs install && git lfs pull` (parquet came down as a 134-byte
LFS pointer stub, confirmed the real 163,356,047-byte file after pulling;
`verify_transfer.py`'s 2026-09-26 `_check_parquet_pulled()` guard would have
caught this cleanly if I hadn't pulled first, but pulling first is still the
right order) and `pip install duckdb pandas pyarrow streamlit pyflakes
vulture playwright` (playwright wasn't in the standing toolchain list before
today — needed it for live UI verification, see below). No stale-`HEAD`
issue this session (local `main` and `origin/main` agreed from a fresh
clone).

**Diagnosing the residual.** Rather than guess, replicated
`build_links.py`'s exact `by_date`/`cc_blocks`/`cc_clause_candidates` logic
in a standalone read-only script and ran it against all 158 `unresolved`
`article_amendment` rows, classifying each by exactly which step failed (no
`amend_date`, no act at all on that date, ambiguous title match, zero
block-match candidates, ambiguous block-match). Result: **156/158** fell
into "acts exist on the clause's date, but none of them, in any modda-block,
mention the target article" — a single dominant failure mode, not scattered
noise. Read the first failing case by hand against the raw parquet text (not
the derived `corpus.duckdb` tables) to find out why: clause `event_id=24`
targets Article 26¹ (superscript), amending act "OʻRQ-911" dated
2024-02-21. The only plausible same-date candidate, doc -6809366
("Toʻlovga qobiliyatsizlik toʻgʻrisida"gi ... qabul qilinganligi munosabati
bilan ... ayrim qonun hujjatlariga ... kiritish haqida"), genuinely *does*
contain a Civil-Code-amending block reading "...Fuqarolik kodeksiga ...
quyidagi oʻzgartirishlar va qoʻshimcha kiritilsin: 1) 26-modda quyidagi
tahrirda bayon etilsin: ... 2) quyidagi mazmundagi 261-modda bilan
toʻldirilsin: ..." — the exact clause that inserts Article 26¹ — but
`corpus.duckdb`'s own `src_provision` table, queried directly, held only
**2,482 characters** of this act's text, cut off mid-sentence right after
"26-modda quyidagi tahrirda bayon etilsin:" and never reaching the 26¹
insertion two sentences later.

Traced why: queried the raw parquet directly for every row sharing this
act's id (`-6809366-full`) and found **9 separate raw rows**, not one —
lengths 477, 425, 3687, 2482, 1746, 2193, 16061, 756, 554 characters,
clearly LexUZ's own pagination of one long act into several scraped chunks
that all carry the same corpus id. `corpus_row` correctly has all 9 (plus 2
numbered-article rows, matching `act.n_articles = 11` for this doc) — but
`build_links.py`'s `text_by_doc` (used only by the amending-act
block-match, introduced 2026-09-24) was built by joining `corpus_row` to
`src_provision`, and `src_provision` is deliberately scoped narrower: "rows
that themselves produced a link_edge" (its own comment: citing provisions,
so the UI can show the actual citing rule, not just a pointer). Only
whichever of the 9 chunks happened to contain an extractable citation
landed in `src_provision` — for this doc, exactly one, the 2482-char chunk.
The other 8 chunks, including the one with the Article 26¹ insertion, were
never even queried by the amending-act resolver. Confirmed this isn't
niche: only 647 of 24,267 acts have *any* row in `src_provision` at all
(`src_provision` exists to hold citing provisions, not full act bodies) —
`text_by_doc` was silently working with a near-empty or truncated text for
the overwhelming majority of candidate acts.

**The fix**, in `build_links.py`'s `text_by_doc` construction only: read
every raw parquet row belonging to the doc_id directly (`corpus_row` joined
to `read_parquet(...)` by `file_row_number`, `string_agg(... ORDER BY
file_row_number)` to preserve document/page order) instead of routing
through `src_provision`. No change to the matching logic itself — same
same-block requirement, same `\b<article>\s*-\s*modda` regex, same
"Fuqarolik kodeks" title check — just complete input text.

**Measured, before touching the real `corpus.duckdb`**: copied the
committed database to a throwaway file, ran the patched `build_links.py`
against it, and diffed `article_amendment` row-for-row by `event_id`
against the pre-fix table: **0 rows regressed** from resolved back to
`unresolved`, **0 rows changed which act they resolved to** (pure
addition, no re-adjudication), **67 rows newly resolved**. Spot-checked
several by hand against the raw text rather than trusting the diff alone:
for one newly-resolved case (article 925, act OʻRQ-683/doc -5388561),
verified the regex's `\b` word boundary correctly distinguishes a genuine
"925-modda" occurrence from the substring "1925-moddaning" earlier in the
same document (both look identical to a naive substring search but the
regex only fires on the real one — checked with `re.finditer` directly, one
match, at the correct position), and confirmed that match sits inside the
same "55-modda." block that opens with the Civil Code's own bibliographic
citation, not a different law's block. **Result: 454/612 (74.2%) -> 521/612
(85.1%)** amending-act resolution corpus-wide; `by match_method`:
`date+cc-clause-match` 411 -> 478, `unresolved` 158 -> 91,
`date+civil-code-title` unchanged at 43 (that tier doesn't touch
`text_by_doc` at all).

Applied the fix to the real `corpus.duckdb`: reran `build_links.py` (numbers
matched the throwaway-copy test exactly), then `build_okoz.py` (unaffected,
same 386/386 classified) and `build_llc.py` (`llc_implementing_act` 132/132,
`llc_norm` 100/100, both unchanged — expected, since nothing about LLC
foundation mapping or the LLC-specific query logic was touched, only the
General/Special Part amending-act resolver). `repeal_clause` numbers also
unchanged (840/885 resolved, same `by match_method` breakdown as
2026-09-26) — it's a separate, earlier code path in the same file that
never touches `text_by_doc`.

**Verified live, not just in the diff.** Started both Streamlit apps and
used Playwright (newly added to the toolchain this session — wasn't
installed before) to check the actual rendered UI, not just HTTP 200:
`app_hierarchy.py`'s Article 384 (General Part; `unresolved` before today)
now shows "Amending act: *Oʻzbekiston Respublikasining ayrim qonun
hujjatlariga oʻzgartishlar kiritish toʻgʻrisida*" inside its amendment-
history expander, screenshotted directly from the running app. Also checked
`app_llc.py`'s "Follow a norm down" page on CC art. 39 — one of the rows
*still* unresolved after today's fix (a different, deeper gap, see below) —
to confirm the `LEFT JOIN act a ON a.doc_id = am.amending_doc_id` degrades
gracefully when `amending_doc_id` is NULL: no crash, the "Amending act:"
line is simply omitted, exactly as the existing code already handles it.
(Note: the two apps can't run concurrently against the same `corpus.duckdb`
— `app_hierarchy.py` opens read-write first if the file is free, which then
blocks `app_llc.py`'s read-only open with a DuckDB lock conflict; this is
pre-existing, already-commented behavior in `app_hierarchy.py`'s `_connect`,
not something today's change caused — tested each app one at a time to
avoid it.)

**Characterized, but did not chase, the new 91-row residual** — diminishing
returns past this point, each case needs individual forensics rather than
sharing one root cause the way the src_provision bug did. Reran the same
classification script against the new residual: 57/91 have a same-date
candidate act that mentions "Fuqarolik kodeks" *somewhere* in its full raw
text but not inside the same `<N>-modda.` block as the target article.
Read the dominant example by hand: the 2025-02-07 cluster (36 of the 91, all
pointing at act "OʻRQ-1025") resolves its date to a real candidate, doc
-7367697 ("Korporativ munosabatlarning huquqiy asoslari yanada
takomillashtirilishi munosabati bilan ... ayrim qonun hujjatlariga ...
kiritish toʻgʻrisida" — plausible by title, corporate-relations reform), and
that doc does contain "Fuqarolik kodeks" — but only twice, both as a
descriptive aside ("...ularning huquqlarini amalga oshirish toʻgʻrisida
Oʻzbekiston Respublikasining Fuqarolik kodeksida belgilangan tartibda
korporativ shartnoma tuzish") sitting inside an "8-modda." block that is
actually amending the *Joint-Stock-Companies law*, not the Civil Code
itself. Confirmed by listing every block in the document that mentions
"Fuqarolik kodeks" (exactly 2, both this same descriptive block) — neither
is a genuine CC-amending block, and neither contains "39-modda" nearby. So
either this act genuinely doesn't touch CC article 39 despite the
`amendment_note`'s date pointing at it (meaning doc -7367697 isn't really
the target "OʻRQ-1025", and the true one is missing from the corpus or the
`amend_date` itself is a transcription slip in the source), or the
provision was later moved/renumbered in a way this document's text doesn't
reflect. Either way it's a source-data question, not a `build_links.py`
matching-logic gap — logged as a real, honestly-measured finding rather
than force-fitting a fix. The other 34/91 have no same-date candidate
mentioning the Civil Code at all, same "genuine corpus-coverage gap" shape
as the already-closed 2026-09-09 repeal-resolution residual.

**Full verification.** `python verify_transfer.py`: all checks green, same
INFO-line numbers as 2026-09-26 (248 superseded acts, 494 stale edges, 372/386
General Part articles cited — none of AC5/AC7's currency checks changed,
since they don't inspect `article_amendment.match_method` directly).
`pyflakes *.py` and `vulture *.py --min-confidence 60`: both clean.
`python -m unittest test_transfer_e2e.py`: 14/14. `score_gold.py`: unchanged
at precision 297/299, recall 297/299 (this fix never touches
`citation_extractor.py`). Committing the `corpus.duckdb` diff this time
(unlike several recent sessions) since the actual row-level content changed
— 67 real new `amending_doc_id` values, not just non-deterministic
serialization churn from an unrelated table.

**Decision and thread status**: closing today's thread. The 91-row residual
is now honestly characterized into two clusters with different likely next
steps (see Backlog) rather than left as an opaque count — consistent with
how this project has closed previous "still some % unresolved, but it's a
genuine data-coverage gap" threads (e.g. repeal resolution, 2026-09-09).
Next Data-currency rotation could pick up the "CC mentioned elsewhere, not
in the article's own block" cluster specifically (the more promising half —
the act is very likely already correctly identified, it just needs a
smarter block-scoping heuristic), but that's a new, narrower investigation,
not a continuation of today's src_provision fix.

### 2026-09-26 — Cleanup rotation: audited every f-string SQL call for the hard constraint's own rule, fixed 3 real violations, closed a 15-session-old environment paper cut

Rotation: 09-24 was Data currency, 09-25 was Extractor, so today is Cleanup.
The Cleanup backlog section had no open items left (everything in it is
struck through as resolved) — invented a new angle instead of forcing a
backlog item: actually check the codebase against the hard constraint this
project runs under ("no f-string SQL with any value that isn't a hardcoded
constant"), which had only ever been enforced reactively (deleting
`hierarchy_engine.py` on 2026-09-07) rather than swept for elsewhere.

**Environment**, same as most sessions since 09-19/09-04: `git-lfs` wasn't
preinstalled (`articles/train-00000-of-00001.parquet` came down as a
134-byte pointer stub, `git lfs pull` fixed it — confirmed the pulled file
is exactly 163,356,047 bytes) and local `HEAD` was detached 2 commits ahead
of local `main` (2026-09-24's and 2026-09-25's commits) — `git fetch origin
main` confirmed origin already had both, so fast-forwarded local `main` and
pushed (no-op, "Everything up-to-date": the previous two sessions had
already pushed correctly; only the local ref was stale).

**The audit.** Grepped every `.execute(f"..."` / `.cursor().execute(f"..."`
call across the whole `*.py` set: 29 call sites in 8 files
(`build_corpus_db.py`, `build_gold_sample.py`, `build_gold_sample_novel.py`,
`build_links.py`, `build_llc.py`, `measure_extractor_recall.py`,
`score_gold.py`, `verify_transfer.py`). Read every one and classified the
interpolated value:
- **allowed** (hardcoded constant): the fixed `raw = f"read_parquet('{PARQUET}', ...)"`
  expression built from the `PARQUET` path constant (appears in most files);
  doc-id constants like `CC_GENERAL_PART`, `CC_DOCS`, `LLC_LAW_CURRENT`/
  `LLC_LAW_PRIOR` (appear in `build_corpus_db.py`, `build_links.py`,
  `build_llc.py`, `verify_transfer.py`).
- **violation**: a value computed at runtime from a query result, joined
  into the SQL text with `",".join(str(i) for i in ...)` instead of bound as
  a parameter. Found exactly 3, all the same shape:
  - `build_gold_sample_novel.py:169-172` — `row_ids` (gold-set record row
    numbers) into `file_row_number IN (...)`.
  - `score_gold.py:90-93` — the identical pattern, same `row_ids` source
    (both files recompute a gold window's signature from its stored anchor
    position the same way — `build_gold_sample_novel.py`'s own docstring at
    `gold_signatures()` says as much).
  - `build_llc.py:253-257` — `hits` dict keys (`doc_id`s found by scanning
    for acts that name the LLC Law) into `a.doc_id IN (...)`.

  None are exploitable today: every interpolated value is a Python `int`
  produced by DuckDB's own typed integer columns (`file_row_number`,
  `doc_id`), and `str()` on an `int` can't contain SQL syntax. But each is a
  live violation of the project's own written rule, and each is exactly the
  shape that silently becomes exploitable the day someone interpolates a
  string instead of an int into the same pattern — worth closing on
  principle, not just on today's measured risk. Traced `build_llc.py`'s
  violation back to its likely origin: it's a near-verbatim copy of
  `build_gold_sample.py`'s own `alias_docs`/`rows` two-query pattern, which
  only ever interpolates the hardcoded `raw` constant — the violation was
  introduced when that pattern got reused with a *different*, dynamic
  collection in the `IN (...)` clause. Also explicitly checked the actual
  user-facing surface, `app_hierarchy.py` and `app_llc.py`: **zero**
  f-string SQL in either — every `con.execute()` there already goes through
  DuckDB's `?` parameter list (see `run_query`/`run_query_df` helpers in
  each). So the real risk was already correctly quarantined to batch/build
  scripts, never reaching anything a user's input could influence — lower
  severity than "SQL injection" sounds, but still worth fixing so the
  pattern doesn't get copy-pasted into a future script the way it already
  was once.

**The fix.** DuckDB accepts a Python list bound to a single `?` via
`WHERE col IN (SELECT * FROM UNNEST(?))` — confirmed working in isolation
first (`SELECT * FROM t WHERE id IN (SELECT * FROM UNNEST(?))` with
`[[1, 3]]` bound, on a 3-row scratch table) before touching any real code.
Applied to all 3 sites, replacing the f-string join with a bound parameter
list; no other line in any of the 3 functions needed to change.

**Verification, not just "looks equivalent."** `score_gold.py` re-run:
precision 297/299 (99.3%), recall 297/299 (99.3%) — byte-identical to
2026-09-25's number, same 2 mismatches (`gold_id` 52 and 123, the documented
`known_gap` records). `build_gold_sample_novel.py --n 3 --seed 1`: ran
clean; its own coverage measurement now reads 98/451 signatures covered
(1419/3251 windows still novel), up from 58/451 on 2026-09-22 — consistent
with 2026-09-25's 40-record batch having landed, not a symptom of the fix.
`build_llc.py` got the most rigorous check since its fix touches an
`INSERT` into `llc_implementing_act`, not just a read: ran the *original*
(pre-fix, loaded from `git show HEAD:build_llc.py`) and the *fixed* version
each against its own fresh throwaway copy of `corpus.duckdb`
(`DB_PATH`/`PARQUET` monkeypatched, real code otherwise unchanged), then
diffed `llc_implementing_act` row-for-row between the two — **132/132 rows
byte-identical**. Did not touch the committed `corpus.duckdb` itself: since
the fix is proven byte-identical in its output, re-running `build_llc.py`
against the real database would only add the non-deterministic
serialization byte-churn the 2026-09-23 and 2026-09-25 entries already
flagged as a real cost, for zero actual change to any row. `pyflakes *.py`
and `vulture *.py --min-confidence 60` both clean (no new dead code).
`python -m unittest test_transfer_e2e.py`: 14/14 pass. Both Streamlit apps
smoke-tested live via `streamlit run --server.headless`: HTTP 200 from
both, no exceptions in either log — no schema changed, so this is the load
check the project's own rule calls for, not a full query-level check.

**Also fixed, same file already open for the audit above**: added
`_check_parquet_pulled()` to the very top of `verify_transfer.py`'s
`main()`. The "raw parquet is an unpulled LFS pointer stub" gotcha has now
cost a paragraph in roughly 15 prior sessions' log entries (09-04 onward,
by grep) with a bare `_duckdb.InvalidInputException: No magic bytes found`
as the only symptom, surfacing deep inside AC3 rather than up front. The
new check runs before any DuckDB connection opens: if the parquet is under
10KB and its content starts with `version https://git-lfs`, it raises a
`SystemExit` naming the exact fix (`git lfs install && git lfs pull`)
instead. Verified both branches by hand — swapped the real 163MB file for a
synthetic 134-byte pointer stub, confirmed the new clear message fires;
restored the real file, confirmed the full suite is still green. This
doesn't remove the need to `git lfs pull` each session (nothing can, short
of the container image preinstalling `git-lfs`) — it just turns next
session's first failure into an immediate, actionable one-liner instead of
a detour into a cryptic DuckDB error.

`verify_transfer.py`: all AC1-AC7 checks green (ran twice — once before any
edit as a baseline, once after everything above). Files changed:
`build_gold_sample_novel.py`, `score_gold.py`, `build_llc.py`,
`verify_transfer.py`. `corpus.duckdb` untouched — no functional change to
land, confirmed above.

### 2026-09-25 — Extractor rotation: signature-stratified gold sampling instead of a fourth uniform batch, one real bug found and fixed

Rotation note from 09-24 flagged Extractor as due (hadn't run since 09-22;
Cleanup and Data currency had each run twice in the last five sessions).

**Environment note** (same cold-start pattern as every session since
09-19): fresh clone needed `duckdb`, `pytz`, `streamlit`, `pyflakes`,
`vulture` installed and `git-lfs` installed + `git lfs install --local &&
git lfs pull` for the raw parquet (came down as a 134-byte pointer file,
`_duckdb.InvalidInputException: No magic bytes found` on the first
`read_parquet` attempt). Verified the pulled file before use: 163,356,047
bytes, sha256 `e7a30c5348e0eecfb81470b44c691b23226187800e0be8697019c307336d0d00`
matching the recorded oid exactly — matches every prior session's same
check.

**Why not another uniform batch**: the backlog's own next step for the
gold-set thread was "draw another disjoint 50-window batch with a new
seed." But looking at the sampling history first: 2026-09-20 and
2026-09-22's batches were the *first two* (of 9 before them) not to find a
new bug on the first pass. That's not proof uniform sampling is exhausted,
but it's a real signal worth checking rather than just re-rolling the same
dice a fourth time and hoping.

**Built `build_gold_sample_novel.py`**: computes a cheap structural
*signature* per anchor window from the raw text alone (separator type —
comma/"va"/"hamda"/ascii-hyphen/en-dash/doubled-dash — which unit words
appear, qism-digit vs. qism-ordinal, parens, roman numerals, quote marks,
4-digit runs, anchor kind, source field), deliberately not re-running any
of `citation_extractor.py`'s own logic (that would just re-encode "what the
extractor already handles" and miss exactly the shapes it doesn't). Then:
recompute the signature of every one of the 100 already-annotated gold
windows (from their own stored anchor position, same recompute pattern
`score_gold.py` uses, so novelty is measured against what was actually
read, not an approximation) and diff against the full candidate-window
population.

**Measurement (the methodology finding, independent of any bug)**: 3251
real candidate windows corpus-wide carry 451 distinct signatures; the
100-record gold set has exercised only 58 of them. 1456 windows (44.8% of
all candidates) sit in a signature the gold set has *never* annotated a
single example of. This directly explains the two dry batches: uniform
random sampling keeps re-landing on the same common shapes (plain single-
article, hyphen-separated, `fuqarolik_kodeksi`-anchored citations dominate
the corpus by sheer count), so each additional uniform batch's marginal
coverage of the *rare* shapes shrinks fast.

**Drew 40 windows** from the never-covered signatures, capping at 3
examples per signature (so one common "novel" combination doesn't crowd
out the batch) and prioritizing the rarest signatures first, `--seed
20260925`. Read every one by hand against the raw Uzbek text.

**Found and fixed one real, live precision bug**: row 6071 (a Supreme
Court plenum resolution on intellectual-property disputes), inside an
`fk_alias`-anchored window: "...sudlar bunday muddatlarni FKning 60-bobi
(1065-modda), "Mualliflik huquqi va turdosh huquqlar toʻgʻrisida"gi qonun
(35-modda) asosida qoʻllashlari lozim" — "FK" (the Civil Code alias) names
chapter 60/article 1065 correctly, but the *next* clause is a parenthetical
shorthand for the Copyright Law's own article 35 ("...that law (article
35)..."), not a continuation of the Civil Code citation. Nothing in
`RE_STOP` caught bare lowercase "qonun" immediately followed by an open
paren, so `extract()` kept scanning past it and attributed "35" to the
Code too. This was already live in `corpus.duckdb`: `link_edge` edge_id 187
carried `dst_article_number='35', dst_doc_id=-111189` (DOC_GENERAL) sourced
from this exact clause — confirmed by direct lookup before touching
anything, not assumed.

Checked the risk before fixing: the general "stop on any bare lowercase
qonun" fix was already measured and explicitly rejected 2026-09-05 (49484
generic occurrences of the word vs. only 3 that happen to precede a
modda/bob clause — stopping unconditionally would silently truncate real
Code citations far more often than it would fix anything). So the fix here
is deliberately narrower: `qonun\s*\(` — bare "qonun" immediately followed
by "(", nothing else. Measured corpus-wide before shipping: exactly 6 bare
"qonun(" occurrences exist in the whole corpus (any case), all 6 read by
hand — every one is a parenthetical aside naming some OTHER act or
provision, never a continuation of a real Civil Code citation — and only 1
of the 6 (row 6071) sits inside any Civil-Code/FK anchor's window in the
first place (the other 5 are nowhere near a `Fuqarolik kodeksi`/FK mention
at all, so they're inert as far as `extract()` is concerned regardless).
Zero collateral risk measured, one real bug fixed.

Added one self-test case (`citation_extractor.py`, `stop_cases`) reproducing
this exact shape. 48/48 self-tests pass (was 48 total after +1 case, was 47
before). `measure_extractor_recall.py`: still 0 real misses on article and
chapter recall (unchanged), qism/band attachment residual unchanged at
7/630. `score_gold.py` on the pre-existing 100 records: unchanged at
217/218 — none of those windows touch this pattern, confirming the fix is
additive, not a regression.

**Rebuilt only `build_links.py`** against the existing `corpus.duckdb` (no
`build_corpus_db.py` rerun — the fix is purely in `citation_extractor.py`'s
stop-word logic, not the base tables): `link_edge` 9531 -> 9530 (exactly the
one bad edge removed; re-checked `WHERE src_row_id=6071 AND
source_field='article_text' AND dst_article_number='35'` returns zero rows
after, the correct `dst_article_number='1065'` edge is untouched). Re-ran
`build_llc.py` against a throwaway copy of the post-fix `corpus.duckdb`
(not the file being committed) purely to confirm zero LLC-slice impact
without adding `build_llc.py`'s own non-deterministic `CREATE OR REPLACE
TABLE` byte-churn to the diff for no reason (same discipline as the
2026-09-23 Cleanup entry): `llc_implementing_act` 132/132, `llc_norm`
100/100, `llc_stage` 8/8, all unchanged — row 6071 isn't in the LLC slice's
scope. `verify_transfer.py`: all checks green, same structural INFO lines
as 2026-09-24 (`link_edge` count line reads 9530 in place of 9531, nothing
else moved). `pyflakes *.py` and `vulture *.py --min-confidence 60`: both
clean, including the new `build_gold_sample_novel.py` (one initial vulture
hit — an unused `STOP_NING` regex left over from an earlier draft of the
signature function — fixed by deleting it, not by wiring it in for its own
sake). `python -m unittest` on `test_transfer_e2e.py`: 14/14 pass. Both
Streamlit apps smoke-tested live (`streamlit run` + `curl`, HTTP 200, no
exceptions in either log) — no schema changed by this fix, so no query-level
check was needed per the project's own rule, just a load check.

**Found, measured, and deliberately left unfixed** (two more windows from
the same batch, same single-occurrence and low-priority-grain precedents
this project has applied repeatedly before):

1. Row 15441: "Fuqarolik kodeksi IV bobining 2 paragrafi" — a Roman-numeral
   chapter (IV) followed by a paragraf reference. `extract()`'s Roman-chapter
   fallback branch (used only when the main Arabic-digit `RE_CLAUSE` loop
   found nothing) never runs the paragraf/section lookahead the Arabic
   `bob` branch has, so this always produces a bare chapter-4 citation,
   losing the section-2 grain — `dst_kind` would read `section` not
   `chapter`, a real `link_edge` column, the same class of gap as
   2026-09-22's "paragrafi"/"paragrifi" miss (gold_id 52). Measured
   corpus-wide: exactly 1 occurrence in the whole corpus (checked every
   Roman-numeral-chapter match's tail for an immediately-following paragraf
   reference). Recorded as a `known_gap` gold record (gold_id 123) with its
   true expected output (`target_kind=section, struct_number=4,
   section_number=2`) rather than silently scored as correct — same
   "record the honest true value" convention gold_id 52 established. Not
   fixed today, same single-occurrence-scope precedent as several existing
   Backlog items (e.g. the 2026-09-15 chapter+paragraph space-separator gap,
   also 1 occurrence, also left unfixed).
2. Row 21303 (two separate anchor occurrences in the same row): the
   already-known qism/band grain-collapse limitation (`RE_QISM`'s tail
   search finds only the ONE ordinal/digit immediately before "qism"/"band",
   silently dropping any others in a list or range — documented since
   2026-09-15 for the dash-RANGE form, "ikkinchi — toʻrtinchi qismlarida")
   now also measured in comma-separated LIST form: "11-moddasining 1,
   4-bandlari" (band list, digits) and "377-moddasining ikkinchi,
   toʻrtinchi, oltinchi qismlari" (qism list, ordinal words) both collapse
   to just their last member today. Measured corpus-wide (regex-only, not
   requiring a real `RE_QISM` match — an upper bound on how often the SHAPE
   appears, not a claim every one is currently mishandled): 14 digit
   comma-list and 68 ordinal comma-list occurrences inside anchor windows.
   Still not load-bearing (qism isn't consumed by any downstream table/view
   — see Backlog "Qism-level grain"), so left alone per the existing,
   repeatedly-reaffirmed decision; the two counts are folded into that
   Backlog item as newly-measured sub-forms rather than opening a new one.

**Merged the batch into `gold_citations.json`** as batch 3 (gold_id
100-139, 40 records, `_meta.batches` records `method:
"signature-stratified"` so future readers can tell this batch apart from
the three uniform-random ones). 38/40 `verdict: correct` (including
gold_id 108, the row-6071 bug — recorded with its now-correct expected
output, not its old wrong one), 2/40 `verdict: known_gap` (gold_id 123 —
the Roman-chapter+paragraf miss above; gold_id 131 — the qism/band
comma-list collapse, folded in as a documentation note since qism isn't
scored). **New combined score across all 140 records: precision 297/299
(99.3%), recall 297/299 (99.3%)** — the two mismatches are exactly the two
known_gap records (2026-09-22's "paragrif" + today's Roman-chapter), both
honest misses by design, not silent inflation.

**Decision**: keep this thread open rather than closing it. One batch under
a new method is a promising first result (1 real bug + 1 known_gap in 40,
versus the two most recent uniform batches' 0-and-1), not proof the method
is generally better — the next Extractor rotation should run
`build_gold_sample_novel.py` again (it recomputes novelty coverage fresh
against whatever the gold set has grown to, so it never goes stale the way
a fixed sample would) and see whether the yield holds up over a second
round.

### 2026-09-24 — Data currency rotation: built a new amending-act resolution tier, 33/594 (5.6%) -> 454/612 (74.2%)

Rotation note from 09-23 flagged Extractor or Data currency as due (Cleanup
had gone twice in five days: 09-19, 09-23). Picked Data currency.

**Environment note** (same cold-start pattern as every session since
09-19): fresh clone needed `duckdb`, `numpy`, `pandas`, `streamlit`,
`playwright`, `pyflakes`, `vulture` reinstalled and `git-lfs` reinstalled +
`git lfs pull` for the raw parquet (came down as a 134-byte pointer).
Verified the pulled file before use: 163,356,047 bytes, sha256
`e7a30c53...` matching the recorded oid, 54,173 rows — matches every prior
session's same check.

**Starting angle, and why it didn't pan out**: today's date is 2026-09-24,
so before touching the backlog I checked how current the corpus actually
is against that calendar date — a literal reading of "Data currency" the
backlog hasn't tried before. `act.doc_date` runs through 2026-06-08 (June
tapering to 12 acts vs. a ~100/month baseline, consistent with a mid-month
export cutoff), so the corpus is genuinely only ~3.5 months stale, not the
big gap I expected. Checked whether any 2026 act text actually *amends*
the Civil Code (searched `src_provision.article_text` for "fuqarolik
kodeks" in every act dated after 2025-07-01, 22 hits): all of them are
mere citations ("in accordance with the Civil Code...", "the Civil Code
approved by law No. 256-I...") — zero are real amendments the pipeline is
missing. `-8151376` (2026-04-21, "Masʼuliyati cheklangan jamiyatlar
toʻgʻrisida") turned up in that search too; double-checked it's not a new
LLC Law the pipeline has failed to notice — it's already `LLC_LAW_CURRENT`
in `app_llc.py`, correctly set since that constant was first written. No
bug here; ruled out and moved on rather than forcing a result.

**The real finding**: while reading those 22 hits, one — `-7773606`
(2025-10-17, an omnibus consumer-protection/standards act) — visibly
amends Civil Code Article 1018 in its own body text ("1018-moddasi
quyidagi mazmundagi toʻrtinchi qism bilan toʻldirilsin"), and
`article_amendment` already has a matching row for that exact date and
article, but with `amending_doc_id NULL` — the "amending-act resolution
caps at 5.6% because `act.doc_number` is empty corpus-wide" gap flagged in
Active threads since 2026-09-11 and re-confirmed unfixable every time it
came up since. **Confirmed `doc_number` really is empty everywhere in the
raw parquet itself** (0/54,173 rows have a non-empty value) — the earlier
sessions were right that this isn't a pipeline bug, it's LexUZ's own
export. But `-7773606`'s own text names the *article* it changes, and
`amendment_note`'s existing `amend_act_number` field (`OʻRQ-1088`, parsed
straight from the CC's own annotation) gave a number to independently
confirm the match — meaning the CC article number itself, not the missing
doc_number, could be the join key.

Measured before building anything: for all 569 currently-unresolved
`article_amendment` rows with a known `amend_date`, does the target CC
article number appear as "`<N>-modda`" anywhere in *some* same-date
candidate act's own body text? **First pass: dangerous false-positive
risk, caught before shipping.** A naive whole-body search "resolved" 435
uniquely with zero ambiguous — but manual inspection showed most of that
was a coincidence: omnibus acts number their *own* internal articles
sequentially ("1-modda. ... 2-modda. ..."), so a target CC article number
under ~30 trivially matches the candidate's own numbering regardless of
what it's actually about (`-5388561`, one 31-article 2021 omnibus act,
absorbed 271 of the 435 "matches" for target articles 1–15 this way).
**Fix: split each candidate's body into blocks on its own top-level
`<N>-modda.` markers, and only count a match when the Civil Code mention
and the target article number fall in the *same* block** — exploiting the
fact that these omnibus acts really are structured "one top-level article
per law being amended, each opening with that law's full bibliographic
citation." Re-measured with block-scoping: 413 unique, still zero
ambiguous. Spot-checked ~10 cases by hand across different candidate acts
and dates (not just the big 2021 one) before trusting it — every one held
up, including `-5388561`'s own block-6 (marker "55-modda"), confirmed by
inspection to be a genuine 248-article terminology-substitution clause
("qonun hujjatlari" → "qonunchiligi") from the real `OʻRQ-683`, not a
coincidence; and a `sha256`-independent case, `-1518988` (2009, an
anti-money-laundering omnibus act), correctly resolved articles
229/769/770/778/785 — all financial-obligations provisions, thematically
consistent with the act's own subject.

**Shipped** in `build_links.py` as a new fallback tier,
`date+cc-clause-match`, tried only when the existing `date+civil-code-title`
tier doesn't resolve uniquely (title-tier stays first and unchanged — 43
resolve there, same as before this session). Ran against the existing
`corpus.duckdb` (not a from-scratch rebuild): `link_edge` (9531),
`repeal_clause` (885), `article_amendment` (612), `v_act_partial_repeal`
(137) row counts all byte-identical to before — purely additive, only
`amending_doc_id`/`match_method` values filled in on existing rows.
**Result: amending-act resolution 43/612 (7.0%, this session's baseline —
today's clause count differs slightly from the 33/594 figure logged
2026-09-11 as the table grew since) -> 454/612 (74.2%)**, 411 newly
resolved, zero ambiguous across all 569 candidates tried. `pyflakes *.py`
and `vulture *.py --min-confidence 60` both clean; `verify_transfer.py`
green with the same INFO-line numbers as 2026-09-23 (this doesn't touch
`link_edge`, repeal resolution, or any AC1-AC7 check).

**Wired into both apps**: `amend_act_number` was already shown next to
each amendment event ("Law OʻRQ-1088") but as a bare number with no name
attached three-quarters of the time it now resolves — added a `LEFT JOIN
act` to the existing `article_amendment` query in `app_hierarchy.py`'s
`page_article()` and `app_llc.py`'s `page_norm()` (same shared query
shape both already use) and a new caption line, "Amending act: *{title}*",
shown only when `amending_doc_id` resolved. Grepped both apps first for
`doc_title` display conventions — found the existing pattern is verbatim,
truncated-to-110-chars, no case transformation (`app_hierarchy.py`'s
realization-pyramid list already does this) — and matched it, after first
trying `.title()` and catching that Python's title-case mangles Uzbek
apostrophe letters (`OʻZbekiston`, `QoʻShimchalar` — the modifier letter ʻ
reads as a word boundary), which would have shipped visibly broken text.
Verified live in both apps via Playwright: `app_hierarchy.py` Article 1's
amendment history now shows "Amending act: *Oʻzbekiston Respublikasining
ayrim qonun hujjatlariga oʻzgartishlar kiritish toʻgʻrisida*" under the
`OʻRQ-683` entry; `app_llc.py`'s "Follow a norm down" page, stage 2
("Jamiyatni taʼsis etish"), CC art. 44, shows the same act name under its
own `OʻRQ-683` entry. `build_llc.py` doesn't read `article_amendment` at
all (grepped to confirm) so it needed no re-run.

**Decision and residual**: not chasing this further today — 158/612
(25.8%) stay unresolved, split between genuine chapter/paragraph-level
clauses with no article number to probe (can't apply this tier at all)
and clauses where no same-date candidate's body contains a matching block
(most likely candidates whose CC-amending block is itself malformed by
some regex edge case in `re_own_modda_marker`, or dates where the
omnibus act is a `code` type rather than `law` and structured
differently — not investigated). Worth a future look if this thread is
picked up again, but 74.2% from 5.6% in one session is a large, real,
already-measured win; diminishing-returns territory for today.

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
