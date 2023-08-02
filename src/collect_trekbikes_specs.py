from airflow.decorators import dag, task
from datetime import datetime, timedelta

from constants.airflow import CONNECTION_ID, DATABASE_NAME
import services.mongo as mongo
import services.trekbikes as trekbikes
from utils.airflow import get_context_params


SOURCE_COLLECTION_PARAM = 'source_collection'
TARGET_COLLECTION_PARAM = 'target_collection'
TARGET_YEAR_PARAM = 'target_year'


@task()
def get_bike_variant_list(**context):
    try:
        model_year = get_context_params(TARGET_YEAR_PARAM, **context)
        db = mongo.db_from_params(**context)
        source_coll_name = get_context_params(SOURCE_COLLECTION_PARAM, **context)
        source_coll = db.get_collection(source_coll_name)
        pipeline = [
            { '$match': { 'year': model_year } },
            { '$project': { 'code': '$details.variants.code', '_id': 0 } },
            { '$unwind': '$code' },
            { '$group': { '_id': '_', 'variants': { '$addToSet': '$code' } } },
            { '$project': { '_id': 0 } },
        ]
        result = list(source_coll.aggregate(pipeline))
        return list(set(result[0]['variants']))
    except Exception as ex:
        print(f'error: {ex}')


@task()
def get_bike_spec_details(spec_id: str):
    if spec_id is None: return
    return trekbikes.get_bike_spec(spec_id=spec_id)


@task()
def save_bike_spec_details(spec_details, **context):
    if spec_details is None: return
    try:
        db = mongo.db_from_params(**context)
        target_coll_name = get_context_params(TARGET_COLLECTION_PARAM, **context)
        target_coll = db.get_collection(target_coll_name)
        filter = {
            'id': spec_details['id'],
        }
        update = {
            **spec_details,
        }
        existed = target_coll.find_one(filter)
        if existed is None:
            target_coll.insert_one(update)
            return spec_details['specItems']
    except Exception as ex:
        print(f'error: {ex}')


@dag(
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    params={
        f'{CONNECTION_ID}': 'mongo_default',
        f'{DATABASE_NAME}': 'test',
        f'{SOURCE_COLLECTION_PARAM}': 'trekbikes',
        f'{TARGET_COLLECTION_PARAM}': 'trekbike_specs',
        f'{TARGET_YEAR_PARAM}': '2024',
    },
)
def collect_trekbikes_specs():
    variants = get_bike_variant_list()
    details = get_bike_spec_details.expand(spec_id=variants)
    save_bike_spec_details.expand(spec_details=details)


_ = collect_trekbikes_specs()