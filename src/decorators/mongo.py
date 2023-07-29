''' Contain few decorators that make it easier to interact with MongoDB. '''

import functools
import services.mongo as mongo


def inject(name = 'test', connection_id = 'mongo_default'):
    ''' Inject a Database instance as a function parameter `db`. '''
    def wrapper(func):
        @functools.wraps(func)
        def inner_wrapper(*args, **kwargs):
            return func(
                *args,
                **kwargs,
                db=mongo.db(name=name, connection_id=connection_id),
            )
        return inner_wrapper
    return wrapper