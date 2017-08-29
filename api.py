import util
import requests
import session
import config
import json
import time
import re
import urlparse

from retrying import retry

from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import Timeout

# Retry transport and file IO errors.
RETRYABLE_ERRORS = (HTTPError, ConnectionError, Timeout)

# Number of times to retry failed downloads.
NUM_RETRIES = 5

WAIT_EXPONENTIAL_MULTIPLIER = 1000


def _retry_on_retryable_error(exception):
    if isinstance(exception, HTTPError) and exception.response.status_code < 500:
        return False

    return isinstance(exception, RETRYABLE_ERRORS)


def _deprecated(func):
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


@_deprecated
def list_saved(object_to_list, **kwargs):
    return list_object(object_to_list, **kwargs)


def list_object(object_to_list, **kwargs):
    return make_get_request("conduce/api/v1/{}/list".format(object_to_list), **kwargs)


def list_datasets(**kwargs):
    return list_object('datasets', **kwargs)


def list_substrates(**kwargs):
    return list_object('substrates', **kwargs)


def list_templates(**kwargs):
    return list_object('templates', **kwargs)


def wait_for_job(job_id, **kwargs):
    while True:
        time.sleep(0.5)
        response = make_get_request(job_id, **kwargs)
        response.raise_for_status()

        if response.ok:
            msg = response.json()
            if 'response' in msg:
                return response
        else:
            print response.status_code, response.text
            return response


def compose_uri(fragment):
    prefix = 'conduce/api/v1'
    fragment = fragment.lstrip('/')
    uri = '{}'.format(fragment)
    if not prefix in fragment:
        uri = '{}/{}'.format(prefix, fragment)

    return uri


def get_generic_data(dataset_id, entity_id, **kwargs):
    entity = get_entity(dataset_id, entity_id, **kwargs)
    return json.loads(json.loads(entity.content)[0]['attrs'][0]['str_value'])


def get_entity(dataset_id, entity_id, **kwargs):
    return make_get_request('datasets/entity/{}/{}'.format(dataset_id, entity_id), **kwargs)


def make_get_request(fragment, **kwargs):
    """
    Send an HTTP GET request to a Conduce server.

    Sends an HTTP GET request for the specified endpoint to a Conduce server.

    Parameters
    ----------
    fragment : string
        The URI fragment of the requested endpoint. See https://app.conduce.com/docs for a list of endpoints.

    **kwargs : key-value
        Target host and user authorization parameters used to make the request.

        host : string
            The Conduce server's hostname (ex. app.conduce.com) 
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both `api_key` takes precident.
        user : string
            The user's email address.  Used to look up an API key from the Conduce config or, if not found, authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See :py:func:`requests.Response.raise_for_status` for more information.

    """
    return _make_get_request(compose_uri(fragment), **kwargs)


@retry(retry_on_exception=_retry_on_retryable_error, wait_exponential_multiplier=WAIT_EXPONENTIAL_MULTIPLIER, stop_max_attempt_number=NUM_RETRIES)
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

    url = 'https://{}/{}'.format(host, uri)
    if 'Authorization' in auth:
        response = requests.get(url, headers=auth)
    else:
        response = requests.get(url, cookies=auth)
    response.raise_for_status()
    return response


def create_team(team_name, **kwargs):
    return make_post_request({'name': team_name}, 'team-create', **kwargs)


def list_teams(**kwargs):
    return make_get_request('user/list-teams', **kwargs)


def add_user_to_team(team_id, email_address, **kwargs):
    return make_post_request({'invitee': {'email': email_address}}, 'team/{}/invite'.format(team_id), **kwargs)


def list_team_members(team_id, **kwargs):
    return make_get_request('team/{}/users'.format(team_id), **kwargs)


def create_group(team_id, group_name, **kwargs):
    return make_post_request({'name': group_name}, 'team/{}/group-create'.format(team_id), **kwargs)


def list_groups(team_id, **kwargs):
    return make_get_request('team/{}/group-list'.format(team_id), **kwargs)


def add_user_to_group(team_id, group_id, user_id, **kwargs):
    return make_post_request({'id': user_id}, 'team/{}/group/{}/add-user'.format(team_id, group_id), **kwargs)


def list_group_members(team_id, group_id, **kwargs):
    return make_get_request('team/{}/group/{}/users'.format(team_id, group_id), **kwargs)


def set_owner(team_id, resource_id, **kwargs):
    return make_post_request({}, 'acl/{}/transfer-to-team/{}'.format(resource_id, team_id), **kwargs)


def list_permissions(resource_id, **kwargs):
    return make_get_request('acl/{}/view'.format(resource_id), **kwargs)


def set_public_permissions(resource_id, read, write, share, **kwargs):
    target_string = 'public'
    return set_permissions(target_string, resource_id, read, write, share, **kwargs)


def set_team_permissions(resource_id, read, write, share, **kwargs):
    target_string = 'team'
    return set_permissions(target_string, resource_id, read, write, share, **kwargs)


def set_group_permissions(group_id, resource_id, read, write, share, **kwargs):
    target_string = 'group/{}'.format(group_id)
    return set_permissions(target_string, resource_id, read, write, share, **kwargs)


def set_user_permissions(user_id, resource_id, read, write, share, **kwargs):
    target_string = 'user/{}'.format(user_id)
    return set_permissions(target_string, resource_id, read, write, share, **kwargs)


def grant_permissions(target_string, resource_id, read, write, share, **kwargs):
    permissions = {
        'share': share,
        'write': write,
        'read': read,
        'target': target_string
    }
    return make_post_request(permissions, 'acl/{}/grant'.format(resource_id), **kwargs)


def revoke_permissions(target_string, resource_id, read, write, share, **kwargs):
    permissions = {
        'share': share,
        'write': write,
        'read': read,
        'target': target_string
    }
    return make_post_request(permissions, 'acl/{}/revoke'.format(resource_id), **kwargs)


def set_permissions(target_string, resource_id, read, write, share, **kwargs):
    grant_permissions(target_string, resource_id, read, write, share, **kwargs)
    revoke_permissions(target_string, resource_id, not read, not write, not share, **kwargs)


def create_dataset(dataset_name, **kwargs):
    """
    Create a new user owned dataset.

    Creates a dataset with the specified name.  The dataset will be owned by the user who authorized the requested.

    Parameters
    ----------
    dataset_name : string
        A string used to help identify a dataset

    **kwargs
        See :py:func:`make_post_request`

    Returns
    -------
    requests.Response
        The HTTP response from the server in the form of a dictionary with a single key `dataset`. It's value is the datasets unique identifier (UUID).

    """
    response = make_post_request(
        {'name': dataset_name}, 'datasets/create', **kwargs)

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

    ingest_entities(dataset_id, {'entities': [remove_entity]}, **kwargs)

    entity = {
        "identity": key,
        "kind": 'raw_data',
        "timestamp_ms": timestamp,
        "endtime_ms": timestamp,
        "path": [location],
        "attrs": attributes,
    }

    return ingest_entities(dataset_id, {'entities': [entity]}, **kwargs)


def ingest_entities(dataset_id, data, **kwargs):
    if isinstance(data, list):
        data = {'entities': data}

    response = make_post_request(
        data, 'datasets/add-data/{}'.format(dataset_id), **kwargs)
    if 'location' in response.headers:
        job_id = response.headers['location']
        response = wait_for_job(job_id, **kwargs)

    return response


def _clear_dataset(dataset_id, **kwargs):
    response = make_post_request(
        None, 'datasets/clear/{}'.format(dataset_id), **kwargs)

    return True


def _remove_dataset(dataset_id, **kwargs):
    response = make_post_request(
        None, 'datasets/delete/{}'.format(dataset_id), **kwargs)

    return True


def find_dataset(**kwargs):
    return_message = None
    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None

    found = []
    if kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        datasets = json.loads(list_datasets(**kwargs).content)
        for dataset in datasets:
            if dataset['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], dataset['name'])) or dataset['id'] == kwargs['id']:
                found.append(dataset)

    return found


def clear_dataset(**kwargs):
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
        _clear_dataset(kwargs['id'], **kwargs)
        return_message = 'cleared 1 dataset'
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        datasets = json.loads(list_datasets(**kwargs).content)
        to_clear = []
        for dataset in datasets:
            if dataset['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], dataset['name'])):
                to_clear.append(dataset)
        if len(to_clear) == 1:
            _clear_dataset(to_clear[0]['id'], **kwargs)
            return_message = 'cleared 1 dataset'
        elif kwargs['all']:
            for dataset in to_clear:
                _clear_dataset(dataset['id'], **kwargs)
            return_message = "cleared {:d} datasets".format(len(to_clear))
        elif len(to_clear) > 1:
            return_message = "Matching datasets:\n"
            return_message += json.dumps(to_clear)
            return_message += "\n\nName or regular expression matched multiple datasets.  Pass --all to clear all matching datasets."
        else:
            return_message = "No matching datasets found."

    return return_message


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
            return_message = "Removed {:d} datasets".format(len(to_remove))
        elif len(to_remove) > 1:
            return_message = "Matching datasets:\n"
            return_message += json.dumps(to_remove)
            return_message += "\n\nName or regular expression matched multiple datasets.  Pass --all to remove all matching datasets."
        else:
            return_message = "No matching datasets found."

    return return_message


def _remove_substrate(substrate_id, **kwargs):
    response = make_post_request(
        None, 'substrates/delete/{}'.format(substrate_id), **kwargs)

    return True


def _remove_resource_by_id(uri_part, resource_id, **kwargs):
    response = make_post_request(
        None, ('{}/delete/{}'.format(uri_part, resource_id)), **kwargs)

    return True


def _find_resource(resource, **kwargs):
    return_message = None

    if not 'resources' in kwargs:
        resources = '{}s'.format(resource)
    else:
        resources = kwargs['resources']
    if not 'resource_list' in kwargs:
        resource_list = '{}_list'.format(resource)
    else:
        resource_list = kwargs['resource_list']
    if not 'uri_part' in kwargs:
        uri_part = resources
    else:
        uri_part = kwargs['uri_part']
        del kwargs['uri_part']

    search_uri = '{}/search'.format(uri_part)

    if 'id' in kwargs:
        payload = {'query': kwargs['id']}
    elif 'name' in kwargs:
        payload = {'query': kwargs['name']}
    elif 'regex' in kwargs:
        payload = {'query': kwargs['regex']}

    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None

    results = json.loads(make_post_request(payload, search_uri, **kwargs).content)
    found = []
    if resource_list in results and 'files' in results[resource_list]:
        resource_obj_list = results[resource_list]['files']
        for resource_obj in resource_obj_list:
            if resource_obj['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name'])):
                found.append(resource_obj)

    return found


def _remove_resource(resource, **kwargs):
    return_message = None

    if not 'resources' in kwargs:
        resources = '{}s'.format(resource)
    else:
        resources = kwargs['resources']
    if not 'resource_list' in kwargs:
        resource_list = '{}_list'.format(resource)
    else:
        resource_list = kwargs['resource_list']
    if not 'uri_part' in kwargs:
        uri_part = resources
    else:
        uri_part = kwargs['uri_part']
        del kwargs['uri_part']

    search_uri = '{}/search'.format(uri_part)

    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None
    if not 'all' in kwargs:
        kwargs['all'] = None

    if kwargs['id']:
        _remove_resource_by_id(uri_part, kwargs['id'], **kwargs)
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        if kwargs['name']:
            payload = {'query': kwargs['name']}
        elif kwargs['id']:
            payload = {'query': kwargs['id']}
        results = json.loads(make_post_request(payload, search_uri, **kwargs).content)
        if resource_list in results and 'files' in results[resource_list]:
            resource_obj_list = results[resource_list]['files']
            to_remove = []
            for resource_obj in resource_obj_list:
                if resource_obj['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name'])):
                    to_remove.append(resource_obj)
            if len(to_remove) == 1:
                _remove_resource_by_id(uri_part, to_remove[0]['id'], **kwargs)
                return_message = 'Removed 1 {}'.format(resource)
            elif kwargs['all']:
                for resource_obj in to_remove:
                    _remove_resource_by_id(uri_part, resource_obj['id'], **kwargs)
                return_message = "Removed {:d} {}".format(
                    len(to_remove), resources)
            elif len(to_remove) > 1:
                return_message = "Matching {}:\n".format(resources)
                return_message += json.dumps(to_remove)
                return_message += "\n\nName or regular expression matched multiple {}.  Pass --all to remove all matching {}.".format(
                    resources, resources)
            else:
                return_message = "No matching {} found.".format(resources)
        else:
            return_message = "The query did not match any {}.".format(resources)

    return return_message


def find_substrate(**kwargs):
    return _find_resource('substrate', **kwargs)


def remove_substrate(**kwargs):
    return _remove_resource('substrate', **kwargs)


def create_substrate(name, substrate_def, **kwargs):
    return make_post_request(substrate_def, 'substrates/create/{}'.format(name), **kwargs)


# NOTE No 'remove lens' method because they are supposedly dropped when
# the orchestration is removed.

def set_lens_order(lens_id_list, orchestration_id, **kwargs):
    # NOTE Provide the lenses ordered top-to-bottom, but this API wants them
    # the other way around!
    ids = list(reversed(lens_id_list))
    param = {"lens_ids": ids}
    return make_post_request(param, '/conduce/api/v1/orchestration/{}/reorder-lenses'.format(orchestration_id), **kwargs)


def change_lens_opacity(orchestration_id, lens_id, opacity, **kwargs):
    param = {"lens_id": lens_id, "opacity": opacity}
    return make_post_request(param, '/conduce/api/v1/orchestration/{}/change-lens-opacity'.format(orchestration_id), **kwargs)


def create_lens(name, lens_def, orchestration_id, **kwargs):
    return make_post_request(lens_def, 'orchestration/{}/create-lens'.format(orchestration_id), **kwargs)


def _remove_template(template_id, **kwargs):
    response = make_post_request(
        None, 'templates/delete/{}'.format(template_id), **kwargs)

    return True


def find_template(**kwargs):
    return _find_resource('template', **kwargs)


def remove_template(**kwargs):
    return _remove_resource('template', **kwargs)


def create_template(name, template_def, **kwargs):
    return make_post_request(template_def, 'templates/create/{}'.format(name), **kwargs)


def get_template(id, **kwargs):
    return make_get_request('templates/get/{}'.format(id), **kwargs)


def save_template(id, template_def, **kwargs):
    return make_post_request(template_def, 'templates/save/{}'.format(id), **kwargs)


def set_time(orchestration_id, time_def, **kwargs):
    return make_post_request(time_def, 'orchestration/{}/set-time'.format(orchestration_id), **kwargs)


def set_time_fixed(orchestration_id, **kwargs):
    time_config = {}

    start_ms = None
    if 'start' in kwargs and int(kwargs['start']):
        start_ms = kwargs['start']
        time_config["start"] = {"bound_value": start_ms, "type": "FIXED"}
    end_ms = None
    if 'end' in kwargs and int(kwargs['end']):
        end_ms = kwargs['end']
        time_config["end"] = {"bound_value": end_ms, "type": "FIXED"}
    if start_ms and end_ms and (end_ms < start_ms):
        # Swap the values
        time_config["start"] = {"bound_value": end_ms, "type": "FIXED"}
        time_config["end"] = {"bound_value": start_ms, "type": "FIXED"}

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
        "position": config['position'],
        "normal": {"x": 0, "y": 0, "z": 1},
        "over": {"x": 1, "y": 0, "z": 0},
        "aperture": config['aperture']
    }
    return make_post_request(camera, 'orchestration/{}/move-camera'.format(orchestration_id), **kwargs)


def find_orchestration(**kwargs):
    return _find_resource('orchestration', **kwargs)


def remove_orchestration(**kwargs):
    return _remove_resource('orchestration', **kwargs)


def create_orchestration(orchestration_def, **kwargs):
    return make_post_request(orchestration_def, 'orchestrations/create', **kwargs)


def save_as_orchestration(orchestration_id, saveas_orchestration_def, replace, **kwargs):
    if replace:
        saveas_orchestration_def["replace"] = True
    return make_post_request(saveas_orchestration_def, 'orchestrations/save-as/{}'.format(orchestration_id), **kwargs)


def save_orchestration(orchestration_id, **kwargs):
    return make_post_request(None, 'orchestrations/save/{}'.format(orchestration_id), **kwargs)


def create_api_key(**kwargs):
    response = make_post_request(
        {"description": "Generated and used by conduce-python-api"}, 'apikeys/create', **kwargs)
    return json.loads(response.content)['apikey']


def make_post_request(payload, fragment, **kwargs):
    """
    Send an HTTP POST request to a Conduce server.

    Sends an HTTP POST request for the specified endpoint to a Conduce server.

    Parameters
    ----------
    payload : dictionary
        A dictionary representation of JSON content to be posted to the Conduce server.  See the `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/#more-complicated-post-requests>`_ for more information.

    fragment : string
        The URI fragment of the requested endpoint. See https://app.conduce.com/docs for a list of endpoints.

    **kwargs : key-value
        Target host and user authorization parameters used to make the request.

        host : string
            The Conduce server's hostname (ex. app.conduce.com) 
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both `api_key` takes precident.
        user : string
            The user's email address.  Used to look up an API key from the Conduce config or, if not found, authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See :py:func:`requests.Response.raise_for_status` for more information.

    """
    return _make_post_request(payload, compose_uri(fragment), **kwargs)


@retry(retry_on_exception=_retry_on_retryable_error, wait_exponential_multiplier=WAIT_EXPONENTIAL_MULTIPLIER, stop_max_attempt_number=NUM_RETRIES)
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

    headers = {}
    url = 'https://{}/{}'.format(host, uri)
    if 'Authorization' in auth:
        if 'headers' in kwargs and kwargs['headers']:
            headers = kwargs['headers']
            headers.update(auth)
        else:
            headers = auth

        if 'orchestrations/delete' in uri:
            headers['Origin'] = "https://{}".format(host)
        response = requests.post(url, json=payload, headers=headers)
    else:
        if 'orchestrations/delete' in uri:
            headers['Origin'] = "https://{}".format(host)
        response = requests.post(
            url, json=payload, cookies=auth, headers=headers)
    response.raise_for_status()
    return response


def create_asset(name, content, mime_type, **kwargs):
    content_type = {'Content-Type': mime_type}
    if 'headers' in kwargs and kwargs['headers']:
        headers = kwargs['headers']
        headers.update(content_type)
    else:
        headers = content_type

    return file_post_request(content, 'userassets/create/{}'.format(name), headers=headers, **kwargs)


def file_post_request(payload, fragment, **kwargs):
    return _file_post_request(payload, compose_uri(fragment), **kwargs)


def _file_post_request(payload, uri, **kwargs):
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

    headers = {}
    url = 'https://{}/{}'.format(host, uri)
    if 'Authorization' in auth:
        if 'headers' in kwargs and kwargs['headers']:
            headers = kwargs['headers']
            headers.update(auth)
        else:
            headers = auth
        response = requests.post(url, data=payload, headers=headers)
    else:
        response = requests.post(
            url, data=payload, cookies=auth, headers=headers)
    response.raise_for_status()
    return response


def find_asset(**kwargs):
    return _find_resource('asset', uri_part='userassets', **kwargs)


def remove_asset(**kwargs):
    return _remove_resource('asset', uri_part='userassets', **kwargs)


def _remove_asset(asset_id, **kwargs):
    return make_post_request({}, 'userassets/delete/{}'.format(asset_id), **kwargs)


def account_exists(email, **kwargs):
    try:
        make_post_request({'email': email}, 'user/public/email-available', **kwargs)
        return False
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            return True
        else:
            raise e


def create_account(name, email, **kwargs):
    return make_post_request({'email': email, 'name': name}, 'admin/create-user', **kwargs)
