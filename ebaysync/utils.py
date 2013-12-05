import collections
import os
import pickle

from django.http import HttpRequest


PICKLED_REQUEST_FILE = os.environ.get('PICKLED_REQUEST')


def load_request(pickle_req_path=PICKLED_REQUEST_FILE):
    """
    Debugging helper... while our notification view is saving
    pickled last_request to a file, here we reconstitute it
    """
    request = HttpRequest()
    with open(pickle_req_path) as request_file:
        unpickled = pickle.load(request_file)
        request.method = 'POST'
        request._body = unpickled['body']
        request.META = unpickled['META']
    return request


def update(d, u):
    """
    Recursively update a dict in place without completely overwriting
    intermediate keys
    http://stackoverflow.com/a/3233356/202168
    """
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d
