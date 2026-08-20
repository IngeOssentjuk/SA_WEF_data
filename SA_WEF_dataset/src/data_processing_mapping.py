import os
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.font_manager import FontProperties
from matplotlib.colors import to_hex, LinearSegmentedColormap
import cmcrameri.cm as cmc
import contextily as cx
import fiona
import math
import textwrap

mpl.rcParams['hatch.linewidth'] = 0.15

def load_spatial_data_shp(spatial_abbrev: str, year: int, input_dir: str) -> gpd.GeoDataFrame:

    """
    Method to load in spatial data for a specific year and spatial demarcation used.
    :param spatial_abbrev: has to be MN (local municipality), DC (district municipality), PR (province). For 2011,
    also the SAL (small area level) is possible.
    :param year: the year of spatial demarcations used (has to be 2001, 2005, 2011, or 2016)
    :return: a gpd.GeoDataFrame consisting of the code and name of the spatial demarcation used, as well as the geometry.
    """

    # go to file based on function input
    file = os.path.join(input_dir, f"spatial_data/{year}/{spatial_abbrev}/{spatial_abbrev}.shp")

    # load data and extract required columns for merging and mapping
    spatial_data = gpd.read_file(file)
    required_columns = [f"{spatial_abbrev}_CODE", f"{spatial_abbrev}_NAME", 'geometry']
    spatial_data = spatial_data[required_columns]

    return spatial_data


def load_spatial_data_gdb(spatial_abbrev: str, year: int, input_dir: str):

    # go to file based on function input
    gdb_path = os.path.join(input_dir, f"spatial_data/{year}/{spatial_abbrev}.gdb")
    gdb_path = os.path.normpath(gdb_path)

    # See if there are multiple layers, for each layer, return a spatial df
    for feature_class in fiona.listlayers(gdb_path):

        spatial_df = gpd.read_file(filename=gdb_path, layer=feature_class)

        return spatial_df

    # layers = {}
    # for layer in fiona.listlayers(gdb_path, driver="OpenFileGDB"):
    #     layers[layer] = gpd.read_file(gdb_path, layer=layer, driver="OpenFileGDB")
    #
    # return layers


def weighted_average(series, weights):
    # Remove NaN values in series and corresponding weights
    mask = (~series.isna()) & (~weights.isna()) & np.isfinite(series) & np.isfinite(weights)
    series, weights = series[mask], weights[mask]

    # Avoid division by zero
    weight_sum = weights.sum()
    return (series * weights).sum() / weight_sum if weight_sum != 0 else np.nan


def aggregating_data_wgt_avg(df, grouping_col, weighting_col, col_list):
    agg_df = df.groupby(grouping_col).agg(
        {col: lambda x: weighted_average(x, df.loc[x.index, weighting_col]) for col in col_list}
    ).reset_index()

    return agg_df


def aggregating_data_min_max_wgt_avg(df, grouping_col, weighting_col, col_list):
    agg_funcs = {}
    for col in col_list:
        agg_funcs[f"{col}_min"] = (col, 'min')
        agg_funcs[f"{col}_max"] = (col, lambda x: x[x != np.inf].max() if np.isfinite(x[x != np.inf]).any() else np.nan)
        agg_funcs[f"{col}_wgt_avg"] = (col, lambda x: weighted_average(x, df.loc[x.index, weighting_col]))

    agg_df = df.groupby(grouping_col).agg(**agg_funcs).reset_index()

    return agg_df


def select_rural_entries(df: pd.DataFrame, area_col) -> pd.DataFrame:

    # Geo types classifying "rural" households
    rural_mask = ((df[area_col] == 'Farm areas') | (df[area_col] == 'Tribal/traditional areas') | (df[area_col] == 2) |
                  (df[area_col] == 3) | (df[area_col] == 'Farms') | (df[area_col] == 'Traditional'))

    # Assigning values based on the masks
    rural_df = df[rural_mask]

    return rural_df


def select_urban_entries(dataset: pd.DataFrame, area_col) -> pd.DataFrame:

    df = dataset

    # Geo types classifying "urban" households
    urban_mask = ((df[area_col] == 'Urban') | (df[area_col] == 'Urban areas') | (df[area_col] == 1))

    # Assigning values based on the masks
    urban_df = df[urban_mask]

    return urban_df

### -------- PLOT FUNCTIONS ---------

def map_multiple_columns(gdf, column_list, area, spatial_demarcation_gdf, path, year):

    # Reproject to Web Mercator if needed
    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    for col in column_list:

        plot_name = f'{col}_{area}_{year}.jpeg'
        plot_file = os.path.join(path, plot_name)

        # set figure size
        fig, ax = plt.subplots(figsize=(12, 8))

        # plot the map, add municipal/provincial lines and add a basemap
        gdf.plot(ax=ax, column=col, cmap=cmc.devon_r, legend=True, vmin=0, vmax=1, edgecolor='black', linewidth=0.25,
                 missing_kwds={'color': 'lightcoral', 'edgecolor':'black', 'hatch':'////', 'label': 'Missing values'})

        # add provincial boundaries to plot
        spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black')

        cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels)

        ax.set_title(f'Score of {col} at MN level for {area} areas')
        ax.axis('off')
        plt.savefig(plot_file, bbox_inches='tight', dpi=300)
        plt.close(fig)

def map_column(gdf, column, area, spatial_demarcation_gdf, path):

    # Reproject to Web Mercator if needed
    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    plot_name = f'{column}_{area}.jpeg'
    plot_file = os.path.join(path, plot_name)

    # set figure size
    fig, ax = plt.subplots(figsize=(12, 8))

    # plot the map, add municipal/provincial lines and add a basemap
    gdf.plot(ax=ax, column=column, cmap='Grays', vmin=0, vmax=1, legend=True, edgecolor='black', linewidth=0.25,
             missing_kwds={'color': 'lightcoral', 'edgecolor':'black', 'hatch':'////', 'label': 'Missing values'})
    spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black')
    cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels)

    ax.set_title(f'Score of {column} at MN level for {area} areas')
    ax.axis('off')
    plt.savefig(plot_file, bbox_inches='tight', dpi=300)
    plt.close(fig)


def map_column_categorical(gdf, column, spatial_demarcation_gdf, colour_mapping: dict, path):

    # Reproject to Web Mercator if needed
    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    plot_name = f'{column}.jpeg'
    plot_file = os.path.join(path, plot_name)

    # set figure size
    fig, ax = plt.subplots(figsize=(12, 8))

    # plot the map, add municipal/provincial lines and add a basemap
    gdf.plot(ax=ax, color=gdf[column].map(colour_mapping), edgecolor='black', linewidth=0.25,
             missing_kwds={'color': 'lightgrey', 'edgecolor':'black', 'hatch':'///', 'label': 'Missing values'})
    spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5)
    cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels)

    # add categorical legend
    # patches = [mpatches.Patch(color=to_hex(c), label=label) for label, c in colour_mapping.items()]
    # ax.legend(handles=patches, title=column, loc='lower right')

    ax.set_title(f'Score of {column} at MN level')
    ax.axis('off')
    plt.savefig(plot_file, bbox_inches='tight')
    plt.close(fig)

def map_hotspots(gdf, column, area, spatial_demarcation_gdf, path, stats_df=None, agg_method=None):

    # Reproject to Web Mercator if needed
    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    # set global fonts for axis labels:
    font = FontProperties(family='Times New Roman', weight='bold', size=10)

    # Normalize column input
    if isinstance(column, str):
        columns = [column]
    elif isinstance(column, list):
        columns = column
    else:
        raise TypeError("column must be str or list")

    nr = len(columns)

    plot_name = f'Hotspot_analysis_{agg_method}_{area}_{nr}.jpeg'
    plot_file = os.path.join(path, plot_name)

    # set figure size
    fig, axs = plt.subplots(nrows=1, ncols=nr, figsize=(5*nr, 5))

    if nr == 1:
        axs = [axs]

    # ---- DISCRETE COLORMAP ----
    bounds = list(range(11))  # 0–9
    norm = mcolors.BoundaryNorm(bounds, cmc.lajolla_r.N)
    cmap = cmc.lajolla_r

    for i, col in enumerate(columns):
        gdf.plot(ax=axs[i], column=col, cmap=cmap, norm=norm, legend=False, edgecolor='black', linewidth=0.25)

        spatial_demarcation_gdf.plot(ax=axs[i], facecolor='none', edgecolor='black')

        cx.add_basemap(axs[i], source=cx.providers.CartoDB.PositronNoLabels, attribution=False)
        axs[i].axis('off')

        # if not 'domain' in col:
        #     min = gdf[col].min()
        #     max = gdf[col].max()
        #     type = col.split("_")[1]
        #     letters = ['a)', 'b)', 'c)']
        #     letter = letters[i]
        #     axs[i].set_title(f'{letter} Number of {type}s for which the limiting domain is insecure ({min}-{max})', font_properties=font)
        # else:
        #     axs[i].set_title(f'{letter} Number of insecure domains in total (0-12)', font_properties=font)

        if stats_df is not None:

            I_value = stats_df.loc[stats_df['column'] == col, 'moran_I'].squeeze()
            I_value = round(I_value, 2)
            axs[i].text(0.02, 0.98, f"GMI = {I_value}", transform=axs[i].transAxes, fontsize=14, font="Times New Roman",
                        verticalalignment='top')

            # Only plot p-value if Moran’s I is valid
            if not np.isnan(I_value):
                p_value = stats_df.loc[stats_df['column'] == col, 'moran_p_value'].squeeze()
                axs[i].text(0.02, 0.90, f"p = {p_value}", transform=axs[i].transAxes, fontsize=14,
                            font="Times New Roman", verticalalignment='top')

    # ---- SHARED CATEGORICAL LEGEND ----
    legend_elements = [mpatches.Patch(facecolor=cmap(norm(i)), edgecolor='black', label=str(i)) for i in range(10)]

    fig.legend(handles=legend_elements, title='Number of limiting domains below threshold',
               title_fontproperties=font, loc='lower center', ncol=10, frameon=False)

    plt.tight_layout(rect=[0, 0.08, 1, 1])
    plt.savefig(plot_file, bbox_inches='tight', dpi=300)
    plt.close(fig)

def plot_grid_maps(gdf, columns_dict, spatial_demarcation_gdf, plot_name, path, resource_layout: dict,
                   dimensions_layout: dict, stats_gdf=None, suptitle=None, font=None, **subplot_kwargs):

    """
    Create an A4-sized figure with a grid of subplots of 5x4, based of four sub-grids.
    """

    # Reproject to Web Mercator if needed
    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    width = 6.42 * 1.8
    heigth = 8 * 1.8
    fig = plt.figure(figsize=(width, heigth))

    # CREATE GRIDS OF PLOTS (incl. background colour)
    # Outer 3x2 grid (2x2 for plots, bottom row for legends)
    outer = gridspec.GridSpec(3, 2, width_ratios=[3, 1], height_ratios=[4, 1, 0.6], wspace=0.05, hspace=0.05)

    # # set grid colours:
    # tl_colour = "mediumpurple"
    # tr_colour = "lightgrey"
    # bl_colour = "lightgrey"
    # br_colour = "lightcoral"

    # TOP-LEFT: 4x3 grid with all domain scores
    gs_tl = gridspec.GridSpecFromSubplotSpec(4, 3, subplot_spec=outer[0, 0], wspace=0, hspace=0)
    ax_tl = [[plt.subplot(gs_tl[j, i]) for j in range(4)] for i in range(3)]
    # add_grid_background(ax_tl[0][0], color=tl_colour)

    # TOP-RIGHT: 4x1 grid with horizontal (dimension) aggregation
    gs_tr = gridspec.GridSpecFromSubplotSpec(4, 1, subplot_spec=outer[0, 1], hspace=0)
    ax_tr = [plt.subplot(gs_tr[j, 0], sharey=ax_tl[0][0]) for j in range(4)]
    # add_grid_background(ax_tr[0], color=tr_colour)

    # BOTTOM-LEFT: 1x3 grid with vertical (resource) aggregation
    gs_bl = gridspec.GridSpecFromSubplotSpec(1, 3, subplot_spec=outer[1, 0], wspace=0)
    ax_bl = [plt.subplot(gs_bl[0, i], sharex=ax_tl[0][0]) for i in range(3)]
    # add_grid_background(ax_bl[0], color=bl_colour)

    # BOTTOM-RIGHT: 1×1 with full aggregation
    ax_br = plt.subplot(outer[1, 1])
    # add_grid_background(ax_br, color=br_colour)

    # flatten the axes, so that the plotting loop ignores the grids and goes row-by-row across the entire figure:
    axes_flat = []

    for i in range(4):
        for j in range(3):
            axes_flat.append(ax_tl[j][i])
        axes_flat.append(ax_tr[i])

    # then bottom row
    axes_flat.extend(ax_bl)
    axes_flat.append(ax_br)

    # turn off all ticks:
    for ax in axes_flat:
        ax.set_xticks([0])
        ax.set_yticks([0])

    # set global fonts for axis labels:
    if font is None:
        font = FontProperties(family='Times New Roman', weight='bold', size=12)

    # set axis titles for the figure (W, E, F, 4As, limiting):
    labelpad = 12
    ax_tl[0][0].set_ylabel("Availability (A1)", labelpad=labelpad, fontproperties=font)
    ax_tl[0][1].set_ylabel("Accessibility (A2)", labelpad=labelpad, fontproperties=font)
    ax_tl[0][2].set_ylabel("Affordability (A3)", labelpad=labelpad, fontproperties=font)
    ax_tl[0][3].set_ylabel("Acceptability (A4)", labelpad=labelpad, fontproperties=font)
    ax_bl[0].set_ylabel("Limiting dimension", labelpad=labelpad, fontproperties=font)
    for ax in axes_flat:
        ax.xaxis.set_label_position("top")
    ax_tl[0][0].set_xlabel("Water", labelpad=labelpad, fontproperties=font)
    ax_tl[1][0].set_xlabel("Energy", labelpad=labelpad, fontproperties=font)
    ax_tl[2][0].set_xlabel("Food", labelpad=labelpad, fontproperties=font)
    ax_tr[0].set_xlabel("Limiting resource", labelpad=labelpad, fontproperties=font)

    # --- Fill subplots ---
    for ax, col in zip(axes_flat, columns_dict.keys()):

        # allow blank cells
        if col in (0, None, "", False):
            ax.axis("off")
            continue

        col_info = columns_dict[col]
        plot_func = col_info.get('plot_func')
        corr_flag = col_info.get('correlation')

        if corr_flag not in (None, False, '') and stats_gdf is not None:

            I_value = stats_gdf.loc[stats_gdf['column'] == col, 'moran_I'].squeeze()
            I_value = round(I_value, 2)
            ax.text(0.02, 0.98, f"GMI = {I_value}", transform=ax.transAxes, fontsize=12, font="Times New Roman",
                    verticalalignment='top')

            # Only plot p-value if Moran’s I is valid
            if not np.isnan(I_value):
                p_value = stats_gdf.loc[stats_gdf['column'] == col, 'moran_p_value'].squeeze()
                ax.text(0.02, 0.90, f"p = {p_value}", transform=ax.transAxes, fontsize=12,
                        font="Times New Roman", verticalalignment='top')

        # Call the plotting function for this column
        if plot_func is None:
            raise ValueError(f"No plot_func provided for column {col}")

        plot_func(ax=ax, gdf=gdf, col=col, spatial_demarcation_gdf=spatial_demarcation_gdf)

    gs_leg = gridspec.GridSpecFromSubplotSpec(1, 4,  subplot_spec=outer[2, :], wspace=0)

    ax_leg_tl = fig.add_subplot(gs_leg[0, 0]); ax_leg_tl.axis("off")
    ax_leg_tr = fig.add_subplot(gs_leg[0, 1]); ax_leg_tr.axis("off")
    ax_leg_bl = fig.add_subplot(gs_leg[0, 2]); ax_leg_bl.axis("off")
    ax_leg_br = fig.add_subplot(gs_leg[0, 3]); ax_leg_br.axis("off")

    # Collect sample handles
    handles_tr = grouped_resource_legend(resource_layout)
    handles_bl = grouped_dimension_legend(dimensions_layout)
    handles_br = grouped_wef_legend(resource_layout, dimensions_layout)

    draw_grouped_block(ax_leg_tr, handles_tr, color_bg="white", label_key="label", title_area_frac=0.12, label_area_frac=0.35)
    draw_grouped_block(ax_leg_bl, handles_bl, color_bg="white", label_key="label", title_area_frac=0.12, label_area_frac=0.30,
                       vertical_compact=0.80)
    draw_grouped_block(ax_leg_br, handles_br, color_bg="white", label_key="label", title_area_frac=0.12, label_area_frac=0.20)

    colls = ax_tl[0][0].collections
    mappable = colls[0]
    cax = ax_leg_tl.inset_axes([0.15, 0.375, 0.70, 0.25])
    cbar = fig.colorbar(mappable, cax=cax, orientation="horizontal", ticks=[0, 0.25, 0.50, 0.75, 1])
    cbar.ax.tick_params(labelsize=8, labelfontfamily="Times New Roman")
    cbar.set_label("Domain score", fontsize=8, font="Times New Roman", weight='bold', labelpad=-60, rotation=0)

    if suptitle:
        fig.suptitle(suptitle)

    # plt.savefig(os.path.join(path, f'{plot_name}.svg'))
    plt.savefig(os.path.join(path, f'{plot_name}_300dpi.jpeg'), dpi=300)
    plt.close(fig)

    return fig


def plot_map_for_grid(ax, gdf, col, spatial_demarcation_gdf):
    """
    Plot a single map panel on a given axis.
    """

    # 1. Plot main thematic map
    gdf.plot(ax=ax, column=col, cmap=cmc.devon_r, legend=False, vmin=0, vmax=1, edgecolor='black', linewidth=0.25,
        missing_kwds={'color': 'lightcoral', 'edgecolor':'black', 'label': 'Missing values'})

    # 2. Add provincial boundaries
    spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5)

    # 3. Add basemap
    cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels, attribution=False)

    # # Remove axis ticks for clean maps
    # ax.set_axis_off()

def plot_hatch_map_for_grid(ax, gdf, col, spatial_demarcation_gdf):
    """
    Generic map plotting function using hatches and shading rules.
    Works as the plot_func for plot_grid_maps().

    Parameters
    ----------
    col : str
        The domain column (e.g. "W_limiting_domain").
    value_col : str
        The matching value column (e.g. "W_limiting_domain_value").
    mode : {"resource","dimension","wef"}
        Determines which rule-set to use.
    """

    if col == 'WEF_limiting_domain':
        colour_col = f'{col}_colours'
    else:
        colour_col = f'{col}_value_colours'

    bad = gdf[gdf[colour_col].apply(lambda x: isinstance(x[-1], str))]
    print(bad[colour_col].head())

    # 1. Plot column (based on pre-mapped colour column)

    if col in ['W_limiting_domain', 'E_limiting_domain', 'F_limiting_domain', 'WEF_limiting_domain']:

        # Mapping: dimension → hatch pattern
        hatch_map = {
            "availability": "||||",
            "accessibility": "xxxx",
            "affordability": "----",
            "acceptability": "....",
        }

        # Extract limiting dimension (2nd part of the string)
        gdf["_dimension"] = None
        mask_valid = gdf[col].notnull()
        gdf.loc[mask_valid, "_dimension"] = gdf.loc[mask_valid, col].str.split("_", expand=True).iloc[:, 1]

        # Plot each dimension block in a controlled order
        for dimension, hatch in hatch_map.items():
            df_sel = gdf[gdf["_dimension"] == dimension]
            if len(df_sel):
                df_sel.plot(
                    ax=ax,
                    color=df_sel[colour_col],
                    legend=False,
                    edgecolor="black",
                    linewidth=0.25,
                    hatch=hatch
                )

        # Plot missing values last (if needed)
        df_missing = gdf[gdf["_dimension"].isnull()]
        if len(df_missing):
            df_missing.plot(
                ax=ax,
                color="lightcoral",
                legend=False,
                edgecolor="black",
                linewidth=0.25
            )

    else:

        # Plot non-missing values
        df_valid = gdf[gdf[colour_col].notnull()]
        if len(df_valid):
            df_valid.plot(
                ax=ax,
                color=df_valid[colour_col],
                legend=False,
                edgecolor='black',
                linewidth=0.25
            )

        # Plot missing values separately
        df_missing = gdf[gdf[colour_col].isnull()]
        if len(df_missing):
            df_missing.plot(
                ax=ax,
                color='lightcoral',
                legend=False,
                edgecolor='black',
                linewidth=0.25,
                zorder=1
            )

    # 2. Add provincial boundaries
    spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5)

    # 3. Add basemap
    cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels, attribution=False)

    # # Remove axis ticks for clean maps
    # ax.set_axis_off()

def plot_sensitivity_maps(gdf, columns, titles, area, path, spatial_demarcation_gdf, plot_name, stats_df=None):

    """
    Plot multiple GeoDataFrame columns in a grid.

    Parameters
    ----------
    gdf: geopandas.GeoDataFrame
        GeoDataFrame containing the columns to plot.

    columns : list
        List of column names to plot. Use None to leave a grid position empty.

    titles : list
        List of titles corresponding to `columns`. Use None for empty positions.

    output_path : str
        Full path, including filename, where the figure will be saved.

    PR_boundaries : geopandas.GeoDataFrame
        GeoDataFrame containing the boundaries to overlay on each map.
        :param stats_df: dataframe with statistics

    """

    if len(columns) != len(titles):
        raise ValueError(
            f"`columns` and `titles` must have the same length. "
            f"Got {len(columns)} columns and {len(titles)} titles."
        )

    # Set style options
    cmap = cmc.devon_r
    font = FontProperties(family='Times New Roman', weight='bold', size=10)
    ncols = 3
    figsize_per_subplot = (5, 4)

    # Reproject to Web Mercator if needed
    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    # set grid dimensions
    n = len(columns)
    nrows = math.ceil(n / ncols)

    fig, axs = plt.subplots(nrows=nrows, ncols=ncols,
                            figsize=(figsize_per_subplot[0] * ncols, figsize_per_subplot[1] * nrows),
                            constrained_layout=True
    )

    axs = np.atleast_1d(axs).flatten()

    # plot list of columns
    for i, (col, title) in enumerate(zip(columns, titles)):

        ax = axs[i]

        # Leave this position empty
        if col is None:
            ax.axis('off')
            continue

        if col is not None and stats_df is not None:

            I_value = stats_df.loc[stats_df['column'] == col, 'moran_I'].squeeze()
            I_value = round(I_value, 2)
            ax.text(0.02, 0.98, f"GMI = {I_value}", transform=ax.transAxes, fontsize=12, font="Times New Roman",
                    verticalalignment='top')

            # Only plot p-value if Moran’s I is valid
            if not np.isnan(I_value):
                p_value = stats_df.loc[stats_df['column'] == col, 'moran_p_value'].squeeze()
                ax.text(0.02, 0.90, f"p = {p_value}", transform=ax.transAxes, fontsize=12,
                        font="Times New Roman", verticalalignment='top')
        else:
            # Mean value
            mean = round(gdf[col].mean(), 2)
            ax.text(0.02, 0.98, f"mean = {mean}", transform=ax.transAxes, fontsize=10, font="Times New Roman",
                    verticalalignment='top')

        # Plot the data
        gdf.plot(ax=ax, column=col, cmap=cmap, vmin=0, vmax=1, legend=False, edgecolor='black', linewidth=0.25,
                 missing_kwds={'color': 'lightcoral', 'edgecolor': 'black'})

        # Add boundaries
        spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black')
        # Add basemap
        cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels)
        ax.axis('off')

        # Title
        if title is not None:
            ax.set_title(title, font_properties=font)

    for j in range(n, len(axs)):
        fig.delaxes(axs[j])

    # create a shared color bar
    plot_axes = [axs[i] for i, col in enumerate(columns) if col is not None]
    norm = mpl.colors.Normalize(vmin=0, vmax=1)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    sm._A = []
    fig.colorbar(sm,ax=plot_axes, location='right', fraction=0.03, pad=0.02, shrink=0.5)

    # save figure
    plt.savefig(os.path.join(path, f'{plot_name}_{area}.jpeg'), dpi=300)
    plt.close(fig)

### ------ HELPER FUNCTIONS ------

def rgb255_to_rgba(r, g, b, a=1.0):
    return (r/255, g/255, b/255, float(a))

def map_value_to_shade(value, shade_levels: list):
    """Map continuous 0–1 → one of the 4 fixed shade levels."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        value = 1.0
    value = np.clip(float(value), 0, 1)

    # segment index 0–3
    idx = min(int(value * 4), 3)
    return shade_levels[idx]

def shade_color(base, shade):
    """
    Lightens base color as value decreases.
    - value = 1 → original base color
    - value = 0 → lightened color, but capped so it never becomes white.

    base is (r, g, b, a) in 0–1.
    max_lightness controls how close to white the color may get.
    """
    r, g, b, a = [float(c) for c in base]

    # Linear lighten toward white
    r_l = r + (1 - r) * (1 - shade)
    g_l = g + (1 - g) * (1 - shade)
    b_l = b + (1 - b) * (1 - shade)

    return float(r_l), float(g_l), float(b_l), float(a)

def get_style(domain, value, mode, layout_dict):
    """
    mode = 'resource'     → first pair
    mode = 'dimension'    → second pair
    mode = 'wef'          → third pair
    """

    # Handle missing domain or value
    if domain is None or (isinstance(domain, float) and math.isnan(domain)):
        return (0.94, 0.5, 0.5, 1)

    if value is None or (isinstance(value, float) and math.isnan(value)):
        value = 0  # fallback to minimum shade

    # -------------------------------------------------------------------
    # 1) FIRST PAIR — resource {W,E,F} limiting domain → grey cmap
    # -------------------------------------------------------------------
    if mode == "resource":
        shade_levels = [0.25, 0.50, 0.75, 1.00]
        shade = map_value_to_shade(value, shade_levels)
        # find which of the 4 dimension substrings occurs
        key = next(k for k in layout_dict.keys() if k in domain)
        rule = layout_dict[key]
        cmap = cm.get_cmap(rule["cmap"])
        color = cmap(shade)  # directly use shade = 0.25–1.0
        return color

    # -------------------------------------------------------------------
    # 2) SECOND PAIR — dimension limiting domain → W/E/F base colors
    # -------------------------------------------------------------------
    if mode == "dimension":
        shade_levels = [0.25, 0.50, 0.75, 1.00]
        shade = map_value_to_shade(value, shade_levels)
        key = next(k for k in layout_dict.keys() if k in domain)
        base = layout_dict[key]["base_color"]
        color = shade_color(base, shade)
        return color

    # -------------------------------------------------------------------
    # 3) THIRD PAIR — W/E/F part → color, dimension part → hatch
    # -------------------------------------------------------------------
    if mode == "wef":
        # extract W_, E_, F_
        res_key = next(k for k in layout_dict.keys() if domain.startswith(k))
        color = layout_dict[res_key]["base_color"]
        return color

    raise ValueError("Invalid mode")

def apply_styles(gdf, domain_col, value_col, mode, layout_dict, colour_column):
    colors = gdf.apply(lambda r: get_style(r[domain_col], r[value_col], mode, layout_dict), axis=1)
    gdf[colour_column] = colors

    return gdf

def make_shade(color, weight):
    """Interpolate base color toward white."""
    r, g, b = mcolors.to_rgb(color)
    w = 1 - weight

    return (r + (1-r)*w, g + (1-g)*w, b + (1-b)*w)

def trimmed_greys():
    # Avoid Greys(0)=white and Greys(1)=black
    base = mpl.colormaps.get_cmap("Greys")(np.linspace(0.15, 0.85, 256))
    return LinearSegmentedColormap.from_list("TrimmedGreys", base)

GREYS4 = trimmed_greys()
SEGMENTS = [0.25, 0.50, 0.75, 1]

def grouped_dimension_legend(layout_dict):
    """
    Returns handles = [(dimension_label, [patch1..patch4])]
    Each patch uses the trimmed greyscale + the dimension's hatch style.
    """

    # Assign hatches once
    layout_dict['availability']['hatch']   = "||||"
    layout_dict['accessibility']['hatch']  = "xxxx"
    layout_dict['affordability']['hatch']  = "----"
    layout_dict['acceptability']['hatch']  = "...."

    SEG_LABELS = ["0–0.25", "0.25–0.50", "0.50–0.75", "0.75–1"]
    shade_levels = [0.25, 0.50, 0.75, 1.0]  # same as map
    handles = []

    for dim, rule in layout_dict.items():
        base_color = (0, 0, 0, 1)  # you can pick black for Greys, shade_color will lighten
        patches = []
        for shade, lab in zip(shade_levels, SEG_LABELS):
            color = shade_color(base_color, shade)
            patch = mpatches.Rectangle(
                (0, 0), 1, 1,
                facecolor=color,
                edgecolor="black",
                hatch=rule["hatch"]
            )
            patch.label = lab
            patches.append(patch)
        handles.append((rule["label"], patches))

    return handles

def grouped_resource_legend(resource_layout):
    """
    Returns: handles = [(resource_label, [patch1..patch4])]
    """
    SEG_LABELS = ["0–0.25", "0.25–0.50", "0.50–0.75", "0.75–1"]
    handles = []
    for res_key, rule in resource_layout.items():
        base = rule["base_color"]
        shades = [make_shade(base, s) for s in SEGMENTS]
        patches = []
        for sh, lab in zip(shades, SEG_LABELS):
            patch = mpatches.Rectangle((0, 0), 1, 1,
                                       facecolor=sh,
                                       edgecolor="black")
            patch.label = lab
            patches.append(patch)
        handles.append((rule["label"], patches))
    return handles

def grouped_wef_legend(resource_layout, dim_layout):
    """
    Returns: handles = [(resource_label, [patch_dim1..patch_dim4])]
    """
    dim_layout['availability']['hatch']   = "||||"
    dim_layout['accessibility']['hatch']  = "xxxx"
    dim_layout['affordability']['hatch']  = "----"
    dim_layout['acceptability']['hatch']  = "...."

    handles = []
    for res_key, rule in resource_layout.items():
        base = rule["base_color"]
        patches = []
        for dimkey, d_rule in dim_layout.items():
            patch = mpatches.Rectangle((0, 0), 1, 1,
                                       facecolor=base,
                                       edgecolor="black",
                                       hatch=d_rule["hatch"])
            patch.label = d_rule["label"]
            patches.append(patch)
        handles.append((rule["label"], patches))
    return handles


def wrap_text(text, max_chars):
    if text is None:
        return ""
    return textwrap.fill(str(text), width=max_chars)


def draw_grouped_block(
    ax,
    handles,
    color_bg,
    label_key="label",

    # NEW: top area for column titles (fraction of vertical space)
    title_area_frac=0.18,          # 18% at top is typical for short titles

    # right-side label width
    label_area_frac=0.28,

    # padding around entire block
    x_pad=0.04,
    y_pad=0.04,

    # compactness tweaks
    vertical_compact=0.92,         # compress space between rows
    square_fill=0.85               # square size inside each row
):
    """
    Draws a grouped legend with reserved areas for:
        • top column titles
        • right-side row labels
    ensuring everything stays inside the axis.
    """

    ax.axis("off")

    n_cols = len(handles)
    if n_cols == 0:
        return

    n_rows = len(handles[0][1])

    # Background
    bg = mpatches.Rectangle((0, 0), 1, 1, facecolor=color_bg,
                            edgecolor="none", transform=ax.transAxes)
    ax.add_patch(bg)

    # padded interior box
    inner_left   = x_pad
    inner_right  = 1.0 - x_pad
    inner_width  = inner_right - inner_left

    inner_bottom = y_pad
    inner_top    = 1.0 - y_pad
    inner_height = inner_top - inner_bottom

    # --- Split vertical space ---
    title_area_height = inner_height * title_area_frac
    rows_area_height  = inner_height - title_area_height

    # optionally compact rows vertically
    effective_rows_height = rows_area_height * vertical_compact

    # rows area: centered inside its vertical band
    rows_top    = inner_top - title_area_height - (rows_area_height - effective_rows_height)/2
    rows_bottom = rows_top - effective_rows_height

    row_height  = effective_rows_height / n_rows
    square_size = row_height * square_fill

    # --- Split horizontal space ---
    label_area = inner_width * label_area_frac
    cols_area  = inner_width - label_area
    col_width  = cols_area / n_cols

    # wrapping widths
    max_chars_title = max(4, int(col_width * 35))
    max_chars_label = max(6, int(label_area * 45))

    # --- Draw everything ---
    for col_index, (title, patches) in enumerate(handles):

        # column left
        x0 = inner_left + col_index * col_width

        # ---------- TITLE AREA (wrapped, inside reserved top band) ----------
        wrapped_title = wrap_text(title, max_chars=max_chars_title)
        title_y = inner_top - title_area_height/2  # center inside top band

        ax.text(
            x0 + col_width/2,
            title_y,
            wrapped_title,
            ha="center",
            va="center",
            fontsize=8,
            font="Times New Roman",
            weight="bold",
            transform=ax.transAxes,
            clip_on=True
        )

        # ---------- PATCHES ----------
        for i, p in enumerate(patches):
            y0 = rows_top - (i + 1) * row_height + (row_height - square_size)/2
            if y0 < 0 or y0 + square_size > 1:
                continue

            sq = mpatches.Rectangle(
                (x0 + (col_width - square_size)/2, y0),
                square_size, square_size,
                facecolor=p.get_facecolor(),
                edgecolor="black",
                hatch=p.get_hatch(),
                transform=ax.transAxes
            )
            ax.add_patch(sq)

        # ---------- LABELS (right-side column, wrapped) ----------
        if col_index == n_cols - 1:
            label_x = inner_left + cols_area + 0.005

            for i, p in enumerate(patches):
                label_val = getattr(p, label_key, "")
                wrapped_label = wrap_text(label_val, max_chars=max_chars_label)

                y_mid = rows_top - (i + 1) * row_height + row_height/2
                if y_mid < 0 or y_mid > 1:
                    continue

                ax.text(
                    label_x,
                    y_mid,
                    wrapped_label,
                    fontsize=8,
                    font="Times New Roman",
                    ha="left",
                    va="center",
                    transform=ax.transAxes,
                    clip_on=True
                )


def generate_shades(n, cmap_name=None, base_color=None):
    """
    Returns n hex colours.
    Either from a named matplotlib colormap, or based on a base RGBA colour.
    """
    if cmap_name:
        cmap = plt.get_cmap(cmap_name)
        return [to_hex(cmap(i)) for i in np.linspace(0.3, 1.0, n)]  # avoid too-light edge

    if base_color is not None:
        # Create a light→dark sequential colormap from a base colour
        cmap = LinearSegmentedColormap.from_list(
            "custommap",
            [(1, 1, 1, 1), base_color]  # white → base colour
        )
        return [to_hex(cmap(i)) for i in np.linspace(0.3, 1.0, n)]

    raise ValueError("Either cmap_name or base_color must be provided.")


def obtain_cat_value_color_and_hatch(row, category_column, value_column, domain_cols):
    """
    Returns (color, hatch) where:
    - color depends on numeric value
    - hatch depends only on the domain (one per domain)
    """
    category = row[category_column]
    value = row[value_column]

    if pd.isna(category) or pd.isna(value):
        return (float("nan"), None)

    # Match domain
    domain = next((d for d in domain_cols if d in str(category)), None)
    if domain is None:
        return (float("nan"), None)

    cfg = domain_cols[domain]
    n = cfg["n_colors"]

    # --- Generate color shades ---
    shades = generate_shades(
        n=n,
        cmap_name=cfg.get("cmap"),
        base_color=cfg.get("base_color")
    )

    # Determine which bin a value falls into
    bins = np.linspace(0, 1, n + 1)
    idx = np.digitize(value, bins, right=True) - 1
    idx = max(0, min(idx, n - 1))  # clip

    # Ensure low value → light, high value → dark
    color = shades[::-1][idx]

    # One hatch per domain
    hatch = cfg.get("hatch", "")

    return color, hatch


def get_final_hex_colour_map(domain_cols):
    final_map = {}

    for domain, settings in domain_cols.items():
        n = settings["n_colors"]
        shades = generate_shades(
            n=n,
            cmap_name=settings.get("cmap"),
            base_color=settings.get("base_color")
        )
        final_map[domain] = shades[::-1]  # darkest first, consistent with earlier logic

    return final_map


def create_legend_from_mapping(ax, domain_cols: dict, nr_categories: int):
    colour_mapping_hex = get_final_hex_colour_map(domain_cols, nr_categories)
    patches = [
        mpatches.Patch(color=hex_list[-1], label=domain.capitalize())
        for domain, hex_list in colour_mapping_hex.items()
    ]
    ax.legend(handles=patches, loc='lower right', title="Domain")


def map_colour_column_with_legend(gdf, colour_column, plot_name, spatial_demarcation_gdf, path, domain_cols, nr_categories):

    if gdf.crs != "EPSG:3857":
        gdf = gdf.to_crs(epsg=3857)
        spatial_demarcation_gdf = spatial_demarcation_gdf.to_crs(epsg=3857)

    plot_file = os.path.join(path, f'{plot_name}.jpeg')
    fig, ax = plt.subplots(figsize=(12, 8))

    gdf.plot(color=gdf[colour_column], ax=ax, edgecolor='black', linewidth=0.25,
             missing_kwds={'color': 'lightgrey', 'edgecolor':'black', 'hatch':'///', 'label': 'Missing values'})
    spatial_demarcation_gdf.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5)
    cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels)
    ax.set_title(f'{plot_name} at MN level')
    ax.axis('off')

    create_legend_from_mapping(ax, domain_cols, nr_categories)

    plt.savefig(plot_file, bbox_inches='tight')
    plt.close()

def indices_to_colours(index_map: dict, cmap_name: str = "tab20c") -> dict:
    """
    Convert a dict mapping labels -> int (index into a colormap) to
    labels -> hex colour strings using the given matplotlib colormap.

    - index_map: dict[label] -> int (colormap index) or already-a-color (str/tuple)
    - cmap_name: matplotlib colormap name (default 'tab20c')
    """
    cmap = plt.get_cmap(cmap_name)
    n = cmap.N  # number of colours in the colormap, usually 20 for tab20/tab20c

    out = {}
    for label, val in index_map.items():
        # if val already looks like a color string or tuple, try to convert directly
        if isinstance(val, (str, tuple, list)):
            try:
                out[label] = to_hex(val)
                continue
            except Exception:
                # fallthrough to treat as index if it wasn't actually a color
                pass

        # otherwise treat val as an integer index into the colormap
        try:
            idx = int(val)
        except Exception:
            raise ValueError(f"Value for '{label}' is not an int or valid colour: {val}")

        # wrap indices so they don't exceed cmap.N
        rgba = cmap(idx % n)
        out[label] = to_hex(rgba)

    return out

def add_grid_background(ax, color, pad=1):
    """Draw a rectangle behind an axes (including padding), in axes coordinates."""
    rect = mpatches.Rectangle(
        (-pad, -pad), 1 + 2*pad, 1 + 2*pad,
        transform=ax.transAxes,
        facecolor=color,
        edgecolor='none',
        zorder=-10  # behind axes content
    )
    ax.add_patch(rect)


def add_special_area_flags(muns, areas, name):
    """
    Adds two columns to a municipality GeoDataFrame:
      - has_<name>            : 1 if municipality has positive-area overlap
      - adjacent_to_<name>    : 1 if municipality touches another municipality
                                that has positive-area overlap

    Parameters
    ----------
    muns : GeoDataFrame
        Municipality polygons (attributes & geometry preserved)
    areas : GeoDataFrame
        Special-area polygons
    name : str
        Identifier used in column names (e.g. 'act9', 'homeland')

    Returns
    -------
    GeoDataFrame
        Same GeoDataFrame as `muns` with two new columns added
    """

    # ---- SAFETY CHECK ----
    if muns.crs != areas.crs:
        raise ValueError("CRS of municipalities and areas must match")

    # ---- 1. CHECK WHETHER AREAS OVERLAP WITH MUNICIPALITIES
    intersections = gpd.sjoin(
        muns,
        areas,
        predicate='intersects',
        how='left'
    )

    has_col = f'contains_{name}'

    # create boolean
    intersections[has_col] = intersections['index_right'].notna().astype(int)

    # Make sure that there is one row per municipality (even if multiple areas intersect with one mun)
    intersections = intersections.groupby(['LocalMunicipalityCode'], as_index=False)[has_col].max()

    # join back to municipalities
    muns = muns.merge(intersections, on='LocalMunicipalityCode', how='left')
    muns[has_col] = muns[has_col].fillna(0).astype(int)

    # ---- 2. ADJACENCY (only for those WITHOUT overlap) ----

    area_muns = muns[muns[has_col] == 1][['geometry']]

    touching = gpd.sjoin(
        muns[['LocalMunicipalityCode', 'geometry']],
        area_muns,
        how='left',
        predicate='touches'
    )

    adj_col = f'adjacent_to_{name}'

    touching[adj_col] = touching['index_right'].notna().astype(int)
    touching = touching.groupby(['LocalMunicipalityCode'], as_index=False)[adj_col].max()

    muns = muns.merge(touching[['LocalMunicipalityCode', adj_col]], on='LocalMunicipalityCode', how='left')
    muns.loc[muns[has_col] == 1, adj_col] = 0

    return muns
