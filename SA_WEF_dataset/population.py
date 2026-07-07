import pandas as pd
import glob
import os
import geopandas as gpd
import fiona
from collections import defaultdict

# Folder containing the CSV files with population data
input_dir = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/raw/"
output_dir = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/processed/"
output_file_name_muns = "Municipal_population_rural_urban_1994_2024.csv"
output_file_name_dist = "District_population_rural_urban_1994_2024.csv"

# Method for loading data from a geodatabase file:
def load_spatial_data_gdb(spatial_abbrev: str, year: int, input_dir: str):
    # go to file based on function input
    gdb_path = os.path.join(input_dir, f"spatial_data/{year}/{spatial_abbrev}.gdb")
    gdb_path = os.path.normpath(gdb_path)
    # See if there are multiple layers, for each layer, return a spatial df
    for feature_class in fiona.listlayers(gdb_path):
        spatial_df = gpd.read_file(filename=gdb_path, layer=feature_class)
        return spatial_df

# Get a list of all relevant CSV files
csv_files = glob.glob(os.path.join(input_dir, "Municipal population data (rural-urban)/Population Rural Urban_*.csv"))

# Initialize an empty list to store dataframes
dataframes = []

# Load each CSV file
for file in csv_files:
    try:
        # Read the file using 'latin1' encoding
        df = pd.read_csv(file, encoding="latin1", engine="python", skipfooter=1)

        # Clean up non-breaking spaces and thousand-separators (space) in numeric columns:
        for col in df.columns:
            if df[col].dtype == "object" and col not in ["Region", "Code", "Category"]:
                df[col] = (
                    df[col]
                    .str.replace("\xa0", "", regex=False)
                    .str.replace(" ", "", regex=False)
                )

        # Append the cleaned DataFrame to the list
        dataframes.append(df)

    except Exception as e:
        print(f"Error reading {file}: {e}")


# Concatenate all DataFrames into one
merged_df = pd.concat(dataframes, ignore_index=True)
# Drop unnamed columns
merged_df = merged_df.loc[:, ~merged_df.columns.str.contains("Unnamed")]
# Normalize column names
merged_df.columns = (
    merged_df.columns
    .str.strip()
    .str.replace(" Population", "", regex=False)
    .str.replace("population", "", regex=False)
)

# Convert all numeric-looking columns to numeric
for col in merged_df.columns:
    if col not in ["Code", "Region", "Category"]:
        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

# interpolate between 2002 and 2004 to account for missing 2003 value:
merged_df['2003'] = (merged_df['2002'] + merged_df['2004']) / 2
# sort so that 2003 value is in the correct place:
cols_order = ['Code', 'Region', 'Category'] + sorted(
    [c for c in merged_df.columns if c not in ['Code', 'Region', 'Category']],
    key=int
)
merged_df = merged_df[cols_order]

# Pivot the data to create separate columns for rural and urban populations
pivoted_df = merged_df.pivot_table(
    index=["Code", "Region"],
    columns="Category",
    aggfunc="first"  # Avoid summing or concatenating; take the first value
)

# Flatten the multi-level columns
pivoted_df.columns = [
    f"{col[0]}_{col[1]}" if col[1] else col[0]
    for col in pivoted_df.columns
]

pivoted_df = pivoted_df.reset_index()

# Add total population columns by summing rural and urban populations for each year
# identify year:
year_pattern = pivoted_df.columns.str.extract(r"(\d{4})")[0]
years = year_pattern.dropna().unique()

for year in years:
    rural_col = next((c for c in pivoted_df.columns if year in c and "Rural" in c), None)
    urban_col = next((c for c in pivoted_df.columns if year in c and "Urban" in c), None)

    if rural_col and urban_col:
        total_col = f"{year}_Total"

        pivoted_df[total_col] = (
            pivoted_df[rural_col].fillna(0) +
            pivoted_df[urban_col].fillna(0)
        )

        share_rural_col = f"{year}_share_rural"
        share_urban_col = f"{year}_share_urban"

        pivoted_df[share_rural_col] = pivoted_df[rural_col] / pivoted_df[total_col]
        pivoted_df[share_urban_col] = pivoted_df[urban_col] / pivoted_df[total_col]

        # If both are NaN, set total to NaN instead of 0
        both_nan = pivoted_df[[rural_col, urban_col]].isna().all(axis=1)
        pivoted_df.loc[both_nan, total_col] = pd.NA
        pivoted_df.loc[both_nan, share_rural_col] = pd.NA
        pivoted_df.loc[both_nan, share_urban_col] = pd.NA

pivoted_df['Region'] = pivoted_df['Region'].str.strip()

### Adding spatial demarcations:
MUN_boundaries_16 = load_spatial_data_gdb('MN', 2016, input_dir)  # the relevant columns are called "LocalMunicipalityName" and "LocalMunicipalityCode"
MUN_boundaries_16.loc[:, 'LocalMunicipalityName'] = MUN_boundaries_16['LocalMunicipalityName'].replace('New', 'Collins Chabane')

local_muns = MUN_boundaries_16[['LocalMunicipalityCode', 'LocalMunicipalityName']]
district_muns = MUN_boundaries_16[['DistrictMunicipalityCode', 'DistrictMunicipalityName']]
district_muns = district_muns.groupby('DistrictMunicipalityCode').first()

mun_pop = pivoted_df.merge(local_muns, left_on='Code', right_on='LocalMunicipalityCode', how='right')
mun_pop = mun_pop.drop(columns=['Code', 'Region'])
district_pop = pivoted_df.merge(district_muns, left_on='Code', right_on='DistrictMunicipalityCode', how='right')
district_pop = district_pop.drop(columns=['Region'])
district_pop = district_pop.rename(columns={'Code': 'DistrictMunicipalityCode'})

# start dataset with spatial information
mun_pop = mun_pop[
    ['LocalMunicipalityCode', 'LocalMunicipalityName'] +
    [col for col in mun_pop.columns if col not in ['LocalMunicipalityName', 'LocalMunicipalityCode']]]
district_pop = district_pop[
    ['DistrictMunicipalityCode', 'DistrictMunicipalityName'] +
    [col for col in district_pop.columns if col not in ['DistrictMunicipalityCode', 'DistrictMunicipalityName']]]

# Save the cleaned DataFrame to a file (optional)
mun_pop.to_csv(os.path.join(output_dir + output_file_name_muns), index=False)
district_pop.to_csv(os.path.join(output_dir + output_file_name_dist), index=False)