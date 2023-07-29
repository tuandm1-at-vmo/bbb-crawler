from airflow.decorators import dag, task
from datetime import datetime, timedelta
from pymongo.database import Database

import decorators.mongo as mongo


@mongo.inject(
    connection_id='mongo_bbb',
    name='bbb-dev',
)
@task()
def list_colls(db: Database):
    colls = db.list_collection_names()
    print(f'test ping db: {colls}')


@dag(
    schedule_interval=timedelta(hours=6),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)
def test_mongo():
    list_colls()


_ = test_mongo