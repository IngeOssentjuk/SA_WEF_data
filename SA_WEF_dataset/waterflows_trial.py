import geopandas as gpd
import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm


# Load your data (this would typically be cached)
@st.cache_data
def load_data():
    green_water_flows_2007 = gpd.read_file("raw_data/Green_water_flows/hist_green.shp")
    blue_water_flows_2007 = gpd.read_file("raw_data/Blue_water_flows/hist_blue.shp")
    white_water_flows_2007 = gpd.read_file("raw_data/White_water_flows/hist_white.shp")

    # Rename columns
    green_columns = {"GREEN01": "January", "GREEN02": "February", "GREEN03": "March", "GREEN04": "April",
                     "GREEN05": "May", "GREEN06": "June", "GREEN07": "July", "GREEN08": "August",
                     "GREEN09": "September", "GREEN10": "October", "GREEN11": "November",
                     "GREEN12": "December", "GREEN13": "Annual"}
    green_water_flows_2007.rename(columns=green_columns, inplace=True)

    blue_columns = {"SIMQMEAN01": "January", "SIMQMEAN02": "February", "SIMQMEAN03": "March",
                    "SIMQMEAN04": "April", "SIMQMEAN05": "May", "SIMQMEAN06": "June",
                    "SIMQMEAN07": "July", "SIMQMEAN08": "August", "SIMQMEAN09": "September",
                    "SIMQMEAN10": "October", "SIMQMEAN11": "November", "SIMQMEAN12": "December",
                    "SIMQMEAN13": "Annual"}
    blue_water_flows_2007.rename(columns=blue_columns, inplace=True)

    white_water_flows_2007.rename(columns={"WHITE13": "Annual"}, inplace=True)

    return green_water_flows_2007, blue_water_flows_2007, white_water_flows_2007


# Load data
green_water_flows_2007, blue_water_flows_2007, white_water_flows_2007 = load_data()

# Mapping datasets to user-friendly names
water_dataframes = {
    "Green": green_water_flows_2007,
    "Blue": blue_water_flows_2007,
    "White": white_water_flows_2007
}

# Initialize session state variables
if "water_type" not in st.session_state:
    st.session_state.water_type = "Green"
if "period" not in st.session_state:
    st.session_state.period = "Annual"

# Dropdown for dataset selection
selected_water_type = st.selectbox("Choose dataset", list(water_dataframes.keys()),
                                           index=list(water_dataframes.keys()).index(st.session_state.water_type))

if selected_water_type != st.session_state.water_type:
    st.session_state.water_type = selected_water_type

dataframe = water_dataframes[st.session_state.water_type]

# Update period options based on dataset selection
if st.session_state.water_type == "White":
    periods = ["Annual"]
else:
    periods = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
               'October', 'November', 'December', 'Annual']

selected_period = st.selectbox("Choose time period", periods, index=periods.index(st.session_state.period))

if selected_period != st.session_state.period:
    st.session_state.period = selected_period

# Extract data for the selected period
plot_data = dataframe[[st.session_state.period, "geometry"]]

# Create a color map based on the data
# Define color intervals
def get_color(value):
    if value < 50:
        return '#89c4ff'
    elif 50 <= value < 100:
        return '#42a0ff'
    elif 100 <= value < 150:
        return '#007cf9'
    elif 150 <= value < 200:
        return '#006bd6'
    elif 200 <= value < 250:
        return '#0059b2'
    elif 250 <= value < 300:
        return '#00478e'
    elif 300 <= value < 350:
        return '#00356b'
    else:
        return '#002347'


# Function to style each feature based on the selected period
def style_function(feature):
    value = feature["properties"][st.session_state.period]
    return {
        'fillOpacity': 0.7,
        'weight': 0.5,
        'color': 'black',
        'fillColor': get_color(value) if value is not None else 'transparent'
    }


# Create the map
def create_map():
    if 'map' not in st.session_state or st.session_state.map is None:
        m = folium.Map(location=[-29.459, 24.947], zoom_start=5)

        # Add GeoJson with the style function
        folium.GeoJson(
            plot_data,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(fields=[st.session_state.period])
        ).add_to(m)

        # saving the map in the session state
        st.session_state.map = m
    return st.session_state.map

def show_map():
    m = create_map()

    # Display the map in Streamlit
    st_folium(m, width=1000, returned_objects=[])

show_map()