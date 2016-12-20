import requests
import session
import config
import json
import time
import re

def deprecated(func):
    '''This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used.'''
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func

@deprecated
def list_saved(object_to_list, **kwargs):
    return list_object(object_to_list, **kwargs)


def list_object(object_to_list, **kwargs):
    return make_get_request("conduce/api/v1/%s/list" % object_to_list, **kwargs)


def list_datasets(**kwargs):
    return list_object('datasets', **kwargs)


def list_substrates(**kwargs):
    return list_object('substrates', **kwargs)


def wait_for_job(job_id):
    finished = False

    while not finished:
        time.sleep(0.5)
        response = make_get_request('conduce/api/%s' % job_id)
        response.raise_for_status()

        #TODO: This is probably dead code
        if int(response.status_code / 100) != 2:
            print "Error code %s: %s" % (response.status_code, response.text)
            return False;

        if response.ok:
            msg = response.json()
            if 'response' in msg:
                finished = True
        else:
            print resp, resp.content
            break


"""
from saveSubstrate
        var cfg = {
            background: {
                asset_id: this.image,
                bottom_left: bounds.bottom_left,
                top_right: bounds.top_right,
                //pixel_width: res.pixel_width,
                //pixel_height: res.pixel_height,
            },
        };
{
    "substrate": {
        "id": "9428b576-05eb-4d9c-b6b5-2c87034455ff",
        "name": "DHL_Beringe_Kyocera",
        "background": {
            "asset_id": "13784280-405d-4ac2-aed3-5913e56464b4",
            "bottom_left": {
                "x": -102938,
                "y": 161021
            },
            "top_right": {
                "x": 187243,
                "y": -967
            }
        }
    }
}
"""

def get_generic_data(dataset_id, entity_id, **kwargs):
    entity = get_entity(dataset_id, entity_id, **kwargs)
    return json.loads(json.loads(entity.content)[0]['attrs'][0]['str_value'])


def get_entity(dataset_id, entity_id, **kwargs):
    return make_get_request('conduce/api/v1/datasets/entity/%s/%s' % (dataset_id, entity_id), **kwargs)


def make_get_request(uri, **kwargs):
    cfg = config.get_full_config()

    if 'host' in kwargs and kwargs['host']:
        host = kwargs['host']
    else:
        host = cfg['default-host']

    if 'user' in kwargs and kwargs['user']:
        user = kwargs['user']
    else:
        user = cfg['default-user']

    if 'api_key' in kwargs and kwargs['api_key']:
        auth = session.api_key_header(kwargs['api_key'])
    else:
        auth = session.get_session(host, user)

    url = 'https://%s/%s' % (host, uri)
    if 'Authorization' in auth:
        response = requests.get(url, headers=auth)
    else:
        response = requests.get(url, cookies=auth)
    response.raise_for_status()
    return response


def create_dataset(dataset_name, **kwargs):
    response = make_post_request({'name':dataset_name}, 'conduce/api/v1/datasets/create', **kwargs)
    response_dict = json.loads(response.content)
    if 'json' in kwargs and kwargs['json']:
        ingest_entities(response_dict['dataset'], json.load(open(kwargs['json'])), **kwargs)
    elif 'csv' in kwargs and kwargs['csv']:
        ingest_entities(response_dict['dataset'], util.csv_to_entities(kwargs['csv']), **kwargs)

    return response


def set_generic_data(dataset_id, key, data_string, **kwargs):
    timestamp = 0
    location = {}
    location["x"] = 0
    location["y"] = 0
    location["z"] = 0

    attributes = [{
        "key": "json_data",
        "type": "STRING",
        #"str_value": base64.b64encode(data),
        "str_value": data_string,
    }]

    remove_entity = {
        "identity": key,
        "kind": 'raw_data',
        "timestamp_ms": timestamp,
        "endtime_ms": timestamp,
        "path": [location],
        "removed": True,
    }

    ingest_entities(dataset_id, {'entities':[remove_entity]}, **kwargs)

    entity = {
        "identity": key,
        "kind": 'raw_data',
        "timestamp_ms": timestamp,
        "endtime_ms": timestamp,
        "path": [location],
        "attrs": attributes,
    }

    return ingest_entities(dataset_id, {'entities':[entity]}, **kwargs)


def ingest_entities(dataset_id, data, **kwargs):
    if isinstance(data, list):
        data = {'entities': data}

    response = make_post_request(data, 'conduce/api/v1/datasets/add-data/%s' % dataset_id, **kwargs)
    if 'location' in response.headers:
        job_id = response.headers['location']
        response = wait_for_job(job_id)
    return response


def _remove_dataset(dataset_id, **kwargs):
    response = make_post_request(None, 'conduce/api/v1/datasets/delete/' + dataset_id, **kwargs)
    response.raise_for_status()
    return True


def remove_dataset(**kwargs):
    return_message = None
    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None

    if kwargs['id']:
        _remove_dataset(kwargs['id'], **kwargs)
        return_message = 'Removed 1 dataset'
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        datasets = json.loads(list_datasets(**kwargs).content)
        to_remove = []
        for dataset in datasets:
            if dataset['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], dataset['name'])):
                to_remove.append(dataset)
        if len(to_remove) == 1:
            _remove_dataset(to_remove[0]['id'], **kwargs)
            return_message = 'Removed 1 dataset'
        elif kwargs['all']:
            for dataset in to_remove:
                _remove_dataset(dataset['id'], **kwargs)
            return_message = "Removed %s datasets" % len(to_remove)
        elif len(to_remove) > 1:
            return_message = "Matching datasets:\n"
            return_message += json.dumps(to_remove)
            return_message += "\n\nName or regular expression matched multiple datasets.  Pass --all to remove all matching datasets."
        else:
            return_message = "No matching datasets found."

    return return_message



def make_post_request(payload, uri, **kwargs):
    cfg = config.get_full_config()

    if 'host' in kwargs and kwargs['host']:
        host = kwargs['host']
    else:
        host = cfg['default-host']

    if 'user' in kwargs and kwargs['user']:
        user = kwargs['user']
    else:
        user = cfg['default-user']

    if 'api_key' in kwargs and kwargs['api_key']:
        auth = session.api_key_header(kwargs['api_key'])
    else:
        auth = session.get_session(host, user)

    url = 'https://%s/%s' % (host, uri)
    if 'Authorization' in auth:
        response = requests.post(url, json=payload, headers=auth)
    else:
        response = requests.post(url, json=payload, cookies=auth)
    response.raise_for_status()
    return response
