import requests
import session
import config
import json
import time
import re
import urlparse

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
        response = make_get_request(job_id)
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

def compose_uri(fragment):
    prefix = 'conduce/api/v1'
    fragment = fragment.lstrip('/')
    uri = '/%s' % fragment
    if not prefix in fragment:
        uri = '/%s/%s' % (prefix, fragment)

    return uri

def get_generic_data(dataset_id, entity_id, **kwargs):
    entity = get_entity(dataset_id, entity_id, **kwargs)
    return json.loads(json.loads(entity.content)[0]['attrs'][0]['str_value'])


def get_entity(dataset_id, entity_id, **kwargs):
    return make_get_request('datasets/entity/%s/%s' % (dataset_id, entity_id), **kwargs)

def make_get_request(fragment, **kwargs):
    return _make_get_request(compose_uri(fragment), **kwargs)

def _make_get_request(uri, **kwargs):
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
    response = make_post_request({'name':dataset_name}, 'datasets/create', **kwargs)
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

    response = make_post_request(data, 'datasets/add-data/%s' % dataset_id, **kwargs)
    if 'location' in response.headers:
        job_id = response.headers['location']
        response = wait_for_job(job_id)
    return response


def _remove_dataset(dataset_id, **kwargs):
    response = make_post_request(None, 'datasets/delete/' + dataset_id, **kwargs)
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
    if not 'all' in kwargs:
        kwargs['all'] = None

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


def _remove_substrate(substrate_id, **kwargs):
    response = make_post_request(None, 'substrates/delete/' + substrate_id, **kwargs)
    response.raise_for_status()
    return True


def remove_substrate(**kwargs):
    return_message = None
    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None
    if not 'all' in kwargs:
        kwargs['all'] = None


    if kwargs['id']:
        _remove_substrate(kwargs['id'], **kwargs)
        return_message = 'Removed 1 substrate'
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        results = json.loads(make_post_request({'query':kwargs['name']}, 'substrates/search', **kwargs).content)
        if 'substrate_list' in results and 'files' in results['substrate_list']:
            substrates = results['substrate_list']['files']
            to_remove = []
            for substrate in substrates:
                if substrate['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], substrate['name'])):
                    to_remove.append(substrate)
            if len(to_remove) == 1:
                _remove_substrate(to_remove[0]['id'], **kwargs)
                return_message = 'Removed 1 substrate'
            elif kwargs['all']:
                for substrate in to_remove:
                    _remove_substrate(substrate['id'], **kwargs)
                return_message = "Removed %s substrates" % len(to_remove)
            elif len(to_remove) > 1:
                return_message = "Matching substrates:\n"
                return_message += json.dumps(to_remove)
                return_message += "\n\nName or regular expression matched multiple substrates.  Pass --all to remove all matching substrates."
            else:
                return_message = "No matching substrates found."
        else:
            return_message = "The query did not match any substrates."

    return return_message


def create_substrate(name, substrate_def, **kwargs):
    return make_post_request(substrate_def, 'substrates/create/%s' % name, **kwargs)


def _remove_template(template_id, **kwargs):
    response = make_post_request(None, 'templates/delete/' + template_id, **kwargs)
    response.raise_for_status()
    return True


def remove_template(**kwargs):
    return_message = None
    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None
    if not 'all' in kwargs:
        kwargs['all'] = None

    if kwargs['id']:
        _remove_substrate(kwargs['id'], **kwargs)
        return_message = 'Removed 1 substrate'
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        results = json.loads(make_post_request({'query':kwargs['name']}, 'templates/search', **kwargs).content)
        if 'template_list' in results and 'files' in results['template_list']:
            templates = results['template_list']['files']
            to_remove = []
            for template in templates:
                if template['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], template['name'])):
                    to_remove.append(template)
            if len(to_remove) == 1:
                _remove_template(to_remove[0]['id'], **kwargs)
                return_message = 'Removed 1 template'
            elif kwargs['all']:
                for template in to_remove:
                    _remove_template(template['id'], **kwargs)
                return_message = "Removed %s templates" % len(to_remove)
            elif len(to_remove) > 1:
                return_message = "Matching templates:\n"
                return_message += json.dumps(to_remove)
                return_message += "\n\nName or regular expression matched multiple templates.  Pass --all to remove all matching templates."
            else:
                return_message = "No matching templates found."
        else:
            return_message = "The query did not match any templates."

    return return_message


def create_template(name, template_def, **kwargs):
    return make_post_request(template_def, 'templates/create/%s' % name, **kwargs)


def make_post_request(payload, fragment, **kwargs):
    return _make_post_request(payload, compose_uri(fragment), **kwargs)


def _make_post_request(payload, uri, **kwargs):
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
        if 'headers' in kwargs and kwars['headers']:
            headers = kwargs['headers']
            headers.update(auth)
        else:
            headers = auth

        response = requests.post(url, json=payload, headers=headers)
    else:
        response = requests.post(url, json=payload, cookies=auth, headers=headers)
    response.raise_for_status()
    return response

def create_asset(name, content, mime_type, **kwargs):
    content_type = {'Content-Type': mime_type}
    if 'headers' in kwargs and kwars['headers']:
        headers = kwargs['headers']
        headers.update(content_type)
    else:
        headers = content_type

    return file_post_request(content, 'userassets/create/%s' % name, headers=headers, **kwargs)

def file_post_request(payload, fragment, **kwargs):
    return _file_post_request(payload, compose_uri(fragment), **kwargs)

def _file_post_request(payload, uri, **kwargs):
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
        if 'headers' in kwargs and kwargs['headers']:
            headers = kwargs['headers']
            headers.update(auth)
        else:
            headers = auth

        response = requests.post(url, data=payload, headers=headers)
    else:
        response = requests.post(url, data=payload, cookies=auth, headers=headers)
    response.raise_for_status()
    return response


def remove_asset(**kwargs):
    return_message = None
    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None
    if not 'all' in kwargs:
        kwargs['all'] = None

    if kwargs['id']:
        _remove_substrate(kwargs['id'], **kwargs)
        return_message = 'Removed 1 substrate'
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        results = json.loads(make_post_request({'query':kwargs['name']}, 'userassets/search', **kwargs).content)
        if 'asset_list' in results and 'files' in results['asset_list']:
            assets = results['asset_list']['files']
            to_remove = []
            for asset in assets:
                if asset['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], asset['name'])):
                    to_remove.append(asset)
            if len(to_remove) == 1:
                _remove_asset(to_remove[0]['id'], **kwargs)
                return_message = 'Removed 1 asset'
            elif kwargs['all']:
                for asset in to_remove:
                    _remove_asset(asset['id'], **kwargs)
                return_message = "Removed %s assets" % len(to_remove)
            elif len(to_remove) > 1:
                return_message = "Matching assets:\n"
                return_message += json.dumps(to_remove)
                return_message += "\n\nName or regular expression matched multiple assets.  Pass --all to remove all matching assets."
            else:
                return_message = "No matching assets found."
        else:
            return_message = "The query did not match any assets."

    return return_message

def _remove_asset(asset_id, **kwargs):
    return make_post_request({}, 'userassets/delete/' + asset_id, **kwargs)
