"""QC figures, saved as PNG files (docs/ARCHITECTURE.md, section 7).

Colours: grey for the values as written, blue for the harmonised values. The
four class colours are colour-blind safe in this order.
"""

import matplotlib

matplotlib.use("Agg")                     # draw to files, no window
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator
import pandas as pd

from facedata.harmonise import rank_correlation

INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
BEFORE, AFTER, ORANGE = "#9a9993", "#2a78d6", "#eb6834"
CLASS_COLOURS = {"value": "#2a78d6", "censored": "#eb6834", "missing code": "#1baf7a",
                 "unparsed": "#eda100", "empty": "#e4e3df"}
BLUES = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95",
         "#104281", "#0d366b"]            # one hue, light to dark, for ordered levels


def style(axis, title):
    """The same quiet look for every panel."""
    axis.set_title(title, loc="left", fontsize=10, color=INK)
    axis.set_facecolor(SURFACE)
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    for side in ["top", "right"]:
        axis.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        axis.spines[side].set_color(GRID)
    axis.tick_params(colors=MUTED, labelsize=8, length=0)


def legend_above(axis):
    """A legend on the title line, at the right: it never covers the marks."""
    axis.legend(fontsize=8, frameon=False, labelcolor=MUTED, ncols=2, loc="lower right",
                bbox_to_anchor=(1, 0.99), borderaxespad=0, handlelength=1.2, columnspacing=1)


def share_axis(axis, n_entries):
    """For stacked shares: room above the bars for the legend, whole years below."""
    axis.set_ylim(0, 1.32)
    axis.set_yticks([0, 0.25, 0.5, 0.75, 1])
    axis.legend(fontsize=7, frameon=False, labelcolor=MUTED, ncols=min(n_entries, 5), loc="upper left",
                handlelength=1.2, columnspacing=1)


def label_of(level):
    """3.0 is written 3; text stays as it is."""
    return f"{level:g}" if isinstance(level, float) else str(level)


def panel_distribution(axis, before, after, limits):
    """Panel 1 for numbers: distribution as written and harmonised, with the limits."""
    style(axis, "Distribution")
    low = min(before.quantile(0.005), after.min())
    high = max(before.quantile(0.995), after.max())
    if not high > low:
        low, high = low - 1, high + 1
    bins = np.linspace(low, high, 41)
    axis.hist(before.clip(low, high), bins=bins, histtype="step", color=BEFORE, linewidth=1.5, label="as written")
    axis.hist(after, bins=bins, histtype="step", color=AFTER, linewidth=2, label="harmonised")
    lines = [("range", "hard range", INK), ("winsor", "winsor limits", ORANGE)]
    for key, label, colour in lines:
        for position in limits.get(key, []):
            if low <= position <= high:
                axis.axvline(position, color=colour, linewidth=1, label=label)
                label = None                       # one legend entry for the two lines
    axis.legend(fontsize=8, frameon=False, labelcolor=MUTED)


def panel_classes(axis, classes, year):
    """Panel 2: what the raw cells held, year by year."""
    style(axis, "Raw cells per year (share)")
    shares = pd.crosstab(year, classes, normalize="index")
    bottom = np.zeros(len(shares))
    for name, colour in CLASS_COLOURS.items():
        if name in shares.columns:
            axis.bar(shares.index, shares[name], bottom=bottom, color=colour, edgecolor=SURFACE,
                     linewidth=1, label=name)
            bottom = bottom + shares[name].to_numpy()
    axis.xaxis.set_major_locator(MaxNLocator(integer=True))
    share_axis(axis, len(shares.columns))


def panel_by_group(axis, before, after, groups, title, as_line):
    """Panels 3 and 4 for numbers: median and quartiles of the harmonised value per group."""
    style(axis, title + ": median and quartiles")
    quartiles = after.groupby(groups).quantile([0.25, 0.5, 0.75]).unstack()
    if len(quartiles) == 0:
        return
    written = before.groupby(groups).median().reindex(quartiles.index)
    where = quartiles.index if as_line else np.arange(len(quartiles))
    if as_line:
        axis.plot(where, written, color=BEFORE, linewidth=1.5, label="as written")
        axis.fill_between(where, quartiles[0.25], quartiles[0.75], color=AFTER, alpha=0.18, linewidth=0)
        axis.plot(where, quartiles[0.5], color=AFTER, linewidth=2, label="harmonised")
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
    else:
        axis.plot(where, written, "o", color=BEFORE, markersize=9, label="as written")
        axis.vlines(where, quartiles[0.25], quartiles[0.75], color=AFTER, linewidth=2)
        axis.plot(where, quartiles[0.5], "o", color=AFTER, markersize=6, markeredgecolor=SURFACE, label="harmonised")
        axis.set_xticks(where, quartiles.index)
    legend_above(axis)


def panel_counts(axis, after):
    """Panel 1 for categories and short scales: how many values at each level."""
    style(axis, "Values per level")
    counts = after.value_counts().sort_index()
    axis.bar([label_of(level) for level in counts.index], counts, color=AFTER, width=0.6)


def panel_levels(axis, after, groups, title):
    """Panels 3 and 4 for categories and short scales: share of each level per group."""
    style(axis, title)
    levels = sorted(after.dropna().unique())
    step = max(1, (len(BLUES) - 1) // max(1, len(levels) - 1))
    shares = pd.crosstab(groups, after, normalize="index").reindex(columns=levels, fill_value=0)
    where = np.arange(len(shares))
    bottom = np.zeros(len(shares))
    for number, level in enumerate(levels):
        colour = BLUES[min(number * step, len(BLUES) - 1)]
        axis.bar(where, shares[level], bottom=bottom, color=colour, edgecolor=SURFACE, linewidth=1,
                 label=label_of(level))
        bottom = bottom + shares[level].to_numpy()
    axis.set_xticks(where, shares.index, rotation=90 if len(shares) > 12 else 0)
    share_axis(axis, len(levels))


def plot_variable(path, title, kind, before, after, classes, keys, limits):
    """The four-panel figure of one variable.

    before, after: the values as written and harmonised. classes: what each
    raw cell held. limits: {"range": [low, high], "winsor": [low, high]}.
    """
    figure, axes = plt.subplots(2, 2, figsize=(11, 6.5), dpi=80)
    year = keys["visit_date"].dt.year.astype("Int64")
    site = keys["siteid"]
    panel_classes(axes[0, 1], classes[year.notna()], year[year.notna()])
    if after.notna().sum() == 0:
        pass
    elif kind == "category" or after.nunique() <= 10:
        panel_counts(axes[0, 0], after)
        panel_levels(axes[1, 0], after[year.notna()], year[year.notna()], "Levels per year (share)")
        panel_levels(axes[1, 1], after, site, "Levels per site (share)")
    else:
        panel_distribution(axes[0, 0], before.dropna(), after.dropna(), limits)
        panel_by_group(axes[1, 0], before, after, year, "Per year", as_line=True)
        panel_by_group(axes[1, 1], before, after, site, "Per site", as_line=False)
    figure.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    figure.tight_layout()
    figure.savefig(path, facecolor=SURFACE)
    plt.close(figure)


def plot_instrument(path, title, values, version, sign_pairs, keys):
    """One figure per instrument: completeness per year, visits per year, sign check.

    values: the delivered variables. version: the edition per visit, or None.
    sign_pairs: {standard score: (raw value, score as written)}, or {}.
    """
    year = keys["visit_date"].dt.year
    figure, axes = plt.subplots(1, 3 if sign_pairs else 2, figsize=(14 if sign_pairs else 11, 4.5), dpi=80)

    style(axes[0], "Share of visits with a value, per variable and year")
    complete = values.notna().groupby(year).mean().T
    image = axes[0].imshow(complete, aspect="auto", cmap="Blues", vmin=0, interpolation="nearest")
    axes[0].grid(False)
    axes[0].set_xticks(range(len(complete.columns)), [int(y) for y in complete.columns], rotation=90)
    if len(complete) <= 30:
        axes[0].set_yticks(range(len(complete)), complete.index)
    figure.colorbar(image, ax=axes[0], fraction=0.03)

    style(axes[1], "Visits with at least one value, per year")
    seen = values.notna().any(axis=1)
    edition = version[seen].fillna("unknown") if version is not None else pd.Series("visits", index=keys.index)[seen]
    counts = pd.crosstab(year[seen], edition)
    bottom = np.zeros(len(counts))
    for name, colour in zip(counts.columns, list(CLASS_COLOURS.values())):
        axes[1].bar(counts.index, counts[name], bottom=bottom, color=colour, edgecolor=SURFACE, linewidth=1, label=name)
        bottom = bottom + counts[name].to_numpy()
    axes[1].xaxis.set_major_locator(MaxNLocator(integer=True))
    if len(counts.columns) > 1:                    # one series needs no legend: the title names it
        legend_above(axes[1])

    if sign_pairs:
        style(axes[2], "Rank correlation, raw value and score")
        table = pd.DataFrame(index=sorted(year.dropna().unique()), columns=["as written", "harmonised"], dtype=float)
        for one_year in table.index:
            rows = year == one_year
            written = pd.Series([rank_correlation(raw[rows], old[rows]) for raw, old in sign_pairs.values()])
            fixed = pd.Series([rank_correlation(sign_pairs[score][0][rows], values[score][rows]) for score in sign_pairs])
            table.loc[one_year] = [written.mean(), fixed.mean()]          # mean() leaves missing values out
        axes[2].plot(table.index, table["as written"], color=BEFORE, linewidth=1.5, label="as written")
        axes[2].plot(table.index, table["harmonised"], color=AFTER, linewidth=2, label="harmonised")
        axes[2].axhline(0, color=INK, linewidth=0.8)
        axes[2].set_ylim(-1, 1)
        axes[2].xaxis.set_major_locator(MaxNLocator(integer=True))
        axes[2].legend(fontsize=8, frameon=False, labelcolor=MUTED, loc="upper right")
    figure.suptitle(title, x=0.01, ha="left", fontsize=12, color=INK)
    figure.tight_layout()
    figure.savefig(path, facecolor=SURFACE)
    plt.close(figure)
