from airflow.decorators import dag, task
from datetime import datetime, timedelta

from constants.airflow import CONNECTION_ID, DATABASE_NAME
import services.mongo as mongo
from utils.airflow import get_context_params


SOURCE_COLLECTION_PARAM = 'source_collection'
TARGET_COLLECTION_PARAM = 'target_collection'
TARGET_YEAR_PARAM = 'target_year'


@task()
def get_trekbikes(**context):
    try:
        model_year = str(get_context_params(TARGET_YEAR_PARAM, **context))
        db = mongo.db_from_params(**context)
        coll_name = get_context_params(SOURCE_COLLECTION_PARAM, **context)
        coll = db.get_collection(coll_name)
        pipeline = [
            {
                '$match': {
                    'year': model_year,
                },
            },
            {
                '$addFields': {
                    'categorizationHierarchyValue': {
                        '$arrayElemAt': ['$details.categorizationHierarchyValues', 0],
                    },
                },
            },
            {
                '$addFields': {
                    'sku': '$categorizationHierarchyValue.options.productCode',
                },
            },
            {
                '$addFields': {
                    'colors': {
                        '$objectToArray': '$details.images',
                    }
                }
            },
            {
                '$lookup': {
                    'from': 'trekbike_specs',
                    'localField': 'sku',
                    'foreignField': 'id',
                    'as': 'specs',
                }
            },
            {
                '$addFields': {
                    'spec': {
                        '$arrayElemAt': ['$specs.specItems', 0],
                    },
                },
            },
            {
                '$project': {
                    '_id': 0,
                    'id': 1,
                    'brand': {
                        '$let': {
                            'vars': {
                                'variant': {
                                    '$arrayElemAt': ['$details.variants', 0],
                                },
                            },
                            'in': '$$variant.brandNameFull',
                        },
                    },
                    'model': '$technicalData.description',
                    'year': 1,
                    'description': '$details.description',
                    'msrp': '$details.consumerPrice.price.low.value',
                    'defaultImage': '$details.defaultImage',
                    'images': '$details.defaultImages',
                    'sku': 1,
                    'genders': '$details.genders',
                    'gtin': '$details.productUpc',
                    'colors': {
                        '$map': {
                            'input': '$colors',
                            'as': 'color',
                            'in': '$$color.k',
                        },
                    },
                    'specItems': {
                        '$arrayToObject': {
                            '$map': {
                                'input': '$spec',
                                'as': 'item',
                                'in': {
                                    'k': '$$item.partId',
                                    'v': '$$item.description',
                                },
                            },
                        },
                    },
                },
            },
        ]
        return list(coll.aggregate(pipeline))
    except Exception as ex:
        print(f'error: {ex}')


@task()
def save_as_sebike(trekbike, **context):
    run_id = context['dag_run'].run_id
    db = mongo.db_from_params(**context)
    coll_name = get_context_params(TARGET_COLLECTION_PARAM, **context)
    coll = db.get_collection(coll_name)
    doc = {
        **trekbike,
        'createdAt': datetime.now(),
        'createdBy': run_id,
    }
    if doc['specItems'] is not None and isinstance(doc['specItems'], dict):
        for spec_name in doc['specItems'].keys():
            if '.' in str(spec_name):
                spec_value = doc['specItems'][spec_name]
                del doc['specItems'][spec_name]
                doc['specItems'][str(spec_name).replace('.', '')] = spec_value
    coll.insert(doc)


@dag(
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    params={
        f'{CONNECTION_ID}': 'mongo_default',
        f'{DATABASE_NAME}': 'test',
        f'{SOURCE_COLLECTION_PARAM}': 'trekbikes',
        f'{TARGET_COLLECTION_PARAM}': 'se_trekbikes',
        f'{TARGET_YEAR_PARAM}': '2024',
    },
)
def convert_sebikes():
    trekbikes = get_trekbikes()
    save_as_sebike.expand(trekbike=trekbikes)


_ = convert_sebikes()