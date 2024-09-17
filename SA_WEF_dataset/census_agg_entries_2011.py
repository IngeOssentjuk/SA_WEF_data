import pandas as pd
import geopandas as gpd
import os
import matplotlib.pyplot as plt
from CE11_aggregated_labels import *
from spatial_data import PR_CE11, MN_CE11, SAL_CE11
import contextily as cx
import cmcrameri.cm as cmc
import seaborn as sns
from matplotlib.colors import ListedColormap

input_data = r"C:/Github/SA_WEF_dataset/raw_data/CE_2011/2011_spatial_entries"


# Collect grouped data (household and individual count per area): dta to df
# FUEL USE: Cooking, heating, lighting
CEN11_E_cooking_hh = pd.read_stata(os.path.join(input_data, "energy-for-cooking.dta"))
CEN11_E_cooking_ind = pd.read_stata(os.path.join(input_data, "energy-for-cooking-individual.dta"))
CEN11_E_heating_hh = pd.read_stata(os.path.join(input_data, "energy-for-heating.dta"))
CEN11_E_heating_ind = pd.read_stata(os.path.join(input_data, "energy-for-heating-individual.dta"))
CEN11_E_lighting_hh = pd.read_stata(os.path.join(input_data, "energy-for-lighting.dta"))
CEN11_E_lighting_ind = pd.read_stata(os.path.join(input_data, "energy-for-lighting-individual.dta"))

# WATER
# access to piped water
CEN11_W_piped_hh = pd.read_stata(os.path.join(input_data, "piped-water.dta"))
CEN11_W_piped_ind = pd.read_stata(os.path.join(input_data, "piped-water-individual.dta"))

# source of water
CEN11_W_source_hh = pd.read_stata(os.path.join(input_data, "source-of-water.dta"))
CEN11_W_source_ind = pd.read_stata(os.path.join(input_data, "source-of-water-individual.dta"))

# FACILITIES
CEN11_F_stove_hh = pd.read_stata(os.path.join(input_data, "electric-gas-stove.dta"))
CEN11_F_refrigerator_hh = pd.read_stata(os.path.join(input_data, "refrigerator.dta"))
CEN11_cellphone_hh = pd.read_stata(os.path.join(input_data, "cellphone.dta"))
CEN11_communication_hh = pd.read_stata(os.path.join(input_data, "communication.dta"))
CEN11_computer_hh = pd.read_stata(os.path.join(input_data, "computer.dta"))
CEN11_dvd_hh = pd.read_stata(os.path.join(input_data, "dvd-player.dta"))
CEN11_internet_access_hh = pd.read_stata(os.path.join(input_data, "internet-access.dta"))
CEN11_landline_telephone_hh = pd.read_stata(os.path.join(input_data, "landline-telephone.dta"))
CEN11_radio_hh = pd.read_stata(os.path.join(input_data, "radio.dta"))
CEN11_tv_satellite_hh = pd.read_stata(os.path.join(input_data, "satellite-television.dta"))
CEN11_tv_hh = pd.read_stata(os.path.join(input_data, "television.dta"))
CEN11_mail_delivered_hh = pd.read_stata(os.path.join(input_data, "mail-delivered.dta"))
CEN11_mail_box_hh = pd.read_stata(os.path.join(input_data, "mail-post-box-bag.dta"))
CEN11_car_hh = pd.read_stata(os.path.join(input_data, "motor-car.dta"))
CEN11_vacuum_hh = pd.read_stata(os.path.join(input_data, "vacuum-cleaner.dta"))
CEN11_washing_machine_hh = pd.read_stata(os.path.join(input_data, "washing-machine.dta"))

# HYGIENE
CEN11_waste_hh = pd.read_stata(os.path.join(input_data, "refuse-disposal.dta"))
CEN11_waste_ind = pd.read_stata(os.path.join(input_data, "refuse-disposal-individual.dta"))
CEN11_toilet_hh = pd.read_stata(os.path.join(input_data, "toilet-facilities.dta"))
CEN11_toilet_ind = pd.read_stata(os.path.join(input_data, "toilet-facilities-individual.dta"))

# HEALTH
CEN11_chronic_meds_ind = pd.read_stata(os.path.join(input_data, "chronic-medication.dta"))
CEN11_seeing_ind = pd.read_stata(os.path.join(input_data, "seeing.dta"))
CEN11_glasses_ind = pd.read_stata(os.path.join(input_data, "eye-glasses.dta"))
CEN11_hearing_ind = pd.read_stata(os.path.join(input_data, "hearing.dta"))
CEN11_hearing_aid_ind = pd.read_stata(os.path.join(input_data, "hearing-aid.dta"))
CEN11_memory_concentration_ind = pd.read_stata(os.path.join(input_data, "remembering-concentrating.dta"))
CEN11_selfcare_ind = pd.read_stata(os.path.join(input_data, "self-care.dta"))
CEN11_stairs_ind = pd.read_stata(os.path.join(input_data, "walking-or-climbing-stairs.dta"))
CEN11_walking_aid_ind = pd.read_stata(os.path.join(input_data, "walking-stick-or-frame.dta"))
CEN11_wheelchair_ind = pd.read_stata(os.path.join(input_data, "wheelchair.dta"))

# GENERAL DATA
CEN11_age_head_hh = pd.read_stata(os.path.join(input_data, "age-hhold-head.dta"))
CEN11_age_ind = pd.read_stata(os.path.join(input_data, "age-in-completed-years.dta"))
CEN11_pop_group_ind = pd.read_stata(os.path.join(input_data, "population-group.dta"))
CEN11_pop_group_head_hh = pd.read_stata(os.path.join(input_data, "population-group-household-head.dta"))
CEN11_gender_head_hh = pd.read_stata(os.path.join(input_data, "gender-hhold-head.dta"))
CEN11_gender_ind = pd.read_stata(os.path.join(input_data, "gender.dta"))
CEN11_size_hh = pd.read_stata(os.path.join(input_data, "hhold-size.dta"))
CEN11_rooms_hh = pd.read_stata(os.path.join(input_data, "number-of-rooms.dta"))
CEN11_language_ind = pd.read_stata(os.path.join(input_data, "language.dta"))
CEN11_marital_status_ind = pd.read_stata(os.path.join(input_data, "marital-status.dta"))
CEN11_father_alive_ind = pd.read_stata(os.path.join(input_data, "father-alive.dta"))
CEN11_mother_alive_ind = pd.read_stata(os.path.join(input_data, "mother-alive.dta"))
CEN11_citizenship = pd.read_stata(os.path.join(input_data, "citizenship-grouped.dta"))
CEN11_EA_type = pd.read_stata(os.path.join(input_data, "enumeration-area-type.dta"))
CEN11_geo_type_hh = pd.read_stata(os.path.join(input_data, "geo-type.dta"))
CEN11_tenure_status_hh = pd.read_stata(os.path.join(input_data, "tenure-status.dta"))
CEN11_dwelling_type_hh = pd.read_stata(os.path.join(input_data, "type-of-main-dwelling.dta"))
CEN11_dwelling_type_ind = pd.read_stata(os.path.join(input_data, "type-of-main-dwelling-individual.dta"))

# ECONOMY
CEN11_annual_income_hh = pd.read_stata(os.path.join(input_data, "annual-household-income.dta"))
CEN11_monthly_income_ind = pd.read_stata(os.path.join(input_data, "monthly-income-individual.dta"))
CEN11_employment_head_hh = pd.read_stata(os.path.join(input_data, "employment-status-hhold-head.dta"))
CEN11_employment_ind = pd.read_stata(os.path.join(input_data, "official-employment-status.dta"))
CEN11_employment_sector_ind = pd.read_stata(os.path.join(input_data, "type-of-sector.dta"))

# EDUCATION
CEN11_edu_level_ind = pd.read_stata(os.path.join(input_data, "education-level.dta"))
CEN11_edu_inst_ind = pd.read_stata(os.path.join(input_data, "educational-institution.dta"))
CEN11_edu_highest_grouped = pd.read_stata(os.path.join(input_data, "highest-education-level-grouped.dta"))
CEN11_edu_highest_ind = pd.read_stata(os.path.join(input_data, "highest-educational-level.dta"))
CEN11_edu_attendance_ind = pd.read_stata(os.path.join(input_data, "present-school-attendance.dta"))

# PREPARE SPATIAL DATA: rename column of gdf so that it matches datasets
SAL_CE11 = SAL_CE11.rename(columns={'SAL_CODE': 'sal_code'}) # SAL level
MN_CE11 = MN_CE11.rename(columns={'MN_CODE': 'mn_code'}) # MUN level
PR_CE11 = PR_CE11.rename(columns={'PR_CODE': 'pr_code'}) # PR level

spatial_dict = {"SAL_CE11": "sal_code", "MN_CE11": "mn_code", "PR_CE11": "pr_code"}


def prepare_aggregated_data(dataset_name, spatial_level):

    # get actual dataframe from dataset name
    dataset = eval(dataset_name)

    # get label dictionary corresponding to that dataset and rename the dataframe columns
    labels_dict = eval(f'{dataset_name}_labels')
    dataset.rename(columns=labels_dict, inplace=True)

    # obtain spatial data based on chosen spatial level code
    spatial_dataset = eval(spatial_level)
    spatial_column_name = spatial_dict[spatial_level]
    spatial_dataset = spatial_dataset[[spatial_column_name, 'geometry']]

    # extract only relevant columns: i.e., columns with answers and the spatial code column
    answer_columns = list(labels_dict.values())
    answer_columns.append(spatial_column_name)
    dataset = dataset[answer_columns]

    # group data based on chosen spatial level code
    if spatial_level == "MN_CE11" or "PR_CE11":
        dataset = dataset.groupby(spatial_column_name).sum()
    else:
        return

    # merge spatial data to dataset based on chosen spatial level code
    dataset = spatial_dataset.merge(dataset, on=spatial_column_name)

    return dataset, labels_dict


def obtain_shares(dataset, labels_dict):
    # calculate total number of counts per question based on column names corresponding to the answers
    # TODO check whether to include or exclude unspecified / not applicable in total (or no access)
    dataset['Total'] = dataset[labels_dict.values()].sum(axis=1)

    # TODO check whether to exclude certain categories for % calculation
    for column in labels_dict.values():
        dataset[f'{column}_%'] = dataset[column] / dataset['Total']

    return dataset


def obtain_highest_value(dataset, labels_dict):

    # PLOT ANSWER OF HIGHEST COUNT PER AREA
    reduced_dataset = dataset[list(labels_dict.values())]
    dataset['Maximum_value'] = reduced_dataset.idxmax(axis=1)

    return dataset


def consistent_colours(labels: dict, dataset_name):

    # collect categories from dataset (to assign consistent colours across spatial scales)
    dataset_categories_map = {dataset_name: list(labels.values())}
    categorical_colour_palette = sns.color_palette(palette='colorblind',
                                                   n_colors=len(dataset_categories_map[dataset_name]))

    # initialize dictionary to store label-colour pairs:
    dataset_color_map = {}

    for dataset_name, categories in dataset_categories_map.items():
        # Map each unique category to a color
        dataset_color_map[dataset_name] = dict(zip(categories, categorical_colour_palette))

    return dataset_color_map


# 'CEN11_E_cooking_hh', 'CEN11_E_heating_hh', 'CEN11_E_lighting_hh', 'CEN11_W_piped_hh',
#                      'CEN11_W_source_hh', 'CEN11_F_stove_hh', 'CEN11_F_refrigerator_hh', 'CEN11_internet_access_hh',
#                      'CEN11_waste_hh', 'CEN11_toilet_hh', 'CEN11_chronic_meds_ind', 'CEN11_selfcare_ind',
#                      'CEN11_pop_group_ind', 'CEN11_size_hh', 'CEN11_rooms_hh', 'CEN11_EA_type', 'CEN11_geo_type_hh',
#                      'CEN11_tenure_status_hh', 'CEN11_dwelling_type_hh', 'CEN11_annual_income_hh',
#                      'CEN11_monthly_income_ind', 'CEN11_employment_ind', 'CEN11_edu_highest_grouped'

for dataset_name in ['CEN11_W_piped_hh']:

    # # only needed for categorical data (can be commented out for continuous share plots)
    # labels_dict = eval(f'{dataset_name}_labels')
    # dataset_color_map = consistent_colours(labels_dict, dataset_name)
    # selected_color_map = dataset_color_map[dataset_name]

    for spatial_level in ['SAL_CE11']:  # must be loaded above and present in datasets

        desired_spatial_level = spatial_level
        prepared_data = prepare_aggregated_data(dataset_name, spatial_level=desired_spatial_level)
        dataset = prepared_data[0]
        labels_dict = prepared_data[1]
        spatial_label = spatial_level.rstrip('_CE11')

        # # get a column "maximum value" that has for each row the column name with most counts / the highest value:
        # dataset = obtain_highest_value(dataset, labels_dict)
        #
        # plot_name = f'{dataset_name}_{spatial_label}_highest_incidence.jpeg'
        # plot_file = os.path.join("C:/Github/SA_WEF_dataset/maps", plot_name)
        #
        # # set column to categorical
        # dataset['Maximum_value'] = dataset['Maximum_value'].astype('category')
        #
        # # Create a ListedColormap from the consistent color map for this dataset
        # categorical_consistent_cmap = ListedColormap([selected_color_map[cat] for cat in dataset['Maximum_value'].cat.categories])
        #
        # # set figure size
        # fig, ax = plt.subplots(figsize=(12, 8))
        #
        # # plot the map and add a basemap
        # dataset.plot(ax=ax, column='Maximum_value', categorical=True, cmap=categorical_consistent_cmap, legend=True,
        #              legend_kwds={'loc': 'upper left','title': f'Category'},
        #              missing_kwds={'color': 'lightgrey', 'label': 'Missing values'})
        #
        # if spatial_level == 'SAL_CE11':
        #     MN_CE11.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5)
        #     PR_CE11.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5)
        # elif spatial_level == 'MN_CE11' or 'PR_CE11':
        #     PR_CE11.plot(ax=ax, facecolor='none', edgecolor='black')
        # else:
        #     pass
        #
        # cx.add_basemap(ax, crs=dataset.crs, source=cx.providers.CartoDB.PositronNoLabels)
        #
        # ax.set_title(f'Answer with highest incidence for {dataset_name} at {spatial_label} level')
        # ax.axis('off')
        # plt.savefig(plot_file, bbox_inches='tight')
        # plt.close(fig)

      # COMMENT OUT IF NOT USING!
        # EASY PLOTS: SHARE ANSWER A OF TOTAL ANSWERS PER QUESTION
        # get shares:
        dataset = obtain_shares(dataset, labels_dict)

        # plotting each column with the share of that answer
        for column in labels_dict.values():

            plot_name = f'{dataset_name}_{spatial_label}_{column}_share.jpeg'
            plot_file = os.path.join("C:/Github/SA_WEF_dataset/maps", plot_name)

            # set figure size
            fig, ax = plt.subplots(figsize=(12, 8))

            # plot the map, add municipal/provincial lines and add a basemap
            dataset.plot(ax=ax, column=dataset[f'{column}_%'], cmap=cmc.turku_r, legend=True,
                         legend_kwds={"label": f'Share of {column} of total'},
                         missing_kwds={'color': 'lightgrey', 'label': 'Missing values'})

            if spatial_level == 'SAL_CE11':
                MN_CE11.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=0.5)
                PR_CE11.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1)
            elif spatial_level == 'MN_CE11' or 'PR_CE11':
                PR_CE11.plot(ax=ax, facecolor='none', edgecolor='black')
            else:
                pass

            cx.add_basemap(ax, crs=dataset.crs, source=cx.providers.CartoDB.PositronNoLabels)

            ax.set_title(f'Share of {column} for {dataset_name} at SAL level')
            ax.axis('off')
            plt.savefig(plot_file, bbox_inches='tight')
            plt.close(fig)

# useful commands
# to check names and thus a common value to merge on:
# print(dataframe.columns.values.tolist())
# for geodataframes even easier:
# print(geodataframe.columns)












