import pandas as pd
import os

input_data = "C:/Github/SA_WEF_dataset/raw_data/2016_community_survey"

CS16_hh = pd.read_csv(os.path.join(input_data, "cs-2016-household.csv"), encoding='latin-1')

print(CS16_hh.columns.values.tolist())

def obtain_shares(dataset, dataset_name, column_list):
    # calculate total number of counts per question based on column names corresponding to the answers
    # TODO check whether to include or exclude unspecified / not applicable in total (or no access)
    dataset[f'{dataset_name}_total'] = dataset[column_list].sum(axis=1)

    # TODO check whether to exclude certain categories for % calculation
    for column in column_list:
        dataset[f'{column}_%'] = dataset[column] / dataset[f'{dataset_name}_total']

    return dataset

for column in ['MunicDiff', 'LMuniSolve', 'RateWater', 'RateRefuse', 'RateElectricity', 'RateToilet',
               'RateHospital', 'RateClinic', 'HealthImportance', 'LivingCondImportance', 'HHAssetsImportance',
               'EmploymentImportance', 'SafetyImportance', 'WaterSource', 'DistanceWater', 'WaterAccess',
               'WaterSupplier', 'WaterInterrupt', 'WaterInterruptTime', 'WaterInterrupt2days', 'AltSource',
               'Toilet', 'ToiletLocation', 'ToiletShared', 'MaintainToilet', 'ElectrAccess', 'ElectrSupplier',
               'ElectrInterrupt', 'ElecInterruptTime', 'MainDwellType', 'TenureStat', 'TitleDeed', 'SubsDwell',
               'RDPQuality', 'EnergyCook', 'EnergyLight', 'EnergyWaterHeat', 'EnergySpaceHeat',
               'EnergySource_Electricity', 'EnergySource_Paraffin', 'EnergySource_Gas', 'EnergySource_Candles',
               'EnergySource_Coal', 'EnergySource_Firewood', 'EnergySource_SolarSystem', 'EnergySource_Carbatteries',
               'EnergySource_Otherbatteries', 'EnergySource_Generator', 'EnergySource_Other', 'SafetyInDay',
               'SafetyInDark', 'CrimeExperience__5', 'AgricAct', 'AgricType__1', 'AgricType__2', 'AgricType__3',
               'AgricType__4', 'AgricType__5', 'AgricType__6', 'AgricType__7', 'FarmPrac', 'OwnLivestock', 'Cattle',
               'Sheep', 'Goats', 'Pigs', 'Chickens', 'OtherPoultry', 'FoodMoney', 'FreqOutOfFood', 'SkipMeal',
               'FreqSkipMeal', 'PR_CODE_2011', 'DC_MDB_C_2011', 'MN_CODE_2011', 'PR_CODE_2016', 'DC_MDB_C_2016',
               'MN_CODE_2016', 'EA_GTYPE_C', 'hhld_pstrwgt']:

    # labels to columns > columns_list is labels

    CS16_hh = obtain_shares(CS16_hh, column, column_list=None)
