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
