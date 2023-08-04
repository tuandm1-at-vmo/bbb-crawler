import json
import requests
from typing import Dict

from utils.requests import error_response


TREKBIKES_BASE_URL = 'https://www.trekbikes.com/us/en_US'
TREKBIKES_MEDIA_BASE_URL = 'https://media.trekbikes.com/image/upload/f_auto,fl_progressive:semi,q_auto,w_1920,h_1440,c_pad'
MOZILLA_HEADERS = {
    'User-Agent': 'Mozilla/5.0', # imitate sending request from a firefox browser
}


def list_bikes_by_year(year: str):
    ''' List all bikes for a specific model year. '''
    url = f'{TREKBIKES_BASE_URL}/product/archived?modelYear={year}&type=Bikes'
    headers = MOZILLA_HEADERS
    res = requests.get(url=url, headers=headers)
    if res.status_code == 200:
        data = json.loads(res.text)
        return list(data['data']['results'])
    raise error_response(res)


def get_bike_details(model_id: str) -> Dict[str, object]:
    ''' Fetch full information of a specific bike model. '''
    url = f'{TREKBIKES_BASE_URL}/v1/api/product/{model_id}/full'
    headers = MOZILLA_HEADERS
    res = requests.get(url=url, headers=headers)
    if res.status_code == 200:
        data = json.loads(res.text)
        return {
            **data['data'],
            'id': model_id,
        }
    raise error_response(res)


def get_bike_image_url(asset_id: str):
    ''' Get url for a specific bike asset. '''
    return f'{TREKBIKES_MEDIA_BASE_URL}/{asset_id}'


def get_bike_product_page(product_url: str):
    ''' Get raw page content of a specific bike model. '''
    url = f'{TREKBIKES_BASE_URL}{product_url}'
    headers = MOZILLA_HEADERS
    res = requests.get(url=url, headers=headers)
    if res.status_code == 200:
        return res.text
    raise error_response(res)


def get_bike_spec(spec_id: str):
    ''' Fetch information for a specific bike spec. '''
    url = f'{TREKBIKES_BASE_URL}/product/spec/{spec_id}'
    headers = MOZILLA_HEADERS
    res = requests.get(url=url, headers=headers)
    if res.status_code == 200:
        data = json.loads(res.text)
        return {
            **data['data'],
            'id': spec_id,
        }
    raise error_response(res)


def get_bike_technical_data(model_id: str):
    ''' Get technical data for a specific bike model. '''
    url = f'{TREKBIKES_BASE_URL}/product/spec/technicalData/{model_id}'
    headers = MOZILLA_HEADERS
    res = requests.get(url=url, headers=headers)
    if res.status_code == 200:
        data = json.loads(res.text)
        return {
            **data['data'],
            'id': model_id,
        }
    return error_response(res)


def get_bike_spec_item(spec_item_id: str):
    pass