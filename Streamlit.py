#!/usr/bin/env python
# coding: utf-8

# Import libraries
#import json
#import requests
import time
import googlemaps
import pandas as pd
#import os
#import re
from datetime import datetime
#import matplotlib.pyplot as plt
#import seaborn as sns
from haversine import haversine, Unit
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

# googleapi.txt holds my API key
# Open txt and assign API key to API_KEY

#with open('C:\Users\nmack\OneDrive\Documents\GitHub\business_location\googleapi.txt') as f:
#  for line in f:
#    API_KEY = line

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
        start_time = time.time()

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

        # Connet to Google Maps API
        map_client = googlemaps.Client(API_KEY)

        # Convert origin address to latitutde and longitude
        geocode = map_client.geocode(address=ad)
        (lat, lng) = map(geocode[0]['geometry']['location'].get, ('lat', 'lng'))
        origin = (lat, lng)

        # Convert input radius into meters
        distance = miles_to_meters(rad)

        # Create empty list so we can add API output to it in the next step
        business_list = []

        # Run Places_Nearby using origin, search terms, and radius provided earlier
        response = map_client.places_nearby(
            location=(lat, lng),
            keyword=search_string,
            radius=distance,
        )

        # Add results from Places_Nearby API into the empty list we creaetd, business_list
        business_list.extend(response.get('results'))

        # next_page_token: token for retrieving the next page of results
        # Original API pull is only able to get 20 results, this will aim to get the remaining 60, which is the max allowed by the Google API
        next_page_token = response.get('next_page_token')

        # This 'while' loop gets the 20 + 20 more results and stops functioning upon the API not allowing additional pulls
        while next_page_token:
            # Need to pause the script for token to generate otherwise may not work
            time.sleep(2)
            response = map_client.places_nearby(
                location=(lat, lng),
                keyword=search_string,
                radius=distance,
                page_token=next_page_token
            )
            business_list.extend(response.get('results'))
            next_page_token = response.get('next_page_token')

        # Create dataframe from list of search items
        df = pd.DataFrame(business_list)

        # Function to extract latitude and longitude
        @st.cache(persist=True)
        def coord(dictionary):
            for key, value in dictionary.items():
                return value['lat'],value['lng']

        # Apply the function created previously 'coord' to the 'geometry' column to extract nested IF statement
        df['coord'] = df['geometry'].apply(coord)

        # Create latitude (lat) and longitude (lon) data from 'coord' column
        df['lat'] = df['coord'].apply(lambda x: x[0])
        df['lon'] = df['coord'].apply(lambda x: x[1])

        # Calculate distance of fast food restaurant from origin location
        df['distance_origin'] = df['coord'].apply(lambda x: haversine(origin,x, unit = 'mi'))

        # Calculate distance of fast food restaurant from origin location
        #df['distance_origin'] = df['coord'].apply(lambda x: haversine(origin,x, unit = 'mi'))

        #def chunker(seq, size):
            #return (seq[pos:pos + size] for pos in range(0, len(seq), size))

        #for location in chunker(df['coord'],25):
            #print(location)

        # While there is no maximum number of elements per day (EPD), the following usage limits are in place for the Distance Matrix API:

        # Maximum of 25 origins or 25 destinations per request.
        # Maximum 100 elements per server-side request.
        # Maximum 100 elements per client-side request.
        # 1000 elements per second (EPS), calculated as the sum of client-side and server-side queries.

        #dist_matrix = map_client.distance_matrix(
            #destinations = df['coord'],
            #origins = origin,
        #)

        # Let's add those types of 'fast food' and make them columns in our dataframe
        # df = df.join(pd.DataFrame(columns=['restaurant', 'food', 'point_of_interest', 'establishment', 'cafe', 'store', 'meal_takeaway']))

        # We'll make it '1' if they are that type and '0' if they are not that type
        # df['restaurant'] = df['types'].apply(lambda x: 1 if 'restaurant' in x else 0)
        # df['food'] = df['types'].apply(lambda x: 1 if 'food' in x else 0)
        # df['point_of_interest'] = df['types'].apply(lambda x: 1 if 'point_of_interest' in x else 0)
        # df['establishment'] = df['types'].apply(lambda x: 1 if 'establishment' in x else 0)
        # df['cafe'] = df['types'].apply(lambda x: 1 if 'cafe' in x else 0)
        # df['store'] = df['types'].apply(lambda x: 1 if 'store' in x else 0)
        # df['meal_takeaway'] = df['types'].apply(lambda x: 1 if 'meal_takeaway' in x else 0)

        # Icon background color, icon mask base, photos, place id, plus code, reference, scope, and types are not relevant; will drop.
        # Will keep name

        df = df.drop(['business_status', 'geometry', 'icon', 'icon_background_color', 'icon_mask_base_uri', 'photos', 'place_id', 'plus_code','reference', 'scope', 'types'], axis=1)

        df['address'] = df['vicinity']
        df = df.drop(['vicinity'], axis=1)
        df = df.drop(['opening_hours'], axis=1)

        # Drop for now. Will add as a feature later
        #df = df.drop(['open'], axis=1)
        df = df.drop(['more_opening_hours'], axis=1)


        # SPLIT COORDINATES INTO LAT AND LON

        # Rename columns
        df.rename(columns = {
        "name":"Name",
        "price_level":"Price (0-5)",
        "rating":"Rating (0-5)",
        "user_ratings_total":"Total Ratings",
        "permanently_closed":"Closed",
        "coord":"Coordinates",
        "distance_origin":"Distance from Origin",
        "address":"Address"
        }, inplace = True )


        df = df[["Name", "Address", "Distance from Origin", "Price (0-5)", "Rating (0-5)", "Total Ratings", "Coordinates", "lat", "lon"]]



        with st.container():
            st.dataframe(
                data = df,
                #use_container_width = True
                )

            # Measure how long it takes program to run - End Time
            end_time = time.time()
            st.write("Loaded in:", round(end_time - start_time, 1), "seconds.")


            st.map(
                data = df,
            )





        # Download data as .csv
        #df.to_csv(filecsv)
        #files.download(filecsv)
