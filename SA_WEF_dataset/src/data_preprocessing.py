import pandas as pd
import numpy as np
import os
from typing import Optional


def load_stata_files(path, file_name):
    file = os.path.join(path, f'{file_name}')
    df = pd.read_stata(file)
    df_metadata = pd.read_stata(os.path.join(path, f'{file_name}'), iterator=True)
    df_var_labels = df_metadata.variable_labels()
    # df_val_labels = df_metadata.value_labels()

    return df, df_var_labels


def load_csv_files(path, file_name):
    df = pd.read_csv(os.path.join(path, f'{file_name}'), encoding='latin-1')
    return df


def extract_relevant_columns_census_data(dataframe, column_list, columns_for_calc):
    column_list.extend(columns_for_calc)
    df_reqs = dataframe[column_list]
    return df_reqs


def reform_w_access_vars_to_census_var(df):
    """
    a function to combine the 2016 community survey variables of WaterSource and DistanceWater into a variable similar
    to the WATERPIPED variable in the census surveys (2011 and 2022).
    :param df:
    :return:
    """

    census_options = ['No access to piped (tap) water',
                      'Piped (tap) water inside the dwelling',
                      'Piped (tap) water inside the yard',
                      'Piped (tap) water on community stand: distance less than 200m from dwelling',
                      'Piped (tap) water to community stand: distance less than 200m and 500m from dwelling',
                      'Piped (tap) water to community stand: distance less than 500m and 1000m from dwelling',
                      'Piped (tap) water on community stand: distance greater than 1000m (1 km) from dwelling']

    water_not_piped = ['Borehole in the yard', 'Borehole outside the yard', 'Flowing water/stream/river',
                       'Other', 'Rain-water tank in yard', 'Spring', 'Water-carrier/tanker', 'Well']

    water_piped_other = ['Neighbours tap', 'Piped water on community stand', 'Public/communal tap']

    w_not_piped_mask = (df['WaterSource'].isin(water_not_piped))
    w_piped_dwelling_mask = (df['WaterSource'].isin(['Piped (tap) water inside the dwelling/house']))
    w_piped_yard_mask = (df['WaterSource'].isin(['Piped (tap) water inside yard']))
    w_piped_distance_200m_mask = ((df['WaterSource'].isin(water_piped_other)) &
                                  (df['DistanceWater'].isin(['Less than 200 metres'])))
    w_piped_distance_200_500m_mask = ((df['WaterSource'].isin(water_piped_other)) &
                                  (df['DistanceWater'].isin(['201-500 metres'])))
    w_piped_distance_500_1000m_mask = ((df['WaterSource'].isin(water_piped_other)) &
                                  (df['DistanceWater'].isin(['501 metres-1 kilometre'])))
    w_piped_distance_gt_1000m_mask = ((df['WaterSource'].isin(water_piped_other)) &
                                  (df['DistanceWater'].isin(['More than 1 kilometre', 'Unspecified', 'Do not know'])))

    # assign census variable names to new column "WATERPIPED" in community survey dataset based on answers
    df.loc[w_not_piped_mask, 'WATERPIPED'] = census_options[0]
    df.loc[w_piped_dwelling_mask, 'WATERPIPED'] = census_options[1]
    df.loc[w_piped_yard_mask, 'WATERPIPED'] = census_options[2]
    df.loc[w_piped_distance_200m_mask, 'WATERPIPED'] = census_options[3]
    df.loc[w_piped_distance_200_500m_mask, 'WATERPIPED'] = census_options[4]
    df.loc[w_piped_distance_500_1000m_mask, 'WATERPIPED'] = census_options[5]
    df.loc[w_piped_distance_gt_1000m_mask, 'WATERPIPED'] = census_options[6]

    return df


def create_proxy_income_column(df: pd.DataFrame, income_column: str, income_proxy_list: list) -> pd.DataFrame:
    # derive the income classes from the dataframe
    income_classes = list(df[income_column].cat.categories)
    # create dictionary with income classes as keys and the proxy for each class as value
    income_conversion = dict(zip(income_classes, income_proxy_list))

    # remove entries for which there is no income class specified
    df = df.drop(df[df[income_column] == 'Unspecified'].index)

    # create a new column with the proxy income for each income class
    df['HH_INCOME_PROXY_2011'] = df[income_column].map(income_conversion)

    return df


def extrapolate_income(df: pd.DataFrame, annual_growth_rate: float, year: int):

    income_col = df['HH_INCOME_PROXY_2011']

    # based on Income_new = income_old * (1 + growth_rate) ** (delta_t)
    df[f'HH_INCOME_PROXY_{year}'] = income_col * (1 + annual_growth_rate) ** (year - 2011)

    return df


def calculate_hh_reqs(df, requirements_dict):
    """
    Calculates required resources per household based on required_resources_per_person * household_size.
    :param df:
    :param requirements_dict:
    :return:
    """
    df = df.copy()

    # General cost calculation for all resources except water
    for key, req_per_person in requirements_dict.items():
        resource = key.split('_')[0]  # Correctly extracts 'W', 'E', 'F'
        amount = key.split('_')[2]
        req_col = f'HH_{resource}_REQS_{amount}'
        df[req_col] = df['DERH_HSIZE'].astype(float) * float(req_per_person)
        df[req_col] = df[req_col].astype('int64')

    return df


def calculate_hh_costs(df, price_dict, free_basic_electricity=None):
    """
    Calculates household resource costs given requirements and resource prices.
    Handles special case for food (same reqs, different prices in 2022).
    """

    df = df.copy()

    for price_key, price_value in price_dict.items():
        # Example price_key: 'E_price_2011', 'F_price_2022_low'
        parts = price_key.split('_')
        resource = parts[0]  # E, F, W
        year = parts[2]  # e.g. "2011" or "2022"

        if len(parts) == 4:  # low/high prices in 2022
            amount = parts[3]  # "low" or "high"
            req_col = f"HH_{resource}_REQS_{amount}"
            cost_col = f"HH_{resource}_COST_{amount}_{year}"

            if free_basic_electricity == 'Yes' and resource == 'E':
                df[cost_col] = df[req_col] * float(price_value)
                df[f"HH_{resource}_COST_{amount}_FBE_{year}"] = (df[req_col] - (50*12)) * float(price_value) # monthly per household 50 kWh uncharged
            else:
                df[cost_col] = df[req_col] * float(price_value)

        else:
            # Always two requirement columns (low, high)
            for amount in ["low", "high"]:
                req_col = f"HH_{resource}_REQS_{amount}"
                if req_col in df.columns:

                    cost_col = f"HH_{resource}_COST_{amount}_{year}"

                    if free_basic_electricity == 'Yes' and resource == 'E':
                        df[cost_col] = df[req_col] * float(price_value)
                        df[f'{req_col}_minus_FBE'] = (df[req_col] - (50 * 12)).clip(lower=0) # monthly per household 50 kWh uncharged
                        df[f"HH_{resource}_COST_{amount}_FBE_{year}"] = df[f'{req_col}_minus_FBE'] * float(price_value)
                    else:
                        df[cost_col] = df[req_col] * float(price_value)

    return df


def calculate_w_costs_mun_block_tariffs(df, block_tariffs_df, year, free_basic_water=None):

    # Merge with tariff data using corrected municipality names
    df = df.merge(block_tariffs_df, on='LocalMunicipalityCode', how='left')

    # Compute water cost using block tariffs
    block_limits = np.array([6, 20, 60]) * 12

    for year in [2011, year]:

        tariffs = [
            df[f'Tariff 0-6kl (incl#VAT)_{year}'],
            df[f'Tariff 6-20kl (incl#VAT)_{year}'],
            df[f'Tariff 20-60kl (incl#VAT)_{year}'],
            df[f'Tariff >60kl (incl#VAT)_{year}']
        ]

        for water_requirements in ['high', 'low']:

            water_cost = np.zeros(len(df))
            remaining_water = df[f'HH_W_REQS_{water_requirements}'].copy()

            previous_limit = 0
            for i, limit in enumerate(block_limits):
                in_block = remaining_water > 0
                volume = np.minimum(remaining_water, limit - previous_limit) * in_block
                water_cost += volume * tariffs[i]
                remaining_water -= volume
                previous_limit = limit

            excess_usage = remaining_water > 0
            water_cost += excess_usage * remaining_water * tariffs[-1]

            df[f'HH_W_COST_{water_requirements}_{year}'] = water_cost


    if free_basic_water == 'Yes':
        first_tariff_cols = [col for col in df.columns if '0-6kl' in col]
        for col in first_tariff_cols:
            df[col] = 0

        for year in [2011, year]:

            tariffs = [
                df[f'Tariff 0-6kl (incl#VAT)_{year}'],
                df[f'Tariff 6-20kl (incl#VAT)_{year}'],
                df[f'Tariff 20-60kl (incl#VAT)_{year}'],
                df[f'Tariff >60kl (incl#VAT)_{year}']
            ]

            for water_requirements in ['high', 'low']:

                water_cost = np.zeros(len(df))
                remaining_water = df[f'HH_W_REQS_{water_requirements}'].copy()

                previous_limit = 0
                for i, limit in enumerate(block_limits):
                    in_block = remaining_water > 0
                    volume = np.minimum(remaining_water, limit - previous_limit) * in_block
                    water_cost += volume * tariffs[i]
                    remaining_water -= volume
                    previous_limit = limit

                excess_usage = remaining_water > 0
                water_cost += excess_usage * remaining_water * tariffs[-1]

                df[f'HH_W_COST_{water_requirements}_FBW_{year}'] = water_cost

    else:
        pass

    return df


def categorize_water_quality_compliance_scores(df, col, thresholds):

    # Population masks: for populations below 100,000 and above 100,000, different conversions from % into category are
    # used by DWS (in their Blue Drop Report).
    low_mask = df["Population_2023"] < 100000
    high_mask = ~low_mask  # opposite

    # fill in "unacceptable" as default value (for all values from 0% until the first threshold).
    result = np.full(len(df), "Unacceptable", dtype=object)  # default

    # --- Low population rules ---
    # Assign categories based on respective thresholds:
    result = np.where(
        low_mask & (df[col] >= thresholds["low_population"]["Excellent"]),
        "Excellent", result
    )
    result = np.where(
        low_mask & (df[col] >= thresholds["low_population"]["Good"]) & (df[col] < thresholds["low_population"]["Excellent"]),
        "Good", result
    )

    # --- High population rules ---
    # Assign categories based on respective thresholds:
    result = np.where(
        high_mask & (df[col] >= thresholds["high_population"]["Excellent"]),
        "Excellent", result
    )
    result = np.where(
        high_mask & (df[col] >= thresholds["high_population"]["Good"]) & (df[col] < thresholds["high_population"]["Excellent"]),
        "Good", result
    )

    return result

def extract_year(col):
    return col.split('_')[0] if '_' in col else None