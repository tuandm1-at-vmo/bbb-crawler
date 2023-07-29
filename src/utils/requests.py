import json
from requests import Response


def error_response(res: Response):
    ''' Get a RuntimeError version of a requests.Response. '''
    err = {
        'method': res.request.method,
        'url': res.request.url,
        'status': res.status_code,
        'text': res.text,
    }
    return RuntimeError(json.dumps(err))