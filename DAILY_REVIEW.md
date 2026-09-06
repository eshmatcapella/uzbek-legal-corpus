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
  was one specific, measured misattribution pattern. It does not mean
  precision is now fully verified — no gold set exists (see Backlog), and
  other misattribution patterns (wrong doc_id resolution, wrong qism
  attachment beyond what's already checked, other stop-word gaps not yet
  hypothesized) haven't been searched for. Next session: either invent
  another falsifiable precision hypothesis the way "Qonun" was found (by
  sampling extractor output and reading the raw text), or pivot to Data
  currency / Cleanup per the rotation.

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
  set exists yet — `citation_extractor.py`'s 28 self-tests (see Log) check
  surface-form parsing, not corpus-wide recall/precision. Recall is measured
  clean across all anchor kinds; the "Qonun" precision bug is fixed and
  measured (see Log 2026-09-05). Still no gold set and no systematic search
  for OTHER misattribution patterns beyond the two found so far by sampling
  — revisit whether hand-annotation is now the highest-value next step or
  whether more hypothesis-driven sampling keeps finding gaps faster.
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

### Data currency
- ~~**175/885 repeal items still unresolved.**~~ **Fixed 2026-09-06**: tiered
  `date+substring`/`date+fuzzy` fallback in `build_links.py` resolved 130 of
  them (now 840/885, 94.9%), each tagged with a confidence-scored
  `match_method` exactly as this item proposed. See Active threads and Log
  for the remaining 45 and next steps.
- **Amendment chains, not just repeals.** An act can *amend* another without
  repealing it (redlines specific articles). No detection exists for this at
  all yet — only whole-act repeal. Worth inventing a detector for "kiritilsin"
  / "oʻzgartirish kiritilsin" style amendment clauses, at least at the
  citing-act level, so `v_act_currency` can distinguish "superseded" from
  "amended but still partly in force."
- **Propagate currency into the LLC dossier's implementing-acts list** (and
  eventually the general explorer) as a first-class filter rather than a
  toggle buried in an expander — currency should probably gate what counts as
  "implements" by default.

### Cleanup
- **Retire superseded prototypes**, once confirmed dead:
  `hierarchy_engine.py` (f-string SQL, empty `okoz_to_fk_map`, superseded by
  `build_okoz.py`+`app_hierarchy.py`), `app_deep.py` (superseded by
  `app_hierarchy.py`), `app.py` (earliest Streamlit prototype, superseded).
  Confirm nothing imports them before deleting.
- **`test_transfer_e2e.py`** (956 lines, unittest-based, covers "AC1-AC3")
  predates `verify_transfer.py`'s AC1-AC7 and may now be fully redundant —
  or may cover cases verify_transfer.py dropped. Diff their actual coverage
  before deciding: merge anything unique into verify_transfer.py, then retire
  the rest rather than keeping two acceptance suites that can drift apart.
- **One-off exploration scripts** (`analyze_civil_code.py`, `analyze_fk.py`,
  `analyze_fk_deep.py`, `find_civil_code.py`) were scratch queries from the
  original orchestrator run, not part of the maintained pipeline. Either
  fold anything still-useful into a proper diagnostic script or delete.
- **`hierarchy_engine.py`'s f-string SQL** is a live SQL-injection pattern if
  anything ever calls it with user input — even if the file is slated for
  deletion, flag/fix it first in case deletion gets deprioritized.

---

## Log

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
