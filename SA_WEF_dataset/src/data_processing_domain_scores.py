import pandas as pd
import numpy as np
import re

# AVAILABILITY SCORES:

def obtain_w_availability_score(dataset: pd.DataFrame, threshold: str, thresholds_dict=None, min_val=None, max_val=None):

    df = dataset

    if threshold == 'linear_minmax':

        # Ensure min and max are valid
        if min_val is None or max_val is None:
            raise ValueError("For 'linear_minmax', you must provide both min_val and max_val.")

        slope = 1 / (max_val - min_val)
        intercept = - (slope * min_val)

        df['W_availability_linear_minmax'] = np.where(df['Q_total_cap_yr'] <= min_val, 0,
                                                   np.where(df['Q_total_cap_yr'] >= max_val, 1,
                                                            (slope * df['Q_total_cap_yr'] + intercept)))

    elif threshold == 'categorical':
        # Ensure thresholds are valid
        if thresholds_dict is None:
            raise ValueError("For 'categorical', you must provide a thresholds_dict.")

        df.loc[:, 'W_availability_categorical'] = df['Falkenmark_cat'].replace(thresholds_dict).infer_objects(copy=False)

    else:
        raise ValueError("Standardization threshold should be 'linear_minmax' or 'categorical'.")

    return df

def aggregate_indicators_into_score(df: pd.DataFrame, agg_column_name: str, columns: list, aggregation_method: str):

    # Water accessibility score is computed as the mean of the access to piped water and access to sanitation scores:
    if aggregation_method == 'mean':

        df[f'{agg_column_name}_{aggregation_method}'] = df[columns].mean(axis=1, skipna=True)

    # Water accessibility score is determined by the lowest score among the access to piped water and access to
    # sanitation variables:
    elif aggregation_method == 'limiting_factor':
        df[f'{agg_column_name}_{aggregation_method}'] = df[columns].min(axis=1, skipna=True)

    elif aggregation_method == 'maximum':
        df[f'{agg_column_name}_{aggregation_method}'] = df[columns].max(axis=1, skipna=True)

    return df


# ACCESSIBILITY SCORES:

def obtain_w_access_piped_score_hh(dataset: pd.DataFrame, standard: str, water_access_col: str):

    """
    Function to calculate the score for the "access to piped water" indicator, based on the variable of distance to
    piped water and different standards/thresholds (NS (no standard) - meaning that the distance category determines the score in
    linear fashion; RDP - based on the South African RDP regulation where piped water has to be within 200 metres of the
    household; WHO - based on the WHO standard for piped water, meaning it has to be within the dwelling (or yard)).
    :param dataset:
    :param standard:
    :param water_access_col:
    :return:
    """
    # Made for Census variables

    df = dataset

    on_site = ['Piped (tap) water inside the dwelling', 'Piped (tap) water inside the yard']
    within_200m = ['Piped (tap) water on community stand: distance less than 200m from dwelling']
    within_500m = ['Piped (tap) water to community stand: distance less than 200m and 500m from dwelling']
    within_1km = ['Piped (tap) water to community stand: distance less than 500m and 1000m from dwelling']
    beyond_1km = ['Piped (tap) water on community stand: distance greater than 1000m (1 km) from dwelling']
    no_access = ['No access to piped (tap) water']

    if standard == 'NS':

        # getting accessibility scores based on distance categories provided by Stats SA
        no_accessibility_mask = (df[water_access_col].isin(no_access))
        low_accessibility_mask = (df[water_access_col].isin(beyond_1km))
        moderately_low_accessibility_mask = (df[water_access_col].isin(within_1km))
        moderate_accessibility_mask = (df[water_access_col].isin(within_500m))
        moderately_high_accessibility_mask = (df[water_access_col].isin(within_200m))
        high_accessibility_mask = (df[water_access_col].isin(on_site))

        # Assigning values based on the masks
        df.loc[no_accessibility_mask, 'W_access_piped_NS'] = 0
        df.loc[low_accessibility_mask, 'W_access_piped_NS'] = 0.2
        df.loc[moderately_low_accessibility_mask, 'W_access_piped_NS'] = 0.4
        df.loc[moderate_accessibility_mask, 'W_access_piped_NS'] = 0.6
        df.loc[moderately_high_accessibility_mask, 'W_access_piped_NS'] = 0.8
        df.loc[high_accessibility_mask, 'W_access_piped_NS'] = 1

    elif standard == 'RDP':

        # the RDP standard is "within 200 metres from dwelling".

        # low accessibility (score 0) is then everything outside RDP standard (more than 200 metres from dwelling):
        low_accessibility_mask = (
            (df[water_access_col].isin(no_access)) | (df[water_access_col].isin(beyond_1km)) |
            (df[water_access_col].isin(within_1km)) | (df[water_access_col].isin(within_500m))
        )

        # high accessibility (score 1) adheres to RDP standard for distance (within 200 metres from dwelling)
        high_accessibility_mask = (
            (df[water_access_col].isin(within_200m)) | (df[water_access_col].isin(on_site))
        )

        # Assigning values based on the masks
        df.loc[low_accessibility_mask, 'W_access_piped_RDP'] = 0
        df.loc[high_accessibility_mask, 'W_access_piped_RDP'] = 1

    elif standard == 'WHO':

        # the WHO standard is "50-100 L per capita per day should be piped into households",
        # here translated to "on site"

        # low accessibility (score 0) is then everything outside WHO standard (not on site):
        low_accessibility_mask = (
            (df[water_access_col].isin(no_access)) | (df[water_access_col].isin(beyond_1km)) |
            (df[water_access_col].isin(within_1km)) | (df[water_access_col].isin(within_500m)) |
            (df[water_access_col].isin(within_200m))
        )

        # high accessibility (score 1) adheres to WHO standard for distance (on site)
        high_accessibility_mask = ((
            df[water_access_col].isin(on_site))
        )

        # Assigning values based on the masks
        df.loc[low_accessibility_mask, 'W_access_piped_WHO'] = 0
        df.loc[high_accessibility_mask, 'W_access_piped_WHO'] = 1

    else:
        Warning(print("Standard should be NS (no standard), RDP or WHO"))

    return df


def obtain_w_access_sanitation_score_hh(dataset: pd.DataFrame, standard: str, sanitation_col: str or list):
    """

    :param dataset:
    :param standard:
    :param sanitation_col:
    :return:
    """

    # Made for Census variables

    df = dataset

    # Define categories in order (best → worst)
    categories = {
        "cat_a": ['Flush toilet connected to a public sewerage system', 'Flush toilet (connected to sewerage system)'],
        "cat_b": ['Flush toilet connected to a septic tank or conservancy tank', 'Flush toilet (with septic tank)'],
        "cat_c": ['Chemical toilet'],
        "cat_d": ['Pit latrine/toilet with ventilation pipe', 'Pit latrine with ventilation (VIP)'],
        "cat_e": ['Pit latrine/toilet without ventilation pipe', 'Pit latrine without ventilation'],
        "cat_f": ['Ecological toilet (e.g. urine diversion; enviroloo; etc.)'],
        "cat_g": ['Bucket toilet (collected by municipality)'],
        "cat_h": ['Bucket toilet (emptied by household)', 'Bucket latrine'],
        "cat_i": ['Other'],
        "cat_j": ['None', np.nan]
    }

    if type(sanitation_col) is list:
        sanitation_type_col = sanitation_col[0]
        sanitation_shared_col = sanitation_col[1]
    else:
        sanitation_type_col = sanitation_col

    if standard == 'NS':

        # Assign linear scores (1.0 → 0.0)
        n = len(categories) - 1
        score_map = {}
        for i, (cat, labels) in enumerate(categories.items()):
            score = 1 - (i / n)
            for label in labels:
                score_map[label] = score
        df['W_access_sanitation_NS'] = df[sanitation_type_col].map(score_map)

    elif standard == 'SA':

        # the South African standard is access to an IMPROVED sanitation facility.
        # based on: https://www.statssa.gov.za/publications/P0318/P03182023.pdf (pg. 36)

        # low accessibility (score 0) is then everything outside SA standard (unimproved facility):
        low_accessibility_mask = (
            (df[sanitation_type_col].isin(categories["cat_c"])) | (df[sanitation_type_col].isin(categories["cat_e"])) |
            (df[sanitation_type_col].isin(categories["cat_g"])) | (df[sanitation_type_col].isin(categories["cat_h"])) |
            (df[sanitation_type_col].isin(categories["cat_i"])) | (df[sanitation_type_col].isin(categories["cat_j"])) |
            (df[sanitation_type_col].isin(categories["cat_f"]))
        )

        # high accessibility (score 1) adheres to SA standard for facility (improved)
        high_accessibility_mask = (
            (df[sanitation_type_col].isin(categories["cat_a"])) | (df[sanitation_type_col].isin(categories["cat_b"])) |
            (df[sanitation_type_col].isin(categories["cat_d"]))
        )

        # Assigning values based on the masks
        df.loc[low_accessibility_mask, 'W_access_sanitation_SA'] = 0
        df.loc[high_accessibility_mask, 'W_access_sanitation_SA'] = 1

    elif standard == 'WHO':

        # the WHO standard is access to an IMPROVED PRIVATE sanitation facility.
        # high accessibility (score 1) adheres to WHO standard for facility (improved)
        high_accessibility_mask_san_type = (
            (df[sanitation_type_col].isin(categories["cat_a"])) | (df[sanitation_type_col].isin(categories["cat_b"])) |
            (df[sanitation_type_col].isin(categories["cat_c"])) | (df[sanitation_type_col].isin(categories["cat_d"])) |
            (df[sanitation_type_col].isin(categories["cat_e"])) | (df[sanitation_type_col].isin(categories["cat_f"]))
        )

        if type(sanitation_col) is list:

            # high accessibility (score 1) adheres to WHO standard for facility not shared.
            high_accessibility_mask_san_shared = (df[sanitation_shared_col] == 'No')
            # Assigning values based on the masks
            df.loc[~high_accessibility_mask_san_type, 'W_access_sanitation_WHO'] = 0
            df.loc[high_accessibility_mask_san_type & ~high_accessibility_mask_san_shared, 'W_access_sanitation_WHO'] = 0
            df.loc[high_accessibility_mask_san_type & high_accessibility_mask_san_shared, 'W_access_sanitation_WHO'] = 1

        else:
            # Assigning values based on the masks
            df.loc[~high_accessibility_mask_san_type, 'W_access_sanitation_WHO'] = 0
            df.loc[high_accessibility_mask_san_type, 'W_access_sanitation_WHO'] = 1


    else:
        Warning(print("Standard should be NS (No Standard), SA (South African standard) or WHO"))

    return df


def obtain_w_accessibility_score_hh(dataset: pd.DataFrame, aggregation_method: str):
    """

    :param dataset:
    :param combination_method:
    :return:
    """

    # Made for Census variables

    df = dataset

    for piped_water_standard in ['NS', 'RDP', 'WHO']:

        for sanitation_standard in ['NS', 'SA', 'WHO']:

            water_column = f'W_access_piped_{piped_water_standard}'
            sanitation_column = f'W_access_sanitation_{sanitation_standard}'

            columns = [water_column] + [sanitation_column]

            # Water accessibility score is computed as the mean of the access to piped water and access to sanitation scores:
            if aggregation_method == 'mean':

                df[f'W_accessibility_{piped_water_standard}_{sanitation_standard}_{aggregation_method}'] = df[columns].mean(axis=1, skipna=True)

            # Water accessibility score is determined by the lowest score among the access to piped water and access to
            # sanitation variables:
            elif aggregation_method == 'limiting_factor':
                df[f'W_accessibility_{piped_water_standard}_{sanitation_standard}_{aggregation_method}'] = df[columns].min(axis=1, skipna=True)

    return df


# obtain scores for the energy (E) domains:
def obtain_e_access_elect_score_hh(df: pd.DataFrame, census_type: str, e_access_cols: str or list, sensitivity=None):

    """
     Calculates the access to electricity variable 'E_accessibility' score

     :param df:
     :param e_access_cols:
     :return:

    """

    if census_type == 'census':

        if sensitivity is None:

            electricity_fuel = ['Electricity from mains', 'Other source of electricity (e.g. generator; etc.)',
                                'Other source of electricity (e.g. generator etc.)', 'Electricity', 'Solar']

            # Create a combined mask using OR condition across all specified columns
            electricity_access_mask = df[e_access_cols].isin(electricity_fuel).any(axis=1)

            # Assign 1 to rows that meet the condition, and 0 otherwise
            df.loc[electricity_access_mask, 'E_access_elec'] = 1
            df.loc[~electricity_access_mask, 'E_access_elec'] = 0

        else:

            electricity_from_mains = ['Electricity from mains', 'Electricity']

            # Create a combined mask using OR condition across all specified columns
            electricity_access_mask = df[e_access_cols].isin(electricity_from_mains).any(axis=1)

            # Assign 1 to rows that meet the condition, and 0 otherwise
            df.loc[electricity_access_mask, 'E_access_elec_sensitivity'] = 1
            df.loc[~electricity_access_mask, 'E_access_elec_sensitivity'] = 0

    elif census_type == 'community survey':

        if sensitivity is None: # all sources of electricity are deemed appropriate:

            electricity_access = ['In-house conventional meter', 'In-house prepaid meter', 'Solar home system',
                                  'Connected to other source which household pays for (e.g. con', 'Battery',
                                  'Connected to other source which household is not paying for', 'Other', 'Generator']

            electricity_access_mask = df[e_access_cols].isin(electricity_access)

            # Assign 1 to rows that meet the condition, and 0 otherwise
            df.loc[electricity_access_mask, 'E_access_elec'] = 1
            df.loc[~electricity_access_mask, 'E_access_elec'] = 0

        else: # only metered electricity and solar home systems
            electricity_from_mains = ['In-house conventional meter', 'In-house prepaid meter', 'Solar home system']
            electricity_access_mask = df[e_access_cols].isin(electricity_from_mains)

            # Assign 1 to rows that meet the condition, and 0 otherwise
            df.loc[electricity_access_mask, 'E_access_elec_sensitivity'] = 1
            df.loc[~electricity_access_mask, 'E_access_elec_sensitivity'] = 0

    return df


def obtain_f_access_agriculture_score_hh(df: pd.DataFrame, food_access_col: str):

    # if the household is involved in agriculture, the F accessibility score is 1:
    df.loc[(df[food_access_col] == 'Yes'), 'F_access_agri'] = 1
    # if the household is not involved in agriculture, the food accessibility score is 0:
    df.loc[(df[food_access_col] == 'No'), 'F_access_agri'] = 0

    return df

# AFFORDABILITY SCORES:

def calculate_affordability_perc(df):
    """
    Calculates the percentage of income spent on water, electricity, and food.
    """
    df = df.copy()
    cost_columns = [col for col in df.columns if 'COST' in col]

    for col in cost_columns:
        strings = col.split("_")
        year = [x for x in strings if '20' in x]
        year = year[0]
        new_col = f'{col}_%'
        income_col = f'HH_INCOME_PROXY_{year}'

        # ensure that there is an income column for the year that cost data is calculated for:
        if income_col in df.columns:
            df[new_col] = np.where(
                df[col] == 0,
                0,
                df[col] / df[f'HH_INCOME_PROXY_{year}']
            )

    return df


def obtain_hh_affordability_score(dataset: pd.DataFrame, threshold_dict: dict, year, free_basic_services=None) -> pd.DataFrame:
    """
    This method calculates the municipal affordability score for each resource, based on the percentage of households
    for which the required expenditures for that resource as percentage of household income is lower than the resource
    poverty threshold.
    :param dataset:
    :param threshold_dict: should include the poverty threshold for W, E and F. The key name should be W_poverty,
    E_poverty, F_poverty, and the value should be the poverty threshold as a decimal where 1 equals 100% of income.
    :return:
    """
    df = dataset.copy()  # Avoid modifying the original dataset

    for year in [2011, year]:
        for resource in ['W', 'E', 'F']:
            for resource_requirements in ['low', 'high']:

                # Vectorized comparison (no if statement needed)
                df[f'{resource}_affordability_{resource_requirements}reqs_{year}'] = (
                    df[f'HH_{resource}_COST_{resource_requirements}_{year}_%'] <= threshold_dict[f'{resource}_poverty']
                ).astype(int)  # Convert True/False to 1/0

                if free_basic_services == 'Yes' and resource != 'F':
                    df[f'{resource}_affordability_{resource_requirements}reqs_FB{resource}_{year}'] = (
                            df[f'HH_{resource}_COST_{resource_requirements}_FB{resource}_{year}_%'] <= threshold_dict[
                        f'{resource}_poverty']
                    ).astype(int)  # Convert True/False to 1/0
                else:
                    pass

    return df


def obtain_f_affordability_score_cs(df: pd.DataFrame, threshold='No'):

    # made for CS data variables

    # Low acceptability mask
    low_affordability_mask = (
        (df['FoodMoney'] == 'Yes') & (df['FreqOutOfFood'] == 'Yes')
    )

    # Moderate acceptability mask
    moderate_affordability_mask = (
        (df['FoodMoney'] == 'Yes') & (df['FreqOutOfFood'] == 'No')
    )

    # High acceptability mask
    high_affordability_mask = (
        (df['FoodMoney'] == 'No')
    )

    if threshold == 'Yes':

        # Assigning values based on the masks
        df.loc[low_affordability_mask, 'F_affordability_qualitative'] = 0
        df.loc[moderate_affordability_mask, 'F_affordability_qualitative'] = 0
        df.loc[high_affordability_mask, 'F_affordability_qualitative'] = 1

    elif threshold == 'No':

        # Assigning values based on the masks
        df.loc[low_affordability_mask, 'F_affordability_qualitative'] = 0
        df.loc[moderate_affordability_mask, 'F_affordability_qualitative'] = 0.5
        df.loc[high_affordability_mask, 'F_affordability_qualitative'] = 1

    else:
        Warning(print("Threshold for assigning a score should be either 'Yes' or 'No'."))

    return df

# ACCEPTABILITY SCORES:

def obtain_w_interruptions_score(df: pd.DataFrame, cols_interrupt: str or list, threshold="No"):

    if type(cols_interrupt) is str:

        # Interruptions score (based on whether the water supply was interrupted).
        # Low acceptability: experience interruptions
        low_acceptability_mask = (df[cols_interrupt] == 'Yes')

        # High acceptability: do not experience interruptions
        high_acceptability_mask = (df[cols_interrupt] == 'No')

        # if no data on interruptions or people do not have piped water, assign a NaN value:
        no_acceptability_mask = (df[cols_interrupt].isin(['Not applicable', 'Do not know', 'Unspecified']))

        # Assigning values based on the masks
        df.loc[low_acceptability_mask, 'W_interruptions'] = 0
        df.loc[high_acceptability_mask, 'W_interruptions'] = 1
        df.loc[no_acceptability_mask, 'W_interruptions'] = np.nan

        return df

    elif type(cols_interrupt) is list:

        col_interrupt = cols_interrupt[0]
        col_duration = cols_interrupt[1]

        # Interruptions score (based on whether the water supply was interrupted and if this lasted > 2 days.
        # Low acceptability: experience interruptions AND lasted longer than 2 days in past 3 months
        low_acceptability_mask = ((df[col_interrupt] == 'Yes') & (df[col_duration] == 'Yes'))

        # Moderate acceptability: experience interruptions but did not last longer than 2 days in past 3 months
        moderate_acceptability_mask = ((df[col_interrupt] == 'Yes') & (df[col_duration] == 'No'))

        # High acceptability: do not experience interruptions
        high_acceptability_mask = (df[col_interrupt] == 'No')

        # if no data on interruptions or people do not have piped water, assign a NaN value:
        no_acceptability_mask = (df[col_interrupt].isin(['Not applicable', 'Do not know', 'Unspecified']))

        if threshold == 'WHO':

            # Assigning values based on the masks
            df.loc[low_acceptability_mask, 'W_interruptions_WHO'] = 0
            df.loc[moderate_acceptability_mask, 'W_interruptions_WHO'] = 0
            df.loc[high_acceptability_mask, 'W_interruptions_WHO'] = 1
            df.loc[no_acceptability_mask, 'W_interruptions_WHO'] = np.nan

        elif threshold == 'SA':

            # Assigning values based on the masks
            df.loc[low_acceptability_mask, 'W_interruptions_SA'] = 0
            df.loc[moderate_acceptability_mask, 'W_interruptions_SA'] = 1
            df.loc[high_acceptability_mask, 'W_interruptions_SA'] = 1
            df.loc[no_acceptability_mask, 'W_interruptions_SA'] = np.nan

        else:
            Warning(print("Threshold for assigning a score should be either 'Yes' or 'No'."))
    else:
        Warning(print("Columns for interruptions should be either 1 or 2."))

    return df


def obtain_w_accept_source_supply_score_hh(dataset: pd.DataFrame):

    # made for CE data variables

    df = dataset

    w_interruption = 'Reliability of water supply'
    w_interruption_long = 'Did interruption of water supply last longer than two days'
    w_source_good = 'Borehole'
    w_source_depend = 'Regional/local water scheme (operated by a Water Service Authority or provider)'
    w_source_moderate = ['Spring', 'Rain-water tank']
    w_source_low = ['Dam / pool / stagnant water', 'River/stream', 'Water vendor', 'Water tanker', 'Other', 'None']

    # Low acceptability mask
    low_acceptability_mask = (
        (df['Source of water'].isin(w_source_low)) |
        ((df['Source of water'] == w_source_depend) &
         (df[w_interruption] == 'Yes') &
         (df[w_interruption_long] == 'Yes') &
         (df['Alternative water source'].isin(w_source_low) |
          df['Alternative water source'].isin(w_source_moderate)))
    )

    # Moderate acceptability mask
    moderate_acceptability_mask = (
        (df['Source of water'].isin(w_source_moderate)) |
        ((df['Source of water'] == w_source_depend) &
         (df[w_interruption] == 'Yes') &
         ((df[w_interruption_long] == 'No') |
          ((df[w_interruption_long] == 'Yes') &
           (df['Alternative water source'] == w_source_good))))
    )

    # High acceptability mask
    high_acceptability_mask = (
        (df['Source of water'] == w_source_good) |
        ((df['Source of water'] == w_source_depend) &
         (df[w_interruption] == 'No'))
    )

    # Assigning values based on the masks
    df.loc[low_acceptability_mask, 'W_acceptability'] = 'Low'
    df.loc[moderate_acceptability_mask, 'W_acceptability'] = 'Moderate'
    df.loc[high_acceptability_mask, 'W_acceptability'] = 'High'

    return df


def obtain_e_accept_fuel_score_hh(df: pd.DataFrame, e_fuel_cols: list):
    """
     Calculates the access to processed fuels variable "E_access_fuel", based on the WHO standards of processed fuels (to be
     found here: https://www.who.int/tools/clean-household-energy-solutions-toolkit/module-7-defining-clean#:~:text=Polluting%20sources%20of%20light,%2C%20candles%2C%20or%20open%20fires.)
     Clean fuels are then: electricity, solar, biogas, LPG, alcohol. Since the stove type is not in the data, all
     biomass is considered dirty. Dirty fuels are then: Kerosene/paraffin, coal, biomass (including wood, animal dung),
     candles, other, unspecified and none. The score of 0 is given when for any category (cooking, lighting or heating)
     a dirty fuel is used, only if all of these are done by processed fuels a score of 1 is given.

     :param df:
     :param e_fuel_cols:
     :return:

    """

    clean_fuels = ['Electricity from mains', 'Other source of electricity (e.g. generator; etc.)',
                   'Other source of electricity (e.g. generator etc.)', 'Electricity', 'Solar', 'Gas']

    # Create a combined mask using OR condition across all specified columns
    clean_fuel_mask = df[e_fuel_cols].isin(clean_fuels).all(axis=1, skipna=True)

    # Assign 1 to rows that meet the condition, and 0 otherwise
    df.loc[clean_fuel_mask, 'E_accept_fuel'] = 1
    df.loc[~clean_fuel_mask, 'E_accept_fuel'] = 0

    return df


def obtain_e_interruptions_score_cs(df: pd.DataFrame, threshold: str):
    """
    Method to obtain a numeric score for interruptions based on the community survey variables of "ElectrInterrupt"
    (asking whether the household experienced interruptions without prior notice in the past three months) and
    "ElecInterruptTime" (asking whether any of those interruptions lasted longer than 12 hours).
    :param df:
    :return: df with a new column added called E_interruptions
    """

    # Interruptions score (based on 'ElectrInterrupt' and 'ElecInterruptTime')
    # Low acceptability: experience interruptions (without prior notice) AND lasted longer than 12 hours in past
    # 3 months
    low_acceptability_mask = ((df['ElectrInterrupt'] == 'Yes') & (df['ElecInterruptTime'] == 'Yes'))

    # Moderate acceptability: experience interruptions (without prior notice) but did not last longer than 12 hours
    # in past 3 months
    moderate_acceptability_mask = ((df['ElectrInterrupt'] == 'Yes') & (df['ElecInterruptTime'] == 'No'))

    # High acceptability: do not experience interruptions (without prior notice)
    high_acceptability_mask = (df['ElectrInterrupt'] == 'No')

    # if no data on interruptions or people do not have electricity, assign a NaN value:
    no_acceptability_mask = (df['ElectrInterrupt'].isin(['Not applicable', 'Do not know', 'Unspecified']))

    if threshold == 'Yes':

        # Assigning values based on the masks
        df.loc[low_acceptability_mask, 'E_interruptions'] = 0
        df.loc[moderate_acceptability_mask, 'E_interruptions'] = 0
        df.loc[high_acceptability_mask, 'E_interruptions'] = 1
        df.loc[no_acceptability_mask, 'E_interruptions'] = np.nan

    elif threshold == 'No':

        # Assigning values based on the masks
        df.loc[low_acceptability_mask, 'E_interruptions'] = 0
        df.loc[moderate_acceptability_mask, 'E_interruptions'] = 0.5
        df.loc[high_acceptability_mask, 'E_interruptions'] = 1
        df.loc[no_acceptability_mask, 'E_interruptions'] = np.nan

    else:
        Warning(print("Threshold for assigning a score should be either 'Yes' or 'No'."))

    return df


def obtain_perception_score_cs(df: pd.DataFrame, service: str):
    """
    Method to obtain a numeric score for perception based on the community survey variables regarding rating of services
    (asking how people would rate the overall quality of services on a scale of good-average-poor). Note that the column
    corresponding to the selected service should be extracted from the original dataset (column of the form RateService
    (replacing Service with one of the options in the service parameter) should be extracted from the original dataset).
    :param df:
    :param service: one of the following strings: Water, Refuse, Electricity, Toilet, Hospital, Clinic, Police, School
    :return: df with a new column added called {service}_perception
    """

    column = f'Rate{service}'
    # Perception score (based on RateElectricity):
    low_rating_mask = (df[column] == 'Poor')
    moderate_rating_mask = (df[column] == 'Average')
    high_rating_mask = (df[column] == 'Good')
    no_rating_mask = (df[column].isin(['No access', 'Do not use', 'Unspecified']))

    # Assigning values based on the masks
    df.loc[low_rating_mask, f'{service}_perception'] = 0
    df.loc[moderate_rating_mask, f'{service}_perception'] = 0.5
    df.loc[high_rating_mask, f'{service}_perception'] = 1
    df.loc[no_rating_mask, f'{service}_perception'] = np.nan

    return df


def obtain_f_acceptability_score_cs(df: pd.DataFrame, threshold='No'):

    # made for community survey (CS) data variables Skipping Meals and Frequency of Skipping Meals

    # Low acceptability mask: frequently skipping meals
    low_acceptability_mask = (
        (df['SkipMeal'] == 'Yes') & (df['FreqSkipMeal'] == 'Yes')
    )

    # Moderate acceptability mask: skipping meals, but not frequently
    moderate_acceptability_mask = (
        (df['SkipMeal'] == 'Yes') & (df['FreqSkipMeal'] == 'No')
    )

    # High acceptability mask: never skipping meals
    high_acceptability_mask = (
        (df['SkipMeal'] == 'No')
    )

    no_rating_mask = (df['SkipMeal'].isin(['Unspecified']))

    if threshold == 'Yes':

        # Assigning values based on the masks
        df.loc[low_acceptability_mask, 'F_acceptability'] = 0
        df.loc[moderate_acceptability_mask, 'F_acceptability'] = 0
        df.loc[high_acceptability_mask, 'F_acceptability'] = 1
        df.loc[no_rating_mask, 'F_acceptability'] = np.nan

    elif threshold == 'No':

        # Assigning values based on the masks
        df.loc[low_acceptability_mask, 'F_acceptability'] = 0
        df.loc[moderate_acceptability_mask, 'F_acceptability'] = 0.5
        df.loc[high_acceptability_mask, 'F_acceptability'] = 1
        df.loc[no_rating_mask, 'F_acceptability'] = np.nan

    else:
        Warning(print("Threshold for assigning a score should be either 'Yes' or 'No'."))

    return df


def obtain_f_acceptability_score_ce(df: pd.DataFrame, threshold: str, aggregation_method: str):

    # made for census (CE) data variables Adult Hunger and Child Hunger: categories are 'Never' < 'Seldom' < 'Sometimes'
    # < 'Often' < 'Always' < 'Not applicable (no adult in the household)' < 'Unspecified'.

    # create numerical values for each category based on either a set threshold at "never" or by assigning scores to
    # all categories.

    if threshold == 'Yes':
        category_mapping = {
            'Never': 1,
            'Seldom': 0,
            'Sometimes': 0,
            'Often': 0,
            'Always': 0,
            'Not applicable (no adult in the household)': np.nan,  # Convert to NaN
            'Not applicable (no child in the household)': np.nan,  # convert to NaN
            'Unspecified': np.nan  # Convert to NaN
        }

    elif threshold == 'No':
        category_mapping = {
            'Never': 1,
            'Seldom': 0.75,
            'Sometimes': 0.5,
            'Often': 0.25,
            'Always': 0,
            'Not applicable (no adult in the household)': np.nan,  # Convert to NaN
            'Not applicable (no child in the household)': np.nan,  # convert to NaN
            'Unspecified': np.nan  # Convert to NaN
        }

    else:
        Warning(print("Threshold should be either Yes or No."))

    # Map categories to numerical scores
    df['adult_hunger_numeric'] = df["A4_ADULT_HUNGER"].map(category_mapping)
    df['child_hunger_numeric'] = df['A5_CHILD_HUNGER'].map(category_mapping)

    if aggregation_method == 'mean':

        # Compute row-wise meanwhile ignoring NaNs
        df[f'F_acceptability_{aggregation_method}'] = df[['adult_hunger_numeric', 'child_hunger_numeric']].mean(axis=1, skipna=True)

    elif aggregation_method == 'limiting_factor':
        df[f'F_acceptability_{aggregation_method}'] = df[['adult_hunger_numeric', 'child_hunger_numeric']].min(axis=1, skipna=True)

    else:
        Warning(print("Aggregation method should be either mean or limiting_factor."))

    return df

# ADDITIONAL FUNCTIONS

def normalize_minmax(df, columns: list):

    for column in columns:
        df[f'{column}_n'] = (df[column] - df[column].min()) / (df[column].max() - df[column].min())

    return df


def normalize_max(df, columns: list):

    for column in columns:
        df[f'{column}_n'] = df[column] / df[column].max()

    return df

def normalize_log(df, columns: list):
    for column in columns:
        df[f'{column}_log'] = np.log(df[column]) / np.log(df[column]).sum()

    return df

def numerical_to_categories(value, thresholds: dict):

    if pd.isna(value):
        return np.nan

    # Sort thresholds by value
    sorted_thresholds = sorted(thresholds.items(), key=lambda item: item[1])

    for category, max_value in sorted_thresholds:
        if value <= max_value:
            return category

    # If value exceeds all thresholds
    return 'Other'

def parse_domain(col):
    # examples: W_availability_baseline, E_accessibility_remote, F_affordability_cost
    parts = col.split("_")
    resource = parts[0]            # W or E or F
    aspect = parts[1]              # availability/accessibility/affordability/acceptability
    return resource, aspect

def shorten_category(cat):
    """
    Converts full column names like:
        W_availability_irrigation_surface_2019
    into:
        W_availability
    """
    match = re.match(r"([WEF]_(availability|accessibility|affordability|acceptability))", cat)
    if match:
        return match.group(1)
    return cat  # fallback in case of unexpected format


def collect_stats(df, scenario_info):
    stats = scenario_info.copy()

    alt_col = scenario_info["Alternative domain"]
    stats['Alternative_domain_mean'] = df[alt_col].mean()
    stats['Alternative_domain_std'] = df[alt_col].std()
    stats['Alternative_domain_min'] = df[alt_col].min()
    stats['Alternative_domain_median'] = df[alt_col].median()
    stats['Alternative_domain_max'] = df[alt_col].max()

    # --- NUMERIC COLUMNS ------------------------------------
    numeric_cols = [col for col in df.columns if col.endswith("_mean") or col.endswith("_value")]
    for col in numeric_cols:
        stats[f"{col}_mean"]   = df[col].mean()

    # --- CATEGORICAL COLUMNS --------------------------------
    domain_cols = [col for col in df.columns if col.endswith("_domain")]
    for col in domain_cols:
        vc = df[col].value_counts()
        for category, count in vc.items():
            simplified = shorten_category(category)  # e.g., W_availability
            key = f"{col}_{simplified}"
            stats[key] = count

    return stats


