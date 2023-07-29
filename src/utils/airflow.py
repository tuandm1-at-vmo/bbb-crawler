from constants.airflow import PARAMS


def get_context_params(key: str, **context):
    ''' Retrieve a specific parameter from Airflow Context. '''
    params = context.get(PARAMS)
    if params is not None:
        return dict(params).get(key)
