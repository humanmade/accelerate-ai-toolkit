# Ability reference

Every Accelerate capability the toolkit can access, grouped by purpose. This is the technical reference for developers and curious users; the skills handle the plain-English translation at runtime.

All capabilities are invoked by the toolkit via a single MCP tool (`mcp__wordpress__mcp-adapter-execute-ability`) against your WordPress site's MCP adapter endpoint. You do not call these directly — the skills do.

---

## Permission tiers

Accelerate currently uses two WordPress capabilities as permission gates, not three. The authoritative source is `../altis-accelerate/inc/abilities/namespace.php:88–112`.

| Tier | WordPress capability | Unlocks |
|---|---|---|
| Analytics + experiments | `edit_posts` | All 35 analytics and experimentation capabilities below (discovery, author, engagement, attribution, realtime, query, variant management, A/B tests, audiences, personalisation rules) |
| Admin | `manage_options` | Stopping experiments, broadcasting content, exporting raw event data |

A stricter read-only capability for marketing-only roles is tracked as a future upstream improvement in `ROADMAP.md`. Until then, any user with `edit_posts` can both read analytics and create A/B tests.

---

## Discovery & context (11)

### `accelerate/get-performance-summary`
Retrieve aggregated performance metrics for blocks, posts, experiments, or the entire site.
- **Inputs:** `entity_type` (site \| block \| post \| experiment, default site), `entity_id`, `date_range_preset` (1h \| 4h \| 12h \| 24h \| 7d \| 30d \| 90d), `date_range`, `granularity`, `segment`
- **Returns:** views, visitors, conversions, conversion_rate, confidence_interval, time_series

### `accelerate/get-post-performance`
Detailed metrics for a specific post, page, or reusable block including views, conversions, and period comparison.
- **Inputs (required):** `post_id`
- **Inputs (optional):** `date_range`
- **Returns:** post, metrics, comparison, experiment, period

### `accelerate/get-top-content`
Best-performing content ranked by views.
- **Inputs:** `type` (post type filter), `limit` (1–50, default 10), `date_range`
- **Returns:** array of { id, title, type, views, conversions, url }

### `accelerate/get-content-diff`
Compare content performance between two time periods.
- **Inputs (required):** `post_ids`, `current_period`
- **Inputs (optional):** `comparison_period`
- **Returns:** object keyed by post_id with { current, previous, change_percent }

### `accelerate/get-traffic-breakdown`
Traffic breakdown by country, browser, OS, or referrer.
- **Inputs:** `dimension` (country \| browser \| os \| referrer, default country), `date_range`, `limit`
- **Returns:** array of { key, value, percent }

### `accelerate/get-taxonomy-performance`
Performance metrics grouped by WordPress taxonomy (category, tag, or custom).
- **Inputs:** `taxonomy` (default category), `date_range`, `limit` (1–100, default 20)
- **Returns:** terms array with term_id, name, slug, post_count, views, conversions, conversion_rate, underserved_score

### `accelerate/get-site-context`
The site's design system: colour palette, typography, spacing, available block types with style variations.
- **Inputs:** `include_blocks` (default false)
- **Returns:** site, colors, typography, spacing, blocks

### `accelerate/list-active-experiments`
All currently running A/B tests and personalisation rules.
- **Inputs:** `type` (all \| abtest \| personalization, default all), `post_id`
- **Returns:** array of { id, type, title, status, start_time, variants_count }

### `accelerate/list-experiments`
Discover historical and active experiments with filtering by status, type, date range, post, and annotations. Supports pagination — use this when you want every experiment ever run, not just the live ones.
- **Inputs:** `status` (all \| active \| running \| completed \| paused \| draft, default all), `type` (all \| abtest \| personalization, default all), `date_range`, `subject_post_id`, `annotation_key`, `annotation_value`, `page` (default 1), `per_page` (1–100, default 50)
- **Returns:** experiments array with { experiment_id, block_id, test_id, type, status, title, goal, started_at, ended_at, has_winner, winner_variant_index, annotations }, plus `total` and `pages` for pagination

### `accelerate/get-audience-segments`
Defined audiences with their targeting rules.
- **Inputs:** `include_estimates` (default false)
- **Returns:** array of audiences with id, title, description, rules, optional estimate

### `accelerate/get-audience-fields`
Available targeting fields and their values. Used to translate natural language into audience rules.
- **Inputs:** `refresh` (default false)
- **Returns:** array of { name, label, type, operators, values }

---

## Author analytics (2)

### `accelerate/get-author-performance`
Metrics for a specific author or comparison across all authors.
- **Inputs:** `author_id` (optional — omit for all authors), `date_range`, `limit` (1–100, default 20), `order_by` (views \| conversions \| conversion_rate \| posts_count)
- **Returns:** authors array, period

### `accelerate/get-author-content`
All content by a specific author with performance metrics.
- **Inputs (required):** `author_id`
- **Inputs (optional):** `date_range`, `order_by` (views \| conversions \| publish_date), `limit` (1–100, default 50)
- **Returns:** author object, posts array, period

---

## Engagement (1)

### `accelerate/get-engagement-metrics`
Quality engagement: bounce rate, time on page, scroll depth, recirculation, return visitor rate.
- **Inputs:** `entity_type` (post \| site, default site), `entity_id`, `date_range`
- **Returns:** avg_time_on_page_seconds, bounce_rate, pages_per_session, recirculation_rate, return_visitor_rate, scroll_depth { p25, p50, p75, p100 }, exit_pages, period

---

## Attribution & campaigns (4)

### `accelerate/get-attribution-comparison`
First-touch vs last-touch attribution with insights (best introducer, best closer, most undervalued).
- **Inputs:** `date_range`, `conversion_goal`
- **Returns:** channels array, insights object, period

### `accelerate/get-source-breakdown`
Detailed traffic source analysis.
- **Inputs:** `date_range`, `group_by` (source \| medium \| campaign \| referrer_domain, default source), `limit` (1–100, default 20)
- **Returns:** sources array with key, views, visitors, conversions, conversion_rate, percent_of_total

### `accelerate/get-utm-performance`
UTM parameter metrics grouped by campaign, source, medium, term, or content.
- **Inputs:** `date_range`, `group_by` (default campaign), `campaign` (filter by specific name)
- **Returns:** campaigns array

### `accelerate/get-landing-pages`
Top entry pages with engagement and conversion metrics.
- **Inputs:** `date_range`, `limit` (1–100, default 20)
- **Returns:** pages array with post_id, title, url, entries, bounce_rate, avg_time_on_page, conversion_rate

---

## Realtime (2)

### `accelerate/get-trending-content`
Content ranked by current momentum (velocity) — rising, stable, or falling.
- **Inputs:** `window` (1h \| 4h \| 12h \| 24h, default 1h), `metric` (views \| conversions \| visitors, default views), `content_type`, `limit` (1–50, default 20), `min_threshold` (default 10)
- **Returns:** trending array with direction, velocity_percent

### `accelerate/get-concurrent-visitors`
Real-time concurrent visitor count with polling guidance.
- **Inputs:** `post_id`, `active_window_minutes` (1–15, default 5), `include_breakdown` (default false)
- **Returns:** concurrent_visitors, optional breakdown, comparison { same_time_yesterday, change_percent }, polling object

---

## Content search (1)

### `accelerate/search-content`
Find content by title, URL, or text.
- **Inputs (required):** `query`
- **Inputs (optional):** `search_in` (title \| url \| content, default title), `post_type`, `limit` (1–100, default 20)
- **Returns:** results array with post_id, title, url, post_type, excerpt

---

## Experiment management (9)

### `accelerate/get-variants`
Inspect all variants in a reusable block.
- **Inputs (required):** `block_id`
- **Returns:** block_id, block_type, variants, experiment, edit_url

### `accelerate/add-variant`
Add a new variant to a block.
- **Inputs (required):** `block_id`, `content`
- **Inputs (optional):** `title`, `percentage` (1–100), `audience_id`
- **Returns:** success, block_id, variant_index, variant_count, edit_url

### `accelerate/update-variant`
Update an existing variant's content, title, traffic weight, or audience.
- **Inputs (required):** `block_id`, `variant_index`
- **Inputs (optional):** `content`, `title`, `percentage`, `audience_id`
- **Returns:** success, block_id, variant_index, variant_title, edit_url

### `accelerate/remove-variant`
Remove a variant. Cannot remove the last one. Destructive.
- **Inputs (required):** `block_id`, `variant_index`
- **Returns:** success, block_id, remaining_variants, edit_url

### `accelerate/create-ab-test`
Create a multi-variant A/B test on a block.
- **Inputs (required):** `block_id`, `variants` (min 2 of { title, content })
- **Inputs (optional):** `hypothesis`, `goal` (engagement \| click_any_link \| submit_form, default engagement), `traffic_percentage` (1–100, default 100)
- **Returns:** success, block_id, variants_count, edit_url

### `accelerate/set-block-goal`
Define the conversion metric for a block.
- **Inputs (required):** `block_id`, `goal` (engagement \| click_any_link \| submit_form)
- **Returns:** success, block_id, goal

### `accelerate/set-traffic-percentage`
Adjust how much traffic is included in a block's experiment.
- **Inputs (required):** `block_id`, `percentage` (1–100)
- **Returns:** success, block_id, percentage

### `accelerate/get-experiment-results`
Detailed statistical results for a running or completed experiment.
- **Inputs (required):** `block_id`
- **Inputs (optional):** `refresh` (default false)
- **Returns:** block_id, experiment_type, status, started_at, ended_at, traffic_percentage, confidence_threshold, has_winner, winner_variant_index, variants, recommendation, edit_url

### `accelerate/stop-experiment`
Pause, resume, stop, or declare a winner. Destructive. Requires confirmation.
- **Inputs (required):** `block_id`, `action` (pause \| resume \| stop \| declare_winner)
- **Inputs (optional):** `winner_variant_index` (required for declare_winner)
- **Returns:** success, block_id, action, new_status, message, edit_url

---

## Personalisation (3)

### `accelerate/create-audience`
Define a new audience with targeting rules.
- **Inputs (required):** `title`, `rules` { include: any\|all\|none, groups: [...] }
- **Inputs (optional):** `description`
- **Returns:** success, audience_id, edit_url

### `accelerate/update-audience`
Modify an existing audience.
- **Inputs (required):** `audience_id`
- **Inputs (optional):** `title`, `description`, `rules`
- **Returns:** success, audience_id

### `accelerate/create-personalization-rule`
Attach personalised content to a block for an audience.
- **Inputs (required):** `block_id`, `audience_id`, `personalized_content`
- **Inputs (optional):** `fallback_content`
- **Returns:** success, block_id, edit_url

---

## Broadcasts & integration (3)

### `accelerate/broadcast-content`
Create a site-wide broadcast campaign pushing blocks to multiple locations. Destructive. Requires confirmation.
- **Inputs (required):** `block_ids`, `title`
- **Returns:** success, broadcast_id, block_count, edit_url

### `accelerate/export-events`
Export raw analytics events for a specific date.
- **Inputs (required):** `date` (YYYY-MM-DD)
- **Inputs (optional):** `format` (json \| csv, default json)
- **Returns:** success, export_url, total_events, format

### `accelerate/get-export-status`
Check availability of exported data.
- **Inputs (required):** `date` (YYYY-MM-DD)
- **Returns:** available, total_events, export_url, retention

---

## Raw query (3, power users)

### `accelerate/query-events`
Raw event queries with custom filters.
- **Inputs:** `filters` array, `fields`, `date_range`, `limit` (1–10000, default 100), `offset`
- **Returns:** events array, total_count, query_time_ms

### `accelerate/get-event-schema`
Discover available analytics event fields.
- **Inputs:** `refresh` (default false)
- **Returns:** fields array with name, type, description, example_values

### `accelerate/aggregate`
Custom aggregations over analytics data with flexible dimensions and metrics.
- **Inputs (required):** `metrics` array of { field, function }
- **Inputs (optional):** `dimensions`, `filters`, `date_range`, `limit` (1–1000, default 100)
- **Returns:** rows array, query_time_ms

---

## Total: 39 capabilities

Structural breakdown by section: 11 discovery + 2 author + 1 engagement + 4 attribution + 2 realtime + 1 content search + 9 experiment management + 3 personalisation + 3 broadcasts & integration + 3 raw query = **39**.

Permission-tier breakdown (see the Permission tiers table at the top of this file):

- **35** abilities gated by `edit_posts` — analytics, experimentation, personalisation, reads of experiment state and export status
- **3** abilities gated by `manage_options` — `stop-experiment`, `broadcast-content`, `export-events`
