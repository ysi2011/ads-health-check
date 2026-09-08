# Ads Health Check

A read-only CLI tool that summarizes Google Ads keyword performance for a car
dealership client and flags plain-English optimization opportunities.

Point it at a keyword-performance CSV export and it reports:

- **Low CTR keywords** — impressions that aren't turning into clicks (an ad
  relevance / targeting problem)
- **Wasted spend** — clicks that are costing money but producing zero
  conversions (a cost efficiency problem)
- **Optimization suggestions** — plain-English recommendations generated
  from the flagged data above

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

| Flag       | Required | Description                                        |
|------------|----------|-----------------------------------------------------|
| `--file`   | yes      | Path to a Google Ads keyword-performance CSV export |
| `--output` | no       | Also save the printed report to this file           |

### Expected CSV columns

`Keyword, Clicks, Impressions, CTR, Avg CPC, Cost, Conversions`

`sample_data.csv` is included as a small fake dataset for testing without
real client data. `empty_sample.csv` (headers only, no rows) is included to
demo the empty-report edge case.

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
parser.py         # Reads and cleans the CSV into a pandas DataFrame
report.py         # Core logic: low-CTR flagging, wasted-spend detection, suggestions
requirements.txt  # pandas
sample_data.csv   # Fake keyword export for testing
empty_sample.csv  # Headers-only CSV for testing the empty-report edge case
```
