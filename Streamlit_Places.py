
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


        query_result = google_places.nearby_search(
            location='London, England', keyword='Fish and Chips',
            radius=20000, types=[types.TYPE_FOOD])

        if query_result.has_attributions:
            st.write(query_result.html_attributions)

        for place in query_result.places:
            # Returned places from a query are place summaries.

            st.write(place.name)
            st.write(place.geo_location)
            st.write( place.place_id)

            # The following method has to make a further API call.
            place.get_details()
            # Referencing any of the attributes below, prior to making a call to
            # get_details() will raise a googleplaces.GooglePlacesAttributeError.

            st.write(place.details)  # A dict matching the JSON response from Google.
            st.write(place.local_phone_number)
            st.write(place.international_phone_number)
            st.write(place.website)
            st.write(place.url)


        # Are there any additional pages of results?
        if query_result.has_next_page_token:
            query_result_next_page = google_places.nearby_search(
                pagetoken=query_result.next_page_token)

        # Adding and deleting a place
        try:
            added_place = google_places.add_place(name='Mom and Pop local store',
                                                  lat_lng={'lat': 51.501984, 'lng': -0.141792},
                                                  accuracy=100,
                                                  types=types.TYPE_HOME_GOODS_STORE,
                                                  language=lang.ENGLISH_GREAT_BRITAIN)

            st.write(added_place.place_id)  # The Google Places identifier - Important!
            st.write(added_place.id)

            # Delete the place that you've just added.
            google_places.delete_place(added_place.place_id)
        except GooglePlacesError as error_detail:
            # You've passed in parameter values that the Places API doesn't like..
            st.write(error_detail)
