import logging
import os
import csv
from pb_avail_check import get_html_and_avail
from datetime import datetime
from dotenv import load_dotenv
import aiohttp
import asyncio


import azure.functions as func

load_dotenv()
API_KEY = f'Bearer {os.environ.get("API_KEY")}'
BASE_URL = os.environ.get('BASE_URL')
VHC_ORG = os.environ.get('ORG')


def request_path(path):
    return f'https://{BASE_URL}/api/v1/{path}'


async def get_location(session, store_id):
    url = request_path(f'locations/external/{store_id}')
    response = await session.get(url, headers={'accept': 'application/json'})
    data = None
    try:
        data = await response.json()
    except aiohttp.client_exceptions.ContentTypeError: # if location does not exist
        if not data:
            return None
    return data['id']

async def create_location(session, store_id, name, address, postal_code, province, url):
    data = {
        'name': name,
        'postcode': postal_code,
        'external_key': store_id,
        'line1': address,
        'active': 1,
        'url': url,
        'organization': VHC_ORG,
        'province': province
    }

    headers = {'Authorization': API_KEY, 'Content-Type': 'application/json'}
    location_post = await session.post(request_path('locations/expanded'), headers=headers, json=data)
    location_id = await location_post.text()
    logging.info(location_id)
    return location_id

async def get_availability(session, location):
    params = {
        'locationID': location,
        'min_date': str(datetime.now().date())
    }
    logging.info(params)
    url = request_path(f'vaccine-availability/location/')
    response = await session.get(url, params=params)
    
    if response.status != 200:
        logging.info(await response.json())
        return None
    logging.info(await response.json())
    availabilities = await response.json()
    if len(availabilities) > 0:
        return availabilities[0]['id']
    return None

async def create_availability(session, location, available):
    date = str(datetime.now().date())+'T00:00:00Z'
    vacc_avail_body = {
        "numberAvailable": available,
        "numberTotal": available,
        "vaccine": 1,
        "inputType": 1,
        "tags": "",
        "location": location,
        "date": date
    }
    
    vacc_avail_headers = {'accept': 'application/json', 'Authorization': API_KEY, 'Content-Type':'application/json'}
    response = await session.post(request_path('vaccine-availability'), headers=vacc_avail_headers, json=vacc_avail_body)
    logging.info(f'create_availability: {response.status}')
    data = await response.json()
    return  data['id']

async def update_availability(session, id, location, available):
    date = str(datetime.now().date())+'T00:00:00Z'
    vacc_avail_body = {
        "numberAvailable": available,
        "numberTotal": available,
        "vaccine": 1,
        "inputType": 1,
        "tags": "",
        "location": location,
        "date": date
    }
    
    vacc_avail_headers = {'accept': 'application/json', 'Authorization': API_KEY, 'Content-Type':'application/json'}
    response = await session.put(request_path(f'vaccine-availability/{id}'), headers=vacc_avail_headers, json=vacc_avail_body)
    logging.info(f'update_availability: {response.status}')
    data = await response.json()
    return data['id']


async def get_or_create_location(session, store_id, name, address, postal_code, province, url):
    location = await get_location(session, store_id)
    if location is None:
        logging.info('Creating Location')
        location = await create_location(session, store_id, name, address, postal_code, province, url)
    return location

async def create_or_update_availability(session, location, available):
    availability = await get_availability(session, location)
    if availability is None:
        logging.info('Creating Availability')
        availability = await create_availability(session, location, available)
    else:
        logging.info(f'Updating Availability: {availability}')
        availability = await update_availability(session, availability, location, available)
    return availability


async def main(mytimer: func.TimerRequest) -> None:

    async with aiohttp.ClientSession() as session:

        with open('list.csv', newline='') as pharma:
            pharma_reader = csv.reader(pharma)
            next(pharma_reader)
            pharmacies = [i for i in pharma_reader]

        for i in pharmacies:

            store_name = i[0]
            address = i[1]
            postal_code = i[2]
            province = i[3]
            store_id = i[4]
            store_url = i[6]

            if not postal_code:
                continue

            available = await get_html_and_avail(session, store_url)
            logging.info(f'Location: {store_id} {postal_code}')
            location_id = await get_or_create_location(session, store_id, store_name, address, postal_code, province, store_url)
            print(location_id)
            logging.info(f'Availability: {available}')
            await create_or_update_availability(session, location_id, available)

        

if __name__ == '__main__':
    asyncio.run(main(func.TimerRequest))