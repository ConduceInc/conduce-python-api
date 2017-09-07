import util
import requests
import session
import config
import json
import time
import re
import urlparse
import base64
import warnings

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
def list_object(object_to_list, **kwargs):
    return list_resources(object_to_list.upper().rstrip('S'), **kwargs)


def list_resources(resource_type, **kwargs):
    return find_resource(type=resource_type, **kwargs)


def list_datasets(**kwargs):
    return list_resources('DATASET', **kwargs)


def list_substrates(**kwargs):
    return list_resources('SUBSTRATE', **kwargs)


def list_templates(**kwargs):
    return list_resources('LENS_TEMPLATE', **kwargs)


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
    if not 'conduce/api' in fragment:
        uri = '{}/{}'.format(prefix, fragment)

    return uri


def get_generic_data(dataset_id, entity_id, **kwargs):
    entity = get_entity(dataset_id, entity_id, **kwargs)
    return json.loads(json.loads(entity.content)[0]['attrs'][0]['str_value'])


def get_entity(dataset_id, entity_id, **kwargs):
    return make_get_request('datasets/entity/{}/{}'.format(dataset_id, entity_id), **kwargs)


@retry(retry_on_exception=_retry_on_retryable_error, wait_exponential_multiplier=WAIT_EXPONENTIAL_MULTIPLIER, stop_max_attempt_number=NUM_RETRIES)
def _make_delete_request(uri, **kwargs):
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
        response = requests.delete(url, headers=auth)
    else:
        response = requests.delete(url, cookies=auth)
    response.raise_for_status()
    return response


def make_delete_request(fragment, **kwargs):
    """
    Send an HTTP DELETE request to a Conduce server.

    Sends an HTTP DELETE request for the specified endpoint to a Conduce server.

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
    return _make_delete_request(compose_uri(fragment), **kwargs)


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

    return create_json_resource('DATASET', dataset_name, {'backend': 'SAGE_BACKEND'}, **kwargs)


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
        datasets = list_datasets(**kwargs)
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


def find_resource(**kwargs):
    return_message = None

    search_uri = 'conduce/api/v2/resources/searches'

    if kwargs.get('content', None) is not None:
        search_uri += '?content={}'.format(kwargs.get('content', None))

    payload = {}
    if kwargs.get('type', None) is not None:
        payload.update({'type': kwargs.get('type', None)})
    # TODO: uncomment when fix is pushed to PRD
    # if kwargs.get('name', None) is not None:
    #    payload.update({'name': kwargs.get('name', None)})
    if kwargs.get('mime', None) is not None:
        payload.update({'mime': kwargs.get('mime', None)})
    if kwargs.get('tags', None) is not None:
        payload.update({'tags': kwargs.get('tags', None)})

    if not 'id' in kwargs:
        kwargs['id'] = None
    if not 'regex' in kwargs:
        kwargs['regex'] = None
    if not 'name' in kwargs:
        kwargs['name'] = None

    results = json.loads(make_post_request(payload, search_uri, **kwargs).content)

    if kwargs.get('content', None) == 'id':
        return results['resource_ids']

    found = []
    if 'resources' in results:
        if kwargs['name'] is None and kwargs['regex'] is None and kwargs['id'] is None:
            return results['resources']
        else:
            for resource_obj in results['resources']:
                if resource_obj['id'] == kwargs['id'] or resource_obj['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name'])):
                    found.append(resource_obj)

    return found


def _remove_resource(resource_id, **kwargs):
    return make_delete_request('conduce/api/v2/resources/{}?permanent={}'.format(resource_id, kwargs.get('permanent', False)), **kwargs)


def remove_resource(resource_type, **kwargs):
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
        _remove_resource(kwargs['id'], **kwargs)
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        results = find_resource(type=resource_type, **kwargs)
        to_remove = []
        for resource_obj in results:
            if resource_obj['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name'])):
                to_remove.append(resource_obj)
        if len(to_remove) == 1:
            _remove_resource(to_remove[0]['id'], **kwargs)
            return_message = 'Removed 1 {}'.format(resource_type)
        elif kwargs['all']:
            for resource_obj in to_remove:
                _remove_resource(resource_obj['id'], **kwargs)
            return_message = "Removed {:d} {}".format(
                len(to_remove), resource_type)
        elif len(to_remove) > 1:
            return_message = "Matching {}:\n".format(resource_type)
            return_message += json.dumps(to_remove)
            return_message += "\n\nName or regular expression matched multiple {}.  Pass --all to remove all matching {}.".format(
                resource_type, resource_type)
        else:
            return_message = "No matching {} found.".format(resource_type)
    else:
        return_message = "The query did not match any {}.".format(resource_type)

    return return_message


def remove_substrate(**kwargs):
    return remove_resource('SUBSTRATE', **kwargs)


def remove_dataset(**kwargs):
    return remove_resource('DATASET', **kwargs)


def remove_template(**kwargs):
    return remove_resource('LENS_TEMPLATE', **kwargs)


def remove_asset(**kwargs):
    return remove_resource('ASSET', **kwargs)


def remove_orchestration(**kwargs):
    return remove_resource('ORCHESTRATION', **kwargs)


def create_substrate(name, substrate_def, **kwargs):
    return create_json_resource('SUBSTRATE', name, substrate_def, **kwargs)


def find_orchestration(**kwargs):
    return find_resource(type='ORCHESTRATION', **kwargs)


def find_asset(**kwargs):
    return find_resource(type='ASSET', **kwargs)


def find_substrate(**kwargs):
    return find_resource(type='SUBSTRATE', **kwargs)


def find_template(**kwargs):
    return find_resource(type='LENS_TEMPLATE', **kwargs)


def find_dataset(**kwargs):
    return find_resource(type='DATASET', **kwargs)


def create_template(name, template_def, **kwargs):
    return create_json_resource('LENS_TEMPLATE', name, template_def, **kwargs)


def get_resource(resource_id, **kwargs):
    fragment = 'conduce/api/v2/resources/{}'.format(resource_id)
    if kwargs.get('raw', False) == True:
        fragment += '?content=raw'

    response = make_get_request(fragment, **kwargs).content
    if kwargs.get('raw', False) == False:
        response = json.loads(response)

    return response


def _update_resource(resource_id, resource_def, **kwargs):
    return json.loads(make_put_request(resource_def, 'conduce/api/v2/resources/{}'.format(resource_id), **kwargs).content)


def get_time_fixed(time):
    time_config = {}

    start_ms = None
    if 'start' in time and int(time['start']):
        start_ms = time['start']
        time_config["start"] = {"bound_value": start_ms, "type": "FIXED"}
    end_ms = None
    if 'end' in time and int(time['end']):
        end_ms = time['end']
        time_config["end"] = {"bound_value": end_ms, "type": "FIXED"}
    if start_ms and end_ms and (end_ms < start_ms):
        # Swap the values
        time_config["start"] = {"bound_value": end_ms, "type": "FIXED"}
        time_config["end"] = {"bound_value": start_ms, "type": "FIXED"}

    ctrl_params = {}
    if 'initial' in time and int(time['initial']):
        ctrl_params["set_orch_time_ms"] = time['initial']
    if 'playrate' in time and int(time['playrate']):
        ctrl_params["playrate"] = time['playrate']
    if 'paused' in time:
        ctrl_params["paused"] = time['paused']
    if len(ctrl_params) > 0:
        time_config["time"] = ctrl_params

    return time_config


def get_camera(config):
    return {
        "position": config['position'],
        "normal": {"x": 0, "y": 0, "z": 1},
        "over": {"x": 1, "y": 0, "z": 0},
        "aperture": config['aperture']
    }


def is_base64_encoded(string):
    try:
        if base64.b64encode(base64.b64decode(string)) == string:
            return True
    except:
        pass

    return False


def create_resource(resource_type, resource_name, content, mime_type, **kwargs):
    if not (mime_type.startswith('text') or mime_type == 'application/json'):
        if not is_base64_encoded(content):
            print "base64 encoding content for {}".format(resource_name)
            content = base64.b64encode(content)

    resource_def = {
        'name': resource_name,
        'tags': kwargs.get('tags', None),
        'type': resource_type,
        'mime': mime_type,
        'content': content
    }

    return json.loads(make_post_request(resource_def, 'conduce/api/v2/resources', **kwargs).content)


def create_json_resource(resource_type, resource_name, content, **kwargs):
    return create_resource(
        resource_type,
        resource_name,
        json.dumps(content),
        'application/json',
        **kwargs)


def create_orchestration(name, orchestration_def, **kwargs):
    return create_json_resource('ORCHESTRATION', name, orchestration_def, **kwargs)


def create_api_key(**kwargs):
    response = make_post_request(
        {"description": "Generated and used by conduce-python-api"}, 'apikeys/create', **kwargs)
    return json.loads(response.content)['apikey']


def make_post_request(payload, fragment, **kwargs):
    """
    Send an HTTP POST request to a Conduce server.

    Sends an HTTP POST request for the specified endpoint to a Conduce server.  POST requests are used to create conduce resources.

    Parameters
    ----------
    payload : dictionary
        # more-complicated-post-requests>`_ for more information.
        A dictionary representation of JSON content to be posted to the Conduce server.  See the `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/

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

        response = requests.post(url, json=payload, headers=headers)
    else:
        response = requests.post(url, json=payload, cookies=auth, headers=headers)

    response.raise_for_status()
    return response


def make_put_request(payload, fragment, **kwargs):
    """
    Send an HTTP PUT request to a Conduce server.

    Sends an HTTP PUT request for the specified endpoint to a Conduce server.  PUT requests are used to replace/update Conduce resources.

    Parameters
    ----------
    payload : dictionary
        # more-complicated-post-requests>`_ for more information.
        A dictionary representation of JSON content used to replace the Conduce resource.  See the `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/

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
    return _make_put_request(payload, compose_uri(fragment), **kwargs)


@retry(retry_on_exception=_retry_on_retryable_error, wait_exponential_multiplier=WAIT_EXPONENTIAL_MULTIPLIER, stop_max_attempt_number=NUM_RETRIES)
def _make_put_request(payload, uri, **kwargs):
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

        response = requests.put(url, json=payload, headers=headers)
    else:
        response = requests.put(url, json=payload, cookies=auth, headers=headers)

    response.raise_for_status()
    return response


def make_patch_request(payload, fragment, **kwargs):
    """
    Send an HTTP PATCH request to a Conduce server.

    Sends an HTTP PATCH request for the specified endpoint to a Conduce server.  PATCH requests are used to modify Conduce resources.

    Parameters
    ----------
    payload : dictionary
        # more-complicated-post-requests>`_ for more information.
        A dictionary representation of JSON content to be patched in the Conduce resource.  See the `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/

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
    return _make_patch_request(payload, compose_uri(fragment), **kwargs)


@retry(retry_on_exception=_retry_on_retryable_error, wait_exponential_multiplier=WAIT_EXPONENTIAL_MULTIPLIER, stop_max_attempt_number=NUM_RETRIES)
def _make_patch_request(payload, uri, **kwargs):
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

        response = requests.patch(url, json=payload, headers=headers)
    else:
        response = requests.patch(url, json=payload, cookies=auth, headers=headers)

    response.raise_for_status()
    return response


def update_orchestration(resource, **kwargs):
    return update_resource(resource, **kwargs)


def update_substrate(resource, **kwargs):
    return update_resource(resource, **kwargs)


def update_template(resource, **kwargs):
    return update_resource(resource, **kwargs)


def update_asset(resource, **kwargs):
    return update_resource(resource, **kwargs)


def update_resource(resource, **kwargs):
    resource['revision'] += 1
    return _update_resource(resource['id'], resource, **kwargs)


def create_asset(name, content, mime_type, **kwargs):
    return create_resource(
        'ASSET',
        name,
        content,
        mime_type,
        **kwargs)


def modify_asset_content(resource_id, content, mime_type, **kwargs):
    return modify_resource_content(resource_id, content, mime_type, **kwargs)


def modify_resource_json(resource_id, content, **kwargs):
    return modify_resource_content(resource_id, content, 'application/json', **kwargs)


def modify_resource_content(resource_id, content, mime_type, **kwargs):
    if mime_type == 'application/json':
        print "JSON encoding content for {}".format(resource_id)
        content = json.dumps(content)
    elif not (mime_type.startswith('text') or mime_type == 'application/json'):
        if not is_base64_encoded(content):
            print "base64 encoding content for {}".format(resource_id)
            content = base64.b64encode(content)

    return _modify_resource_content(resource_id, content, **kwargs)


def _modify_resource_content(resource_id, content, **kwargs):
    payload = [{
        'path': '/content',
        'value': content,
        'op': 'add'
    }]
    return make_patch_request(payload, 'conduce/api/v2/resources/{}'.format(resource_id), **kwargs)


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
