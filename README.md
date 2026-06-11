---
dataset_info:
  config_name: articles
  features:
  - name: id
    dtype: large_string
  - name: act_group_id
    dtype: large_string
  - name: doc_id
    dtype: int64
  - name: doc_title
    dtype: large_string
  - name: doc_type
    dtype: large_string
  - name: doc_number
    dtype: large_string
  - name: doc_date
    dtype: large_string
  - name: version_date
    dtype: large_string
  - name: status
    dtype: large_string
  - name: part
    dtype: large_string
  - name: chapter
    dtype: large_string
  - name: article_number
    dtype: large_string
  - name: article_title
    dtype: large_string
  - name: article_text
    dtype: large_string
  - name: amendment_note
    dtype: large_string
  - name: cross_references
    dtype: large_string
  - name: language
    dtype: large_string
  - name: script
    dtype: large_string
  - name: okoz_codes
    list: string
  - name: tsz_codes
    list: string
  - name: source_url
    dtype: large_string
  - name: n_tokens
    dtype: int64
  - name: quality_flag
    dtype: large_string
  splits:
  - name: train
    num_bytes: 465732885
    num_examples: 54173
  download_size: 163356047
  dataset_size: 465732885
configs:
- config_name: articles
  data_files:
  - split: train
    path: articles/train-*
---
