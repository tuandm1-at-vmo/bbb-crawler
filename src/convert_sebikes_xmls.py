from airflow.decorators import dag, task
from datetime import datetime, timedelta
from typing import Dict, Union

from constants.airflow import CONNECTION_ID, DATABASE_NAME
import services.mongo as mongo
import services.smartetailing as se
from utils.airflow import get_context_params
from utils.dict import safe_get


SOURCE_COLLECTION_PARAM = 'source_collection'
TARGET_COLLECTION_PARAM = 'target_collection'
TARGET_YEAR_PARAM = 'target_year'
BULK_SIZE_PARAM = 'bulk_size'


def should_ignore_sebike(model: Union[str, None]):
    if model is None: return True
    if model.lower().find('frameset') >= 0: return True
    if model.lower().find('f/s') >= 0: return True
    return False


def chop_sebikes_to_bulk(sebikes: list, bulk_size = 1):
    bulks: list[Dict[str, Union[list[str], str, int]]] = []
    bulk: list[tuple[str]] = []
    def commit():
        bulks.append({
            'order': len(bulks),
            'total': len(bulk),
            'skus': [c[0] for c in bulk],
            'xml': se.create_xml(products=[c[1] for c in bulk]),
        })
        bulk.clear()
    for sebike in sebikes:
        sku = safe_get(sebike, 'sku')
        model = safe_get(sebike, 'model')
        if sku is None or should_ignore_sebike(model=model):
            print(f'DEBUG: sebike ignored [sku = {sku}, model = {model}]')
            continue
        xml = se.create_product_xml_element(
            sku=sku,
            brand=safe_get(sebike, 'brand'),
            model=model,
            year=safe_get(sebike, 'year'),
            description=safe_get(sebike, 'description'),
            genders=safe_get(sebike, 'genders'),
            msrp=safe_get(sebike, 'msrp'),
            gtin=safe_get(sebike, 'gtin'),
            images=safe_get(sebike, 'images'),
            default_image=safe_get(sebike, 'defaultImage'),
            categories=safe_get(sebike, 'categories'),
            spec_items=safe_get(sebike, 'specItems'),
            length=None,
            width=None,
            height=None,
            weight=None,
        )
        bulk.append((sku, xml,))
        if len(bulk) >= bulk_size: commit()
    if len(bulk) > 0: commit()
    print(f'DEBUG: total sebikes = {len(sebikes)}, total bulks = {len(bulks)}')
    return bulks


@task()
def get_xml_bulks(**context):
    model_year = str(get_context_params(TARGET_YEAR_PARAM, **context))
    bulk_size = int(str(get_context_params(BULK_SIZE_PARAM, **context)))
    db = mongo.db_from_params(**context)
    coll_name = get_context_params(SOURCE_COLLECTION_PARAM, **context)
    coll = db.get_collection(coll_name)
    sebikes = list(coll.find({
        'year': model_year,
    }))
    return chop_sebikes_to_bulk(sebikes=sebikes, bulk_size=bulk_size)


@task()
def save_xml(bulk, **context):
    run_id = context['dag_run'].run_id
    db = mongo.db_from_params(**context)
    coll_name = get_context_params(TARGET_COLLECTION_PARAM, **context)
    coll = db.get_collection(coll_name)
    coll.insert({
        'content': bulk,
        'createdAt': datetime.now(),
        'createdBy': run_id,
    })


@dag(
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    params={
        f'{CONNECTION_ID}': 'mongo_default',
        f'{DATABASE_NAME}': 'test',
        f'{SOURCE_COLLECTION_PARAM}': 'se_trekbikes',
        f'{TARGET_COLLECTION_PARAM}': 'se_trekbike_xmls',
        f'{TARGET_YEAR_PARAM}': '2024',
        f'{BULK_SIZE_PARAM}': 1,
    },
)
def convert_sebikes_xmls():
    bulks = get_xml_bulks()
    save_xml.expand(bulk=bulks)


_ = convert_sebikes_xmls()