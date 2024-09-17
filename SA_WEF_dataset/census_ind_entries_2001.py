import pandas as pd
import geopandas as gpd
from pandas.io.stata import StataReader
import os

input_data = "C:/Github/SA_WEF_dataset/raw_data/CE_2001"

census_2001_mort = pd.read_stata(os.path.join(input_data, "SA Census 2001 Mortality_v1.dta"))

# because there is a non-unique label in the municipal codes:
# Step 1: Read the data without converting categoricals
census_2001_ind = pd.read_stata(os.path.join(input_data, "SA Census 2001 Person_v1.1_20111024.dta"),
                                convert_categoricals=False)
census_2001_hh = pd.read_stata(os.path.join(input_data, "SA Census 2001 Hhold_v1.1_20111024.dta"),
                               convert_categoricals=False)

# Step 2: Use StataReader to read the value labels
for file in ["SA Census 2001 Person_v1.1_20111024.dta", "SA Census 2001 Hhold_v1.1_20111024.dta"]:
    with StataReader(os.path.join(input_data, file)) as reader:
        value_labels = reader.value_labels()
        print(value_labels.items())

# Step 3: Extract the specific value labels for the problematic column
non_unique_labels = value_labels.get('munic_co', {})

# Step 4: Inspect the value labels for duplicates
print("Original value labels:", non_unique_labels)

# Inspect the value labels for the column with issues
print(value_labels['munic_co'])

# Handle duplicate labels (if necessary)
# Example: Append numeric code to duplicate labels to make them unique
unique_labels = {}
seen_labels = set()
for code, label in non_unique_labels.items():
    if label in seen_labels:
        new_label = f"{label}_{code}"  # or any other way to make it unique
        unique_labels[code] = new_label
    else:
        unique_labels[code] = label
        seen_labels.add(label)

print("Processed value labels:", unique_labels)

# Step 5: Map the labels to the DataFrame column
census_2001_ind['munic_co'] = census_2001_ind['munic_co'].map(unique_labels)
census_2001_hh['munic_co'] = census_2001_hh['munic_co'].map(unique_labels)
census_2001_hh.explore()

# column "p11a_pur" > "usual main place" = main place level. but only if Q in column "p11_4ngt" is 1 / yes.