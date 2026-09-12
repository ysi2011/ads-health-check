# Ads Health Check

A read-only CLI tool that summarizes Google Ads performance for a car
dealership client and flags plain-English optimization opportunities.

Point it at a Google Ads CSV export and it reports:

- **Low CTR keywords / search categories** — impressions that aren't turning
  into clicks (an ad relevance / targeting problem)
- **Wasted spend / underperforming categories** — clicks that are producing
  zero conversions (a cost efficiency problem where cost data is available,
  or a targeting-efficiency problem where it isn't)
- **Optimization suggestions** — plain-English recommendations generated
  from the flagged data above

Two report shapes are supported:

- A **per-keyword Search campaign export** (`Keyword, Clicks, Impressions,
  CTR, Avg CPC, Cost, Conversions`) — the full analysis, including
  dollar-based wasted spend.
- A **Performance Max "Search terms insight" export** (`Search category,
  Clicks, Impressions, CTR, Conversions, ...`) — Google doesn't expose Cost
  or Avg CPC at this granularity for Performance Max, so the tool falls back
  to a clicks-based version of the same flags instead.

The tool auto-detects which one you've uploaded from the CSV's columns.

## Setup

Requires Python 3.10+.

```bash
git clone <this-repo>
cd ads-health-check
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py --file sample_data.csv
```

Save the report to a file as well as printing it to the terminal:

```bash
python main.py --file sample_data.csv --output report.txt
```

### Flags

| Flag       | Required | Description                             |
|------------|----------|------------------------------------------|
| `--file`   | yes      | Path to a Google Ads CSV export           |
| `--output` | no       | Also save the printed report to this file |

### Expected CSV columns

- Keyword report: `Keyword, Clicks, Impressions, CTR, Avg CPC, Cost, Conversions`
- Performance Max search-category report: `Search category, Clicks, Impressions, CTR, Conversions`

`sample_data.csv` is included as a small fake keyword dataset for testing
without real client data. `empty_sample.csv` (headers only, no rows) is
included to demo the empty-report edge case.

## Example output

```
Loaded 15 keywords from sample_data.csv

===========================================
Low CTR Keywords (ad relevance / targeting)
===========================================
                 Keyword   CTR  Impressions  Clicks
  car dealership reviews 2.05%         1900      39
     best car deals 2026 2.09%         4700      98
...

===========================================
Wasted Spend (clicks with zero conversions)
===========================================
               Keyword   Cost  Clicks  Conversions
car dealership reviews $42.90      39            0

========================
Optimization Suggestions
========================
- $42.90 of the $6,739.69 total spend (1%) went to keywords with zero conversions...
- "car dealership reviews" spent $42.90 with no conversions. Pause it or cut its bid...
...
```

## Edge cases handled

- **Empty CSV** (no data rows) — prints `No data found in this report.`
  instead of crashing.
- **No issues found** — if every keyword is healthy, each section prints
  `No issues found — this account is performing well.` instead of an empty
  table.
- **Missing/malformed columns** — prints a clear error naming the missing
  column(s) instead of a raw Python traceback.

## Project structure

```
main.py           # CLI entry point (argument parsing, prints the report)
api/index.py      # Flask web entry point (Vercel serverless function)
parser.py         # Reads and cleans the CSV into a pandas DataFrame; detects report kind
report.py         # Core logic: low-CTR flagging, wasted-spend detection, suggestions
html_report.py    # Renders the web report as a standalone HTML page
requirements.txt  # pandas, flask
sample_data.csv   # Fake keyword export for testing
empty_sample.csv  # Headers-only CSV for testing the empty-report edge case
```
