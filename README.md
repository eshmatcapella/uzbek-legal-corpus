---
license: apache-2.0
language:
  - uz
task_categories:
  - text-retrieval
  - text-generation
  - fill-mask
tags:
  - legal
  - law
  - uzbekistan
  - lex.uz
  - legislation
  - latin
pretty_name: "Uzbek Legal Corpus (full, uz-Latin)"
size_categories:
  - 10K<n<100K
---

<!--
Do NOT hand-write a `configs:` block here. `datasets.DatasetDict.push_to_hub`
emits one config per `config_name` (articles / documents) and auto-generates the
correct `configs:` front-matter at publish time. Adding one by hand will drift
from what the build script actually pushes.
-->

# Uzbek Legal Corpus (full, uz-Latin)

**This is a research corpus of published Uzbek legislation — a *pinned consolidated snapshot*, not a live legal database. It is NOT legal advice and NOT an authoritative legal source. The authoritative source is [lex.uz](https://lex.uz). Always verify the current, in-force text there before relying on any provision.**

A cleaned, article-structured corpus of **Uzbek (Latin-script) national legislation** of every type — laws, codes, the Constitution, presidential decrees and orders, cabinet resolutions, and ministerial orders — sourced from [Lex.uz](https://lex.uz), the National Database of Legislation of Uzbekistan (maintained by the "Adolat" National Legal Information Center under the Ministry of Justice). It covers **24,267 acts / 54,173 article rows** spanning **1991–2026**, all in native Uzbek Latin script.

This is the **full single-language** companion to [`sukhrobnurali/uzbek-legal-corpus-v1`](https://huggingface.co/datasets/sukhrobnurali/uzbek-legal-corpus-v1) — a small, curated, trilingual showcase of just the 20 codes + the Constitution. Where v1 is depth on 21 foundational acts in three scripts, **this dataset is breadth**: the whole uz-Latin act set, one script, ~1,200× more distinct acts.

---

## Motivation

Uzbek is a low-resource language for NLP, and Uzbek *legal* text is harder still: it is deeply hierarchical (document → part → chapter → article), and the source HTML mixes the legal text with editorial chrome, amendment notes, and classifier metadata. Most downstream uses — retrieval, RAG, fine-tuning, fill-mask pretraining — want the *article* as the unit, with its document context attached and the noise removed. That structuring is exactly what is missing from the freely available data.

This corpus was built as the data layer behind **AI Huquqshunos**, a legal-assistant project for Uzbek users, and then open-sourced as a dataset in its own right.

### Where this sits relative to what already exists

To be clear and honest: this is **not** the first or only Uzbek legal dataset on the Hub, and it is **not** the first to scrape Lex.uz. Several already exist, for example:

| Dataset | Approx. size | Notes |
|---|---|---|
| `AsrorAsr/lexuz-legal-documents` | ~27k docs | metadata only, no full text, no card, no license |
| `ninetydevuz/lex-uz-legal-text-scaping` | ~10k docs | full text, Apache-2.0, but empty README and uncleaned page dumps |
| `Sohiba01/uzbek-legal-ir` | ~52k rows | no dataset card |
| `AsrorAsr/uzbek-legal-dataset` | ~1.2k rows | Criminal Code only |
| `Mehriddin1997/lex-uzbek-laws` | 307 docs | the one with a genuine dataset card |

What this dataset adds, stated plainly, is **engineering and documentation quality** at full scale:

- **Cleaned, normalized text** — UI chrome and button bars stripped, whitespace collapsed, Unicode NFC-normalized, not raw page dumps.
- **Explicit article-level hierarchy** — every row knows its `part`, `chapter`, and `article_number`; amendment notes and editorial cross-references are routed to their own fields instead of being inlined into the article body.
- **A reproducible, self-verifying enumeration** of the whole uz-Latin act set (below), with an honest coverage account.
- **Quality flags** shipped, not silently dropped.
- A **documented sourcing methodology** and a **clear license with a takedown contact**.

If you need raw coverage including Cyrillic/Russian today, one of the larger scrapes above may suit you better. If you need clean, structured, documented uz-Latin text, that is what this is for.

---

## Coverage — read this before using

lex.uz indexes each act **separately per language**: a given act may exist as a uz-Latin document, a uz-Cyrillic document, a Russian document, and/or an English one, each with its own id. **uz-Latin transliteration is not universal.** Empirically, only about **half** of the acts on lex.uz have a uz-Latin version at all — the rest are published only in uz-Cyrillic and/or Russian.

Concretely:

- **27,488** distinct uz-Latin acts were enumerated across 1991–2026 (the verified uz-Latin universe; see method below). For comparison, lex.uz holds roughly ~54k acts in uz-**Cyrillic** — so a uz-Latin-only corpus is inherently about half the size of the full act count. **If you need maximum act coverage, uz-Cyrillic is the more complete script.**
- Of those 27,488, **3,221** had an empty uz-Latin page (a title-only stub with no server-rendered body — typically acts whose text lives only in the Cyrillic/Russian version) and are excluded.
- The result is **24,267 acts with usable Latin text → 54,173 article rows.**

This is a deliberate single-language scope, documented honestly rather than inflated.

---

## Dataset structure

Two configurations. `articles` is the default.

### `articles` (default) — one row per article

The natural unit for retrieval and training. Document-level metadata is denormalized onto every article row so a single row is self-describing.

| Column | Type | Description |
|---|---|---|
| `id` | string | Row id, `{doc_id}-a{article_number}` (or `{doc_id}-full` for an unstructured act). |
| `act_group_id` | string | The act key, `abs(doc_id)` as a string. |
| `doc_id` | int | Lex.uz uz-Latin document id (negative). |
| `doc_title` | string | Title of the act. |
| `doc_type` | string | `law`, `resolution`, `decree`, `order`, `code`, `constitution`, or `other`. |
| `doc_number` | string | Official act number where the page exposes it (often empty). |
| `doc_date` | string | Adoption date (ISO), from the page. |
| `version_date` | string | The pinned consolidated `ONDATE` at which this text was current (see Limitations). |
| `status` | string | In-force / repealed, best-effort. |
| `part` | string | Part / section heading (`BOʻLIM`), if any. |
| `chapter` | string | Chapter heading (`-bob`), if any. |
| `article_number` | string | Article number, e.g. `12` or `12-1`. |
| `article_title` | string | Article heading text. |
| `article_text` | string | The article body, cleaned. |
| `amendment_note` | string | Editorial amendment annotations, routed to their own field. |
| `cross_references` | string | Editorial cross-reference / comment annotations, routed to their own field. |
| `language` | string | Always `uz`. |
| `script` | string | Always `latin`. |
| `okoz_codes` | list[string] | OKOZ classifier codes (reliable). |
| `tsz_codes` | list[string] | TSZ classifier codes (best-effort, known-incomplete — see Limitations). |
| `source_url` | string | `https://lex.uz/uz/docs/{doc_id}`. |
| `n_tokens` | int | Whitespace token count of `article_text`. |
| `quality_flag` | string | `""` = clean; otherwise `too-short`, `parse-uncertain`, or `no-articles`. |

### `documents` — one row per act

The same acts at whole-document granularity, for users who want full context rather than isolated articles. Columns: `doc_id`, `act_group_id`, `doc_title`, `doc_type`, `language`, `script`, `version_date`, `article_count`, and `full_text` (articles concatenated in order).

### The hierarchy

```
document (act)
└── part        (BOʻLIM)
    └── chapter (-bob)
        └── article  ← one row in the `articles` config
```

`part` and `chapter` are carried forward as context onto each article. Most acts (decrees, resolutions, short laws) have no internal article structure and are stored as a single flat-text row (`{doc_id}-full`, flag `no-articles`); codes and longer laws split into many articles.

---

## Language & script

All text is **fetched directly from lex.uz** — there is **no synthetic transliteration**. uz-Latin documents are identified by their negative document id (the uz-Latin id is the negation of the uz-Cyrillic id); only native uz-Latin documents are included.

Text is Unicode **NFC**-normalized. The Uzbek modifier letters `Oʻ` / `gʻ` and the apostrophe `ʼ` (U+02BB / U+02BC) are **preserved** as-is — not folded to ASCII — because that fold is lossy for Uzbek orthography. A negligible number of rows (~0.03%) contain short quoted Russian passages embedded in otherwise-Uzbek articles.

---

## How it was built

A sequence of small, resumable stages; each logs drop counts so the funnel is auditable end to end.

1. **`sourcing_check`** — fetch and evaluate `robots.txt`; record terms/copyright findings. The gate must pass before anything is crawled.
2. **`enumerate`** — discover the uz-Latin act set (below) into a manifest; resumable and incremental.
3. **`scrape`** — fetch each uz-Latin page with `httpx` and gzip-cache it to `data/raw_html/`. Resumable; cached pages are never re-fetched.
4. **`parse`** — with `selectolax`, split each document on its article-heading CSS class, carry part/chapter context onto each article, and route amendment notes and editorial cross-references into their own fields. UI button-bar chrome is stripped before any text is read. Doc-level metadata (dates, status, OKOZ/TSZ) is read from the page itself.
5. **`clean`** — NFC-normalize and collapse whitespace; assign quality flags; **drop empty-body rows** (see dedup note).
6. **`build_dataset`** — assemble the two configs and (optionally) `push_to_hub`.

### Enumeration — how the uz-Latin act set was found, and verified

lex.uz has no sitemap and no bulk API, and its search is an ASP.NET WebForms app. The bare year-filter listing is dominated by non-Latin documents, but a **Latin-script query term returns native uz-Latin (negative-id) documents**. So, per year (1991→2026), the pipeline unions the native-Latin hits of a few ultra-common Uzbek-Latin words (`va`, `toʻgʻrisida`, …), keeping only negative ids, and **stops once the union stabilizes** (an added term contributes <0.5% new acts). A single common word covers ~99% of a year's uz-Latin acts; the union closes the rest.

Completeness was checked three independent ways and agrees: every year converged (0 unstable years), and adding diverse out-of-set terms (`tasdiqlash`, `kiritish`, `chora`, `tartib`, …) yields **zero** new acts. The manifest (`data/manifest.jsonl`) is committed for reproducibility.

### Crawl rate (honest disclosure)

`robots.txt` states `Crawl-delay: 20` with no `Disallow`. This corpus is far larger than the v1 showcase, so rather than a fixed 20 s delay it uses a **conservative AIMD controller**: concurrency capped at **4**, ~0.3 s launch spacing, additive-increase after clean responses, **halve-on-error**, and it **honors `Retry-After`**. In practice this sustained **~3–4 requests/second** against a single host; the full ~24k-page crawl took ~3–4 hours, runs unattended, and is fully resumable from the gzip cache (a killed run re-fetches nothing already held). The crawler sends a descriptive `User-Agent` with a contact address (`uzbek-legal-corpus-crawler/1.0 (+sukhrobnurali@gmail.com; portfolio research dataset)`). This is brisk but bounded and polite; it is disclosed here rather than hidden.

### On duplicates

**No cross-document text de-duplication is applied**, by design. In legislation, identical text across acts is normal and legitimate: a shared "this law enters into force on publication" article belongs to every law that contains it, and templated decrees (e.g. treaty-ratification laws that differ only by date and counterpart) are **separate, individually-citable legal instruments**. Collapsing them would delete real acts. Every distinct `(act, article)` is therefore kept; only genuinely empty-body rows are dropped.

### Quality flags

`quality_flag` is **shipped, not hard-cut**:

| Flag | Meaning |
|---|---|
| `""` | Clean. |
| `too-short` | Below the minimum token threshold. |
| `parse-uncertain` | Structure extracted with low confidence. |
| `no-articles` | The act did not split into articles; stored as flat text (most decrees/resolutions). |

### Corpus statistics

**Pipeline funnel:**

| Stage | Count |
|---|---|
| uz-Latin acts enumerated (1991–2026) | 27,488 |
| Excluded — empty-body / unavailable Latin page | 3,221 |
| **Documents (final)** | **24,267** |
| **Article rows (final)** | **54,173** |

**Configs:** `articles` 54,173 rows · `documents` 24,267 rows.

**By document type** (`documents`):

| Type | Documents |
|---|---|
| Resolution (qaror) | 16,735 |
| Order (buyruq / farmoyish) | 3,232 |
| Decree (farmon) | 2,000 |
| Law (qonun) | 1,717 |
| Code (kodeks) | 259 |
| Constitution | 113 |
| Other | 211 |

**Structure:** 863 acts split into multiple articles (codes, longer laws); 23,404 are single flat-text acts (decrees, resolutions, short laws).

**Quality flags** (`articles`): clean 29,198 · `no-articles` 23,306 · `parse-uncertain` 1,658 · `too-short` 11.

**Volume:** ~47.3M article tokens (whitespace count); mean 873 tokens/article; max 226,647.

---

## Licensing & takedown

- **Code, pipeline, schema, and annotations** (the structuring, the quality flags, the cross-reference/amendment routing): **Apache-2.0**.
- **The legislative text itself**: public-domain-exempt under Article 8 of the Law on Copyright and Related Rights (LRU-42/2006), which excludes official documents and their official translations from copyright. Wikimedia Commons treats Uzbek legal texts as `PD-UZ-exempt`. Reproduced here with attribution to **lex.uz** as the source.

This dataset reuses the **legal text**. It does not redistribute lex.uz branding or wholesale-copy lex.uz's proprietary editorial/compilation layer; the on-page editorial annotations that are kept (amendment notes, cross-references) are isolated in their own fields and attributed.

**Sourcing checks.** The `/agreement` page on lex.uz is in practice a privacy policy and imposes no restriction on automated access to or reuse of the legislative texts. The national open-data portal `data.egov.uz` publishes legislation registries/metadata under CC BY-SA 4.0 but **not** the full normative text; the full text lives only on lex.uz.

**Takedown / corrections:** `sukhrobnurali@gmail.com`. If you are a rights holder or the source maintainer and want something changed or removed, contact me and I will act on it.

---

## Limitations

- **uz-Latin only, ~half the act universe.** About 50% of lex.uz acts have no uz-Latin version; those exist only in uz-Cyrillic/Russian and are out of scope here. This is a script-coverage limit of the source, not a crawl gap.
- **Pinned snapshot, not a live or amendment-history view.** Each act is captured at a single consolidated `version_date` (`ONDATE`). The dataset is not updated as the law changes. Always check lex.uz for the current text.
- **`status` is best-effort**, extracted heuristically; may be stale or wrong for a given row.
- **`tsz_codes` are known-incomplete** (the TSZ classifier embeds code and label in nested elements). **OKOZ codes are reliable.**
- **`doc_number` is often empty** — it is not reliably exposed in the uz-Latin page HTML.
- **A handful of documents (≈3) with non-standard markup did not parse** and are excluded; the vast majority of excluded docs are genuinely empty-body Latin stubs.
- **Not legal advice, not authoritative.** See the disclaimer at the top.

---

## Intended uses

- Information retrieval and RAG over Uzbek legislation (article-level units with document context).
- Fine-tuning and instruction-tuning of Uzbek legal-assistant models.
- Fill-mask / continued pretraining on legal-domain Uzbek (Latin) text.
- Legal-NLP research: classification by OKOZ code or document type, citation/cross-reference extraction.

### Out-of-scope uses

- **Any use as authoritative legal text or as a substitute for legal advice.** Verify against lex.uz.
- Determining the *current in-force* status of a provision — this is a pinned snapshot.
- Building systems that present generated output as official legal guidance without a qualified human in the loop.

---

## Related datasets

- [`sukhrobnurali/uzbek-legal-corpus-v1`](https://huggingface.co/datasets/sukhrobnurali/uzbek-legal-corpus-v1) — the curated trilingual (uz-Latin / uz-Cyrillic / Russian) showcase of the 20 codes + Constitution, with an aligned uz/ru parallel slice. Depth; this corpus is breadth.

---

*Source: [lex.uz](https://lex.uz) — National Database of Legislation of Uzbekistan. Contact: `sukhrobnurali@gmail.com`.*
