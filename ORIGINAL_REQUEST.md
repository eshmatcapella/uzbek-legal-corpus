# Original User Request

## Initial Request — 2026-08-12T14:20:58Z

<USER_REQUEST>
Transfer the English translation of the Civil Code General Part from `Civil_Code_Part1_Updated_2025.md` into the existing DuckDB legal corpus database, ensuring perfect article-by-article alignment with the Uzbek version without any text distortions or truncation.

Working directory: `c:/uzbek-legal-corpus`
Integrity mode: development

## Requirements

### R1. Parse the Markdown Safely
Parse the `Civil_Code_Part1_Updated_2025.md` file located in `C:\uzbek-legal-corpus\Civil code of Uzbekistan_general part` to extract the full English text for each article.

### R2. Non-Destructive Database Update
Update the dataset (specifically the Parquet file `c:/uzbek-legal-corpus/articles/train-00000-of-00001.parquet` or an equivalent DuckDB view) by appending a new column named `article_text_en`. Do not modify or replace the existing Uzbek `article_text`.

### R3. Strict Alignment
Align the extracted English text to the existing Uzbek rows strictly using the Article Number as the key (e.g., match "Article 1" in the markdown to `article_number='1'` in the database).

### R4. Zero Distortion Guarantee
Ensure absolutely zero distortion, truncation, or loss of formatting of the English text during the parsing and database insertion process.

## Acceptance Criteria

### Data Integrity & Verification
- [ ] A programmatic verification script must be written to assert that the number of articles extracted from the markdown exactly matches the number of non-null `article_text_en` rows updated in the database.
- [ ] The programmatic verification script must sample at least 5 random articles and strictly compare the character count of the text in the database against the raw text in the markdown file to prove zero truncation.
- [ ] The existing Uzbek `article_text` column must remain fully intact.
</USER_REQUEST>
