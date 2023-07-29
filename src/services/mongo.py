''' A service containing functions for interacting with MongoDB. '''

from airflow.providers.mongo.hooks.mongo import MongoHook

import constants.airflow as airflow
from utils.airflow import get_context_params


def client(connection_id = 'mongo_default'):
    ''' Get a MongoClient for a specific Airflow Connection. '''
    hook = MongoHook(conn_id=connection_id)
    return hook.get_conn()


def db(name: str, connection_id = 'mongo_default'):
    ''' Get a Database for a specific Airflow Connection. '''
    return client(connection_id).get_database(name=name)


def db_from_params(**airflow_context):
    ''' Get a Database based on Airflow Context params. '''
    return db(
        name=str(get_context_params(airflow.DATABASE_NAME, **airflow_context)),
        connection_id=str(get_context_params(airflow.CONNECTION_ID, **airflow_context)),
    )