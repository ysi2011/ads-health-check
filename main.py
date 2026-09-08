"""Ads Health Check — entry point."""

import argparse
import sys

from parser import load_keyword_report
from report import low_ctr_keywords, optimization_suggestions, wasted_spend_keywords

NO_ISSUES_MESSAGE = "No issues found — this account is performing well."


def main():
    arg_parser = argparse.ArgumentParser(
        description="Summarize Google Ads keyword performance and suggest optimizations."
    )
    arg_parser.add_argument("--file", required=True, help="Path to the keyword-performance CSV export")
    arg_parser.add_argument("--output", help="Optional path to also save the report to a text file")
    args = arg_parser.parse_args()

    lines: list[str] = []

    def emit(text: str = "") -> None:
        print(text)
        lines.append(text)

    try:
        df = load_keyword_report(args.file)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error loading CSV: {e}", file=sys.stderr)
        sys.exit(1)

    if df.empty:
        emit("No data found in this report.")
        if args.output:
            _write_report(args.output, lines)
        return

    emit(f"Loaded {len(df)} keywords from {args.file}")

    low_ctr_df = low_ctr_keywords(df)
    wasted_df = wasted_spend_keywords(df)

    emit_section(emit, "Low CTR Keywords (ad relevance / targeting)")
    if low_ctr_df.empty:
        emit(NO_ISSUES_MESSAGE)
    else:
        display = low_ctr_df[["Keyword", "CTR", "Impressions", "Clicks"]].copy()
        display["CTR"] = display["CTR"].map("{:.2%}".format)
        emit(display.to_string(index=False))

    emit_section(emit, "Wasted Spend (clicks with zero conversions)")
    if wasted_df.empty:
        emit(NO_ISSUES_MESSAGE)
    else:
        display = wasted_df[["Keyword", "Cost", "Clicks", "Conversions"]].copy()
        display["Cost"] = display["Cost"].map("${:,.2f}".format)
        emit(display.to_string(index=False))

    emit_section(emit, "Optimization Suggestions")
    for suggestion in optimization_suggestions(df, low_ctr_df, wasted_df):
        emit(f"- {suggestion}")

    if args.output:
        _write_report(args.output, lines)


def emit_section(emit, title: str) -> None:
    emit(f"\n{'=' * len(title)}")
    emit(title)
    emit("=" * len(title))


def _write_report(path: str, lines: list[str]) -> None:
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nReport saved to {path}")


if __name__ == "__main__":
    main()
