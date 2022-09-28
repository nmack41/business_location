
# Import libraries
import time
import googlemaps
import pandas as pd
from datetime import datetime
from haversine import haversine, Unit
from googleplaces import GooglePlaces, types, lang


import streamlit as st

st.set_page_config(
    page_title="Find Bussinesses in the Area",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.nickmackowsk.com',
        'Report a bug': 'https://www.nickmackowsk.com',
        'About': "This was created by Nick. Contact him at NickMackowski.com"
    }
)
API_KEY = st.secrets["GAPI"]

with st.form("form_variables"):
    # columns
    col1, col2, col3 = st.columns(3, gap="large")

    with col1:
    # Input address
    #ad = input("What is the address origin? ")

        ad =    st.text_input(
                label = "What is the address origin?",
                key = "origin_address",
                placeholder = "123 Some St, New Brunswick, NJ"
            )

    with col2:
    # Input radius to search
    #rad = int(input("What is the radius in miles you want to search? e.g. 5 "))

        rad =   st.slider(
            label = "What is the radius in miles you want to search?",
            min_value = 0,
            max_value = 20,
            key = "business_radius"
        )

    with col3:
    # What is the search string?
    #search_string = input("What type of business do you want to search for? e.g. urgent care, fast food, etc. ")

        search_string =    st.text_input(
                label = "What type of business do you want to search for? e.g. What would you type in Google Maps",
                key = "business_term",
                placeholder = "restuarants"
            )


    submitted = st.form_submit_button("Run Program")

    if submitted:

        # Google 'Nearby Search' documentation: https://developers.google.com/maps/documentation/places/web-service/search-nearby?hl=en_US#maps_http_places_nearbysearch-py
        # googlemaps library documentation: https://googlemaps.github.io/google-maps-services-python/docs/
        # Google Places Nearby API is only able to get 20 total items at a time. Next_page_token is able pull an additional 20 twice
        # Foundation of this code is from https://learndataanalysis.org/source-code-search-nearby-businesses-with-google-maps-api-and-python/

        # Measure how long it takes program to run - Start Time
        start_time = time.perf_counter()

        # Loading icon
        my_bar = st.progress(0)

        for percent_complete in range (100):
            time.sleep(0.1)
            my_bar.progress(percent_complete + 1)

        #The API uses meters, so we need to convert miles to meters
        @st.cache(persist=True)
        def miles_to_meters(miles):
            try:
                return miles * 1_609.344
            except:
                return 0
