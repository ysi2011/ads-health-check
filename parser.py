"""Loads a Google Ads keyword-performance CSV export into a pandas DataFrame."""

import pandas as pd

EXPECTED_COLUMNS = [
    "Keyword",
    "Clicks",
    "Impressions",
    "CTR",
    "Avg CPC",
    "Cost",
    "Conversions",
]

# Google Ads spells these differently depending on where in the UI you export
# from (e.g. "Avg. CPC" with a period, "Search keyword" instead of "Keyword").
_COLUMN_ALIASES = {
    "keyword": "Keyword",
    "search keyword": "Keyword",
    "clicks": "Clicks",
    "impressions": "Impressions",
    "impr.": "Impressions",
    "impr": "Impressions",
    "ctr": "CTR",
    "avg cpc": "Avg CPC",
    "avg. cpc": "Avg CPC",
    "average cpc": "Avg CPC",
    "cost": "Cost",
    "conversions": "Conversions",
    "conv.": "Conversions",
}

_NUMERIC_COLUMNS = ["Clicks", "Impressions", "CTR", "Avg CPC", "Cost", "Conversions"]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {
        col: _COLUMN_ALIASES[col.strip().lower()]
        for col in df.columns
        if col.strip().lower() in _COLUMN_ALIASES
    }
    return df.rename(columns=renamed)


def _to_number(series: pd.Series) -> pd.Series:
    """Strip currency codes/symbols and thousands separators (e.g. "MYR1,079.50%" -> 1079.50)."""
    cleaned = series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def load_keyword_report(file_path: str) -> pd.DataFrame:
    """Read a keyword-performance CSV export and return a cleaned DataFrame."""
    try:
        # utf-8-sig strips the BOM Google Ads exports prefix the file with.
        df = pd.read_csv(file_path, encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    df = _normalize_columns(df)

    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"This doesn't look like a Google Ads keyword export — "
            f"missing column(s): {', '.join(missing)}"
        )

    if df.empty:
        return df

    # Google Ads appends a "Total: Search ..." summary row at the bottom.
    df = df[~df["Keyword"].astype(str).str.startswith("Total", na=False)]

    for col in _NUMERIC_COLUMNS:
        df[col] = _to_number(df[col])
    df["CTR"] = df["CTR"] / 100

    return df.reset_index(drop=True)
