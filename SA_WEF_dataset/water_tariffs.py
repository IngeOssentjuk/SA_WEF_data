import pandas as pd
import glob
import os
import numpy as np
import geopandas as gpd
import fiona

# Method for loading data from a geodatabase file:
def load_spatial_data_gdb(spatial_abbrev: str, year: int, input_dir: str):
    # go to file based on function input
    gdb_path = os.path.join(input_dir, f"spatial_data/{year}/{spatial_abbrev}.gdb")
    gdb_path = os.path.normpath(gdb_path)
    # See if there are multiple layers, for each layer, return a spatial df
    for feature_class in fiona.listlayers(gdb_path):
        spatial_df = gpd.read_file(filename=gdb_path, layer=feature_class)
        return spatial_df

# Folder containing the CSV files with water tariff data
input_dir = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data"
output_dir = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/processed/"
output_file_name_muns = "Municipal_water_tariffs_2011_16_19_22.csv"
output_file_name_dist = "District_water_tariffs_2011_16_19_22.csv"

# Get a list of all relevant CSV files
csv_files = glob.glob(os.path.join(input_dir + "/raw/Water_tariffs_2011_2016_2019/Residential Tariffs_*.csv"))

# Initialize an empty list to store dataframes
dataframes = []

# Load each CSV file
for file in csv_files:
    try:
        # Read the file using 'latin1' encoding
        df = pd.read_csv(file, encoding="latin1", engine="python", skipfooter=1)

        # Clean up the column values
        for col in df.columns:
            # In the column Time Frame remove the space as a thousand separator in year values
            if df[col].dtype == "object" and col == "Time Frame":  # Only process object (string) columns
                df[col] = df[col].str.replace('\xa0', '', regex=False).str.replace(' ', '')
            # in the tariff columns, remove the currency sign (R) in front of value, and replace decimal comma with
            # decimal point
            elif col.startswith('Tariff'):
                df[col] = df[col].str.replace('R', '', regex=True).str.replace(',', '.', regex=True)

        # Append the cleaned DataFrame to the list
        dataframes.append(df)
    except Exception as e:
        print(f"Error reading {file}: {e}")

# Concatenate all DataFrames into one
merged_df = pd.concat(dataframes, ignore_index=True)
nan_columns = merged_df.columns[merged_df.columns.str.contains("Unnamed")]
merged_df.drop(labels=nan_columns, axis=1, inplace=True)
merged_df['Time Frame'] = merged_df['Time Frame'].replace({'2ï¿½011':'2011', '2ï¿½016':'2016', '2ï¿½019':'2019'})

# Pivot the data to create separate columns for 2011, 2016 and 2019 data:
pivoted_df = merged_df.pivot_table(
    index=["Region"],
    columns="Time Frame",
    aggfunc="first"  # Avoid summing or concatenating; take the first value
).reset_index()  # Reset the index to keep Code and Region as separate columns

# Flatten the multi-level columns
pivoted_df.columns = [
    f"{col[0]}_{col[1]}" if col[1] else col[0]
    for col in pivoted_df.columns
]

# Ensure numeric conversion for all relevant columns (make sure population values are seen as numbers to allow
# for summing)
for col in pivoted_df.columns:
    if "Region" not in col:  # Skip non-numeric columns
        pivoted_df[col] = pd.to_numeric(pivoted_df[col], errors="coerce")  # Convert to numeric, coercing errors to NaN

# We now have a dataframe with 2011, 2016 and 2019 values for the different tariff blocks.

for tariff_block in [
    'Tariff 0-6kl (incl#VAT)',
    'Tariff 6-20kl (incl#VAT)',
    'Tariff 20-60kl (incl#VAT)',
    'Tariff >60kl (incl#VAT)'
]:
    # shorter column names for clarity:
    col11 = f'{tariff_block}_2011'
    col16 = f'{tariff_block}_2016'
    col19 = f'{tariff_block}_2019'
    col22 = f'{tariff_block}_2022'

    # 0. Compute mean exponential growth rates for subperiods
    # 0.1. obtain masks for rows of data for which there are valid values for the years of interest:
    valid_11_16 = (pivoted_df[col11] > 0) & (pivoted_df[col16] > 0)
    valid_16_19 = (pivoted_df[col16] > 0) & (pivoted_df[col19] > 0)
    valid_11_19 = (pivoted_df[col11] > 0) & (pivoted_df[col19] > 0)

    # 0.2. calculate the rate of change for each year combination (2011-2016, 2016-2019, 2011-2019) per municipality
    rate_11_16 = (pivoted_df.loc[valid_11_16, col16] / pivoted_df.loc[valid_11_16, col11]) ** (1 / (2016-2011))
    rate_16_19 = (pivoted_df.loc[valid_16_19, col19] / pivoted_df.loc[valid_16_19, col16]) ** (1 / (2019-2016))
    rate_11_19 = (pivoted_df.loc[valid_11_19, col19] / pivoted_df.loc[valid_11_19, col11]) ** (1 / (2019-2011))

    # 0.3. calculate the mean rate of change for each year combination (2011-2016, 2016-2019, 2011-2019) across all
    # municipalities (with relevant values):
    mean_rate_11_16 = rate_11_16[np.isfinite(rate_11_16)].mean()
    mean_rate_16_19 = rate_16_19[np.isfinite(rate_16_19)].mean()
    mean_rate_11_19 = rate_11_19[np.isfinite(rate_11_19)].mean()

    # IMPUTE MISSING VALUES:
    # 1. Handle all-zero or all-missing rows ---
    all_zero_or_missing = pivoted_df[[col11, col16, col19]].fillna(0).eq(0).all(axis=1)
    pivoted_df.loc[all_zero_or_missing, [col11, col16, col19]] = 0

    # 2: Interpolate/extrapolate missing values from years in dataset (2011,2016,2019)

    # 2.1. Fill for 2011 missing but 2016 & 2019 available:
    mask_11_missing = pivoted_df[col11].isna() & pivoted_df[col16].notna() & pivoted_df[col19].notna() & (pivoted_df[col16] > 0) & (pivoted_df[col19] > 0)
    R_16_19 = (pivoted_df.loc[mask_11_missing, col19] / pivoted_df.loc[mask_11_missing, col16]) ** (1 / (2019-2016))
    pivoted_df.loc[mask_11_missing, col11] = pivoted_df.loc[mask_11_missing, col16] / (R_16_19 ** (2016-2011))

    # 2.2. Fill for 2016 missing but 2011 & 2019 available
    mask_16_missing = pivoted_df[col16].isna() & pivoted_df[col11].notna() & pivoted_df[col19].notna() & (pivoted_df[col11] > 0) & (pivoted_df[col19] > 0)
    R_11_19 = (pivoted_df.loc[mask_16_missing, col19] / pivoted_df.loc[mask_16_missing, col11]) ** (1 / (2019-2011))
    pivoted_df.loc[mask_16_missing, col16] = pivoted_df.loc[mask_16_missing, col11] * (R_11_19 ** (2016-2011))

    # 2.3. Fill for 2019 missing but 2011 & 2016 available
    mask_19_missing = pivoted_df[col19].isna() & pivoted_df[col11].notna() & pivoted_df[col16].notna() & (pivoted_df[col11] > 0) & (pivoted_df[col16] > 0)
    R_11_16 = (pivoted_df.loc[mask_19_missing, col16] / pivoted_df.loc[mask_19_missing, col11]) ** (1 / (2016-2011))
    pivoted_df.loc[mask_19_missing, col19] = pivoted_df.loc[mask_19_missing, col16] * (R_11_16 ** (2019-2016))

    # 2.4. If only one year available → extrapolate using mean rates
    # 2.4.1. only 2011 known
    mask_only_11 = pivoted_df[col11].notna() & pivoted_df[col16].isna() & pivoted_df[col19].isna() & (pivoted_df[col11] > 0)
    pivoted_df.loc[mask_only_11, col16] = pivoted_df.loc[mask_only_11, col11] * (mean_rate_11_16 ** (2016-2011))
    pivoted_df.loc[mask_only_11, col19] = pivoted_df.loc[mask_only_11, col16] * (mean_rate_16_19 ** (2019-2016))

    # 2.4.2. only 2016 known
    mask_only_16 = pivoted_df[col11].isna() & pivoted_df[col16].notna() & pivoted_df[col19].isna() & (pivoted_df[col16] > 0)
    pivoted_df.loc[mask_only_16, col11] = pivoted_df.loc[mask_only_16, col16] / (mean_rate_11_16 ** (2016-2011))
    pivoted_df.loc[mask_only_16, col19] = pivoted_df.loc[mask_only_16, col16] * (mean_rate_16_19 ** (2019-2016))

    # 2.4.3. only 2019 known
    mask_only_19 = pivoted_df[col11].isna() & pivoted_df[col16].isna() & pivoted_df[col19].notna() & (pivoted_df[col19] > 0)
    pivoted_df.loc[mask_only_19, col16] = pivoted_df.loc[mask_only_19, col19] / (mean_rate_16_19 ** (2019-2016))
    pivoted_df.loc[mask_only_19, col11] = pivoted_df.loc[mask_only_19, col16] / (mean_rate_11_16 ** (2016-2011))

    # 2.5. Handle zeros: if any year is 0 and another is missing → fill with 0
    zero_any = (pivoted_df[[col11, col16, col19]] == 0).any(axis=1)
    # Only fill the NaN values within those rows
    pivoted_df.loc[zero_any, [col11, col16, col19]] = (pivoted_df.loc[zero_any, [col11, col16, col19]].where(pivoted_df.loc[zero_any, [col11, col16, col19]].notna(), 0))

    # 3. Extrapolate to 2022
    # Step 3 simplified: extrapolate 2022 from 2016-2019
    R_16_19 = (pivoted_df[col19] / pivoted_df[col16]) ** (1 / (2019-2016))
    pivoted_df[col22] = pivoted_df[col19] * (R_16_19 ** (2022-2019))

    # 3.3. Zeros propagate
    pivoted_df.loc[pivoted_df[col19] == 0, col22] = 0

### Adding spatial demarcations:
MUN_boundaries_16 = load_spatial_data_gdb('MN', 2016, os.path.join(input_dir + "/raw/"))  # the relevant columns are called "LocalMunicipalityName" and "LocalMunicipalityCode"
MUN_boundaries_16.loc[:, 'LocalMunicipalityName'] = MUN_boundaries_16['LocalMunicipalityName'].replace('New', 'Collins Chabane')

district_muns = MUN_boundaries_16[['DistrictMunicipalityCode', 'DistrictMunicipalityName']]
district_muns = district_muns.groupby('DistrictMunicipalityCode').first()
district_tariffs = district_muns.merge(pivoted_df, left_on='DistrictMunicipalityName', right_on='Region', how='inner')

# To add the municipal demarcation codes we merge with a datafile with the mapping of the 2016 local municipality names
# used in this dataset to the municipality codes (which avoids differences in spelling of names across datasets).
MUN_changes_11_16 = pd.read_csv(os.path.join(input_dir + "/processed/municipal_demarcations_mapping_20112016.csv"), delimiter=';', encoding="latin1")
MUN_changes_11_16 = MUN_changes_11_16[['DWS_2016', 'LocalMunicipalityName', 'LocalMunicipalityCode']]
MUN_changes_11_16 = MUN_changes_11_16.drop_duplicates(subset=['DWS_2016'], keep='first')

pivoted_df['Region'] = pivoted_df['Region'].str.strip()
mun_tariffs = pivoted_df.merge(MUN_changes_11_16, left_on='Region', right_on='DWS_2016', how='right')
mun_tariffs = mun_tariffs.drop(columns=['Region', 'DWS_2016'])

# start dataset with spatial information
mun_tariffs = mun_tariffs[
    ['LocalMunicipalityName', 'LocalMunicipalityCode'] +
    [col for col in mun_tariffs.columns if col not in ['LocalMunicipalityName', 'LocalMunicipalityCode']]]

# Save the cleaned DataFrame to a file (optional)
district_tariffs.to_csv(os.path.join(output_dir + output_file_name_dist), index=False)
mun_tariffs.to_csv(os.path.join(output_dir + output_file_name_muns), index=False)