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


def list_templates(**kwargs):
    return list_object('templates', **kwargs)


def wait_for_job(job_id, **kwargs):
    finished = False

    while not finished:
        time.sleep(0.5)
        response = make_get_request(job_id, **kwargs)
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


def compose_uri(fragment):
    prefix = 'conduce/api/v1'
    fragment = fragment.lstrip('/')
    uri = '%s' % fragment
    if not prefix in fragment:
        uri = '%s/%s' % (prefix, fragment)

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

    if 'api_key' in kwargs and kwargs['api_key']:
        auth = session.api_key_header(kwargs['api_key'])
    else:
        if 'user' in kwargs and kwargs['user']:
            user = kwargs['user']
        else:
            user = cfg['default-user']
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
        response = wait_for_job(job_id, **kwargs)
    return response


def _remove_dataset(dataset_id, **kwargs):
    response = make_post_request(None, 'datasets/delete/%s' % dataset_id, **kwargs)
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
    response = make_post_request(None, 'substrates/delete/%s' % substrate_id, **kwargs)
    response.raise_for_status()
    return True


def _remove_thing_by_id(uri_thing, thing_id, **kwargs):
    response = make_post_request(None, ('%s/delete/%s' % (uri_thing, thing_id)), **kwargs)
    response.raise_for_status()
    return True


def _remove_thing(thing, **kwargs):
    return_message = None

    if not 'things' in kwargs:
        things = '%ss' % thing
    else:
        things = kwargs['things']
    if not 'thing_list' in kwargs:
        thing_list = '%s_list' % thing
    else:
        thing_list = kwargs['thing_list']
    if not 'uri_thing' in kwargs:
        uri_thing = things
    else:
        uri_thing = kwargs['uri_thing']
        del kwargs['uri_thing']

    search_uri = '%s/search' % uri_thing

    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None
    if not 'all' in kwargs:
        kwargs['all'] = None

    if kwargs['id']:
        _remove_thing_by_id(uri_thing, kwargs['id'], **kwargs)
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        results = json.loads(make_post_request({'query':kwargs['name']}, search_uri, **kwargs).content)
        if thing_list in results and 'files' in results[thing_list]:
            thing_obj_list = results[thing_list]['files']
            to_remove = []
            for thing_obj in thing_obj_list:
                if thing_obj['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], thing_obj['name'])):
                    to_remove.append(thing_obj)
            if len(to_remove) == 1:
                _remove_thing_by_id(uri_thing, to_remove[0]['id'], **kwargs)
                return_message = 'Removed 1 %s' % thing
            elif kwargs['all']:
                for thing_obj in to_remove:
                    _remove_thing_by_id(uri_thing, thing_obj['id'], **kwargs)
                return_message = "Removed %s %s" % (len(to_remove), things)
            elif len(to_remove) > 1:
                return_message = "Matching %s:\n" % things
                return_message += json.dumps(to_remove)
                return_message += "\n\nName or regular expression matched multiple %s.  Pass --all to remove all matching %s." % (things, things)
            else:
                return_message = "No matching %s found." % things
        else:
            return_message = "The query did not match any %s." % things

    return return_message


def remove_substrate(**kwargs):
    return _remove_thing('substrate', **kwargs)


def create_substrate(name, substrate_def, **kwargs):
    return make_post_request(substrate_def, 'substrates/create/%s' % name, **kwargs)


# NOTE No 'remove lens' method because they are supposedly dropped when the orchestration is removed.

def set_lens_order(lens_id_list, orchestration_id, **kwargs):
    # NOTE Provide the lenses ordered top-to-bottom, but this API wants them the other way around!
    ids = list(reversed(lens_id_list))
    param = { "lens_ids": ids }
    return make_post_request(param, '/conduce/api/v1/orchestration/%s/reorder-lenses' % orchestration_id, **kwargs)

def change_lens_opacity(orchestration_id, lens_id, opacity, **kwargs):
    param = { "lens_id":lens_id, "opacity":opacity }
    return make_post_request(param, '/conduce/api/v1/orchestration/%s/change-lens-opacity' % orchestration_id, **kwargs)

def create_lens(name, lens_def, orchestration_id, **kwargs):
    return make_post_request(lens_def, 'orchestration/%s/create-lens' % orchestration_id, **kwargs)


def _remove_template(template_id, **kwargs):
    response = make_post_request(None, 'templates/delete/%s' % template_id, **kwargs)
    response.raise_for_status()
    return True


def remove_template(**kwargs):
    return _remove_thing('template', **kwargs)

def create_template(name, template_def, **kwargs):
    return make_post_request(template_def, 'templates/create/%s' % name, **kwargs)


def set_time(orchestration_id, time_def, **kwargs):
    return make_post_request(time_def, 'orchestration/%s/set-time' % orchestration_id, **kwargs)

def set_time_fixed(orchestration_id, **kwargs):
    time_config = {}

    start_ms = None
    if 'start' in kwargs and int(kwargs['start']):
        start_ms = kwargs['start']
        time_config["start"] = {"bound_value":start_ms, "type":"FIXED"}
    end_ms = None
    if 'end' in kwargs and int(kwargs['end']):
        end_ms = kwargs['end']
        time_config["end"] = {"bound_value":end_ms, "type":"FIXED"}
    if start_ms and end_ms and (end_ms < start_ms):
        # Swap the values
        time_config["start"] = {"bound_value":end_ms, "type":"FIXED"}
        time_config["end"] = {"bound_value":start_ms, "type":"FIXED"}

    ctrl_params = {}
    if 'initial' in kwargs and int(kwargs['initial']):
        ctrl_params["timestamp_ms"] = kwargs['initial']
    if 'playrate' in kwargs and int(kwargs['playrate']):
        ctrl_params["playrate"] = kwargs['playrate']
    if 'paused' in kwargs:
        ctrl_params["paused"] = kwargs['paused']
    if len(ctrl_params) > 0:
        time_config["time"] = ctrl_params

    if len(time_config):
        return set_time(orchestration_id, time_config, **kwargs)
    return False


def move_camera(orchestration_id, config, **kwargs):
    camera = {
        "position":config['position'],
        "normal":{"x":0, "y":0, "z":1},
        "over":{"x":1, "y":0, "z":0},
        "aperture":config['aperture']
    }
    return make_post_request(camera, 'orchestration/%s/move-camera' % orchestration_id, **kwargs)


def remove_orchestration(**kwargs):
    return _remove_thing('orchestration', **kwargs)


def create_orchestration(orchestration_def, **kwargs):
    return make_post_request(orchestration_def, 'orchestrations/create', **kwargs)


def make_post_request(payload, fragment, **kwargs):
    return _make_post_request(payload, compose_uri(fragment), **kwargs)


def _make_post_request(payload, uri, **kwargs):
    cfg = config.get_full_config()

    if 'host' in kwargs and kwargs['host']:
        host = kwargs['host']
    else:
        host = cfg['default-host']

    if 'api_key' in kwargs and kwargs['api_key']:
        auth = session.api_key_header(kwargs['api_key'])
    else:
        if 'user' in kwargs and kwargs['user']:
            user = kwargs['user']
        else:
            user = cfg['default-user']
        auth = session.get_session(host, user)

    url = 'https://%s/%s' % (host, uri)
    if 'Authorization' in auth:
        if 'headers' in kwargs and kwargs['headers']:
            headers = kwargs['headers']
            headers.update(auth)
        else:
            headers = auth

        if 'orchestrations/delete' in uri:
            headers['Origin'] = "https://%s" % host
        response = requests.post(url, json=payload, headers=headers)
    else:
        if 'orchestrations/delete' in uri:
            headers['Origin'] = "https://%s" % host
        response = requests.post(url, json=payload, cookies=auth, headers=headers)
    response.raise_for_status()
    return response


def create_asset(name, content, mime_type, **kwargs):
    content_type = {'Content-Type': mime_type}
    if 'headers' in kwargs and kwargs['headers']:
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
    return _remove_thing('asset', uri_thing='userassets', **kwargs)

def _remove_asset(asset_id, **kwargs):
    return make_post_request({}, 'userassets/delete/%s' % asset_id, **kwargs)
