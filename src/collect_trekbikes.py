from airflow.decorators import dag, task
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import json
import re

from constants.airflow import CONNECTION_ID, DATABASE_NAME
import services.mongo as mongo
import services.trekbikes as trekbikes
from utils.airflow import get_context_params


TARGET_COLLECTION_PARAM = 'target_collection'
TARGET_YEAR_PARAM = 'target_year'


@task()
def get_bike_list(**context):
    model_year = str(get_context_params(TARGET_YEAR_PARAM, **context))
    return trekbikes.list_bikes_by_year(year=model_year)


@task()
def save_bike_url(bike_metadata, **context):
    if bike_metadata is None: return
    try:
        model_year = str(get_context_params(TARGET_YEAR_PARAM, **context))
        db = mongo.db_from_params(**context)
        coll_name = get_context_params(TARGET_COLLECTION_PARAM, **context)
        coll = db.get_collection(coll_name)
        bike_id = str(bike_metadata['id'])
        bike_url = str(bike_metadata['productUrl'])
        filter = { 'id': bike_id }
        update = {
            **bike_metadata,
            'year': model_year,
        }
        existed = coll.find_one(filter)
        if existed is None:
            coll.insert_one(update)
            return {
                'id': bike_id,
                'url': bike_url,
            }
        else:
            details_missing = not hasattr(existed, 'details') or existed['details'] is None
            technical_data_missing = not hasattr(existed, 'technicalData') or existed['technicalData'] is None
            if not details_missing and not technical_data_missing: return
            return {
                'id': bike_id,
                'url': bike_url if details_missing else None,
            }
    except Exception as ex:
        print(f'error: {ex}')


@task()
def get_bike_details(bike_header):
    bike_id = bike_header['id']
    bike_url = bike_header['url']
    if bike_id is None: return
    details = trekbikes.get_bike_details(model_id=bike_id)
    if details['images'] is not None and isinstance(details['images'], dict):
        images = dict(details['images'])
        for color in images:
            assets = images[color]
            if not isinstance(assets, list) or len(assets) == 0: continue
            default_asset_id = str(assets[0]['assetId'])
            for asset in assets:
                asset_id = str(asset['assetId'])
                if asset_id.lower().endswith('portrait'):
                    default_asset_id = asset_id
                    break
            if default_asset_id is not None:
                details['defaultImage'] = trekbikes.get_bike_image_url(default_asset_id)
                break
    if bike_url is not None:
        categories = [re.sub(r'-', ' ', c).title() for c in str(bike_url).split('/')[2:4]]
        details['categories'] = categories
        product_content = trekbikes.get_bike_product_page(product_url=bike_url)
        # details['productContent'] = product_content
        soup = BeautifulSoup(markup=product_content, features='html.parser')
        container = soup.find('bike-overview-container', {
            ':product-data': True,
        })
        if isinstance(container, Tag):
            product_data = json.loads(str(container.get(':product-data')))
            description = product_data['copyPositioningStatement']
            details['productData'] = product_data
            details['description'] = description
        reviews = soup.find('product-reviews-header', {
            ':options': True,
        })
        if isinstance(reviews, Tag):
            matches = re.findall(r"productUpc:\s*'(.+)',", str(reviews.get(':options')))
            if len(matches) > 0:
                product_upc = matches[0]
                details['productUpc'] = product_upc
        gender_element = soup.select_one('#gender')
        if isinstance(gender_element, Tag):
            genders = str(gender_element.get('data-gender')).split(',')
            details['genders'] = genders
    return details


@task()
def save_bike_details(bike_details, **context):
    if bike_details is None: return
    try:
        db = mongo.db_from_params(**context)
        coll_name = get_context_params(TARGET_COLLECTION_PARAM, **context)
        coll = db.get_collection(coll_name)
        bike_id = str(bike_details['id'])
        filter = {
            'id': bike_id,
        }
        update = {
            '$set': {
                'details': { **bike_details },
            },
        }
        coll.update_one(filter=filter, update=update)
    except Exception as ex:
        print(f'error: {ex}')


@task()
def get_bike_technical_data(bike_header):
    bike_id = bike_header['id']
    if bike_id is None: return
    return trekbikes.get_bike_technical_data(model_id=bike_id)


@task()
def save_bike_technical_data(bike_technical_data, **context):
    if bike_technical_data is None: return
    try:
        db = mongo.db_from_params(**context)
        coll_name = get_context_params(TARGET_COLLECTION_PARAM, **context)
        coll = db.get_collection(coll_name)
        bike_id = str(bike_technical_data['id'])
        filter = {
            'id': bike_id,
        }
        update = {
            '$set': {
                'technicalData': { **bike_technical_data },
            },
        }
        coll.update_one(filter=filter, update=update)
    except Exception as ex:
        print(f'error: {ex}')

@dag(
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    params={
        f'{CONNECTION_ID}': 'mongo_default',
        f'{DATABASE_NAME}': 'test',
        f'{TARGET_COLLECTION_PARAM}': 'trekbikes',
        f'{TARGET_YEAR_PARAM}': '2024',
    },
)
def collect_trekbikes():
    metadata = get_bike_list()
    inserted = save_bike_url.expand(bike_metadata=metadata)
    details = get_bike_details.expand(bike_header=inserted)
    technical_data = get_bike_technical_data.expand(bike_header=inserted)
    save_bike_details.expand(bike_details=details)
    save_bike_technical_data.expand(bike_technical_data=technical_data)


_ = collect_trekbikes()