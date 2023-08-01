from airflow.decorators import dag, task
from datetime import datetime, timedelta

from constants.airflow import CONNECTION_ID, DATABASE_NAME
import services.mongo as mongo


@task()
def list_colls(**context):
    db = mongo.db_from_params(**context)
    colls = db.list_collection_names()
    print(f'test ping db: {colls}')


@dag(
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    params={
        f'{CONNECTION_ID}': 'mongo_bbb',
        f'{DATABASE_NAME}': 'bbb-dev',
    },
)
def test_mongo():
    list_colls()


_ = test_mongo()