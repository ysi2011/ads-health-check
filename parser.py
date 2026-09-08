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


def load_keyword_report(file_path: str) -> pd.DataFrame:
    """Read a keyword-performance CSV export and return a cleaned DataFrame."""
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"This doesn't look like a Google Ads keyword export — "
            f"missing column(s): {', '.join(missing)}"
        )

    if df.empty:
        return df

    df["CTR"] = (
        df["CTR"].astype(str).str.rstrip("%").astype(float) / 100
    )

    for col in ["Clicks", "Impressions", "Avg CPC", "Cost", "Conversions"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
