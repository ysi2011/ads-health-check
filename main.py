"""Ads Health Check — entry point."""

import argparse
import sys

from html_report import generate_empty_html_report, generate_html_report
from parser import load_ads_report
from report import (
    low_ctr_keywords,
    optimization_suggestions,
    optimization_suggestions_no_cost,
    wasted_spend_keywords,
    zero_conversion_keywords,
)

NO_ISSUES_MESSAGE = "No issues found — this account is performing well."


def main():
    arg_parser = argparse.ArgumentParser(
        description="Summarize Google Ads keyword or Performance Max search-category "
        "performance and suggest optimizations."
    )
    arg_parser.add_argument("--file", required=True, help="Path to the Google Ads CSV export")
    arg_parser.add_argument(
        "--output",
        help="Optional path to also save the report. Use a .html extension for a browser-viewable report.",
    )
    args = arg_parser.parse_args()

    lines: list[str] = []

    def emit(text: str = "") -> None:
        print(text)
        lines.append(text)

    try:
        df, kind = load_ads_report(args.file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    if df.empty:
        emit("No data found in this report.")
        if args.output:
            if _is_html(args.output):
                _write_html(args.output, generate_empty_html_report(args.file))
            else:
                _write_report(args.output, lines)
        return

    is_keyword = kind == "keyword"
    row_label = "keywords" if is_keyword else "search categories"
    id_label = "Keyword" if is_keyword else "Search Category"

    emit(f"Loaded {len(df)} {row_label} from {args.file}")

    low_ctr_df = low_ctr_keywords(df)
    wasted_df = wasted_spend_keywords(df) if is_keyword else zero_conversion_keywords(df)
    suggestions = (
        optimization_suggestions(df, low_ctr_df, wasted_df)
        if is_keyword
        else optimization_suggestions_no_cost(df, low_ctr_df, wasted_df)
    )

    emit_section(emit, f"Low CTR {row_label.capitalize()} (ad relevance / targeting)")
    if low_ctr_df.empty:
        emit(NO_ISSUES_MESSAGE)
    else:
        display = low_ctr_df[["Keyword", "CTR", "Impressions", "Clicks"]].rename(
            columns={"Keyword": id_label}
        )
        display["CTR"] = display["CTR"].map("{:.2%}".format)
        emit(display.to_string(index=False))

    if is_keyword:
        emit_section(emit, "Wasted Spend (clicks with zero conversions)")
        display = wasted_df[["Keyword", "Cost", "Clicks", "Conversions"]].rename(
            columns={"Keyword": id_label}
        )
        if not wasted_df.empty:
            display["Cost"] = display["Cost"].map("${:,.2f}".format)
    else:
        emit_section(emit, "Underperforming Categories (clicks with zero conversions)")
        display = wasted_df[["Keyword", "Clicks", "Impressions", "Conversions"]].rename(
            columns={"Keyword": id_label}
        )

    if wasted_df.empty:
        emit(NO_ISSUES_MESSAGE)
    else:
        emit(display.to_string(index=False))

    emit_section(emit, "Optimization Suggestions")
    for suggestion in suggestions:
        emit(f"- {suggestion}")

    if args.output:
        if _is_html(args.output):
            html_doc = generate_html_report(args.file, df, low_ctr_df, wasted_df, suggestions, kind)
            _write_html(args.output, html_doc)
        else:
            _write_report(args.output, lines)


def emit_section(emit, title: str) -> None:
    emit(f"\n{'=' * len(title)}")
    emit(title)
    emit("=" * len(title))


def _is_html(path: str) -> bool:
    return path.lower().endswith((".html", ".htm"))


def _write_report(path: str, lines: list[str]) -> None:
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport saved to {path}")


def _write_html(path: str, html_doc: str) -> None:
    with open(path, "w") as f:
        f.write(html_doc)
    print(f"\nHTML report saved to {path} — open it with the Live Preview extension or in a browser.")


if __name__ == "__main__":
    main()
