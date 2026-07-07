import os
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy.stats import pearsonr
from matplotlib.font_manager import FontProperties
from libpysal.weights import Queen, w_subset
from esda.moran import Moran

def obtain_descriptive_statistics_df(df):

    stats_df = df.describe().transpose()
    stats_df.reset_index(inplace=True)
    stats_df.rename(columns={'index': 'column'}, inplace=True)

    return stats_df

def obtain_spatial_statistics_df(df, gdf, merge_column: str, stats_cols: list):

    # add spatial statistics (global moran's I and significance (p-value)):
    df_geo = df.merge(gdf, on=merge_column, how='outer')
    df_geo = gpd.GeoDataFrame(df_geo, geometry="geometry", crs=gdf.crs)

    moran_results = []

    spatial_cor_data = df_geo.copy()
    spatial_cor_data = spatial_cor_data.dropna()
    w = Queen.from_dataframe(spatial_cor_data, use_index=False)
    w.transform = "r"

    for col in stats_cols:
        mi = Moran(spatial_cor_data[col].astype(float), w, permutations=999)

        moran_results.append({
            'column': col,
            'moran_I': round(mi.I, 4),
            'moran_p_value': round(mi.p_sim, 4)
        })

    moran_df = pd.DataFrame(moran_results)

    return moran_df

def plot_scattermatrix(gdf, columns: list, grouping_col, path):

    plot_name = f'Scatter matrix of {columns} sorted per {grouping_col}.jpeg'
    plot_file = os.path.join(path, plot_name)

    sns.set_theme(style="ticks")
    columns_for_plot = columns + [grouping_col]

    # use kind="reg" to add regression lines
    g = sns.pairplot(
        gdf[columns_for_plot],
        hue=grouping_col,
        corner=True,
        kind="scatter"
    )

    # adjust axes limits across all subplots
    for ax in g.axes.flatten():
        if ax is not None:
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

    plt.savefig(plot_file, bbox_inches='tight')
    plt.close()

def shorten_label(col: str) -> str:
    """
    Convert W_availability_xxx → W availability.
    Keep first letter + second part (availability/accessibility/affordability/acceptability).
    """
    parts = col.split("_")
    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"
    return col

def plot_scattermatrix_group_regression(gdf, columns: list, grouping_col, plot_name: str, path: str, year, size_col=None):

    # ---- FONT SETTINGS ----
    font_dict = {
        "family": "Times New Roman",
        "size": 16
    }

    fp = FontProperties(**font_dict)

    sns.set_context("paper", rc={"font.family": "Times New Roman", "font.size": 16})

    # Output
    plot_name = f"Scatter matrix of {plot_name} domains with regressions ({year}).jpeg"
    plot_file = os.path.join(path, plot_name)

    sns.set_theme(style="ticks")
    cols = list(columns)

    # Short labels for axes
    label_map = {c: shorten_label(c) for c in cols}

    # Palette for groups
    groups = list(gdf[grouping_col].unique())
    palette = dict(zip(groups, sns.color_palette(n_colors=len(groups))))

    # ---- Create PairGrid ----
    g = sns.PairGrid(gdf, vars=cols, hue=grouping_col, palette=palette, corner=False, layout_pad=0.7)

    # Lower triangle: scatterpoints only for clarity
    if size_col is None:
        g.map_lower(sns.scatterplot, alpha=1, s=25, edgecolor="none")
    else:
        g.map_lower(sns.scatterplot, size=gdf[size_col], alpha=1, edgecolor="none")

    # Diagonal: KDE per group
    g.map_diag(sns.kdeplot, fill=True, alpha=0.3)

    for i, j in zip(*np.triu_indices_from(g.axes, 1)):
        ax = g.axes[i, j]

        for group, color in palette.items():
            subset = gdf[gdf[grouping_col] == group]

            text = add_regression_with_significance(
                ax,
                subset[cols[j]],
                subset[cols[i]],
                color=color,
                show_line=True
            )

    # ---- LOWER TRIANGLE: ADD GLOBAL REGRESSION + CORR ----
    for i, j in zip(*np.tril_indices_from(g.axes, -1)):
        ax = g.axes[i, j]

        text = add_regression_with_significance(
            ax,
            gdf[cols[j]],
            gdf[cols[i]],
            color="black",
            show_line=True
        )

        ax.text(
            0.05, 0.95, text,
            transform=ax.transAxes,
            fontsize=14,
            fontfamily="Times New Roman",
            verticalalignment="top"
        )

    # ---- Apply shortened axis labels ----
    for i in range(len(cols)):
        for j in range(len(cols)):
            ax = g.axes[i, j]
            if ax is not None:
                if j < len(cols):
                    ax.set_xlabel(label_map[cols[j]], fontproperties=fp)
                if i < len(cols):
                    ax.set_ylabel(label_map[cols[i]], fontproperties=fp)

    # formatting:
    g.tick_params(labelsize=12, labelfontfamily='Times New Roman')

    ### LEGENDS
    # Add legend below the plots, centered to grid
    g.add_legend(
        title='',
        title_fontproperties=fp,
        prop=fp,
        loc='lower center',  # anchor point of the legend
        bbox_to_anchor=(0.30, -0.15),  # move slightly below grid
        ncol=3,  # number of columns
        frameon=False,  # optional: remove frame,
        markerscale=1.5
    )

    if size_col is not None and len(g.legend.texts) > len(groups):
        # Change the heading of the hue legend
        g.legend.get_texts()[0].set_text("Province")  # The hue header
        # Size legend usually appended after hue labels
        g.legend.get_texts()[len(groups)+1].set_text("Rural population size")
    else:

        # Apply Times New Roman to each text in the legend
        for text in g.legend.get_texts():
            text.set_fontproperties(fp)

    # ---- Set axis limits ----
    for ax in g.axes.flatten():
        if ax is not None:
            ax.tick_params(labelsize=12)
            for label in ax.get_xticklabels() + ax.get_yticklabels():
                label.set_fontproperties(fp)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

    plt.savefig(plot_file, bbox_inches="tight", dpi=300)
    plt.close()

def create_heatmap(gdf, column1: str, column2: str, path, year, row_keywords=None, col_keywords=None):

    plot_name = f'Comparison of {column1} and {column2} for {year}.jpeg'
    plot_file = os.path.join(path, plot_name)

    # Ensure categorical dtype
    gdf[column1] = gdf[column1].astype('category')
    gdf[column2] = gdf[column2].astype('category')

    # Crosstab
    crosstab = pd.crosstab(gdf[column1], gdf[column2])

    # Reindex to make sure ALL categories (including manual ones) appear
    crosstab = crosstab.reindex(
        index=gdf[column1].cat.categories,
        columns=gdf[column2].cat.categories,
        fill_value=0
    )

    # Apply ordering
    if row_keywords:
        row_order = order_by_keywords(crosstab.index.tolist(), row_keywords)
        crosstab = crosstab.reindex(index=row_order)
    if col_keywords:
        col_order = order_by_keywords(crosstab.columns.tolist(), col_keywords)
        crosstab = crosstab.reindex(columns=col_order)

    # Plot
    fig, ax = plt.subplots(figsize=(5, 5))
    sns.heatmap(crosstab, ax = ax, annot=True, fmt='d', cmap="crest", vmin = 0, vmax = 75,
                annot_kws={'size': 25, 'font': "Times New Roman"}, linewidths=0.5, linecolor='white', cbar=False,
                xticklabels=True, yticklabels=True)
    plt.tight_layout()
    plt.savefig(plot_file, bbox_inches='tight')
    plt.close()

def add_regression_with_significance(ax, x, y, color="black", show_line=True):
    """
    Computes Pearson correlation and conditionally plots regression line.
    Always returns formatted annotation text.
    """

    valid = ~(x.isna() | y.isna())
    x_valid = x[valid]
    y_valid = y[valid]

    if len(x_valid) < 2:
        return "NA"

    r, p = pearsonr(x_valid, y_valid)

    # significance stars
    if p < 0.001:
        stars = "***"
    elif p < 0.01:
        stars = "**"
    elif p < 0.05:
        stars = "*"
    else:
        stars = ""

    # draw regression line ONLY if significant
    if show_line and p < 0.05:
        sns.regplot(
            x=x_valid,
            y=y_valid,
            scatter=False,
            ci=None,
            line_kws={"color": color, "lw": 2},
            ax=ax
        )

    return f"r = {r:.2f} {stars}"

def order_by_keywords(labels, keywords):
    """
    Order labels so those containing keywords appear in order,
    then everything else comes after, sorted alphabetically.
    """
    ordered = []
    remaining = set(labels)

    for kw in keywords:
        matched = [lbl for lbl in labels if kw in lbl]
        ordered.extend(matched)
        remaining -= set(matched)

    return ordered + sorted(remaining)