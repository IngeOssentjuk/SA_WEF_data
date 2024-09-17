import pandas as pd
import numpy as np
import geopandas as gpd
from pandas.io.stata import StataReader
import os
from spatial_data import PR_CE11, DC_CE11, MN_CE11

input_data = "C:/Github/SA_WEF_dataset/raw_data/CE_2011/2011_individual_entries"

# INDIVIDUAL ENTRIES DATA
# census_2011_agri_hh = pd.read_stata(os.path.join(input_data, "sa-census-2011-agricultural-households-v1-20151104.dta"))
# census_2011_hh = pd.read_stata(os.path.join(input_data, "sa-census-2011-household-v1.1-20140618.dta"))
# census_2011_mort = pd.read_stata(os.path.join(input_data, "sa-census-2011-mortality-v1.1-20140618.dta"))
# census_2011_pp_6to9 = pd.read_stata(os.path.join(input_data, "sa-census-2011-person-prov-6to9-v1.2-20150825.dta"))

# # because there is a non-unique label in the person datasets for the first five provinces:
# # Step 1: Read the data without converting categoricals
# census_2011_pp_1to5 = pd.read_stata(os.path.join(input_data, "sa-census-2011-person-prov-1to5-v1.2-20150825.dta"),
#                                     convert_categoricals=False)
#
# # Step 2: Use StataReader to read the value labels
# with StataReader(os.path.join(input_data, "sa-census-2011-person-prov-1to5-v1.2-20150825.dta")) as reader:
#     value_labels = reader.value_labels()
#
# # Step 3: Extract the specific value labels for the problematic column
# edu_field_labels = value_labels.get('P21_EDUFIELD', {})
#
# # Step 4: Inspect the value labels for duplicates
# print("Original value labels:", edu_field_labels)
#
# # Inspect the value labels for the column with issues
# print(value_labels['P21_EDUFIELD'])
#
# # Handle duplicate labels (if necessary)
# # Append numeric code to duplicate labels to make them unique
# processed_edu_field_labels = {}
# seen_labels = set()
# for code, label in edu_field_labels.items():
#     if label in seen_labels:
#         new_label = f"{label}_{code}"
#         processed_edu_field_labels[code] = new_label
#     else:
#         processed_edu_field_labels[code] = label
#         seen_labels.add(label)
#
# print("Processed value labels:", processed_edu_field_labels)
#
# # Step 5: Map the labels to the DataFrame column
# census_2011_pp_1to5['P21_EDUFIELD_LABELS'] = census_2011_pp_1to5['P21_EDUFIELD'].map(processed_edu_field_labels)

# # Convert all datasets to csv files
#
# census_2011_agri_hh.to_csv("census_2011_agri_hh.csv")
# census_2011_hh.to_csv("census_2011_hh.csv")
# census_2011_mort.to_csv("census_2011_mort.csv")
# census_2011_pp_1to5.to_csv("census_2011_pp_1to5.csv")
# census_2011_pp_6to9.to_csv("census_2011_pp_6to9.csv")

# print(census_2011_agri_hh.columns.values.tolist())
# print(census_2011_hh.columns.values.tolist())
# print(census_2011_mort.columns.values.tolist())
# print(census_2011_pp_1to5.columns.values.tolist())
# print(census_2011_pp_6to9.columns.values.tolist())

# Set Pandas to raise an exception on chained assignment
pd.set_option('mode.chained_assignment', 'raise')

# load household data
census_2011_hh = pd.read_stata(os.path.join(input_data, "sa-census-2011-household-v1.1-20140618.dta"))

# rename columns to match spatial data columns
census_data_spatial_columns = {'H_PROVINCE': 'PR_NAME', 'H_DISTRICT': 'DC_NAME', 'H_MUNIC': 'MN_NAME'}
census_2011_hh.rename(columns=census_data_spatial_columns, inplace=True)


def labels_to_columns(dataset_name: pd.DataFrame, column_name: str, selected_spatial_column: str):

    dataset = dataset_name

    selected_data = dataset[[selected_spatial_column, column_name]]

    category_columns = pd.get_dummies(selected_data[column_name], prefix=column_name)
    column_list = category_columns.columns.values.tolist()

    appended_dataframe = pd.concat([selected_data[selected_spatial_column], category_columns], axis=1)

    return appended_dataframe, column_list


def prepare_household_data(dataset: pd.DataFrame, spatial_data: dict, spatial_level: str) -> pd.DataFrame:

    # obtain spatial data based on chosen spatial level code
    spatial_dataset = eval(f'{spatial_level}')
    spatial_column_name = spatial_data[spatial_level]
    spatial_dataset = spatial_dataset[[spatial_column_name, 'geometry']]
    spatial_dataset.loc[:, spatial_column_name] = (spatial_dataset[spatial_column_name].str.lower())

    # group data based on chosen spatial level code
    grouped_dataset = dataset.groupby(spatial_column_name, as_index=False, observed=True).sum()

    # set all categorical names to lowercase for consistency between (spatial) datasets
    grouped_dataset[spatial_column_name] = grouped_dataset[spatial_column_name].cat.rename_categories(lambda x: x.lower())

    # merge spatial data to dataset based on chosen spatial level code
    grouped_dataset = pd.merge(spatial_dataset, grouped_dataset, on=spatial_column_name)

    return grouped_dataset


def obtain_shares(dataset, dataset_name, column_list):
    # calculate total number of counts per question based on column names corresponding to the answers
    # TODO check whether to include or exclude unspecified / not applicable in total (or no access)
    dataset[f'{dataset_name}_total'] = dataset[column_list].sum(axis=1)

    # TODO check whether to exclude certain categories for % calculation
    for column in column_list:
        dataset[f'{column}_%'] = dataset[column] / dataset[f'{dataset_name}_total']

    return dataset


spatial_data_columns = {"PR_CE11": "PR_NAME", "DC_CE11": "DC_NAME", "MN_CE11": "MN_NAME"}

for spatial_level in ['PR_CE11', 'DC_CE11', 'MN_CE11']:

    selected_spatial_column = spatial_data_columns[spatial_level]
    combined_dataset = pd.DataFrame()

    for dataset_name in ['H07_WATERPIPED', 'H08_WATERSOURCE', 'H09_WATERSUPPLY', 'H09A_WATERSUPPLY', 'H09B_ALT_WATERSOURCE',
                    'H11_ENERGY_COOKING', 'H11_ENERGY_HEATING', 'H11_ENERGY_LIGHTING']:

        results = labels_to_columns(census_2011_hh, column_name=dataset_name, selected_spatial_column=selected_spatial_column)
        dataset = results[0]
        column_list = results[1]

        dataset = prepare_household_data(dataset, spatial_data_columns, spatial_level)

        dataset = obtain_shares(dataset, dataset_name, column_list)

        if combined_dataset.empty:
            combined_dataset = dataset
        else:
            columns_to_merge = dataset.columns.difference(combined_dataset.columns).tolist()
            columns_to_merge.insert(0, selected_spatial_column)
            combined_dataset = pd.merge(combined_dataset, dataset[columns_to_merge],
                                        on=selected_spatial_column)

    spatial_label = spatial_level.rstrip('_CE11')
    file_name = f'CE11_dataset_{spatial_label}.csv'
    folder_path = r'C:/Github/SA_WEF_dataset/datasets_prelim'
    combined_dataset.to_csv(os.path.join(folder_path, file_name))