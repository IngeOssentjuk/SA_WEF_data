from functools import reduce
from collections import defaultdict

from src.data_preprocessing import *
from src.data_processing_domain_scores import *
from src.data_processing_mapping import *
from src.data_processing_statistics import *

# Directory data: change according to your own directory.
input_dir_raw = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/raw/"
input_dir_processed = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/processed/"
input_dir_clean = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/clean/"
output_dir_data = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/data/clean/"
output_dir_figures = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/results/figures/"
output_dir_maps = "C:/Users/6145795/Documents/GitHub/SA_WEF_dataset/results/maps/"

# 0. THRESHOLDS AND INPUT DATA
# In this section, you can adjust parameters and inputs for the calculation of variables, and for the selection of the
# final twelve domains.

# setting the year for which the final values are calculated, which population numbers are used, etc.
year = 2016

# this section contains the data that can be changed with study-specific values
# Set the areal scope of the calculations: either 'rural', 'urban' or 'total'
area = 'rural'

# set the method of combining two variables into one to either 'mean' or 'limiting factor'.
aggregation_method = 'limiting_factor'
# set the higher ('high') or lower ('low') end of the range of resource requirements for the final maps and statistics
reqs = 'high'

# set CRS for area/density calculations
spatial_crs = "EPSG:9822" # Albers Equal Area

# 0.1. AVAILABILITY INPUT DATA

# 0.1.1 WATER AVAILABILITY INPUTS
# variables used for calculation of water availability (output variables from PCR-GLOBWB 2.0)
water_availability_vars = ['Qsw_mean_m3_max', 'Qro_mean_m3_total', 'Qgw_mean_m3_total', 'Qds_mean_m3_total']
# thresholds for water availability categories, these are the Falkenmark thresholds for scarcity in m3/cap/year.
Falkenmark_thresholds_categorical = {'Absolute scarcity': 500, 'Scarcity': 1000, 'Stress': 1670, 'No stress': np.inf}
# preference for conversion into domain score through categorical data or linear data with minimum and maximum cut-offs:
w_availability_threshold = 'linear_minmax' # should be 'linear_minmax' or 'categorical'
# if the above is 'linear_minmax', set the values of water availability in m3/cap/year that are the minimum cut-off (equated to a score of 0) and the maximum cut-off (equated to a score of 1):
w_min_cutoff = 500 # based on lower Falkenmark category of "absolute scarcity"
w_max_cutoff = 1670 # based on upper Falkenmark category of "no stress"
# conversion of scarcity categories to numerical scores
w_availability_scores_categorical = {'Absolute scarcity': 0, 'Scarcity': 0.25, 'Stress': 0.5, 'No stress': 1}

# 0.1.2. ENERGY AVAILABILITY INPUTS
EAF_2016 = 0.76 # source: https://www.csir.co.za/sites/default/files/Documents/Utility%20Statistics%20Report_Jan%202025_Final.pdf (slide 5)
EAF_2022 = 0.58 # Source: https://www.csir.co.za/sites/default/files/Documents/Statistics%20of%20power%20in%20SA%202022-CSIR-%5BFINAL%5D.pdf

# 0.1.3. FOOD AVAILABILITY INPUTS

# set value for the minimum dietary energy requirement (MDER) in kcal/cap/day:
dietary_energy_reqs = 1849  # average over years 2010-2019 MDER for south africa in kcal/cap/day through: https://www.fao.org/faostat/en/#data/FS
protein_fraction = round(((0.10+0.35) / 2), 3) # mean of 10-35% range of Acceptable Macronutrient Distribution Range.
dietary_protein_reqs = (protein_fraction * dietary_energy_reqs)

# energy density of cereals (maize and wheat) and raw meat (cattle, mutton (sheep) and chicken) in kcal/kg.
energy_density = {
    'Cattle': 2036,
    'Sheep': 2596,
    'Chicken': 1312,
    'Maize': 3560,
    'Wheat': 3340
}

# protein density of cereals (maize and wheat) and raw meat (cattle, mutton (sheep) and chicken) in g/kg.
protein_density = {
    'Cattle': 192,
    'Sheep': 169,
    'Chicken': 211,
    'Maize': 95,
    'Wheat': 122
}

# edible fraction of cereals (maize and wheat) and meat (cattle, mutton (sheep) and chicken) as ratio of
# respectively the harvested grain and the carcass weight.
fraction_edible = {
    'Cattle': 0.62,
    'Sheep': 0.47,
    'Chicken': 0.60,
    'Maize': 1,
    'Wheat': 1
}

# fraction of animals in stock that are taken out of the stock (i.e., slaughtered) each year.
fraction_slaughtered = {
    'Cattle': 0.18,
    'Sheep': 0.27,
    'Chicken': 6.0
}

# carcass weights of animals in kg/animal.
mass_carcass = {
    'Cattle': 215,
    'Sheep': 17,
    'Chicken': 1.262
}

# 0.2. ACCESSIBILITY INPUT DATA

# select a standard for determining the water accessibility scores. For the access to piped water, these can be: 'NS'
# (no standard, then the scores are allocated based on distance categories); 'RDP' (accessible when within 200m from dwelling); 'WHO'
# (accessible when at household). For the sanitation facilities, these can be: 'NS' (no standard, then the scores are allocated
# based on sanitation type categories); 'SA' (accessible when the sanitation type is "improved" according to the South African policy definition),
# 'WHO' (accessible when the sanitation type is "improved" according to WHO definitions). Note that this is only different
# in the final dataframe (all standards and combinations thereof are in the elaborate dataframe).

W_access_piped_standard = 'WHO'
W_sanitation_standard = 'WHO'

# 0.3. AFFORDABILITY INPUT DATA

# 0.3.1. Numerator (= cost of resources)

# 0.3.1.1. Minimum resource requirements
W_req_low = 50 * 365 / 1000  # in kL per person per year, 50 L/p/day is mentioned as potential "basic requirement" value for drinking, cooking, bathing and sanitation: https://iris.who.int/bitstream/handle/10665/338044/9789240015241-eng.pdf?sequence=1.
W_req_high = 100 * 365 / 1000  # in kL per person per year, based on 100 L/p/day.
F_poverty_line_2011 = 335 * 12 # R / person / year (based on 335 R/p/month in 2011: https://www.statssa.gov.za/publications/P03101/P031012024.pdf, Table 2)
F_poverty_line_2016 = 498 * 12 # R / person / year (based on 498 R/p/month in 2016: https://www.statssa.gov.za/publications/P03101/P031012024.pdf, Table 2).
F_poverty_line_2022 = 663 * 12 # R / person / year (based on 663 R/p/month in 2022: https://www.statssa.gov.za/publications/P03101/P031012024.pdf, Table 2)
F_poverty_line_2023 = 760 * 12 # R / person / year (based on 760 R/p/month in 2022: https://www.statssa.gov.za/publications/P03101/P031012024.pdf, Table 2)
F_healthy_poverty_line_2022 = 3184/4 * 12 # R/person/year (based on 3184/household of 4/month in June 2022: https://www.bfap.co.za/wp-content/uploads/2023/04/Food-Inflation-brief_June-2022.pdf)
F_healthy_poverty_line_2023 = 4715/4 * 12 # R/person/year (based on 4715/household of 4/month in January 2023 according to Vermeulen et al. (2023), doi: 10.3389/fsufs.2023.1181683)
F_healthy_poverty_line_2011 = F_poverty_line_2011 * (F_healthy_poverty_line_2023 / F_poverty_line_2023)  # multiplied with factor of change between regular and healthy food basket in 2023
F_healthy_poverty_line_2016 = F_poverty_line_2016 * (F_healthy_poverty_line_2023 / F_poverty_line_2023)  # multiplied with factor of change between regular and healthy food basket in 2023

resource_reqs = {
    'W_req_low': W_req_low,
    'W_req_high': W_req_high,
    'E_req_low': 100, # in kWh per person per year, 100 is upper bound of SDG 7.
    'E_req_high': 300, # Modern Energy Minimum: MEM = 300 kWh/person/year
    'F_req_low': 1, # in food basket per person per year (because the food price is for a food basket)
    'F_req_high': 1 # in healthy food basket per person per year (because the food price is for a food basket)
}
# 0.3.1.2. Price of resources (per unit of required resource in 1.1.1.)
resource_price = {
    'E_price_2011': 0.523, # R/kWh, average Eskom price in 2011 from: https://jknvenergy.co.za/electricity-cost-per-kwh-south-africa/
    'E_price_2016': 0.8253, # R/kWh, average Eskom price in 2016 from: https://jknvenergy.co.za/electricity-cost-per-kwh-south-africa/
    'E_price_2022': 2.40, # R/kWh in August 2022 (from: https://www.eskom.co.za/distribution/residential-calculator/)
    'F_price_2011_low': F_poverty_line_2011,
    'F_price_2011_high': F_healthy_poverty_line_2011,
    'F_price_2016_low': F_poverty_line_2016,
    'F_price_2016_high': F_healthy_poverty_line_2016,
    'F_price_2022_low': F_poverty_line_2022,
    'F_price_2022_high': F_healthy_poverty_line_2022
}

water_tariffs = pd.read_csv(os.path.join(input_dir_processed + "Municipal_water_tariffs.csv"))

# accounting for free basic services:
free_basic_services = 'Yes'
free_basic_water = 'Yes'
free_basic_electricity = 'Yes'

# 0.3.2. Denominator (income)

# proxy income list based on Stats SA metadata for the census.
proxy_incomes = [0, 3200, 7200, 13576, 27153, 54306, 108612, 217223, 434446, 868893, 1737786, 4915200]
annual_wage_growth_rate = 0.054 # the average increase in the decade to 2022 according to https://www.focus-economics.com/country-indicator/south-africa/wages/

# 0.3.3. Thresholds for % of income spend on resource

poverty_thresholds = {
    'W_poverty': 0.03, # according to UN, see: https://www.un.org/en/global-issues/water
    'E_poverty': 0.10, # norm from the South African Department of Energy
    'F_poverty': 1, # because the required spending is already based on the food poverty line
}

# 0.4. ACCEPTABILITY INPUT DATA

# 0.4.1. WATER

W_interruptions_standard = 'WHO'

# dictionaries to convert water compliance scores to status based on the DWS Blue Drop Report thresholds:
# Microbiological:
micro_status = {
    "low_population" : {
    "Excellent" : 97,
    "Good" : 96,
    "Unacceptable" : 0
    },
    "high_population" : {
    "Excellent" : 99,
    "Good" : 98,
    "Unacceptable" : 0
    },
}

# Chemical - acute health:
chem_acute_status = {
    "low_population" : {
    "Excellent" : 97,
    "Good" : 95,
    "Unacceptable" : 0
    },
    "high_population" : {
    "Excellent" : 99,
    "Good" : 97,
    "Unacceptable" : 0
    },
}

# Chemical - chronic health:
chem_chronic_status = {
    "low_population" : {
    "Excellent" : 95,
    "Good" : 93,
    "Unacceptable" : 0
    },
    "high_population" : {
    "Excellent" : 97,
    "Good" : 95,
    "Unacceptable" : 0
    },
}

# 0.5 WEF INPUT DATA
# hotspot analysis:
threshold_value = 0.5

# 1. PREPROCESSING
# all the preprocessing steps can be commented out after an initial run with the raw data.

# 1.1. LOAD RAW DATASETS

# Paths: replace with personal data paths
path_CE11 = os.path.join(input_dir_raw + "CE_2011/2011_individual_entries")
path_CS16 = os.path.join(input_dir_raw + "CS_2016")
path_CE22 = os.path.join(input_dir_raw + "CE_2022")

# load household data
CE11_data = load_stata_files(path_CE11, "sa-census-2011-household-v1.1-20140618.dta")
CE22_data = load_stata_files(path_CE22, "sa-census-2022-household-v1.dta")

CE11_hh = CE11_data[0]
CS16_hh = load_csv_files(path_CS16, "cs-2016-household.csv")
CE22_hh = CE22_data[0]
CE22_hh['QID'] = CE22_hh['QID'].astype(int)
CE22_spatial_vars = load_csv_files(path_CE22, "Census2022sample_F18.csv")
CE22_hh = pd.merge(CE22_hh, CE22_spatial_vars, on='QID')
CE22_agri_hh = pd.read_csv(os.path.join(path_CE22, "CE22_agri_hh.csv"), delimiter=';')

# preprocess survey data: obtain only the entries that are included in the area scope
if area == 'rural':
    CE11_hh = select_rural_entries(CE11_hh, 'H_GEOTYPE')
    CS16_hh = select_rural_entries(CS16_hh, 'EA_GTYPE_C')
    CE22_hh = select_rural_entries(CE22_hh, 'Geo_type')
elif area == 'urban':
    CE11_hh = select_urban_entries(CE11_hh, 'H_GEOTYPE')
    CS16_hh = select_urban_entries(CS16_hh, 'EA_GTYPE_C')
    CE22_hh = select_urban_entries(CE22_hh, 'Geo_type')
else:
    pass

# preprocess 2016 CS data: split municipal column (of the shape CODE : Name, to two columns 'MN_CODE_2016' and
# 'MN_NAME_2016'
CS16_hh[['MN_CODE_2016', 'MN_NAME_2016']] = CS16_hh['MN_CODE_2016'].str.split(' : ', n=1, expand=True)
# rename the municipality code column to "LocalMunicipalityCode" to be consistent with the demarcations file:
CS16_hh = CS16_hh.rename(columns={'MN_CODE_2016': 'LocalMunicipalityCode', 'MN_NAME_2016': 'LocalMunicipalityName'})
CE22_hh = CE22_hh.rename(columns={'Municipality': 'LocalMunicipalityCode'})

# load spatial data
MUN_boundaries_11 = load_spatial_data_shp('MN', 2011, input_dir_raw)  # the relevant column are "MN_NAME" and "MN_CODE"
MUN_boundaries_16 = load_spatial_data_gdb('MN', 2016, input_dir_raw)  # the relevant columns are called "LocalMunicipalityName" and "LocalMunicipalityCode"
MUN_boundaries_16.loc[:, 'LocalMunicipalityName'] = MUN_boundaries_16['LocalMunicipalityName'].replace('New', 'Collins Chabane')
PR_boundaries = load_spatial_data_shp('PR', 2011, input_dir_raw)  # PR boundaries haven't changed

# for area calculations, use albers equal area projection on spatial demarcation data:
MUN_boundaries_16_EA = MUN_boundaries_16[['LocalMunicipalityCode', 'geometry']].to_crs(spatial_crs)
MUN_boundaries_16_EA[f"mun_area_m2_({spatial_crs})"] = MUN_boundaries_16_EA.geometry.area

# data on changes in municipal demarcations and namings across spatial datasets
MUN_changes_11_16 = pd.read_csv(os.path.join(input_dir_processed + "municipal_demarcations_mapping_20112016.csv"),
                                delimiter=';', encoding='latin1')
mun_mapping_CE22_agri = pd.read_csv(os.path.join(input_dir_processed + "mun_mapping_ce22agri_boundaries16.csv"), delimiter=';')

# load population data
pop_total = pd.read_csv(os.path.join(input_dir_processed + "Municipal_population_rural_urban_1994_2024.csv"))
# pop_total = pop_total.infer_objects(copy=False).interpolate() # linear interpolation to avoid missing values
pop_11 = pop_total[['LocalMunicipalityCode', '2011_Total']].copy()
pop_11 = pop_11.rename(columns={'2011_Total': 'Population_mun_2011'})
pop_22 = pop_total[['LocalMunicipalityCode', '2022_Total']].copy()
pop_22 = pop_22.rename(columns={'2022_Total': 'Population_mun_2022'})

# based on the year set in the input data
pop = pop_total[['LocalMunicipalityCode', f'{year}_Total', f'{year}_Rural']].copy()
pop = pop.rename(columns={f'{year}_Total': f'Population_mun_{year}', f'{year}_Rural': f'Population_rural_mun_{year}'})
population_column = f'Population_mun_{year}'
population_column_rural = f'Population_rural_mun_{year}'

# load household data for 2016:
hh = pd.read_csv(os.path.join(input_dir_processed + "hh_ruralurban_MUN_2016.csv"))

# obtain columns relevant for calculations per dataset
CE11_columns_for_calc = ['SN', 'H_MUNIC', 'HHLD_10PERCENT_WGT']
CS16_columns_for_calc = ['UqNo', 'LocalMunicipalityCode', 'LocalMunicipalityName', 'hhld_pstrwgt']
CE22_columns_for_calc = ['QID', 'LocalMunicipalityCode', 'HH_WGT']

### Study Area calculations: area, population, households:

hh = MUN_boundaries_16_EA.merge(hh, on='LocalMunicipalityCode', how='left')
hh["Households_share_rural"] = hh['Rural Households'] / hh['Total Households']
hh["Households_share_urban"] = hh['Urban Households'] / hh['Total Households']

# area_stats = hh.describe()
# area_stats.to_csv(os.path.join(output_dir_data, "municipal_background_stats_2016.csv"))
#
# # 1.2. AVAILABILITY DATA PREPROCESSING
#
# # 1.2.1. WATER
#
# # obtain water availability data from PCR-GLOB variables
# vars_for_map_16 = ['LocalMunicipalityCode', 'LocalMunicipalityName', 'geometry']
#
# w_availability_mun16 = gpd.read_file(os.path.join(input_dir_processed + "municipal_water_availability_2010_2019.gpkg"))
# w_availability_mun16 = w_availability_mun16[(vars_for_map_16 + water_availability_vars)]
# # summing separate water flows to obtain the total freshwater resource per municipality:
# w_availability_mun16['Q_total'] = w_availability_mun16[water_availability_vars].sum(axis=1)
#
# # Check how much of the total flow is made up by the separate flows:
# for var in water_availability_vars:
#     w_availability_mun16[f'{var}_%'] = w_availability_mun16[var] / w_availability_mun16['Q_total'] * 100
#
# w_availability_mun16 = w_availability_mun16.merge(pop, how='left', on='LocalMunicipalityCode')
# w_availability_mun16['Q_total_yr'] = 12 * w_availability_mun16['Q_total']
# w_availability_mun16['Q_total_cap_yr'] = w_availability_mun16['Q_total_yr'] / w_availability_mun16[population_column]
# w_availability_mun16['Falkenmark_cat'] = w_availability_mun16['Q_total_cap_yr'].apply(lambda x: numerical_to_categories(x, Falkenmark_thresholds_categorical))
# w_availability_mun16 = obtain_w_availability_score(w_availability_mun16, 'linear_minmax', min_val=w_min_cutoff, max_val=w_max_cutoff)
# w_availability_mun16 = obtain_w_availability_score(w_availability_mun16, 'categorical', thresholds_dict=w_availability_scores_categorical)
#
# # 1.2.2. ENERGY
#
# e_available_df = MUN_boundaries_16[['LocalMunicipalityCode', 'ProvinceName']].copy()
#
# # OPTION A: provincial electricity distribution data:
# # load provincial electricity distribution data (unit of electricity distributed is GWh)
# E_distributed = pd.read_csv(os.path.join(input_dir_processed + 'Electricity_distribution_2002_2025.csv'))
# E_distributed['Province'] = E_distributed['Province'].str.replace('North west', 'North West')
#
# # obtain provincial population by merging population & spatial dfs, grouping by province while summing population numbers:
# population = pop_total.merge(MUN_boundaries_16[['LocalMunicipalityCode', 'ProvinceName']], on='LocalMunicipalityCode')
# population = population.drop(columns=['LocalMunicipalityCode'])
# pop_province = population.groupby('ProvinceName', as_index=False).sum()
# pop_province = pop_province[['ProvinceName'] + [col for col in pop_province.columns if 'Total' in col]]
# pop_province.columns = pop_province.columns.str.replace('Total', 'Population', regex=False)
#
# # extract only the years that are present in the electricity distribution dataframe:
# year_list = range(2002,2025)
# pop_province = pop_province[['ProvinceName'] + [c for c in pop_province.columns if extract_year(c) and int(extract_year(c)) in year_list]]
#
# # Sum over the provinces to get SA total:
# totals = pop_province.select_dtypes(include='number').sum()
# new_row = totals.to_dict()
# new_row['ProvinceName'] = 'South Africa'
# pop_province_sa = pd.concat([pop_province, pd.DataFrame([new_row])], ignore_index=True)
#
# E_distributed = E_distributed.merge(pop_province_sa, left_on='Province', right_on='ProvinceName', how='left')
#
# for time_step in year_list:
#     # obtain annual electricity availability in GWh per year:
#     E_distributed.loc[:, f'Total_E_distributed_{time_step}_GWh'] = E_distributed[(col for col in E_distributed.columns if f'{time_step}' in col)].sum(axis=1)
#     # obtain E availability in GWh per capita by dividing total distributed electricity by provincial population:
#     E_distributed[f'Total_E_distributed_{time_step}_GWh_per_capita'] = E_distributed[f'Total_E_distributed_{time_step}_GWh'] / E_distributed[f'{time_step}_Population']
#
# E_distributed = E_distributed.drop(columns=['Province', 'Unit', 'Timestep'])
# E_distributed = E_distributed[['ProvinceName'] + [col for col in E_distributed.columns if not 'ProvinceName' in col]]
# E_distributed.to_csv(input_dir_processed + "Provincial_electricity_distribution_per_capita_2002_2025.csv", index=False)
#
# E_distributed_year = E_distributed[['ProvinceName', f'Total_E_distributed_{year}_GWh_per_capita']].copy()
#
# # Assign provincial availability values to all municipalities in that province:
# e_available_df['E_distributed_province'] = e_available_df['ProvinceName'].map(E_distributed_year.set_index('ProvinceName')[f'Total_E_distributed_{year}_GWh_per_capita'])
#
# # OPTION B: municipal values based on distribution grid density:
#
# # load data from OSM retrieved file:
# distribution_lines = gpd.read_file(os.path.join(input_dir_processed, "sa_infra.gpkg"), layer="power_lines")
# distribution_subs = gpd.read_file(os.path.join(input_dir_processed, "sa_infra.gpkg"), layer="substations")
#
# # convert all to Equal Area projection for area calculations:
# distribution_lines_EA = distribution_lines.to_crs(spatial_crs)
# distribution_subs_EA = distribution_subs.to_crs(spatial_crs)
# MUN_boundaries_16_EA = MUN_boundaries_16[['LocalMunicipalityCode', 'geometry']].to_crs(spatial_crs)
#
# # calculate area of municipality:
# MUN_boundaries_16_EA[f"mun_area_m2_({spatial_crs})"] = MUN_boundaries_16_EA.geometry.area
#
# # calculate length of minor lines & number of substations per municipality:
# # calculate length of each line and set each substation to one:
# distribution_lines_EA["length_m"] = distribution_lines_EA.geometry.length
# distribution_subs_EA['nr_substations'] = 1
#
# # join the municipalities df to the lines/substations dfs to have an attribute of the municipality:
# lines_in_mun = gpd.sjoin(distribution_lines_EA, MUN_boundaries_16_EA, how="inner", predicate="intersects")
# subs_in_mun = gpd.sjoin(distribution_subs_EA, MUN_boundaries_16_EA, how="inner", predicate='intersects')
#
# # group by local municipality to get total line length and total number of substations:
# line_length_per_mun = lines_in_mun.groupby("LocalMunicipalityCode", as_index=False)["length_m"].sum()
# line_length_per_mun.rename(columns={"length_m": "total_line_length_m"}, inplace=True)
# subs_in_mun = subs_in_mun.groupby('LocalMunicipalityCode', as_index=False)['nr_substations'].sum()
#
# # obtain final municipal dataset:
# line_length_per_mun = line_length_per_mun[['LocalMunicipalityCode', 'total_line_length_m']]
# subs_in_mun = subs_in_mun[['LocalMunicipalityCode', 'nr_substations']]
# power_infra_mun = line_length_per_mun.merge(subs_in_mun, on='LocalMunicipalityCode', how='outer')
# power_infra_mun = MUN_boundaries_16_EA.merge(power_infra_mun, on='LocalMunicipalityCode', how='left')
#
# # obtain number of households per municipality:
# hh_16 = hh[['LocalMunicipalityCode', 'Total Households']]
#
# # compute density of lines and nodes per municipal area/population/households:
# power_infra_mun = power_infra_mun.merge(pop, on='LocalMunicipalityCode', how='left')
# power_infra_mun = power_infra_mun.merge(hh_16, on='LocalMunicipalityCode', how='left')
# power_infra_mun["line_density_km_per_km2"] = (power_infra_mun["total_line_length_m"] / 1000) / (power_infra_mun[f"mun_area_m2_({spatial_crs})"] / 1e6)
# power_infra_mun["subst_density_nr_per_km2"] = power_infra_mun["nr_substations"] / (power_infra_mun[f"mun_area_m2_({spatial_crs})"] / 1e6)
# power_infra_mun["line_density_km_per_cap"] = (power_infra_mun["total_line_length_m"] / 1000) / power_infra_mun[population_column]
# power_infra_mun["subst_density_nr_per_cap"] = power_infra_mun["nr_substations"] / power_infra_mun[population_column]
# power_infra_mun["line_density_km_per_hh"] = (power_infra_mun["total_line_length_m"] / 1000) / power_infra_mun['Total Households']
# power_infra_mun["subst_density_nr_per_hh"] = power_infra_mun["nr_substations"] / power_infra_mun['Total Households']
#
# # density as in methods [km lines per squared kilometre per household]
# power_infra_mun['line_density_km_per_km2_per_hh'] = power_infra_mun["line_density_km_per_km2"] / power_infra_mun['Total Households']
# power_infra_mun['subst_density_nr_per_km2_per_hh'] = power_infra_mun["subst_density_nr_per_km2"] / power_infra_mun['Total Households']
#
# e_available_df = e_available_df.merge(power_infra_mun[['LocalMunicipalityCode', 'line_density_km_per_km2_per_hh', 'subst_density_nr_per_km2_per_hh']], on='LocalMunicipalityCode', how='left')
#
# # 1.2.3. FOOD
#
# # obtain food availability from separate datafile, pre-processed using a Jupyter Notebook.
# f_availability_mun16 = gpd.read_file(os.path.join(input_dir_processed + "municipal_food_availability_2010_2019.gpkg"))
#
# f_availability_mun16 = f_availability_mun16.drop(columns=['ProvinceCode', 'ProvinceName', 'DistrictMunicipalityCode',
#                                                           'DistrictMunicipalityName', 'Year']).copy()
#
# # merge with equal area mun projection for area:
# f_availability_mun16 = f_availability_mun16.merge(MUN_boundaries_16_EA, on='LocalMunicipalityCode', how='left')
#
# # crops: conversion to calories:
# for crop in ['Wheat', 'Maize']:
#     f_availability_mun16[f'{crop}_production_total_kcal'] = (f_availability_mun16[f'{crop}_production_total_kton'] *
#                                                              (10 ** 6) * fraction_edible[crop] * energy_density[crop])
#     f_availability_mun16[f'{crop}_production_total_g_protein'] = (f_availability_mun16[f'{crop}_production_total_kton'] *
#                                                              (10 ** 6) * fraction_edible[crop] * protein_density[crop])
# # livestock: conversion to calories
# for animal in ['Cattle', 'Sheep', 'Chicken']:
#     # 1 - convert densities to number of animals:
#     f_availability_mun16[f'{animal}_stock_total'] =  (f_availability_mun16[f'{animal}_density_mean'] *
#                                                       (f_availability_mun16[f"mun_area_m2_({spatial_crs})"] * 10 ** -6))
#     # 2.A - convert number of animals to calories produced from meat:
#     f_availability_mun16[f'{animal}_production_total_kcal'] = (f_availability_mun16[f'{animal}_stock_total'] *
#                                                                fraction_slaughtered[animal] * mass_carcass[animal] *
#                                                                fraction_edible[animal] * energy_density[animal])
#     # 2.B - convert number of animals to protein produced from meat:
#     f_availability_mun16[f'{animal}_production_total_g_protein'] = (f_availability_mun16[f'{animal}_stock_total'] *
#                                                                     fraction_slaughtered[animal] * mass_carcass[animal] *
#                                                                     fraction_edible[animal] * protein_density[animal])
#
# # calculate kcal per capita:
# # merge dataset with population data
# f_availability_mun16 = f_availability_mun16.merge(pop, on='LocalMunicipalityCode', how='left')
#
# # energy (kcal) calculations:
# kcal_cols = (col for col in f_availability_mun16.columns if 'kcal' in col)
# f_availability_mun16['Energy_supply_kcal'] = f_availability_mun16[kcal_cols].sum(axis=1)
# f_availability_mun16['Energy_supply_kcal_per_capita_per_day'] = (f_availability_mun16['Energy_supply_kcal'] / 365 /
#                                                                  f_availability_mun16[population_column])
# f_availability_mun16['Energy_supply_sufficiency'] = (f_availability_mun16['Energy_supply_kcal_per_capita_per_day'] /
#                                                      dietary_energy_reqs)
# # protein calculations:
# protein_cols = (col for col in f_availability_mun16.columns if 'protein' in col)
# f_availability_mun16['Protein_supply_g'] = f_availability_mun16[protein_cols].sum(axis=1)
# f_availability_mun16['Protein_supply_kcal'] = f_availability_mun16['Protein_supply_g'] * 4 # kcal per g protein
# f_availability_mun16['Protein_supply_g_per_capita_per_day'] = (f_availability_mun16['Protein_supply_g'] / 365 /
#                                                                f_availability_mun16[population_column])
# f_availability_mun16['Protein_supply_kcal_per_capita_per_day'] = (f_availability_mun16['Protein_supply_kcal'] / 365 /
#                                                                f_availability_mun16[population_column])
#
# for protein_fraction in [0.10, 0.225, 0.35]: # lower bound, mean and upper bound of 10-35% range of Acceptable Macronutrient Distribution Range.
#     dietary_protein_reqs = (protein_fraction * dietary_energy_reqs)
#     f_availability_mun16[f'Protein_supply_sufficiency_{protein_fraction}'] = (f_availability_mun16['Protein_supply_kcal_per_capita_per_day'] /
#                                                          dietary_protein_reqs)
#
# # combine into one availability file, avoiding duplicates (duplicates get suffix _DROP, which are then filtered out)
# wef_availability = w_availability_mun16.merge(e_available_df, on='LocalMunicipalityCode', suffixes=('', '_DROP')).filter(regex='^(?!.*_DROP)')
# wef_availability = wef_availability.merge(f_availability_mun16, on='LocalMunicipalityCode', suffixes=('', '_DROP')).filter(regex='^(?!.*_DROP)')
#
# # processed, sort and save dataframe:
# wef_availability = wef_availability[['LocalMunicipalityCode', 'LocalMunicipalityName', 'ProvinceName'] +
#                                     [col for col in wef_availability.columns if col not in ['LocalMunicipalityCode', 'LocalMunicipalityName', 'ProvinceName', population_column, 'Shape_Area', 'Shape_Length', 'area_km2', 'geometry', 'geometry_x', 'geometry_y']] +
#                                     [population_column, 'area_km2']]
# wef_availability.to_csv(os.path.join(output_dir_data, 'municipal_data', f'wef_availability_mun_{year}.csv'), index=False)
#
# # 1.3. ACCESSIBILITY DATA PREPROCESSING (can be commented out after initial run with spec input data)
#
# # obtain dataframes per year with columns relevant for accessibility
# CE11_access_cols = ['H07_WATERPIPED', 'H10_TOILET', 'H11_ENERGY_COOKING', 'H11_ENERGY_HEATING', 'H11_ENERGY_LIGHTING']
# CS16_access_cols = ['WaterSource', 'DistanceWater', 'Toilet', 'ToiletShared', 'ElectrAccess', 'AgricAct']
# CE22_access_cols = ['H05_WATERPIPED', 'H08_TOILET', 'H09_ENERGY_COOKING', 'H10_ENERGY_LIGHTING']
# access_df_11 = extract_relevant_columns_census_data(CE11_hh, CE11_access_cols, CE11_columns_for_calc).copy()
# access_df_16 = extract_relevant_columns_census_data(CS16_hh, CS16_access_cols, CS16_columns_for_calc).copy()
# access_df_22 = extract_relevant_columns_census_data(CE22_hh, CE22_access_cols, CE22_columns_for_calc).copy()
#
# # 1.3.1. WATER ACCESSIBILITY
#
# # make the categories for water access variables consistent across years (census categories are the default)
# access_df_16 = reform_w_access_vars_to_census_var(access_df_16)
#
# for W_access_piped_standard in ['NS', 'RDP', 'WHO']:
#     # calculate water accessibility scores based on the relevant variable (column):
#     access_df_11 = obtain_w_access_piped_score_hh(access_df_11, standard=W_access_piped_standard, water_access_col='H07_WATERPIPED')
#     access_df_16 = obtain_w_access_piped_score_hh(access_df_16, standard=W_access_piped_standard, water_access_col='WATERPIPED')
#     access_df_22 = obtain_w_access_piped_score_hh(access_df_22, standard=W_access_piped_standard, water_access_col='H05_WATERPIPED')
# #
# for W_sanitation_standard in ['NS', 'SA', 'WHO']:
#     # calculate sanitation scores based on relevant variable/column for two standards of scoring:
#     access_df_11 = obtain_w_access_sanitation_score_hh(access_df_11, standard=W_sanitation_standard, sanitation_col='H10_TOILET')
#     access_df_16 = obtain_w_access_sanitation_score_hh(access_df_16, standard=W_sanitation_standard, sanitation_col=['Toilet', 'ToiletShared'])
#     access_df_22 = obtain_w_access_sanitation_score_hh(access_df_22, standard=W_sanitation_standard, sanitation_col='H08_TOILET')
#
# # 1.3.2 ENERGY ACCESSIBILITY
#
# # calculate electricity accessibility score based on the relevant variables (columns):
# for sensitivity in ['Yes', None]:
#     access_df_11 = obtain_e_access_elect_score_hh(access_df_11, census_type='census', e_access_cols=['H11_ENERGY_COOKING', 'H11_ENERGY_HEATING', 'H11_ENERGY_LIGHTING'], sensitivity=sensitivity)
#     access_df_16 = obtain_e_access_elect_score_hh(access_df_16, census_type='community survey', e_access_cols='ElectrAccess', sensitivity=sensitivity)
#     access_df_22 = obtain_e_access_elect_score_hh(access_df_22, census_type='census', e_access_cols=['H09_ENERGY_COOKING', 'H10_ENERGY_LIGHTING'], sensitivity=sensitivity)
#
# # if energy accessibility is only based on indicator of electricity access (E_access_elec):
# access_df_11 = access_df_11.rename(columns={'E_access_elec': 'E_accessibility', 'E_access_elec_sensitivity': 'E_accessibility_sensitivity'})
# access_df_16 = access_df_16.rename(columns={'E_access_elec': 'E_accessibility', 'E_access_elec_sensitivity': 'E_accessibility_sensitivity'})
# access_df_22 = access_df_22.rename(columns={'E_access_elec': 'E_accessibility', 'E_access_elec_sensitivity': 'E_accessibility_sensitivity'})
#
# # 1.3.3. FOOD ACCESSIBILITY
#
# # INDICATOR A: INVOLVEMENT IN AGRICULTURE:
# # calculate food accessibility scores: household involved in agriculture = 1, household not involved in agriculture = 0.
# access_df_16 = obtain_f_access_agriculture_score_hh(access_df_16, food_access_col='AgricAct')
#
# # for 2022: % of households in agriculture (data not available at household level).
# f_access_vars_22 = ['Total_hh_22', 'Nr_agri_hh_2022']
# f_access_df_mun_22 = CE22_agri_hh[f_access_vars_22 + ['Local Municipality']].copy()
#
# # remove inconsistencies in municipality naming by mapping it to the 2016 municipal boundaries names
# f_access_df_mun_22 = f_access_df_mun_22.merge(mun_mapping_CE22_agri, on='Local Municipality', how='left')
# f_access_df_mun_22 = f_access_df_mun_22.drop(columns=['Local Municipality'], axis=1)
#
# # calculate accessibility score:
# f_access_df_mun_22['F_access_agri'] = (f_access_df_mun_22['Nr_agri_hh_2022'] / f_access_df_mun_22['Total_hh_22'])
# f_access_df_mun_22 = f_access_df_mun_22[['LocalMunicipalityCode', 'F_access_agri']]
#
# # INDICATOR B: DENSITY OF SUPERMARKETS:
# # load data from OSM retrieved file:
# supermarkets = gpd.read_file(os.path.join(input_dir_processed, "sa_infra.gpkg"), layer="supermarkets")
#
# # convert all to Equal Area projection for area calculations:
# supermarkets_EA = supermarkets.to_crs(spatial_crs)
#
# # calculate number of supermarkets per municipality:
# # a. set number to one to count:
# supermarkets_EA['nr_supermarkets'] = 1
# # b. join the municipalities df to the lines/substations dfs to have an attribute of the municipality:
# supermarkets_in_mun = gpd.sjoin(supermarkets_EA, MUN_boundaries_16_EA, how="inner", predicate='intersects')
# # c. group by local municipality to get total number of supermarkets:
# supermarkets_in_mun = supermarkets_in_mun.groupby('LocalMunicipalityCode', as_index=False)['nr_supermarkets'].sum()
#
# # obtain final municipal dataset:
# supermarkets_in_mun = supermarkets_in_mun[['LocalMunicipalityCode', 'nr_supermarkets']]
# food_infra_mun = MUN_boundaries_16_EA.merge(supermarkets_in_mun, on='LocalMunicipalityCode', how='left')
#
# # obtain number of households per municipality:
# hh_16 = hh[['LocalMunicipalityCode', 'Total Households']]
#
# # compute density of supermarkets per municipal area/population/households:
# food_infra_mun = food_infra_mun.merge(pop, on='LocalMunicipalityCode', how='left')
# food_infra_mun = food_infra_mun.merge(hh_16, on='LocalMunicipalityCode', how='left')
# food_infra_mun["market_density_nr_per_km2"] = food_infra_mun["nr_supermarkets"] / (food_infra_mun[f"mun_area_m2_({spatial_crs})"] / 1e6)
# food_infra_mun["market_density_nr_per_cap"] = food_infra_mun["nr_supermarkets"] / food_infra_mun[population_column]
# food_infra_mun["market_density_nr_per_hh"] = food_infra_mun["nr_supermarkets"] / food_infra_mun['Total Households']
#
# # density as in methods [nr of supermarkets per square kilometre per household]
# food_infra_mun['market_density_nr_per_km2_per_hh'] = food_infra_mun["market_density_nr_per_km2"] / food_infra_mun['Total Households']
# food_infra_mun = food_infra_mun.drop(columns='geometry')
#
# # ALL ACCESSIBILITY INDICATORS
# # processed, sort and save household dataframes on accessibility to CSV:
# access_df_11 = access_df_11[CE11_columns_for_calc + [col for col in access_df_11.columns if col not in CE11_columns_for_calc]]
# access_df_11.to_csv(os.path.join(output_dir_data, 'household_data', 'we_accessibility_hh_2011.csv'), index=False)
# access_df_16 = access_df_16[CS16_columns_for_calc + [col for col in access_df_16.columns if col not in CS16_columns_for_calc]]
# access_df_16.to_csv(os.path.join(output_dir_data, 'household_data', 'wef_accessibility_hh_2016.csv'), index=False)
# access_df_22 = access_df_22[CE22_columns_for_calc + [col for col in access_df_22.columns if col not in CE22_columns_for_calc]]
# access_df_22.to_csv(os.path.join(output_dir_data, 'household_data', 'we_accessibility_hh_2022.csv'), index=False)
# # processed, sort and save municipal dataframes on accessibility to CSV:
# f_access_df_mun_22.to_csv(os.path.join(output_dir_data, 'municipal_data', 'f_accessibility_agri_mun_22.csv'), index=False)
# food_infra_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'f_accessibility_infra_mun.csv'), index=False)
#
# # 1.4. AFFORDABILITY DATA PREPROCESSING (can be commented out after initial run with spec input data)
#
# # setting variables and data according to the year chosen for municipal boundaries in the input data section above:
# columns_for_calc = ['HHLD_10PERCENT_WGT', "LocalMunicipalityCode", 'SN']
#
# # columns in census data required for calculations (2011 specific)
# income_census_cols = ['DERH_INCOME_CLASS', 'DERH_HSIZE']
# income_df = extract_relevant_columns_census_data(CE11_hh, income_census_cols, CE11_columns_for_calc)
# income_df = create_proxy_income_column(income_df, income_column='DERH_INCOME_CLASS', income_proxy_list=proxy_incomes)
# income_df = extrapolate_income(income_df, annual_wage_growth_rate, year)
#
# # add mapping to 2016 municipal boundary demarcations and specific names used in the water tariffs CSV:
# income_df = income_df.merge(MUN_changes_11_16, left_on='H_MUNIC', right_on='CE_2011', how='left')
# # fix merging of Khâi-Ma municipal code manually:
# income_df.loc[income_df['H_MUNIC'] == 'Khâi-Ma', 'LocalMunicipalityCode'] = 'NC067'
#
# # calculation of household requirements and costs of resources:
# afford_df = calculate_hh_reqs(income_df, resource_reqs)
# # for energy and food costs (national average price):
# afford_df = calculate_hh_costs(afford_df, resource_price, free_basic_electricity='Yes')
# # for water costs (municipality specific and block tariffs):
# afford_df = calculate_w_costs_mun_block_tariffs(afford_df, water_tariffs, year, 'Yes')
# # calculate the percentage of income spend on each resource
# afford_df = calculate_affordability_perc(afford_df)
# # calculate the scores for the affordability domain based on poverty thresholds
# afford_df = obtain_hh_affordability_score(afford_df, poverty_thresholds, year, 'Yes')
#
# # extract columns relevant for mapping affordability
# cost_share_cols = [col for col in afford_df.columns if '%' in col]
# afford_score_cols = [col for col in afford_df.columns if 'affordability' in col]
# afford_cols = cost_share_cols + afford_score_cols
# afford_df_hh = extract_relevant_columns_census_data(afford_df, afford_cols, columns_for_calc)
#
# # export household affordability data to csv:
# afford_df_hh = afford_df_hh[['LocalMunicipalityCode', 'HHLD_10PERCENT_WGT'] + [col for col in afford_df_hh.columns if col not in ['LocalMunicipalityCode', 'HHLD_10PERCENT_WGT']]]
# afford_df_hh.to_csv(os.path.join(output_dir_data, 'household_data', f'wef_affordability_hh_2011_{year}.csv'), index=False)

# # 1.5. ACCEPTABILITY DATA PREPROCESSING (can be commented out after initial run with spec input data)
#
# # obtain dataframes per year with columns relevant for acceptability, for census and community survey data
# CE11_accept_cols = ['H09_WATERSUPPLY', 'H09A_WATERSUPPLY', 'H09B_ALT_WATERSOURCE', 'H11_ENERGY_COOKING',
#                     'H11_ENERGY_LIGHTING', 'H11_ENERGY_HEATING', 'H13_STOVE', 'H13_REFRIDGERATOR']
# CS16_accept_cols = ['MunicDiff', 'WaterInterrupt', 'WaterInterruptTime', 'WaterInterrupt2days', 'AltSource', 'RateWater',
#                     'ElectrInterrupt', 'ElecInterruptTime', 'RateElectricity', 'EnergyCook', 'EnergyLight',
#                     'EnergySpaceHeat', 'EnergyWaterHeat', 'SkipMeal', 'FreqSkipMeal', 'HHgoods__1',
#                     'HHgoods__2']
# CE22_accept_cols = ['H07A_WATERSUPPLY', 'H09_ENERGY_COOKING', 'H10_ENERGY_LIGHTING', 'A4_ADULT_HUNGER',
#                     'A5_CHILD_HUNGER', 'H12_ELECTRIC_GAS_STOVE', 'H12_REFRIGERATOR']
# accept_df_11 = extract_relevant_columns_census_data(CE11_hh, CE11_accept_cols, CE11_columns_for_calc).copy()
# accept_df_16 = extract_relevant_columns_census_data(CS16_hh, CS16_accept_cols, CS16_columns_for_calc).copy()
# accept_df_22 = extract_relevant_columns_census_data(CE22_hh, CE22_accept_cols, CE22_columns_for_calc).copy()
#
# # 1.5.1. WATER
#
# # Municipal water acceptability scores based on the relevant survey variables:
# accept_df_16 = obtain_perception_score_cs(accept_df_16, 'Water')
# for threshold in ['WHO', 'SA']:
#     accept_df_11 = obtain_w_interruptions_score(accept_df_11, ['H09_WATERSUPPLY', 'H09A_WATERSUPPLY'],
#                                                 threshold=threshold)
#     accept_df_16 = obtain_w_interruptions_score(accept_df_16, ['WaterInterrupt', 'WaterInterrupt2days'],
#                                                 threshold=threshold)
# accept_df_22 = obtain_w_interruptions_score(accept_df_22, 'H07A_WATERSUPPLY')
#
# # Municipal water quality scores (based on blue drop report 2023):
# w_accept_22_mun = pd.read_csv(os.path.join(input_dir_processed, "BDR_municipality.csv"), delimiter=';', index_col=False)
#
# # convert numerical scores (%) into categoricals based on report:
# w_accept_22_mun["Micro_status_2023"] = categorize_water_quality_compliance_scores(w_accept_22_mun, "Compliance_micro_2023", micro_status)
# w_accept_22_mun["Chem_acute_status_2023"] = categorize_water_quality_compliance_scores(w_accept_22_mun, "Compliance_chem_acute_2023", chem_acute_status)
# w_accept_22_mun["Chem_chronic_status_2023"] = categorize_water_quality_compliance_scores(w_accept_22_mun, "Compliance_chem_chron_2023", chem_chronic_status)
# w_accept_22_mun = w_accept_22_mun.drop(columns=['Population_2023'])
#
# # convert percentages to decimal numbers:
# w_quality_score_columns = ['BlueDropScore_2014', 'BlueDropScore_2023', 'Compliance_micro_2023',
#                            'Compliance_chem_acute_2023', 'Compliance_chem_chron_2023']
# for column in w_quality_score_columns:
#     w_accept_22_mun[column] = w_accept_22_mun[column] / 100
#
# w_accept_16_mun = w_accept_22_mun[['LocalMunicipalityCode', 'LocalMunicipalityName', 'BlueDropScore_2014']]
#
# # combine multiple scores into one quality score
# for aggregation in ['mean', 'limiting_factor']:
#     # 'W_accept_compliance': combination of microbiological and two chemical compliance scores
#     w_accept_22_mun = aggregate_indicators_into_score(w_accept_22_mun, 'W_accept_compliance', [col for col in w_accept_22_mun.columns if 'Compliance' in col], aggregation)
#     # W_accept_quality: combination of microbiological and two chemical compliance scores as well as the blue drop score:
#     w_accept_22_mun = aggregate_indicators_into_score(w_accept_22_mun, 'W_accept_quality', [col for col in w_quality_score_columns if '2023' in col], aggregation)
#
# bluedrop = w_accept_22_mun.copy()
# w_accept_22_mun = w_accept_22_mun.drop(columns=['DistrictMunicipalityCode', 'DistrictMunicipalityName'])
#
# # save municipal scores to csv
# bluedrop.to_csv(os.path.join(output_dir_data, 'municipal_data', 'municipal_bluedrop_water_quality_scores_2023.csv'))
# w_accept_16_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'w_acceptability_bdr_mun_2016.csv'))
# w_accept_22_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'w_acceptability_bdr_mun_2022.csv'))
#
# # 1.5.2. ENERGY
# # calculate fuel acceptability score based on the relevant variables (columns):
# accept_df_11 = obtain_e_accept_fuel_score_hh(accept_df_11, e_fuel_cols=['H11_ENERGY_COOKING', 'H11_ENERGY_HEATING', 'H11_ENERGY_LIGHTING'])
# accept_df_16 = obtain_e_accept_fuel_score_hh(accept_df_16, e_fuel_cols=['EnergyCook', 'EnergyLight', 'EnergySpaceHeat', 'EnergyWaterHeat'])
# accept_df_22 = obtain_e_accept_fuel_score_hh(accept_df_22, e_fuel_cols=['H09_ENERGY_COOKING', 'H10_ENERGY_LIGHTING'])
#
# # For 2016 Community Survey, there are additional variables for energy acceptability, namely occurrence of interruptions and
# # rated quality (perception of acceptability).
# accept_df_16 = obtain_e_interruptions_score_cs(accept_df_16, threshold='Yes')
# accept_df_16 = obtain_perception_score_cs(accept_df_16, 'Electricity')
# for aggregation in ['mean', 'limiting_factor']:
#     accept_df_16 = aggregate_indicators_into_score(accept_df_16, 'E_acceptability', ['E_interruptions', 'E_accept_fuel'], aggregation)
#
# # for 2011 and 2022 data, only the fuel acceptability is an indicator for energy acceptability, so set:
# accept_df_11['E_acceptability'] = accept_df_11['E_accept_fuel']
# accept_df_22['E_acceptability'] = accept_df_22['E_accept_fuel']
#
# # for 2016, the perception of the electricity grid is given as sensitivity analysis for the energy acceptability domain:
# accept_df_16['E_acceptability_sensitivity'] = accept_df_16['Electricity_perception']
#
# # 1.5.3. FOOD
#
# # calculate food acceptability scores based on the relevant variables (columns)
# accept_df_16 = obtain_f_acceptability_score_cs(accept_df_16, threshold='No')
# accept_df_16['F_acceptability_sensitivity'] = accept_df_16['F_acceptability']
# accept_df_16 = obtain_f_acceptability_score_cs(accept_df_16, threshold='Yes')
# for aggregation_method in ['mean', 'limiting_factor']:
#     accept_df_22 = obtain_f_acceptability_score_ce(accept_df_22, 'Yes', aggregation_method)
#
# # sort and save files to CSV:
# accept_df_11 = accept_df_11[CE11_columns_for_calc + [col for col in accept_df_11.columns if col not in CE11_columns_for_calc]]
# accept_df_11.to_csv(os.path.join(output_dir_data, 'household_data', 'we_acceptability_hh_2011.csv'), index=False)
# accept_df_16 = accept_df_16[CS16_columns_for_calc + [col for col in accept_df_16.columns if col not in CS16_columns_for_calc]]
# accept_df_16.to_csv(os.path.join(output_dir_data, 'household_data', 'wef_acceptability_hh_2016.csv'), index=False)
# accept_df_22 = accept_df_22[CE22_columns_for_calc + [col for col in accept_df_22.columns if col not in CE22_columns_for_calc]]
# accept_df_22.to_csv(os.path.join(output_dir_data, 'household_data', 'wef_acceptability_hh_2022.csv'), index=False)

# 2. PROCESSING OF WEF-4As data
# If you start with the processed data, start from here.

# # 2.1. AVAILABILITY DATA PROCESSING
#
# # load dataframe that is created in the pre-processing phase
# wef_availability = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_availability_mun_{year}.csv'))
#
# # 2.1.1. WATER
# # not required, already converted to numerical scores in pre-processing
#
# # 2.1.2. ENERGY
#
# # Method A: (provincial electricity distribution data)
# # Compute provincial availability score (normalized version of annual provincial electricity distributed in GWh per capita)
# wef_availability = normalize_max(wef_availability, ['E_distributed_province'])
# wef_availability['E_availability_prov'] = wef_availability['E_distributed_province_n']
#
# # Method B: (municipal infrastructure)
# # conversion of energy infrastructure values using logarithmic conversion:
# # density as in methods [km lines per squared kilometre per household]
# line_col = 'line_density_km_per_km2_per_hh'
# subst_col = 'subst_density_nr_per_km2_per_hh'
# wef_availability = normalize_log(wef_availability, [line_col, subst_col])
# wef_availability = normalize_minmax(wef_availability, [f'{line_col}_log', f'{subst_col}_log'])
#
# wef_availability = aggregate_indicators_into_score(wef_availability, 'E_infra_density',
#                                                        [f'{line_col}_log_n', f'{subst_col}_log_n'],
#                                                        aggregation_method='maximum')
#
# if year == 2016:
#     wef_availability['E_availability'] = wef_availability['E_infra_density_maximum'] * EAF_2016
#     wef_availability['E_availability_subst_only'] = wef_availability[f'{subst_col}_log_n'] * EAF_2016
#     wef_availability['E_availability_lines_only'] = wef_availability[f'{line_col}_log_n'] * EAF_2016
# elif year == 2022:
#     wef_availability['E_availability'] = wef_availability['E_infra_density_maximum'] * EAF_2022
#     wef_availability['E_availability_subst_only'] = wef_availability[f'{subst_col}_log_n'] * EAF_2022
#     wef_availability['E_availability_lines_only'] = wef_availability[f'{line_col}_log_n'] * EAF_2022
# else:
#     Warning(print("No energy availability factor is specified for the year of choice, indicator is ignored."))
#     wef_availability['E_availability'] = wef_availability['E_infra_density_maximum']
#     wef_availability['E_availability_subst_only'] = wef_availability[f'{subst_col}_log_n']
#     wef_availability['E_availability_lines_only'] = wef_availability[f'{line_col}_log_n']
#
# # have the missing data as sensitivity:
# wef_availability['E_availability_sensitivity_OSM'] = wef_availability['E_availability']
#
# for col in ['E_availability', 'E_availability_subst_only', 'E_availability_lines_only']:
#     wef_availability[col] = wef_availability[col].fillna(0)
#
# # 2.1.3. FOOD
# # set threshold for food availability: above 100% sufficiency is always 1.
# for column in ['Energy_supply_sufficiency', 'Protein_supply_sufficiency_0.1', 'Protein_supply_sufficiency_0.225',
#                'Protein_supply_sufficiency_0.35']:
#     wef_availability[f'{column}_n'] = wef_availability[column].clip(upper=1)
#
# # calculate combined "food availability" scores (var "F_availability") based on desired combination method of the
# # two previously calculated variables of "Energy_supply_sufficiency" and "Protein_supply_sufficiency", and based on set
# # protein requirement as fraction of MDER:
# for protein_fraction in [0.1, 0.225, 0.35]:
#     wef_availability[f'F_availability_protein_only_rp_{protein_fraction}'] = wef_availability[f'Protein_supply_sufficiency_{protein_fraction}_n']
#     for aggregation in ['mean', 'limiting_factor']:
#         wef_availability = aggregate_indicators_into_score(wef_availability, f'F_availability_rp_{protein_fraction}',
#                                                            ['Energy_supply_sufficiency_n',
#                                                             f'Protein_supply_sufficiency_{protein_fraction}_n'],
#                                                            aggregation_method=aggregation)
#
# wef_availability['F_availability_energy_only'] = wef_availability['Energy_supply_sufficiency_n']
#
# # save adjusted dataframe:
# wef_availability = wef_availability[['LocalMunicipalityCode'] + [col for col in wef_availability.columns if col not in ['LocalMunicipalityCode']]]
# wef_availability.to_csv(os.path.join(output_dir_data, 'municipal_data', f'wef_availability_mun_{year}.csv'), index=False)
#
# # 2.2. ACCESSIBILITY DATA PROCESSING
#
# # Load files that were created in the preprocessing phase:
# access_df_11 = pd.read_csv(os.path.join(input_dir_clean, 'household_data', 'we_accessibility_hh_2011.csv'))
# access_df_16 = pd.read_csv(os.path.join(input_dir_clean, 'household_data', 'wef_accessibility_hh_2016.csv'))
# access_df_22 = pd.read_csv(os.path.join(input_dir_clean, 'household_data', 'we_accessibility_hh_2022.csv'))
# f_access_df_22 = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', 'f_accessibility_agri_mun_22.csv'))
# f_access_df_infra = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', 'f_accessibility_infra_mun.csv'))
#
# # aggregating indicators into one domain score for water:
# for aggregation in ['mean', 'limiting_factor']:
#     # combine scores of piped water and sanitation access into a combined "Water Accessibility" score:
#     access_df_11 = obtain_w_accessibility_score_hh(access_df_11, aggregation_method=aggregation)
#     access_df_16 = obtain_w_accessibility_score_hh(access_df_16, aggregation_method=aggregation)
#     access_df_22 = obtain_w_accessibility_score_hh(access_df_22, aggregation_method=aggregation)
#
# # extract the accessibility scores:
# access_cols_11 = [col for col in access_df_11.columns if 'access' in col]
# access_cols_16 = [col for col in access_df_16.columns if 'access' in col]
# access_cols_22 = [col for col in access_df_22.columns if 'access' in col]
#
# # aggregating final domain data from households to municipality using a weighted average:
# access_df_11_mun = aggregating_data_wgt_avg(access_df_11, 'H_MUNIC', 'HHLD_10PERCENT_WGT',
#                                             access_cols_11)
# access_df_16_mun = aggregating_data_wgt_avg(access_df_16, 'LocalMunicipalityCode', 'hhld_pstrwgt',
#                                            access_cols_16)
# access_df_22_mun = aggregating_data_wgt_avg(access_df_22, 'LocalMunicipalityCode', 'HH_WGT',
#                                             access_cols_22)
#
# # after aggregation to municipality, add municipal food accessibility scores to 2022 dataframe:
# access_df_22_mun = access_df_22_mun.merge(f_access_df_22, on='LocalMunicipalityCode')
#
# # compute food supply chain infrastructure (supermarkets) indicator score:
# supermarkets_col = 'market_density_nr_per_km2_per_hh'
# f_access_df_infra = normalize_log(f_access_df_infra, [supermarkets_col])
# f_access_df_infra = normalize_minmax(f_access_df_infra, [f'{supermarkets_col}_log'])
# f_access_df_infra = f_access_df_infra[['LocalMunicipalityCode', f'{supermarkets_col}_log_n']]
#
# # merge food infra df with access dfs for each year and take maximum of the two:
# access_df_16_mun = access_df_16_mun.merge(f_access_df_infra, on='LocalMunicipalityCode', how='left')
# access_df_22_mun = access_df_22_mun.merge(f_access_df_infra, on='LocalMunicipalityCode', how='left')
#
# access_df_16_mun = aggregate_indicators_into_score(access_df_16_mun, f'F_accessibility',
#                                                             ['F_access_agri', f'{supermarkets_col}_log_n'],
#                                                             aggregation_method='maximum')
# access_df_22_mun = aggregate_indicators_into_score(access_df_22_mun, f'F_accessibility',
#                                                             ['F_access_agri', f'{supermarkets_col}_log_n'],
#                                                             aggregation_method='maximum')
#
# access_df_16_mun['F_accessibility_infra_only'] = access_df_16_mun[f'{supermarkets_col}_log_n']
# access_df_16_mun['F_accessibility_agri_only'] = access_df_16_mun['F_access_agri']
# access_df_22_mun['F_accessibility_infra_only'] = access_df_22_mun[f'{supermarkets_col}_log_n']
# access_df_22_mun['F_accessibility_agri_only'] = access_df_22_mun['F_access_agri']
#
# # save dataframes of municipal data to CSV:
# access_df_11_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'we_accessibility_mun_2011.csv'), index=False)
# access_df_16_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'wef_accessibility_mun_2016.csv'), index=False)
# access_df_22_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'wef_accessibility_mun_2022.csv'), index=False)
#
# # 2.3. AFFORDABILITY DATA PROCESSING
#
# # Load files that were created in the preprocessing phase:
# afford_df_hh = pd.read_csv(os.path.join(input_dir_clean, 'household_data', f'wef_affordability_hh_2011_{year}.csv'))
#
# # aggregating data to municipality
# # for cols with share of income spend on resource: obtain min, max and weighted average
# cost_share_cols = [col for col in afford_df_hh.columns if '%' in col]
# afford_df_mun_1 = aggregating_data_min_max_wgt_avg(afford_df_hh, 'LocalMunicipalityCode', 'HHLD_10PERCENT_WGT',
#                                                    cost_share_cols)
# # for cols with affordability score: obtain only weighted average (scores range from 0-1 by default)
# afford_score_cols = [col for col in afford_df_hh.columns if 'affordability' in col]
# afford_df_mun_2 = aggregating_data_wgt_avg(afford_df_hh, 'LocalMunicipalityCode', 'HHLD_10PERCENT_WGT',
#                                            afford_score_cols)
#
# # merge the two aggregated dataframes
# afford_df_mun_elaborate = pd.merge(afford_df_mun_1, afford_df_mun_2, on='LocalMunicipalityCode')
#
# # save to CSV
# afford_df_mun_elaborate.to_csv(os.path.join(output_dir_data, 'municipal_data', f'wef_affordability_mun_2011_{year}.csv'))

# # 2.4. ACCEPTABILITY DATA PROCESSING
#
# # Load files that were created in the preprocessing phase:
# accept_df_11 = pd.read_csv(os.path.join(output_dir_data, 'household_data', 'we_acceptability_hh_2011.csv'))
# accept_df_16 = pd.read_csv(os.path.join(output_dir_data, 'household_data', 'wef_acceptability_hh_2016.csv'))
# accept_df_22 = pd.read_csv(os.path.join(output_dir_data, 'household_data', 'wef_acceptability_hh_2022.csv'))
# w_accept_df_16 = pd.read_csv(os.path.join(output_dir_data, 'municipal_data', 'w_acceptability_bdr_mun_2016.csv'))
# w_accept_df_22 = pd.read_csv(os.path.join(output_dir_data, 'municipal_data', 'w_acceptability_bdr_mun_2022.csv'))
#
# cols_accept_score_cs = ['W_interruptions_SA', 'W_interruptions_WHO', 'Water_perception', 'E_interruptions', 'Electricity_perception', 'E_acceptability_sensitivity',
#                         'E_accept_fuel', 'E_acceptability_mean', 'E_acceptability_limiting_factor', 'F_acceptability', 'F_acceptability_sensitivity']
# cols_accept_score_ce11 = ['W_interruptions_SA', 'W_interruptions_WHO', 'E_acceptability']
# cols_accept_score_ce22 = ['W_interruptions', 'E_acceptability', 'F_acceptability_mean', 'F_acceptability_limiting_factor',
#                         'adult_hunger_numeric', 'child_hunger_numeric']
#
# # weighted average to reduce individual entries to municipal aggregates
# accept_df_11_mun = aggregating_data_wgt_avg(accept_df_11, 'H_MUNIC', 'HHLD_10PERCENT_WGT',
#                                             cols_accept_score_ce11)
# accept_df_16_mun = aggregating_data_wgt_avg(accept_df_16, 'LocalMunicipalityCode', 'hhld_pstrwgt',
#                                             cols_accept_score_cs)
# accept_df_22_mun = aggregating_data_wgt_avg(accept_df_22, 'LocalMunicipalityCode', 'HH_WGT',
#                                             cols_accept_score_ce22)
#
# accept_df_16_mun['E_acceptability_fuel_only'] = accept_df_16_mun['E_accept_fuel']
#
# # add water quality parameters to municipal dataframe:
# accept_df_16_mun = accept_df_16_mun.merge(w_accept_df_16, on='LocalMunicipalityCode')
# accept_df_22_mun = accept_df_22_mun.merge(w_accept_df_22, on='LocalMunicipalityCode')
#
# # combine W_acceptability as combination of interruptions and blue drop score:
# for aggregation in ['mean', 'limiting_factor']:
#     accept_df_22_mun = aggregate_indicators_into_score(accept_df_22_mun, 'W_acceptability', ['W_interruptions', 'BlueDropScore_2023'], aggregation)
#     for W_interruptions_standard in ['SA', 'WHO']:
#         accept_df_16_mun = aggregate_indicators_into_score(accept_df_16_mun, f'W_acceptability_{W_interruptions_standard}', [f'W_interruptions_{W_interruptions_standard}', 'BlueDropScore_2014'], aggregation)
#
# # save files to CSV:
# # aggregated to municipality:
# accept_df_11_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'we_acceptability_mun_2011.csv'), index=False)
# accept_df_16_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'wef_acceptability_mun_2016.csv'), index=False)
# accept_df_22_mun.to_csv(os.path.join(output_dir_data, 'municipal_data', 'wef_acceptability_mun_2022.csv'), index=False)
#
# # obtain household datasets:
# wef_hh_11 = access_df_11[[col for col in access_df_11.columns if not 'HHLD_10PERCENT_WGT' in col]].merge(afford_df_hh, on='SN')
# wef_hh_11 = wef_hh_11.merge(accept_df_11[[col for col in accept_df_11.columns if not 'HHLD_10PERCENT_WGT' in col and not 'H_MUNIC' in col]], on='SN')
# wef_hh_16 = access_df_16[[col for col in access_df_16.columns if not 'hhld_pstrwgt' in col and not 'LocalMunicipalityCode' in col]].merge(accept_df_16, on='UqNo')
# wef_hh_22 = access_df_22[[col for col in access_df_22.columns if not 'HH_WGT' in col and not 'LocalMunicipalityCode' in col]].merge(accept_df_22, on='QID')
#
# wef_hh_11 = wef_hh_11[['H_MUNIC', 'HHLD_10PERCENT_WGT'] + [col for col in wef_hh_11.columns if 'access' in col or 'accept' in col or 'interruptions' in col or '2011' in col]]
# wef_hh_16 = wef_hh_16[['LocalMunicipalityCode', 'hhld_pstrwgt'] + [col for col in wef_hh_16.columns if 'access' in col or 'accept' in col or 'perception' in col or 'interruptions' in col]]
# wef_hh_22 = wef_hh_22[['LocalMunicipalityCode', 'HH_WGT'] + [col for col in wef_hh_22.columns if 'access' in col or 'acceptability' in col or 'interruptions' in col]]
#
# wef_hh_11.to_csv(os.path.join(output_dir_data, 'household_data', 'wef_hh_2011.csv'), index=False)
# wef_hh_16.to_csv(os.path.join(output_dir_data, 'household_data', 'wef_hh_2016.csv'), index=False)
# wef_hh_22.to_csv(os.path.join(output_dir_data, 'household_data', 'wef_hh_2022.csv'), index=False)

# # 3.0 PROCESSING OF WEF-4AS DATA INTO SECURITY DATA, STATISTICS AND PLOTS
#
# # if you start with the cleaned data, you can comment out everything before here.
#
# # 3.1: compiling combined WEF-4As dataset:
#
# MUN_boundaries_16 = load_spatial_data_gdb('MN', 2016, input_dir_raw)  # the relevant columns are called "LocalMunicipalityName" and "LocalMunicipalityCode"
# MUN_boundaries_16.loc[:, 'LocalMunicipalityName'] = MUN_boundaries_16['LocalMunicipalityName'].replace('New', 'Collins Chabane')
#
# # Merge municipal datasets of availability, accessibility, affordability and acceptability:
# wef_availability = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_availability_mun_{year}.csv'))
# wef_accessibility = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_accessibility_mun_{year}.csv'))
# wef_affordability = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_affordability_mun_2011_{year}.csv'))
# wef_acceptability = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_acceptability_mun_{year}.csv'))
# wef_dfs = [wef_availability, wef_accessibility, wef_affordability, wef_acceptability]
# wef_security = reduce(lambda left, right: pd.merge(left, right, on="LocalMunicipalityCode", how='outer'), wef_dfs)
#
# # have one dataset with all variants of the domain scores "elaborate" with all latest year values:
# avail_cols = [col for col in wef_security.columns if 'availability' in col]
# access_cols = [col for col in wef_security.columns if 'accessibility' in col]
# afford_cols = [col for col in wef_security.columns if "affordability" in col and f'{year}' in col]
# accept_cols = [col for col in wef_security.columns if 'acceptability' in col]
#
# domain_cols = avail_cols + access_cols + afford_cols + accept_cols
# wef_security_elaborate = wef_security[['LocalMunicipalityCode'] + domain_cols].copy()
#
# # Save WEF security dataset to CSV
# wef_security_elaborate.to_csv(os.path.join(output_dir_data, 'municipal_data', f'wef_4As_elaborate_mun_{year}.csv'), index=False)
#
# # get descriptive statistics of dataframe:
# wef_security_elaborate_stats = obtain_descriptive_statistics_df(wef_security_elaborate)
# # get spatial statistics of dataframe:
# wef_security_elaborate_spatial_stats = obtain_spatial_statistics_df(wef_security_elaborate, MUN_boundaries_16,
#                                                           'LocalMunicipalityCode', domain_cols)
#
# # save combined stats
# wef_security_elaborate_stats = wef_security_elaborate_stats.merge(wef_security_elaborate_spatial_stats, on='column', how='left')
# wef_security_elaborate_stats.to_csv(os.path.join(output_dir_data + f"wef_security_elaborate_stats_{year}.csv"), index=False)
#
# # have one dataset with only the chosen variants of the domain scores "reduced":
# # extract only final domain scores from data based on preferences set in input data (standards, aggregation methods, resource requirements):
# avail_cols_reduced = [f'W_availability_{w_availability_threshold}', 'E_availability', f'F_availability_rp_{protein_fraction}_{aggregation_method}']
# access_cols_reduced = [f'W_accessibility_{W_access_piped_standard}_{W_sanitation_standard}_{aggregation_method}',
#                        'E_accessibility', 'F_accessibility_maximum']
# afford_cols_reduced = [f'W_affordability_{reqs}reqs_{year}', f'E_affordability_{reqs}reqs_{year}', f'F_affordability_{reqs}reqs_{year}']
# if year == 2016:
#     accept_cols_reduced = [f'W_acceptability_{W_interruptions_standard}_{aggregation_method}', f'E_acceptability_{aggregation_method}', 'F_acceptability']
# elif year == 2022:
#     accept_cols_reduced = [f'W_acceptability_{aggregation_method}', 'E_acceptability', f'F_acceptability_{aggregation_method}']
# else:
#     accept_cols_reduced = ['W_acceptability', 'E_acceptability', 'F_acceptability']
#     Warning(print("Year should be either 2011, 2016 or 2022."))
#
# final_domain_cols = avail_cols_reduced + access_cols_reduced + afford_cols_reduced + accept_cols_reduced
# wef_security_reduced = wef_security[['LocalMunicipalityCode'] + final_domain_cols].copy()
#
# # calculate W, E, F security values based on the lowest score (i.e., minimum value across water domain scores)
# # and limiting security aspect (i.e., security aspect with the lowest score) per resource:
# for resource in ['W', 'E', 'F']:
#     vars = [col for col in wef_security_reduced.columns if f'{resource}_' in col]
#     wef_security_reduced[f'{resource}_security_mean'] = wef_security_reduced[vars].mean(axis=1)
#     wef_security_reduced[f'{resource}_limiting_domain_value'] = wef_security_reduced[vars].min(axis=1)
#     wef_security_reduced[f'{resource}_limiting_domain'] = wef_security_reduced[vars].idxmin(axis=1)
#
# for aspect in ['availability', 'accessibility', 'affordability', 'acceptability']:
#     vars = [col for col in wef_security_reduced.columns if f'_{aspect}' in col]
#     wef_security_reduced[f'{aspect}_mean'] = wef_security_reduced[vars].mean(axis=1)
#     wef_security_reduced[f'{aspect}_limiting_domain_value'] = wef_security_reduced[vars].min(axis=1, skipna=True)
#     wef_security_reduced[f'{aspect}_limiting_domain'] = wef_security_reduced[vars].idxmin(axis=1, skipna=True)
#
#
# # calculate WEF security values based on mean, lowest score (i.e., minimum value across all domain scores)
# # and limiting security aspect (i.e., security aspect with the lowest score):
# wef_security_reduced['WEF_security_mean'] = wef_security_reduced[['W_security_mean', 'E_security_mean', 'F_security_mean']].mean(axis=1)
# wef_security_reduced['WEF_limiting_domain_value'] = wef_security_reduced[final_domain_cols].min(axis=1)
# wef_security_reduced['WEF_limiting_domain'] = wef_security_reduced[final_domain_cols].idxmin(axis=1)
#
# # calculate hotspots: number of domains below threshold value:
# wef_security_reduced[f'Nr_domains_below_{threshold_value}'] = (wef_security_reduced[final_domain_cols] <= threshold_value).sum(1)
# resource_cols_limiting = ['W_limiting_domain_value', 'E_limiting_domain_value', 'F_limiting_domain_value']
# wef_security_reduced[f'Nr_resource_lims_below_{threshold_value}'] = (wef_security_reduced[resource_cols_limiting] <= threshold_value).sum(1)
# dimension_cols_limiting = ['availability_limiting_domain_value', 'accessibility_limiting_domain_value',
#                            'affordability_limiting_domain_value', 'acceptability_limiting_domain_value']
# wef_security_reduced[f'Nr_dimension_lims_below_{threshold_value}'] = (wef_security_reduced[dimension_cols_limiting] <= threshold_value).sum(1)
#
# # statistics
# wef_security_reduced_stats = obtain_descriptive_statistics_df(wef_security_reduced)
# cols = (final_domain_cols + [col for col in wef_security_reduced.columns if 'limiting_domain_value' in col] +
#         [col for col in wef_security_reduced.columns if 'mean' in col] +
#         [col for col in wef_security_reduced.columns if '_below_' in col] )
# wef_security_reduced_spatial_stats = obtain_spatial_statistics_df(wef_security_reduced, MUN_boundaries_16,
#                                                           'LocalMunicipalityCode', cols)
# wef_security_reduced_stats = wef_security_reduced_stats.merge(wef_security_reduced_spatial_stats, on='column', how='left')
#
# # correlation stats:
# corr_table_wef4as = pg.pairwise_corr(wef_security_reduced[final_domain_cols], method='pearson')
# corr_table_wef4as.to_csv(os.path.join(output_dir_data, f'wef_4As_correlations_{year}.csv'), index=False)
# col_lims = resource_cols_limiting + dimension_cols_limiting
# corr_table_limiting = pg.pairwise_corr(wef_security_reduced[col_lims], method='pearson')
# corr_table_limiting.to_csv(os.path.join(output_dir_data, f'limiting_domains_correlations_{year}.csv'), index=False)

# # Save WEF security and stats datasets to CSV
# wef_security_reduced.to_csv(os.path.join(output_dir_data, 'municipal_data', f'wef_4As_reduced_mun_{year}.csv'), index=False)
# wef_security_reduced_stats.to_csv(os.path.join(output_dir_data + f"wef_security_reduced_stats_{year}.csv"), index=False)
#
# ### SENSITIVITY ANALYSIS:
# baseline_domains_map = {parse_domain(col): col for col in final_domain_cols}
#
# domain_variations = defaultdict(list)
# for col in domain_cols:
#     parts = col.split("_")
#     if len(parts) < 3:
#         continue
#     resource = parts[0]
#     aspect = parts[1]
#     domain_variations[(resource, aspect)].append(col)
#
# sensitivity_records = []
#
# for (resource, aspect), baseline_col in baseline_domains_map.items():
#
#     # all possible replacements for this domain
#     alternatives = domain_variations[(resource, aspect)]
#
#     # # skip the canonical itself
#     # alternatives = [c for c in alternatives if c != baseline_col]
#
#     for alt_col in alternatives:
#
#         # --- BUILD TEMP DOMAIN SET (11 same, 1 replaced) ---
#         modified_domain_cols = []
#         for (r, a), canon in baseline_domains_map.items():
#             if (r, a) == (resource, aspect):
#                 modified_domain_cols.append(alt_col)
#             else:
#                 modified_domain_cols.append(canon)
#
#         # Create a temporary dataframe for calculations
#         df_temp = wef_security_elaborate.copy()
#
#         # --- RECOMPUTE W/E/F statistics ---
#         for R in ['W', 'E', 'F']:
#             vars_R = [col for col in modified_domain_cols if col.startswith(f"{R}_")]
#             df_temp[f"{R}_security_mean"] = df_temp[vars_R].mean(axis=1, skipna=True)
#             df_temp[f"{R}_limiting_domain_value"] = df_temp[vars_R].min(axis=1, skipna=True)
#             df_temp[f"{R}_limiting_domain"] = df_temp[vars_R].idxmin(axis=1, skipna=True)
#
#         # --- RECOMPUTE dimension statistics ---
#         for A in ['availability','accessibility','affordability','acceptability']:
#             vars_A = [col for col in modified_domain_cols if f"_{A}" in col]
#             df_temp[f"{A}_mean"] = df_temp[vars_A].mean(axis=1, skipna=True)
#             df_temp[f"{A}_limiting_domain_value"] = df_temp[vars_A].min(axis=1, skipna=True)
#             df_temp[f"{A}_limiting_domain"] = df_temp[vars_A].idxmin(axis=1, skipna=True)
#
#         # --- GLOBAL WEF ---
#         df_temp["WEF_security_mean"] = df_temp[["W_security_mean","E_security_mean","F_security_mean"]].mean(axis=1, skipna=True)
#         df_temp["WEF_limiting_domain_value"] = df_temp[modified_domain_cols].min(axis=1, skipna=True)
#         df_temp["WEF_limiting_domain"] = df_temp[modified_domain_cols].idxmin(axis=1, skipna=True)
#
#         # --- COLLECT SUMMARY STATISTICS ---
#
#         scenario_info = {
#             "Baseline domain": baseline_col,
#             "Alternative domain": alt_col
#         }
#
#         derived_stats = collect_stats(df_temp, scenario_info)
#         sensitivity_records.append(derived_stats)
#
# sensitivity_df = pd.DataFrame(sensitivity_records)
# sensitivity_df = sensitivity_df[["Baseline domain", "Alternative domain"] +
#                                 [col for col in sensitivity_df.columns if 'Alternative_domain' in col] +
#                                 [col for col in sensitivity_df.columns if 'W_limiting' in col] +
#                                 [col for col in sensitivity_df.columns if 'E_limiting' in col] +
#                                 [col for col in sensitivity_df.columns if 'F_limiting' in col] +
#                                 [col for col in sensitivity_df.columns if 'availability_limiting' in col] +
#                                 [col for col in sensitivity_df.columns if 'accessibility_limiting' in col] +
#                                 [col for col in sensitivity_df.columns if 'affordability_limiting' in col] +
#                                 [col for col in sensitivity_df.columns if 'acceptability_limiting' in col]
# ]
# sensitivity_df.to_csv(os.path.join(output_dir_data + f'wef_sensitivity_stats_{year}.csv'), index=False)
#

# 3. MAPPING

# reload the spatial data:
MUN_boundaries_16 = load_spatial_data_gdb('MN', 2016, input_dir_raw)  # the relevant columns are called "LocalMunicipalityName" and "LocalMunicipalityCode"
MUN_boundaries_16.loc[:, 'LocalMunicipalityName'] = MUN_boundaries_16['LocalMunicipalityName'].replace('New', 'Collins Chabane')
PR_boundaries = load_spatial_data_shp('PR', 2011, input_dir_raw)  # PR boundaries haven't changed
spatial_df = MUN_boundaries_16[['ProvinceName', 'LocalMunicipalityCode', 'LocalMunicipalityName', 'geometry']]

# load the WEF security dataset:
wef_security_reduced = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_4As_reduced_mun_{year}.csv'))
stats = pd.read_csv(os.path.join(input_dir_clean, f'wef_security_reduced_stats_{year}.csv'))

# merge with spatial dataset containing geometries and ensure that it is seen as a geodataframe:
wef_security_reduced_geo = wef_security_reduced.merge(spatial_df, on='LocalMunicipalityCode', how='outer')
wef_security_reduced_geo = gpd.GeoDataFrame(wef_security_reduced_geo, geometry="geometry", crs=spatial_df.crs)

domain_cols = [col for col in wef_security_reduced.columns if 'W_' in col or 'E_' in col or 'F_' in col]
domain_cols_categorical = [col for col in domain_cols if 'limiting_domain' in col and 'value' not in col]
domain_cols_continuous = [col for col in domain_cols if col not in domain_cols_categorical]
domain_cols_twelve = [col for col in domain_cols if 'mean' not in col and 'domain' not in col]

# load the WEF security dataset:
wef_security_elaborate = pd.read_csv(os.path.join(input_dir_clean, 'municipal_data', f'wef_4As_elaborate_mun_{year}.csv'))
wef_security_elaborate_geo = wef_security_elaborate.merge(spatial_df, on='LocalMunicipalityCode', how='outer')
wef_security_elaborate_geo = gpd.GeoDataFrame(wef_security_elaborate_geo, geometry="geometry", crs=spatial_df.crs)
domain_cols_elaborate = [col for col in wef_security_elaborate.columns if 'LocalMunicipalityCode' not in col]

# map_multiple_columns(wef_security_elaborate_geo, domain_cols_elaborate, area=area, spatial_demarcation_gdf=PR_boundaries, path=output_dir_maps, year=year)

# plot_scattermatrix_group_regression(wef_security_reduced_geo, domain_cols_twelve, 'ProvinceName', 'WEF-4As domains', output_dir_figures, year)
#
# plot_scattermatrix_group_regression(wef_security_reduced_geo, ['W_security_mean','E_security_mean', 'F_security_mean'], 'ProvinceName', 'combined resource', output_dir_figures, year)
# plot_scattermatrix_group_regression(wef_security_reduced_geo, ['W_limiting_domain_value','E_limiting_domain_value', 'F_limiting_domain_value'], 'ProvinceName', 'limiting WEF', output_dir_figures, year)
# plot_scattermatrix_group_regression(wef_security_reduced_geo, ['availability_limiting_domain_value','accessibility_limiting_domain_value', 'affordability_limiting_domain_value', 'acceptability_limiting_domain_value'], 'ProvinceName', 'limiting dimension', output_dir_figures, year)

# wef_security_reduced_geo = wef_security_reduced_geo.merge(pop, on='LocalMunicipalityCode', how='left')
# pop_col = population_column_rural
# for security_aspect in ['availability', 'accessibility', 'affordability', 'acceptability']:
#     vars = [col for col in wef_security_reduced_geo if f'_{security_aspect}' in col]
#     plot_scattermatrix_group_regression(wef_security_reduced_geo, vars, 'ProvinceName', plot_name=f'{security_aspect}', path=output_dir_figures, year=year)
#
# for resource in ['W', 'E', 'F']:
#     vars = [col for col in wef_security_reduced_geo if f'{resource}_a' in col]
#     plot_scattermatrix_group_regression(wef_security_reduced_geo, vars, 'ProvinceName', f'{resource}', output_dir_figures, year=year)


# GREYS4 = trimmed_greys()
#
# dimension_layout = {
#     'availability': {"cmap": GREYS4, "label": "A1"},
#     'accessibility': {"cmap": GREYS4, "label": "A2"},
#     'affordability': {"cmap": GREYS4, "label": "A3"},
#     'acceptability': {"cmap": GREYS4, "label": "A4"},
# }
#
# resource_layout = {
#     'W_': {"base_color": rgb255_to_rgba(68, 114, 196,1), "label": "W"},
#     'E_': {"base_color": rgb255_to_rgba(255, 192, 0, 1), "label": "E"},
#     'F_': {"base_color": rgb255_to_rgba(112, 173, 71, 1), "label": "F"}
# }
#
# for item in ['availability', 'accessibility', 'affordability', 'acceptability']:
#
#     wef_security_reduced_geo = apply_styles(
#         wef_security_reduced_geo,
#         domain_col=f"{item}_limiting_domain",
#         value_col=f"{item}_limiting_domain_value",
#         mode="dimension",
#         layout_dict=resource_layout,
#         colour_column = f'{item}_limiting_domain_value_colours'
#     )
#
# for item in ['W', 'E', 'F']:
#
#     wef_security_reduced_geo = apply_styles(
#         wef_security_reduced_geo,
#         domain_col=f"{item}_limiting_domain",
#         value_col=f"{item}_limiting_domain_value",
#         mode="resource",
#         layout_dict=dimension_layout,
#         colour_column = f'{item}_limiting_domain_value_colours'
#     )
#
# wef_security_reduced_geo = apply_styles(
#     wef_security_reduced_geo,
#     domain_col="WEF_limiting_domain",
#     value_col="WEF_limiting_domain_value",
#     mode="wef",
#     layout_dict=resource_layout,
#     colour_column='WEF_limiting_domain_colours'
# )

# ### PLOT SPATIAL HOTSPOT ANALYSIS:
map_hotspots(wef_security_reduced_geo, column=f'Nr_domains_below_{threshold_value}', area=area,
             spatial_demarcation_gdf=PR_boundaries, path=output_dir_maps)

# map_hotspots(wef_security_reduced_geo, column=[f'Nr_resource_lims_below_{threshold_value}',
#                                                f'Nr_dimension_lims_below_{threshold_value}',
#                                                f'Nr_domains_below_{threshold_value}'], area=area,
#              spatial_demarcation_gdf=PR_boundaries, path=output_dir_maps, stats_df=stats)


# # PLOT GRID: WEF-4As and aggregation plots in one grid:
# nrows = 5
# ncols = 4
#
# columns = {
#     f'W_availability_{w_availability_threshold}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     'E_availability': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     f'F_availability_rp_{protein_fraction}_{aggregation_method}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     "availability_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     f'W_accessibility_{W_access_piped_standard}_{W_sanitation_standard}_{aggregation_method}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     'E_accessibility': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     'F_accessibility_maximum': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     "accessibility_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     f'W_affordability_{reqs}reqs_{year}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     f'E_affordability_{reqs}reqs_{year}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     f'F_affordability_{reqs}reqs_{year}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     "affordability_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     f'W_acceptability_{W_interruptions_standard}_{aggregation_method}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     f'E_acceptability_{aggregation_method}': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     'F_acceptability': {'plot_func':plot_map_for_grid, 'correlation':'Yes'},
#     "acceptability_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     "W_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     "E_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     "F_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None},
#     "WEF_limiting_domain": {'plot_func':plot_hatch_map_for_grid, 'correlation':None}
# }
#
# plot_name = f'WEF_4As_{year}_full_aggregation'
# plot_grid_maps(gdf=wef_security_reduced_geo, columns_dict=columns, spatial_demarcation_gdf=PR_boundaries,
#                plot_name=plot_name, path=output_dir_maps, dimensions_layout=dimension_layout, resource_layout=resource_layout,
#                stats_gdf=stats)


### HEATMAP

# # to ensure E_availability (though never the limiting factor) is included in the heat map it is added as a category:
# domain_order = ['availability', 'accessibility', 'affordability', 'acceptability']
#
# for resource in ['W', 'E', 'F']:
#     wef_security_reduced_geo[f'{resource}_limiting_domain'] = (
#         wef_security_reduced_geo[f'{resource}_limiting_domain'].astype('category'))
#
#     existing_cats = wef_security_reduced_geo[f'{resource}_limiting_domain'].cat.categories.tolist()
#
#     for aspect in domain_order:
#         prefix = f'{resource}_{aspect}'
#         # Check if any category contains this prefix, if not add prefix as category:
#         if not any(prefix in cat for cat in existing_cats):
#             wef_security_reduced_geo[f'{resource}_limiting_domain'] = (
#                 wef_security_reduced_geo[f'{resource}_limiting_domain']
#                 .cat.add_categories([prefix])
#             )
#
# create_heatmap(wef_security_reduced_geo, 'W_limiting_domain', 'E_limiting_domain', output_dir_figures, year, domain_order, domain_order)
# create_heatmap(wef_security_reduced_geo, 'W_limiting_domain', 'F_limiting_domain', output_dir_figures, year, domain_order, domain_order)
# create_heatmap(wef_security_reduced_geo, 'E_limiting_domain', 'F_limiting_domain', output_dir_figures, year, domain_order, domain_order)
#

# ### Spatial analysis: overlay with former Apartheid law areas:
#
# # # load datasets:
# apartheid_areas = gpd.read_file(os.path.join(input_dir_processed, "FormerHomelands_and_Act9Areas"))
# apartheid_areas = apartheid_areas.to_crs(epsg=3857)
# apartheid_areas = apartheid_areas.rename(columns={'sde_sde_bd': 'AreaName'})
# act9_areas = apartheid_areas[apartheid_areas['AreaType'] == 'Act9'][['AreaName', 'AreaType', 'geometry']]
# homeland_areas = apartheid_areas[apartheid_areas['AreaType'] == 'Homeland'][['AreaName', 'AreaType', 'geometry']]
# MUN_boundaries_16 = MUN_boundaries_16.to_crs(epsg=3857)
# MUN_boundaries_16 = MUN_boundaries_16[['LocalMunicipalityCode', 'geometry']]
#
# spatial_sensitivity = add_special_area_flags(MUN_boundaries_16, act9_areas, 'act9_area')
# spatial_sensitivity = add_special_area_flags(spatial_sensitivity, homeland_areas, 'homeland')
# spatial_sensitivity = spatial_sensitivity.drop('geometry', axis=1)
# spatial_sensitivity = spatial_sensitivity.merge(wef_security_reduced_geo, on='LocalMunicipalityCode', how='left')
#
# spatial_sensitivity_results = []
#
# variable_cols = [col for col in spatial_sensitivity.columns if 'W_' in col or 'E_' in col or 'F_' in col or 'WEF_' in col
#                or 'availability_' in col or 'accessibility_' in col or 'affordability_' in col or 'accessibility_' in col]
# variable_cols_categorical = [col for col in domain_cols if 'limiting_domain' in col and 'value' not in col]
# variable_cols_numerical = [col for col in domain_cols if col not in domain_cols_categorical]
#
# for area in ['act9_area', 'homeland']:
#     contains_col = f'contains_{area}'
#     adjacent_col = f'adjacent_to_{area}'
#
#     masks = {
#     'all_municipalities': np.ones(len(spatial_sensitivity), dtype=bool),
#     'contains': (spatial_sensitivity[contains_col] == 1),
#     'adjacent_only': ((spatial_sensitivity[contains_col] == 0) & (spatial_sensitivity[adjacent_col] == 1)),
#     'non_adjacent': ((spatial_sensitivity[contains_col] == 0) & (spatial_sensitivity[adjacent_col] == 0)),
#     'non_containing_all': (spatial_sensitivity[contains_col] == 0)
#     }
#
#     for subset_name, mask in masks.items():
#         means = spatial_sensitivity.loc[mask, variable_cols_numerical].mean()
#
#         means_df = (means.rename('mean_value').reset_index().rename(columns={'index': 'variable'}))
#
#         means_df['area_type'] = area
#         means_df['subset'] = subset_name
#
#         spatial_sensitivity_results.append(means_df)
#
# spatial_sensitivity_results = pd.concat(spatial_sensitivity_results, ignore_index=True)
# spatial_sensitivity_results.to_csv(os.path.join(output_dir_data, f'spatial_sensitivity_stats_{year}.csv'))

# font = FontProperties(family='Times New Roman', weight='bold', size=10)
#
# # columns = [col for col in wef_security_elaborate_geo if 'W_availability' in col]
# columns = ['E_accessibility', 'E_accessibility_sensitivity']
# n = len(columns)
#
# # --- layout: max 3 columns ---
# ncols = min(2, n)
# nrows = math.ceil(n / ncols)
#
# fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5*ncols, 4*nrows), constrained_layout=True)
#
# # make axs always iterable (even if 1 row)
# axs = axs.flatten() if isinstance(axs, (list, np.ndarray)) else [axs]
#
# vmin, vmax = 0, 1
# cmap = cmc.devon_r
#
# for i, col in enumerate(columns):
#     ax = axs[i]
#
#     wef_security_elaborate_geo.plot(
#         ax=ax,
#         column=col,
#         cmap=cmap,
#         vmin=vmin,
#         vmax=vmax,
#         legend=False,
#         edgecolor='black',
#         linewidth=0.25,
#         missing_kwds={'color': 'lightcoral', 'edgecolor':'black'}
#     )
#
#     PR_boundaries.plot(ax=ax, facecolor='none', edgecolor='black')
#     cx.add_basemap(ax, source=cx.providers.CartoDB.PositronNoLabels)
#     ax.axis('off')
#
#     mean = round(wef_security_elaborate_geo[col].mean(), 2)
#     ax.text(0.02, 0.98, f"mean = {mean}",
#             transform=ax.transAxes,
#             fontsize=10, font="Times New Roman",
#             verticalalignment='top')
#
# # remove unused axes (if any)
# for j in range(i + 1, len(axs)):
#     fig.delaxes(axs[j])
#
# # --- shared colorbar ---
# norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)
# sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
# sm._A = []
#
# cbar = fig.colorbar(
#     sm,
#     ax=axs[:n],          # only the used axes
#     location='right',
#     fraction=0.05,
#     pad=0.02,
#     shrink=0.8           # adjust height if desired
# )
#
# axs[0].set_title('Energy accessibility (baseline)', font_properties=font)
# axs[1].set_title('Energy accessibility (grid access only)', font_properties=font)
# axs[2].set_title('Water accessibility (SA sanitation standard)', font_properties=font)
# axs[3].set_title('Water accessibility (SA standards for both)', font_properties=font)
# axs[4].set_title('Food availability (protein sufficiency only)', font_properties=font)

# plt.savefig(os.path.join(output_dir_maps, 'E_accessibility_sensitivity_maps.jpeg'))
# plt.close(fig)