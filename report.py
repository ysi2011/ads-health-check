"""Core Ads Health Check features.

Two flagging functions look at different parts of the funnel so their
output doesn't overlap:
  - low_ctr_keywords     -> impressions that aren't turning into clicks
                            (an ad relevance / targeting problem)
  - wasted_spend_keywords -> clicks that aren't turning into conversions
                            (a cost efficiency problem, independent of CTR)
"""

import pandas as pd


def low_ctr_keywords(df: pd.DataFrame, threshold: float | None = None) -> pd.DataFrame:
    """Flag keywords with underperforming click-through rate.

    Default threshold is 75% of the account's average CTR, so this only
    surfaces keywords that are meaningfully behind the rest of the account
    rather than flagging half the list just for being below average.
    """
    if threshold is None:
        threshold = df["CTR"].mean() * 0.75

    flagged = df[df["CTR"] < threshold].copy()
    return flagged.sort_values("CTR").reset_index(drop=True)


def wasted_spend_keywords(df: pd.DataFrame, min_cost: float = 0.0) -> pd.DataFrame:
    """Flag keywords that have spent money but produced zero conversions.

    This is deliberately unrelated to CTR: a keyword can have a great CTR
    and still burn budget if the traffic never converts.
    """
    flagged = df[(df["Conversions"] == 0) & (df["Cost"] > min_cost)].copy()
    return flagged.sort_values("Cost", ascending=False).reset_index(drop=True)


def optimization_suggestions(
    df: pd.DataFrame, low_ctr_df: pd.DataFrame, wasted_df: pd.DataFrame
) -> list[str]:
    """Generate plain-English optimization suggestions from the flagged data."""
    suggestions: list[str] = []

    total_cost = df["Cost"].sum()
    total_conversions = df["Conversions"].sum()
    wasted_cost = wasted_df["Cost"].sum()

    if wasted_cost > 0:
        pct = (wasted_cost / total_cost) * 100
        suggestions.append(
            f"${wasted_cost:,.2f} of the ${total_cost:,.2f} total spend ({pct:.0f}%) "
            f"went to keywords with zero conversions — that's the fastest place to cut budget."
        )

    if not wasted_df.empty:
        worst = wasted_df.iloc[0]
        suggestions.append(
            f"\"{worst['Keyword']}\" spent ${worst['Cost']:,.2f} with no conversions. "
            f"Pause it or cut its bid before spending more here."
        )

    if not low_ctr_df.empty:
        weakest = low_ctr_df.iloc[0]
        suggestions.append(
            f"\"{weakest['Keyword']}\" has a CTR of {weakest['CTR']:.2%}, well below the "
            f"account average of {df['CTR'].mean():.2%}. Tighten the match type or rewrite "
            f"the ad copy so it better matches what searchers are looking for."
        )
        if len(low_ctr_df) > 1:
            others = ", ".join(f'"{k}"' for k in low_ctr_df["Keyword"].iloc[1:4])
            suggestions.append(
                f"A few other keywords are also under-clicking for the impressions they get: "
                f"{others}. Worth a look at ad copy relevance for these too."
            )

    converting = df[df["Conversions"] > 0].copy()
    if not converting.empty:
        converting["CPA"] = converting["Cost"] / converting["Conversions"]
        best = converting.sort_values("CPA").iloc[0]
        suggestions.append(
            f"\"{best['Keyword']}\" is your most efficient keyword at ${best['CPA']:,.2f} "
            f"per conversion. Consider increasing its budget or bid to capture more volume."
        )

    if not suggestions:
        suggestions.append("No major issues found — this account looks healthy.")

    return suggestions
