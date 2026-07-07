import pandas as pd
import glob
import os
from src.data_processing_mapping import load_spatial_data_gdb

# Folder containing the CSV files with population data
input_dir = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/raw/"
output_dir = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/processed/"
output_file_name_muns = "Municipal_households_rural_urban_2016.csv"
output_file_name_dist = "District_households_rural_urban_2016.csv"

# Get a list of all relevant CSV files
csv_files = glob.glob(os.path.join(input_dir, "Municipal household data (rural-urban)/Total Households_*.csv"))

# Initialize an empty list to store dataframes
dataframes = []

# Load each CSV file
for file in csv_files:
    try:
        # Read the file using 'latin1' encoding
        df = pd.read_csv(file, encoding="latin1", engine="python", skipfooter=1)

        # Clean up non-breaking spaces and thousand-separators (space) in numeric columns:
        for col in df.columns:
            if df[col].dtype == "object" and col not in ["Region", "Time Frame"]:
                df[col] = (
                    df[col]
                    .str.replace("\xa0", "", regex=False)
                    .str.replace("ï¿½", "", regex=False)
                    .str.replace(" ", "", regex=False)
                )

        # Append the cleaned DataFrame to the list
        dataframes.append(df)

    except Exception as e:
        print(f"Error reading {file}: {e}")


# Concatenate all DataFrames into one
merged_df = pd.concat(dataframes, ignore_index=True)
# Drop unnamed columns & time frame column
merged_df = merged_df.loc[:, ~merged_df.columns.str.contains("Unnamed")]
merged_df = merged_df.loc[:, ~merged_df.columns.str.contains("Time Frame")]
# Normalize column names
merged_df.columns = (
    merged_df.columns
    .str.strip()
)

# Convert all numeric-looking columns to numeric
for col in merged_df.columns:
    if col not in ["Region"]:
        merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

merged_df = merged_df.drop_duplicates()

# Remove spaces at end of region names for correct merging:
merged_df['Region'] = merged_df['Region'].str.rstrip()

# Calculate shares of households that are rural and urban:
merged_df['Urban_share_hh'] = merged_df['Urban Households'] / merged_df['Total Households']
merged_df['Rural_share_hh'] = merged_df['Rural Households'] / merged_df['Total Households']

## Adding spatial demarcations:

# obtain municipal demarcations:
MUN_boundaries_16 = load_spatial_data_gdb('MN', 2016, input_dir)
MUN_boundaries_16.loc[:, 'LocalMunicipalityName'] = MUN_boundaries_16['LocalMunicipalityName'].replace('New', 'Collins Chabane')

district_muns = MUN_boundaries_16[['DistrictMunicipalityCode', 'DistrictMunicipalityName']]
district_muns = district_muns.drop_duplicates()
district_mun_mapping = {'Buffalo City Metropolitan Municipality': 'Buffalo City',
                        'City of Cape Town Metropolitan Municipality': 'City of Cape Town', 'OR Tambo': 'O.R.Tambo',
                        'Thabo Mofutsanyana': 'Thabo Mofutsanyane', 'King Cetshwayo': 'Uthungulu',
                        'Bojanala Platinum': 'Bojanala', 'Harry Gwala': 'Sisonke', 'ZF Mgcawu': 'Z F Mgcawu',
                        'Ekurhuleni Metropolitan Municipality': 'Ekurhuleni',
                        'Ethekwini Metropolitan Municipality': 'eThekwini',
                        'City of Johannesburg Metropolitan Municipality': 'City of Johannesburg',
                        'Mangaung Metropolitan Municipality': 'Mangaung',
                        'Nelson Mandela Bay Metropolitan Municipality': 'Nelson Mandela Bay',
                        'City of Tshwane Metropolitan Municipality': 'City of Tshwane'}

# To add the municipal demarcation codes we merge with a datafile with the mapping of the 2016 local municipality names
# used in this dataset to the municipality codes (which avoids differences in spelling of names across datasets).
MUN_changes_11_16 = pd.read_csv(os.path.join(output_dir + "municipal_demarcations_mapping_20112016.csv"), delimiter=';', encoding="latin1")
MUN_changes_11_16 = MUN_changes_11_16[['DWS_2016', 'LocalMunicipalityName', 'LocalMunicipalityCode']]
MUN_changes_11_16 = MUN_changes_11_16.drop_duplicates(subset=['DWS_2016'], keep='first')

# merge
district_data = merged_df.copy()
district_data['Region'] = district_data['Region'].replace(district_mun_mapping)
district_hh = district_muns.merge(district_data, left_on='DistrictMunicipalityName', right_on='Region', how='left')
merged_df = merged_df.replace({'Dr Beyers Naudé': 'Dr Beyers Naudï¿½'})
muns_hh = merged_df.merge(MUN_changes_11_16, left_on='Region', right_on='DWS_2016', how='right')

# clean up files:
muns_hh = muns_hh.drop(columns=['DWS_2016', 'Region'])
district_hh = district_hh.drop(columns=['Region'])
muns_hh = muns_hh[['LocalMunicipalityCode', 'LocalMunicipalityName'] + [col for col in muns_hh.columns if col not in ['LocalMunicipalityCode', 'LocalMunicipalityName']]]

# Save the cleaned DataFrame to a file (optional)
muns_hh.to_csv(os.path.join(output_dir + output_file_name_muns), index=False)
district_hh.to_csv(os.path.join(output_dir + output_file_name_dist), index=False)
