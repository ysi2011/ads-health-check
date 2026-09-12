"""Loads a Google Ads performance CSV export into a pandas DataFrame.

Supports two report shapes:
  - "keyword": a per-keyword Search campaign export (Keyword, Cost, Avg CPC, ...)
  - "category": a Performance Max "Search terms insight" export (Search category,
    ...), which Google doesn't expose Cost or Avg CPC for at this granularity.

Both are normalized to the same identifier column, "Keyword", so the rest of
the app (report.py, html_report.py) only needs to branch on `kind` where the
missing Cost/Avg CPC data actually matters.
"""

import codecs
import io

import pandas as pd

CORE_COLUMNS = ["Keyword", "Clicks", "Impressions", "CTR", "Conversions"]
COST_COLUMNS = ["Avg CPC", "Cost"]

# Google Ads spells these differently depending on where in the UI you export
# from (e.g. "Avg. CPC" with a period, "Search category" for Performance Max).
_COLUMN_ALIASES = {
    "keyword": "Keyword",
    "search keyword": "Keyword",
    "search category": "Keyword",
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


def _decode(raw: bytes) -> str:
    """Google Ads exports show up as UTF-8 (with or without a BOM) or UTF-16
    (with a BOM) depending on which download option was used."""
    if raw.startswith(codecs.BOM_UTF16_LE) or raw.startswith(codecs.BOM_UTF16_BE):
        return raw.decode("utf-16")
    if raw.startswith(codecs.BOM_UTF8):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-16")


def _detect_delimiter(line: str) -> tuple[str, int]:
    """Score a candidate delimiter by how many resulting columns match a known
    Google Ads header name, so we can tell a comma-, tab-, or semicolon-
    separated export apart without guessing blind."""
    best_delim, best_score = ",", -1
    for delim in (",", "\t", ";"):
        cols = [c.strip().strip('"').lower() for c in line.split(delim)]
        score = sum(1 for c in cols if c in _COLUMN_ALIASES)
        if score > best_score:
            best_delim, best_score = delim, score
    return best_delim, best_score


def _find_header(text: str) -> tuple[int, str]:
    """Google Ads report downloads often prefix the real header with a title
    line and a date-range line. Scan for the first line that looks like an
    actual column header rather than assuming line 0 is it."""
    lines = text.splitlines()
    fallback = (0, ",")
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        delim, score = _detect_delimiter(line)
        if i == 0:
            fallback = (0, delim)
        if score >= 2:
            return i, delim
    return fallback


def load_ads_report(file_path: str) -> tuple[pd.DataFrame, str]:
    """Read a Google Ads performance CSV export.

    Returns (df, kind) where kind is "keyword" (Cost/Avg CPC available) or
    "category" (Performance Max search-term insights; no cost data).
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    text = _decode(raw)
    if not text.strip():
        return pd.DataFrame(columns=CORE_COLUMNS), "keyword"

    header_idx, delim = _find_header(text)
    body = "\n".join(text.splitlines()[header_idx:])

    try:
        df = pd.read_csv(io.StringIO(body), sep=delim)
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=CORE_COLUMNS), "keyword"

    df = _normalize_columns(df)

    missing = [col for col in CORE_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"This doesn't look like a Google Ads keyword or search-category export — "
            f"missing column(s): {', '.join(missing)}"
        )

    kind = "keyword" if "Cost" in df.columns and "Avg CPC" in df.columns else "category"

    if df.empty:
        return df, kind

    # Google Ads appends a "Total: Search ..." summary row at the bottom.
    df = df[~df["Keyword"].astype(str).str.startswith("Total", na=False)]

    numeric_cols = CORE_COLUMNS[1:] + (COST_COLUMNS if kind == "keyword" else [])
    for col in numeric_cols:
        df[col] = _to_number(df[col])
    df["CTR"] = df["CTR"] / 100

    keep_cols = CORE_COLUMNS + (COST_COLUMNS if kind == "keyword" else [])
    return df[keep_cols].reset_index(drop=True), kind
