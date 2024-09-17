import geopandas as gpd
import matplotlib.pyplot as plt
import webbrowser
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium, folium_static

def load_data():
    green_water_flows_2007 = gpd.read_file("raw_data/Green_water_flows/hist_green.shp")
    blue_water_flows_2007 = gpd.read_file("raw_data/Blue_water_flows/hist_blue.shp")
    white_water_flows_2007 = gpd.read_file("raw_data/White_water_flows/hist_white.shp")

    green_columns = {"GREEN01": "January",
                     "GREEN02": "February",
                     "GREEN03": "March",
                     "GREEN04": "April",
                     "GREEN05": "May",
                     "GREEN06": "June",
                     "GREEN07": "July",
                     "GREEN08": "August",
                     "GREEN09": "September",
                     "GREEN10": "October",
                     "GREEN11": "November",
                     "GREEN12": "December",
                     "GREEN13": "Annual"}
    blue_columns = {"SIMQMEAN01": "January",
                    "SIMQMEAN02": "February",
                    "SIMQMEAN03": "March",
                    "SIMQMEAN04": "April",
                    "SIMQMEAN05": "May",
                    "SIMQMEAN06": "June",
                    "SIMQMEAN07": "July",
                    "SIMQMEAN08": "August",
                    "SIMQMEAN09": "September",
                    "SIMQMEAN10": "October",
                    "SIMQMEAN11": "November",
                    "SIMQMEAN12": "December",
                    "SIMQMEAN13": "Annual"}
    green_water_flows_2007.rename(columns=green_columns, inplace=True)
    blue_water_flows_2007.rename(columns=blue_columns, inplace=True)
    white_water_flows_2007.rename(columns={"WHITE13": "Annual"}, inplace=True)

    return green_water_flows_2007, blue_water_flows_2007, white_water_flows_2007


# load data
green_water_flows_2007, blue_water_flows_2007, white_water_flows_2007 = load_data()

# # Make a dropdown menu
# create dictionary coupling dataframes to dataset names
water_dataframes = {
    "Green": green_water_flows_2007,
    "Blue": blue_water_flows_2007,
    "White": white_water_flows_2007
}

# Use session state to remember the user's choices
if "water_type" not in st.session_state:
    st.session_state.water_type = "Green"

if "period" not in st.session_state:
    st.session_state.period = "January"

st.session_state.water_type = st.selectbox("Choose dataset", list(water_dataframes.keys()), index=list(water_dataframes.keys()).index(st.session_state.water_type))

df = water_dataframes[st.session_state.water_type]

# set period options depending on selected dataset
if st.session_state.water_type == "White":
    periods = ["Annual"]
else:
    periods = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
               'November', 'December', 'Annual']

st.session_state.period = st.selectbox("Choose time period", periods, index=periods.index(st.session_state.period))

# filter data based on selection criteria
selected_data = df[[st.session_state.period, "geometry"]]

# Create streamlit and plot the empty map
st.title("Water flows in 2007 [mm]")
st.write("A map of periodic water flows in mm")
x_map = df.centroid.x.mean()
y_map = df.centroid.y.mean()
map = folium.Map(location=[x_map, y_map], zoom_start=4)

# add data from geodataframe to the map
folium.GeoJson(selected_data, tooltip=selected_data[st.session_state.period]).add_to(map)

folium_static(map, width=1000)

# Through html with the explore function
# map = blue_water_flows_2007.explore()
# map_file = r"C:\Github\SA_WEF_dataset\map.html"
# map.save(map_file)
# webbrowser.open(map_file)

# Through html on streamlit

# @st.cache_data()
# def get_map_data(file):
#     Html_file = open(file, 'r', encoding='utf-8')
#     map_html = Html_file.read()
#     return map_html
#
# map_html = get_map_data(map_file)
#
# with st.container():
#     components.html(map_html, width=1000, height=1000)


# # Show df
# st.text(green_water_flows)

# st.multiselect for multiple items in list