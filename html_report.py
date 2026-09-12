"""Renders the Ads Health Check report as a standalone HTML page."""

import html

import pandas as pd

_STYLE = """
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 900px; margin: 2rem auto; padding: 0 1.5rem; color: #1a1a1a; }
  h1 { margin-bottom: 0.25rem; }
  .subtitle { color: #666; margin-top: 0; margin-bottom: 2rem; }
  section { margin-bottom: 2.5rem; }
  h2 { font-size: 1.15rem; border-bottom: 2px solid #eee; padding-bottom: 0.5rem; }
  table { border-collapse: collapse; width: 100%; margin-top: 0.75rem; }
  th, td { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #eee; font-size: 0.92rem; }
  th { background: #f7f7f7; font-weight: 600; }
  tr:hover { background: #fafafa; }
  .healthy { color: #1a7f37; background: #eaf7ee; padding: 0.75rem 1rem; border-radius: 6px; }
  ul.suggestions { padding-left: 1.25rem; }
  ul.suggestions li { margin-bottom: 0.75rem; line-height: 1.5; }
  .summary { display: flex; gap: 2rem; margin-bottom: 1rem; flex-wrap: wrap; }
  .stat { background: #f7f7f7; border-radius: 8px; padding: 0.75rem 1.25rem; }
  .stat .value { font-size: 1.4rem; font-weight: 700; display: block; }
  .stat .label { font-size: 0.8rem; color: #666; }
"""


def _esc(text) -> str:
    return html.escape(str(text))


def _df_to_table(df: pd.DataFrame, formatters: dict | None = None) -> str:
    formatters = formatters or {}
    headers = "".join(f"<th>{_esc(col)}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = []
        for col in df.columns:
            value = row[col]
            if col in formatters:
                value = formatters[col](value)
            cells.append(f"<td>{_esc(value)}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")
    return f"<table><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def generate_html_report(
    source_file: str,
    df: pd.DataFrame,
    low_ctr_df: pd.DataFrame,
    wasted_df: pd.DataFrame,
    suggestions: list[str],
    kind: str = "keyword",
) -> str:
    """Build a standalone HTML page for the report. Assumes df is not empty.

    kind is "keyword" (per-keyword Search campaign export, has Cost) or
    "category" (Performance Max search-term insights, no Cost).
    """
    is_keyword = kind == "keyword"
    id_label = "Keyword" if is_keyword else "Search Category"
    row_label = "keywords" if is_keyword else "search categories"
    total_conversions = int(df["Conversions"].sum())

    low_ctr_html = (
        '<p class="healthy">No issues found — this account is performing well.</p>'
        if low_ctr_df.empty
        else _df_to_table(
            low_ctr_df[["Keyword", "CTR", "Impressions", "Clicks"]].rename(
                columns={"Keyword": id_label}
            ),
            {"CTR": "{:.2%}".format},
        )
    )

    if is_keyword:
        wasted_html = (
            '<p class="healthy">No issues found — this account is performing well.</p>'
            if wasted_df.empty
            else _df_to_table(
                wasted_df[["Keyword", "Cost", "Clicks", "Conversions"]].rename(
                    columns={"Keyword": id_label}
                ),
                {"Cost": "${:,.2f}".format},
            )
        )
        wasted_title = "Wasted Spend (clicks with zero conversions)"
    else:
        wasted_html = (
            '<p class="healthy">No issues found — this account is performing well.</p>'
            if wasted_df.empty
            else _df_to_table(
                wasted_df[["Keyword", "Clicks", "Impressions", "Conversions"]].rename(
                    columns={"Keyword": id_label}
                )
            )
        )
        wasted_title = "Underperforming Categories (clicks with zero conversions)"

    if is_keyword:
        third_stat = f'<div class="stat"><span class="value">${_esc(f"{df["Cost"].sum():,.2f}")}</span><span class="label">Total Spend</span></div>'
    else:
        third_stat = f'<div class="stat"><span class="value">{_esc(f"{df["Clicks"].sum():,}")}</span><span class="label">Total Clicks</span></div>'

    suggestions_html = "".join(f"<li>{_esc(s)}</li>" for s in suggestions)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ads Health Check Report</title>
<style>{_STYLE}</style>
</head>
<body>
  <h1>Ads Health Check</h1>
  <p class="subtitle">{_esc(len(df))} {row_label} loaded from {_esc(source_file)}</p>

  <div class="summary">
    <div class="stat"><span class="value">{_esc(len(df))}</span><span class="label">{_esc(row_label.capitalize())}</span></div>
    {third_stat}
    <div class="stat"><span class="value">{_esc(total_conversions)}</span><span class="label">Total Conversions</span></div>
  </div>

  <section>
    <h2>Low CTR {_esc(row_label.capitalize())} (ad relevance / targeting)</h2>
    {low_ctr_html}
  </section>

  <section>
    <h2>{_esc(wasted_title)}</h2>
    {wasted_html}
  </section>

  <section>
    <h2>Optimization Suggestions</h2>
    <ul class="suggestions">{suggestions_html}</ul>
  </section>
</body>
</html>
"""


def generate_empty_html_report(source_file: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Ads Health Check Report</title>
<style>{_STYLE}</style>
</head>
<body>
  <h1>Ads Health Check</h1>
  <p class="subtitle">{_esc(source_file)}</p>
  <p class="healthy">No data found in this report.</p>
</body>
</html>
"""
