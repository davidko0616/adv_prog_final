import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from streamlit_gsheets.gsheets_connection import GSheetsConnection

m = folium.Map(location=[37.659845, 126.992394], zoom_start=13)

folium.Marker([37.659845, 126.992394], popup="Seoul City Hall").add_to(m)

st_folium(m, width=700, height=500)