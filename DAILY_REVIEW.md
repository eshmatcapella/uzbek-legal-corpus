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

- **Precision, not recall, is now the open question.** 2026-09-04 closed out
  the recall thread: article and chapter/section recall is 0 real misses
  across ALL anchor kinds (Fuqarolik kodeksi, FK-alias, self-reference —
  2340 windows, up from the 1559 the FK-alias/self-reference forms weren't
  even being scanned for before), and the qism/band attachment gap found and
  fixed today closes the last open recall question from 2026-09-03's Active
  Threads entry. So: recall is empirically excellent everywhere it's been
  measured. What's NOT measured is precision — does a correctly-found
  citation resolve to the *right* target? Today's "Qonun" investigation
  (see Log) found a real instance: 25 confirmed cases where a citation to
  another named Law ("Qonun N-moddasi") gets misattributed as a Civil Code
  citation, because `RE_STOP` only recognizes suffixed forms of "qonun"
  (qonuni/qonuniga/qonunining) and not the bare nominative "Qonun" that
  precedes a modda clause about as often as the suffixed forms do.
  **Working hypothesis:** this is one instance of a general pattern — any
  Uzbek noun that names another act (qonun, qaror, farmon, nizom, ...) has
  the same bare-nominative gap, since RE_STOP's list is entirely suffixed
  forms. **Not yet measured:** how many of those 25 "Qonun" edges actually
  made it into `link_edge` (some may have been filtered by other checks;
  need to cross-reference by src_row_id + dst_article_number), whether the
  same bare-noun gap exists for qaror/farmon/nizom at comparable scale, and
  what a safe fix looks like — a blanket `qonun\b` addition to RE_STOP is
  almost certainly wrong (it would also match the extremely common generic
  phrase "qonun hujjatlarida", stopping scans that have nothing to do with
  a named Act). **Next step:** measure how often bare "qonun"/"qaror"/
  "farmon"/"nizom" precede a modda/bob clause WITHOUT being part of a
  generic phrase (a capitalized-word heuristic, since named Acts are always
  capitalized in these citations while generic uses aren't, looks promising
  based on the samples — "Qonun 19-moddasining" vs "qonun hujjatlarida"),
  then propose a scoped RE_STOP addition and verify it doesn't regress the
  now-clean recall numbers before touching citation_extractor.py again.

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
  window) instead of re-slicing an already-cut window.

---

## Backlog

### Extractor recall/precision
- **Build the gold set.** ~50 articles, hand-verified ground truth for
  citation extraction (which acts realize them, at what confidence). No gold
  set exists yet — `citation_extractor.py`'s 22 self-tests (now 26, see Log)
  check surface-form parsing, not corpus-wide recall/precision. Recall is now
  measured clean across all anchor kinds (see Active threads); precision is
  the open question, with one confirmed instance already found (the "Qonun"
  bare-nominative misattribution — see Active threads and Log). Once that
  thread's scope is clearer, revisit whether a hand-built gold set is still
  the highest-value next step or whether the same measure-a-hypothesis
  approach keeps finding real, higher-value gaps faster.
- **Bare-nominative act-name gap in RE_STOP, beyond "Qonun".** See Active
  threads — qaror/farmon/nizom likely have the same gap (RE_STOP only lists
  suffixed forms: qarorining, farmonining, etc., never the bare noun), not
  yet measured.
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
- **175/885 repeal items still unresolved** (`repeal_clause` table, see
  `build_links.py`'s repeal-detection block). Sampled failures are acts
  where the quoted title in the repeal clause doesn't exact-match
  `act.doc_title` after normalisation — truncated titles, embedded quote
  marks, or paraphrased titles. Next step: fuzzy match (edit distance or
  token-set match) on (date, title) pairs that fail exact match, with a
  confidence-scored `match_method` so weak matches stay visibly weak rather
  than silently wrong.
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
