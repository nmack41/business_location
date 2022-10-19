#!/usr/bin/env python
# coding: utf-8
import datetime

# Import libraries
import requests
import time
import googlemaps
import pandas as pd
from pandas.io.formats.format import NA

import datetime
from haversine import haversine, Unit
import streamlit as st

from bs4 import BeautifulSoup
from urllib.parse import urlsplit
from collections import deque
import requests.exceptions
import re


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
        ad =    st.text_input(
                label = "What is the address origin?",
                key = "origin_address",
                placeholder = "123 Some St, New Brunswick, NJ"
            )

    with col2:
    # Input radius to search
        rad =   st.slider(
            label = "What is the radius in miles you want to search?",
            min_value = 0,
            max_value = 20,
            key = "business_radius"
        )

        details_check = st.checkbox("See website, phone number, and emails - will significantly increase loading time")

    with col3:
    # What is the search string?
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

    # response_details = map_client.place(
    #     location=(lat, lng),
    #     keyword=search_string,
    #     radius=distance,
    # )
    # places_list = []
    # st.write(response_details)
    #
    # places_list.extend(response_details.get('results'))


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



    df = df.drop(['business_status', 'geometry', 'icon', 'icon_background_color', 'icon_mask_base_uri', 'photos', 'plus_code','reference', 'scope', 'types'], axis=1)

    df['address'] = df['vicinity']
    df = df.drop(['vicinity'], axis=1)
    df = df.drop(['opening_hours'], axis=1)


    # Place Details API
    # Returns name, address, website, phone number

    if details_check:
        def place_details(row):
            result = map_client.place(row['place_id'])
            status = result['status']
            name = result['result']['name']
            address = result['result']['vicinity']
            try:
                site = result['result']['website']
            except:
                site = NA
            try:
                phone = result['result']['formatted_phone_number']
            except:
                phone = NA

            return [name, address, site, phone]

        # Run function
        details = df.apply(place_details, axis=1)
        details_df = details.apply(pd.Series)
        details_df.columns = ['name', 'address', 'website', 'phone']


    # Scrape websites and get emails
    # Based on https://medium.com/swlh/how-to-scrape-email-addresses-from-a-website-and-export-to-a-csv-file-c5d1becbd1a0

        def get_emails(website):
            if (website != website) != False:
                return None
            else:
                # a queue of urls to be crawled
                unprocessed_urls = deque([website])

                # set of already crawled urls for email
                processed_urls = set()

                # a set of fetched emails
                emails = set()

                # process urls one by one from unprocessed_url queue until queue is empty
                while len(unprocessed_urls):

                # move next url from the queue to the set of processed urls
                    url = unprocessed_urls.popleft()
                    processed_urls.add(url)

                    # extract base url to resolve relative links
                    parts = urlsplit(url)
                    base_url = "{0.scheme}://{0.netloc}".format(parts)
                    path = url[:url.rfind('/') + 1] if '/' in parts.path else url

                    # get url's content
                    # print("Crawling URL %s" % url)
                    try:
                        response = requests.get(url)
                    except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                        # ignore pages with errors and continue with next url
                        continue

                    # extract all email addresses and add them into the resulting set
                    # You may edit the regular expression as per your requirement
                    new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", response.text, re.I))
                    emails.update(new_emails)
                    # print(emails)
                    return [url, emails]
                    # create a beutiful soup for the html document
                    soup = BeautifulSoup(response.text, 'lxml')

                    # Once this document is parsed and processed, now find and process all the anchors i.e. linked urls in this document
                    for anchor in soup.find_all("a"):
                        # extract link url from the anchor
                        link = anchor.attrs["href"] if "href" in anchor.attrs else ''
                        # resolve relative links (starting with /)
                        if link.startswith('/'):
                            link = base_url + link
                        elif not link.startswith('http'):
                            link = path + link
                        # add the new url to the queue if it was not in unprocessed list nor in processed list yet
                        if not link in unprocessed_urls and not link in processed_urls:
                            unprocessed_urls.append(link)

        # Run function get_emails
        emails = details_df['website'].apply(lambda x: get_emails(x) if pd.notnull(x) else x)
        emails_df = emails.apply(pd.Series)
        emails_df.columns = ['website', 'emails']


    if details_check:
        # Merge Place Details and Get Emails
        details_df = pd.merge(details_df, emails_df, how='outer', on='website')
        # Merge Place Details, Get Emails, and original dataframe (df)
        df = pd.merge(df, details_df, how='outer', on=['name'])


    # CLEANING
    # Drop duplicate values
    df = df.drop_duplicates(subset = ['place_id'])

    # Drop unnecessary columns
    df = df.drop(['place_id', 'Coordinates', 'address_y'], axis=1, errors='ignore')

    # Reset index so it goes from 0 to n
    df = df.reset_index(drop=True)

    # Change set to list for emails
    # def convert(set):
    #     return list(set)
    #
    # df['emails'] = df['emails'].apply(convert)

    column_dict={
        "name":"Name",
        "price_level":"Price (0-5)",
        "rating":"Rating (0-5)",
        "user_ratings_total":"Total Ratings",
        "permanently_closed":"Closed",
        "coord":"Coordinates",
        "distance_origin":"Distance from Origin",
        "address":"Address",
        "address_x":"Address",
        "lat":"lat",
        "lon":"lon",
        "website":"Website",
        "phone":"Phone",
        "emails":"Email"
        }

    for col in df.columns:
        if col in column_dict.keys():
            df.rename(columns=column_dict,inplace=True)
        else:
            pass





    # Download data as CSV
    current_time = datetime.datetime.now()
    dl_name = search_string + "_" + str(rad) + "mi__" + str(current_time.month) + "_" + str(current_time.day) + "_" + str(current_time.year)
    #dl_name = search_string + "_" + str(rad) + "mi"

    @st.cache
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    csv = convert_df(df)

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name=dl_name,
        mime='text/csv',
    )


    st.map(data=df)



    st.table(
            data = df,
            #use_container_width = True
            )

    # Measure how long it takes program to run - End Time
    end_time = time.perf_counter()
    st.write("Loaded in:", round(end_time - start_time, 1), "seconds.")