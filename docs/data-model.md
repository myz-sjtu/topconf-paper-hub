# Data Model

## `conference`

Curated top-conference definition.

- `acronym`: canonical short name, such as `SIGCOMM` or `NeurIPS`.
- `full_name`: full conference name.
- `domain`: `network`, `architecture`, or `ai`.
- `aliases`: alternative names for matching.
- `default_sources`: preferred metadata sources.

## `conference_edition`

One yearly edition of a conference.

- `conference_id`
- `year`
- `start_date` / `end_date`
- `location`
- `proceedings_url`

The primary browse grouping is conference acronym plus edition year.

## `paper`

Canonical paper metadata.

- `title`, `title_key`
- `authors`, `first_author_key`
- `abstract`
- `doi`
- `paper_url`, `pdf_url`
- `publication_date`
- `conference_id`, `edition_id`, `year`, `domain`
- `source_confidence`

## `paper_source_record`

Raw source trace for a paper.

- `paper_id`
- `source_type`
- `source_url`
- `source_paper_id`
- `raw_payload`
- `fetched_at`

## `taxonomy_tag` and `paper_tag`

Keyword-based first-version subtopic classification.

- `taxonomy_tag`: domain and tag slug.
- `paper_tag`: paper-tag relation, score, and method.

## `crawl_job`

Tracks manual or scheduled crawl runs.

- `status`: `queued`, `running`, `succeeded`, or `failed`.
- `total_tasks`, `completed_tasks`
- `inserted_count`, `updated_count`
- `error`
- timestamps and requested payload.

