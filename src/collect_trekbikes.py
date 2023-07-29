from airflow.decorators import dag, task
from datetime import datetime

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
        filter = { 'id': bike_id }
        update = {
            **bike_metadata,
            'year': model_year,
        }
        existed = coll.find_one(filter)
        if existed is None:
            coll.insert_one(update)
            return bike_id
        elif existed['details'] is None:
            return bike_id
    except Exception as ex:
        print(f'error: {ex}')


@task()
def get_bike_details(bike_id):
    if bike_id is None: return
    return trekbikes.get_bike_details(model_id=bike_id)


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


@dag(
    schedule_interval='@daily',
    start_date=datetime(2023, 1, 1),
    catchup=False,
    params={
        f'{CONNECTION_ID}': 'mongo_bbb',
        f'{DATABASE_NAME}': 'bbb-dev',
        f'{TARGET_COLLECTION_PARAM}': 'bikes',
        f'{TARGET_YEAR_PARAM}': '2024',
    },
)
def collect_trekbikes():
    metadata = get_bike_list()
    inserted = save_bike_url.expand(bike_metadata=metadata)
    details = get_bike_details.expand(bike_id=inserted)
    save_bike_details.expand(bike_details=details)


_ = collect_trekbikes()