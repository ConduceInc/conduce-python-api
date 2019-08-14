from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
from builtins import str
import requests
import json
import time
import re
import base64
import warnings

from datetime import datetime
from retrying import retry

from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from requests.exceptions import Timeout

from . import util
from . import session
from . import config

standard_library.install_aliases()

# Retry transport and file IO errors.
RETRYABLE_ERRORS = (HTTPError, ConnectionError, Timeout)

# Number of times to retry failed downloads.
NUM_RETRIES = 5

WAIT_EXPONENTIAL_MULTIPLIER = 1000


class DatasetBackends:
    BACKEND_TYPES = {
        'simple': 'SimpleStore',
        'tile': 'TileStore',
        'capped_tile': 'CappedTileStore',
        'elasticsearch': 'ElasticsearchStore',
        'histogram': 'HistogramStore',
    }
    simple = BACKEND_TYPES['simple']
    tile = BACKEND_TYPES['tile']
    capped_tile = BACKEND_TYPES['capped_tile']
    elasticsearch = BACKEND_TYPES['elasticsearch']
    histogram = BACKEND_TYPES['histogram']


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
    """
    This function is deprecated.  Call :py:func:`list_resources` instead.
    """
    return list_resources(object_to_list.upper().rstrip('S'), **kwargs)


@_deprecated
def _make_delete_request(uri, **kwargs):
    """
    This function is deprecated.  Call :py:func:`_make_request` instead.
    """
    return _make_request(requests.delete, None, uri, **kwargs)


@_deprecated
def _make_get_request(uri, **kwargs):
    """
    This function is deprecated.  Call :py:func:`_make_request` instead.
    """
    return _make_request(requests.get, None, uri, **kwargs)


@_deprecated
def _make_post_request(payload, uri, **kwargs):
    """
    This function is deprecated.  Call :py:func:`_make_request` instead.
    """
    return _make_request(requests.post, payload, uri, **kwargs)


@_deprecated
def _make_put_request(payload, uri, **kwargs):
    """
    This function is deprecated.  Call :py:func:`_make_request` instead.
    """
    return _make_request(requests.put, payload, uri, **kwargs)


@_deprecated
def _make_patch_request(payload, uri, **kwargs):
    """
    This function is deprecated.  Call :py:func:`_make_request` instead.
    """
    return _make_request(requests.patch, payload, uri, **kwargs)


def list_resources(resource_type, **kwargs):
    """
    List all resources of the given type.

    A convenience method that calls :py:func:`find_resource`.  This function, however, requires
    the user to specify a resource type.

    Parameters
    ----------
    resource_type : string
        Resource type to fetch.  One of: SUBSTRATE, DATASET, ASSET, LENS_TEMPLATE, ORCHESTRATION.
    kwargs : key-value
        host : string
            The Conduce server's hostname (ex. app.conduce.com)
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.
            If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce configuration or,
            if not found, authenticate via password.  Ignored if `api_key` is provided.


    See :py:func:`find_resource` for information on return type.
    """
    return find_resource(type=resource_type, **kwargs)


def list_datasets(**kwargs):
    """
    List all accessible datasets.

    A convenience method that calls :py:func:`list_resources` with the ``type`` field set to "DATASET."

    See :py:func:`find_resource` for information on return type.
    """
    return list_resources('DATASET', **kwargs)


def list_substrates(**kwargs):
    """
    List all accessible substrates.

    A convenience method that calls :py:func:`list_resources` with the ``type`` field set to "SUBSTRATE."

    See :py:func:`find_resource` for information on return type.
    """
    return list_resources('SUBSTRATE', **kwargs)


def list_templates(**kwargs):
    """
    List all accessible lens templates.

    A convenience method that calls :py:func:`list_resources` with the ``type`` field set to "LENS_TEMPLATE."

    See :py:func:`find_resource` for information on return type.
    """
    return list_resources('LENS_TEMPLATE', **kwargs)


def wait_for_job(job_id, **kwargs):
    """
    Wait for a job to complete.

    Block execution until the completion of an asynchronous job.

    Parameters
    ----------
    job_id : string
        The UUID that identifies the job to query.  The job ID is returned in the response header of the request that starts the job.
    **kwargs:
        See :py:func:`make_get_request`

    Returns
    -------
    requests.Response
        Returns the final response message when the job is no longer running.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure.
        See :py:meth:`requests.Response.raise_for_status` for more information.
    """
    while True:
        time.sleep(0.5)
        try:
            response = make_get_request(job_id, **kwargs)

            if response.ok:
                msg = response.json()
                if 'response' in msg:
                    return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code < 500:
                return e.response
            else:
                print("Job status check failed:", e.response.reason)
                print("Will retry after sleep period.")


def compose_uri(fragment):
    if 'api/v' not in fragment:
        prefix = 'conduce/api/v1'
        fragment = fragment.lstrip('/')
        uri = '{}'.format(fragment)
        if 'conduce/api' not in fragment:
            uri = '{}/{}'.format(prefix, fragment)
    else:
        uri = fragment

    return uri


def get_generic_data(dataset_id, entity_id, **kwargs):
    entity = _get_entity(dataset_id, entity_id, **kwargs)
    attrs = json.loads(entity.content)[0]['attrs']
    for attr in attrs:
        if attr["key"] == "json_data":
            return json.loads(attr["str_value"])
    raise ValueError("No generic data found")


def get_entity(dataset_id, entity_id, **kwargs):
    entity = _get_entity(dataset_id, entity_id, **kwargs)
    return json.loads(entity.content)


def _get_entity(dataset_id, entity_id, **kwargs):
    return make_get_request('datasets/entity/{}/{}'.format(dataset_id, entity_id), **kwargs)


def get_dataset_metadata(dataset_id, **kwargs):
    return json.loads(make_get_request('datasets/metadata/{}'.format(dataset_id), **kwargs).content)


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

    Creates a dataset with the specified name.  The dataset will be owned by the user who authorized
    the requested.  :py:func:`create_dataset` is a convenience wrapper that calls
    :py:func:`create_json_resource`, which in turn calls :py:func:`create_resource`.  For general
    information about creating resources see :py:func:`create_resource`.

    Parameters
    ----------
    dataset_name : string
        A string used to help identify a dataset

    **kwargs
        See :py:func:`create_resource`

    Returns
    -------
    dictionary
        Returns information about newly created dataset, here's an example::

           {
               'name': 'some_dataset',
               'tags': [], 'encoded_size': 26,
               'create_time': 1509762757760,
               'mime': 'application/json',
               'modify_time': 1509762757760,
               'revision': 1,
               'type': 'DATASET',
               'id': '19311131-b6d5-4e72-9994-343b9cff80a0',
               'size': 2
           }
    """

    return create_json_resource('DATASET', dataset_name, {'backend': 'SAGE_BACKEND'}, **kwargs)


def set_generic_data(dataset_id, key, data_string, **kwargs):
    timestamp = datetime(1970, 1, 1)
    point = {"x": 0, "y": 0}

    remove_entity = {
        "id": key,
        "kind": 'raw_data',
        "time": timestamp,
        "point": point,
        "removed": True,
    }

    ingest_samples(dataset_id, [remove_entity], **kwargs)

    entity = {
        "id": key,
        "kind": 'raw_data',
        "time": timestamp,
        "point": point,
        "json_data": data_string,
    }

    return ingest_samples(dataset_id, [entity], **kwargs)


@_deprecated
def _convert_coordinates(point):
    if len(point) != 2:
        raise KeyError('A point should only have two dimensions', point)
    if 'lat' and 'lon' in point:
        coord = {
            'x': float(point['lon']),
            'y': float(point['lat'])
        }
    elif 'x' and 'y' in point:
        coord = {
            'x': float(point['x']),
            'y': float(point['y'])
        }
    else:
        raise KeyError('invalid coordinate', point)

    coord['z'] = 0

    return coord


@_deprecated
def _convert_geometries(sample):
    coordinates = []
    if 'point' in sample:
        coordinates = [_convert_coordinates(sample['point'])]
    if 'path' in sample:
        if len(coordinates) > 0:
            raise KeyError('A sample may only contain one of point, path or polygon', sample)
        if len(sample['path']) < 2:
            raise KeyError('paths must have at least two points')
        for point in sample['path']:
            coordinates.append(_convert_coordinates(point))
    if 'polygon' in sample:
        if len(coordinates) > 0:
            raise KeyError('A sample may only contain one of point, path or polygon', sample)
        if len(sample['polygon']) < 3:
            raise KeyError('polygons must have at least three points')
        for point in sample['polygon']:
            coordinates.append(_convert_coordinates(point))

    return coordinates


@_deprecated
def _convert_samples_to_entity_set(sample_list):
    conduce_keys = ['id', 'kind', 'time', 'point', 'path', 'polygon']
    entities = []
    for idx, sample in enumerate(sample_list):
        if 'id' not in sample:
            raise ValueError('Error processing sample at index {}. Samples must include an ID.'.format(idx), sample)
        if 'kind' not in sample:
            raise ValueError('Error processing sample at index {}. Samples must include a kind field.'.format(idx), sample)
        if 'time' not in sample:
            raise ValueError('Error processing sample at index {}. Samples must include a time field.'.format(idx), sample)

        if sample['id'] is None or len(str(sample['id'])) == 0:
            raise ValueError('Error processing sample at index {}. Invalid ID.'.format(idx), sample)
        if sample['kind'] is None or len(sample['kind']) == 0:
            raise ValueError('Error processing sample at index {}. Invalid kind.'.format(idx), sample)
        if sample['time'] is None:
            raise ValueError('Error processing sample at index {}. Invalid time.'.format(idx), sample)

        if not isinstance(sample['time'], datetime):
            raise TypeError('Error processing sample at index {}. Time must be a datetime object.'.format(idx), sample['time'])

        coordinates = _convert_geometries(sample)
        if coordinates == []:
            raise ValueError('Error processing sample at index {}.  Samples must define a location (point, path, or polygon)'.format(idx), sample)

        sample['_kind'] = sample['kind']
        attribute_keys = [key for key in list(sample.keys()) if key not in conduce_keys]
        attributes = util.get_attributes(attribute_keys, sample)

        entities.append({
            'identity': str(sample['id']),
            'kind': sample['kind'],
            'timestamp_ms': util.datetime_to_timestamp_ms(sample['time']),
            'endtime_ms': util.datetime_to_timestamp_ms(sample['time']),
            'path': coordinates,
            'attrs': attributes
        })

    return {'entities': entities}


def ingest_samples(dataset_id, sample_list, **kwargs):
    """
    Upload a :doc:`sample list <conduce-entities>` to the Conduce datastore.

    A convenience method that adds a list of entity samples to the Conduce datastore and
    waits for the job to complete. This function POSTs a sample list to Conduce and :py:func:`wait_for_job`
    until the ingest job completes.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    sample_list : list
        A list of entity samples.  See :doc:`conduce-entities` for documentation on how to build a sample list.

    **kwargs:
        See :py:func:`make_post_request`

    Returns
    -------
    requests.Response
        Returns an error or the final response message when the job is no longer running.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure.
        See :py:meth:`requests.Response.raise_for_status` for more information.
    """

    if not isinstance(sample_list, list):
        raise ValueError('sample_list must be a list', sample_list)

    entity_set = util.samples_to_entity_set(sample_list)
    return _ingest_entity_set(dataset_id, entity_set, **kwargs)


@_deprecated
def convert_entities_to_entity_set(entity_list):
    conduce_keys = ['id', 'kind', 'point', 'path', 'polygon']
    entities = []
    ids = set()
    for idx, ent in enumerate(entity_list):
        if 'id' not in ent:
            raise ValueError('Error processing entity at index {}. Entities must include an ID.'.format(idx), ent)
        if 'kind' not in ent:
            raise ValueError('Error processing entity at index {}. Entities must include a kind field.'.format(idx), ent)

        if ent['id'] is None or len(str(ent['id'])) == 0:
            raise ValueError('Error processing entity at index {}. Invalid ID.'.format(idx), ent)
        if ent['id'] in ids:
            raise ValueError('Error processing entity at index{}. Non-Unique ID'.format(idx), ent)
        if ent['kind'] is None or len(ent['kind']) == 0:
            raise ValueError('Error processing entity at index {}. Invalid kind.'.format(idx), ent)
        if ent.get('time') is not None:
            raise KeyError('Error processing entity at index {}. Timeless entities should not set time.'.format(idx), ent)

        coordinates = _convert_geometries(ent)
        if coordinates == []:
            raise ValueError('Error processing entity at index {}.  Entities must define a location (point, path, or polygon)'.format(idx), ent)

        ids.add(ent['id'])
        ent['_kind'] = ent['kind']
        attribute_keys = [key for key in list(ent.keys()) if key not in conduce_keys]
        attributes = util.get_attributes(attribute_keys, ent)

        entities.append({
            'identity': str(ent['id']),
            'kind': ent['kind'],
            'timestamp_ms': util.get_default('timestamp_ms'),
            'endtime_ms': util.get_default('endtime_ms'),
            'path': coordinates,
            'attrs': attributes
        })

    return {'entities': entities}


def ingest_entities(dataset_id, entity_list, **kwargs):
    """
    Upload :doc:`entities <conduce-entities>` to the Conduce datastore.

    A convenience method that adds entities to the Conduce datastore and waits for the job to
    complete. This function POSTs an entity set to Conduce and :py:func:`wait_for_job` until the
    ingest job completes.

    Each element of ``entity_list`` must be a valid :ref:`entity structure <entity-sample-definitions>`.
    Here is a simple valid structure::

        {
            "id": <string>,
            "kind": <string>,
            "point": {
                "lat": <float>,
                "lon": <float>
            }
        }

    It may also contain additional fields with arbitrary keys.

    Since entities do not have timestamps they exist across all time.  Entities must be unique, that
    means each element in ``entity_list`` must have a unique ID.  Because entities do not have timestamps,
    ID is the only field that makes them unique.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    entity_list : list
        A list of entities.  See :doc:`data-ingest` for documentation on how to build an entity list.
    **kwargs:
        See :py:func:`make_post_request`

    Returns
    -------
    requests.Response
        Returns an error or the final response message when the job is no longer running.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.
    """

    entity_set = util.entities_to_entity_set(entity_list)

    return _ingest_entity_set(dataset_id, entity_set, **kwargs)


def insert_transaction(dataset_id, entity_set, **kwargs):
    """
    Add records to a dataset.

    Inserts unique records at the beginning, middle, or end of a dataset.

    The operation will fail if the records are not unique.  Uniqueness is determined by the combination of a record's ID and timestamp.
    """
    return post_transaction(dataset_id, entity_set, operation='INSERT', **kwargs)


def append_transaction(dataset_id, entity_set, **kwargs):
    """
    Add new records to the end of the dataset.

    Append is an optimization over insert in that it only checks to see that all records in the transaction
    are newer than the newest record in the transaction log.

    Append may fail to add valid records that occur between the end of an entity stream and the end of a dataset.
    """
    return post_transaction(dataset_id, entity_set, operation='APPEND', **kwargs)


def post_transaction(dataset_id, entity_set, **kwargs):
    """
    Add a new dataset transaction.  This method is provided for completeness and
    should be avoided in favor of :py:func:`insert_transaction` and :py:func:`append_transaction`.

    By default, the transaction will not be processed. Use the `process` kwarg to trigger automatic processing.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    entity_set : dictionary
        A dictionary of raw Conduce entities. Use :py:meth:`util.samples_to_entity_set` or
        :py:meth:`util.entities_to_entity_set` to construct an entity set dictionary.
        See :doc:`data-ingest` for documentation on how to ingest data.
    **kwargs : key-value
        **operation**
            The dataset operation to perform on the posted entity set.  Supports all
            operations listed in the REST API.  However, only `INSERT` and `APPEND` are officially supported.
            See https://prd-docs.conduce.com/#/data/createTransaction for a list of endpoints.
        **process**
            Post the transaction and immediately process on backends configured to automatically process transactions.
        **debug**
            Post each entity in the entity set as an individual transaction.
            This enables a user to find bad entities in an entity set but dramatically slows data processing.
            Forces `process=True` to ensure entities are ingested one at a time.

        See :py:func:`make_post_request` for more kwargs.

    Returns
    -------
    requests.Response
        Returns an error or the final response message when the job is no longer running.
    """
    if 'entities' not in entity_set:
        raise ValueError("Parameter entity_set is not an 'entities' dict.")

    if kwargs.get('debug'):
        kwargs['debug'] = False
        kwargs['process'] = True
        print("Debug ingest")
        responses = []
        for idx, entity in enumerate(entity_set['entities'], start=1):
            single_entity = {'entities': [entity]}
            print(single_entity)
            responses.append(post_transaction(dataset_id, single_entity, **kwargs))
            print("{} / {} ingested".format(idx, len(entity_set['entities'])))
        return responses

    payload = {
        'data': entity_set,
        'op': kwargs.get('operation', 'INSERT'),
    }
    response = make_post_request(
        payload, '/api/v2/data/{}/transactions?process={}'.format(dataset_id, bool(kwargs.get('process', False))), **kwargs)
    response.raise_for_status()

    if kwargs.get('process', False):
        if response.status_code == 202:
            if 'location' in response.headers:
                job_id = response.headers['location']
                response = wait_for_job(job_id, **kwargs)

    return response


def get_transactions(dataset_id, **kwargs):
    """
    Read sequence of dataset transactions from transaction log.  If no query parameters are provided,
    the most recent transaction will be queried.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    **kwargs : key-value
        **min**
            The index of the oldest transaction in the sequence.
        **max**
            The index of the newest transaction in the sequence.
        **value**
            The index of a single transaction to query.
        **rows**
            The number of transactions to return.
        **page_state**
            The page state from which to continue.
        **count**
            Return only number of transactions in the log (ignores all other parameters)

        See :py:func:`make_get_request` for more kwargs.
        See https://prd-docs.conduce.com/#/data/readTransactions for more complete parameter documentation.

    Returns
    -------
    requests.Response
        Returns a response, the content of which is a list of transactions.
    """

    fragment = '/api/v2/data/{}/transactions'.format(dataset_id)

    parameters = {
        'min': kwargs.get('min', -1),
        'max': kwargs.get('max'),
        'value': kwargs.get('value'),
        'rows': kwargs.get('rows'),
        'page_state': kwargs.get('page_state', ''),
        'count': bool(kwargs.get('count', False)),
    }

    # HACK: get around bool parameter bug
    if not kwargs.get('count'):
        parameters.pop('count')

    return make_get_request(fragment, parameters=parameters, **kwargs)


def delete_transactions(dataset_id, **kwargs):
    """
    Clear all dataset transactions from Conduce.
    Delete and re-create dataset backends.

    Return the dataset and all backends to an intialized (empty) state.
    Dataset is ready for ingest when request is finished.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    **kwargs : key-value
        See :py:func:`make_delete_request` for more kwargs.

    Returns
    -------
    requests.Response
         On success, an asynchronous job ID.  Check the job status for deletion progress.
         (See :py:func:`wait_for_job`)
    """

    fragment = '/api/v2/data/{}/transactions'.format(dataset_id)
    return make_delete_request(fragment, **kwargs)


def search_dataset_backend(dataset_id, backend_id, query, **kwargs):
    """
    Retrieves data from the dataset matching the query provided.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    query: dictionary
        Query parameters.
    **kwargs : key-value
        See :py:func:`make_delete_request` for more kwargs.

    Returns
    -------
    list
        A list of entities matching the specified query
    """
    response = make_post_request(query, '/api/v2/data/{}/backends/{}/searches'.format(dataset_id, backend_id), **kwargs)
    return json.loads(response.content)


def remove_dataset_backend(dataset_id, backend_id, **kwargs):
    """
    Remove all data from the backend, remove the backend from the dataset.  Delete the backend.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    **kwargs : key-value
        See :py:func:`make_delete_request` for more kwargs.
    """
    return make_delete_request('/api/v2/data/{}/backends/{}'.format(dataset_id, backend_id), **kwargs)


def get_dataset_backend_metadata(dataset_id, backend_id, **kwargs):
    """
    Retrieves dataset backend metadata.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    **kwargs : key-value
        See :py:func:`make_get_request` for more kwargs.
    """
    return make_get_request('/api/v2/data/{}/backends/{}'.format(dataset_id, backend_id), **kwargs)


def list_dataset_backends(dataset_id, **kwargs):
    """
    Retrieves the list of backend UUIDs associated with the specified dataset.

    If no backends are found, the list is empty.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    **kwargs : key-value
        See :py:func:`make_get_request` for more kwargs.
    """
    return make_get_request('/api/v2/data/{}/backends'.format(dataset_id), **kwargs)


def set_default_backend(dataset_id, backend_id, **kwargs):
    """
    Make the specified backend the default for the specified dataset.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    **kwargs : key-value
        See :py:func:`make_patch_request` for more kwargs.

    Returns
    -------
    requests.Response
         On success, an asynchronous job ID.  Check the job status for progress.
         (See :py:func:`wait_for_job`)
    """

    fragment = '/api/v2/data/{}/backends/{}'.format(dataset_id, backend_id)
    return make_patch_request({}, fragment, parameters={'default': 1}, **kwargs)


def process_transactions(dataset_id, backend_id, **kwargs):
    """
    Process transactions on a dataset backend

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    **kwargs : key-value
        **all**
            Process all outstanding transactions to the specified backend
        **transaction**
            Process a specific transaction to the specified backend
        **min**
            The oldest transaction in the sequence to be processed to the backend
        **max**
            The newest transaction in the sequence to be processed to the backend
        **default**
            Make this backend the default backend. Set to any value, all other parameters are ignored.
        See :py:func:`make_patch_request` for more kwargs.

    Returns
    -------
    requests.Response
         On success, an asynchronous job ID.  Check the job status for progress.
         (See :py:func:`wait_for_job`)
    """

    fragment = '/api/v2/data/{}/backends/{}'.format(dataset_id, backend_id)
    parameters = {
        'all': bool(kwargs.get('all')),
        'tx': kwargs.get('transaction'),
        'min': kwargs.get('min'),
        'max': kwargs.get('max'),
        'default': kwargs.get('default'),
    }

    # HACK: Remove when boolean parameters are supported
    if not kwargs.get('all'):
        parameters.pop('all')

    return make_patch_request({}, fragment, parameters=parameters, **kwargs)


def enable_auto_processing(dataset_id, backend_id, enable=True, **kwargs):
    """
    Configure a dataset backend to automatically process new transactions

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    **kwargs : key-value
        **enable**
            When True (default) enables auto processing.  Set to False to disable, or call :py:func:`disable_auto_processing`.
        See :py:func:`make_patch_request` for more kwargs.
    """

    fragment = '/api/v2/data/{}/backends/{}'.format(dataset_id, backend_id)
    payload = [
        {
            "path": "/auto_process",
            "value": enable,
            "op": "add"
        }
    ]
    return make_patch_request(payload, fragment, **kwargs)


def disable_auto_processing(dataset_id, backend_id, **kwargs):
    """
    Configure a dataset backend to ignore new transactions

    Transactions can be triggered to process to the backend manually using :py:func:`process_transactions`.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to which the backend belongs.
    backend_id : string
        The UUID that identifies the dataset backend to update.
    **kwargs : key-value
        See :py:func:`make_patch_request` for kwargs.
    """
    return enable_auto_processing(dataset_id, backend_id, False, **kwargs)


def add_simple_store(dataset_id, auto_process, **kwargs):
    """
    Adds a simple store to the specified dataset.

    If configured for auto-processing (default), transactions will not be auto-processed
    into the store until new transactions are posted.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    auto_process : boolean
        Configure the backend to auto process transactions. Auto processing is enabled by default.
        Set to False to disable auto processing.
    **kwargs : key-value
        See :py:func:`make_post_request` for more kwargs.
    """
    return _create_dataset_backend(dataset_id, DatasetBackends.simple, auto_process, None, **kwargs)


def add_tile_store(dataset_id, auto_process, **kwargs):
    """
    Adds a tile store to the specified dataset.

    If configured for auto-processing (default), transactions will not be auto-processed
    into the store until new transactions are posted.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    auto_process : boolean
        Configure the backend to auto process transactions. Auto processing is enabled by default.
        Set to False to disable auto processing.
    **kwargs : key-value
        See :py:func:`make_post_request` for more kwargs.
    """
    return _create_dataset_backend(dataset_id, DatasetBackends.tile, auto_process, None, **kwargs)


def add_capped_tile_store(dataset_id, auto_process, min_temporal_zoom_level, min_spatial_zoom_level, **kwargs):
    """
    Adds a capped tile store to the specified dataset.

    If configured for auto-processing (default), transactions will not be auto-processed
    into the store until new transactions are posted.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    auto_process : boolean
        Configure the backend to auto process transactions. Auto processing is enabled by default.
        Set to False to disable auto processing.
    min_temporal_zoom_level : integer
        The lowest resolution temporal zoom level at which data will be tiled.
    min_spatial_zoom_level : integer
        The highest resolution temporal zoom level at which data will be tiled.
    **kwargs : key-value
        See :py:func:`make_post_request` for more kwargs.
    """
    config = {
        'minimum_temporal_level': min_temporal_zoom_level,
        'minimum_spatial_level': min_spatial_zoom_level,
    }
    return _create_dataset_backend(dataset_id, DatasetBackends.capped_tile, auto_process, config, **kwargs)


def add_elasticsearch_store(dataset_id, auto_process, **kwargs):
    """
    Adds an Elasticsearch store to the specified dataset.

    If configured for auto-processing (default), transactions will not be auto-processed
    into the store until new transactions are posted.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    auto_process : boolean
        Configure the backend to auto process transactions. Auto processing is enabled by default.
        Set to False to disable auto processing.
    **kwargs : key-value
        See :py:func:`make_post_request` for more kwargs.
    """
    return _create_dataset_backend(dataset_id, DatasetBackends.elasticsearch, auto_process, None, **kwargs)


def add_histogram_store(dataset_id, auto_process, **kwargs):
    """
    Adds a histogram store to the specified dataset.

    If configured for auto-processing (default), transactions will not be auto-processed
    into the store until new transactions are posted.

    Parameters
    ----------
    dataset_id : string
        The UUID that identifies the dataset to modify.
    auto_process : boolean
        Configure the backend to auto process transactions. Auto processing is enabled by default.
        Set to False to disable auto processing.
    **kwargs : key-value
        See :py:func:`make_post_request` for more kwargs.
    """
    return _create_dataset_backend(dataset_id, DatasetBackends.histogram, auto_process, None, **kwargs)


def _create_dataset_backend(dataset_id, backend_type, auto_process, config, **kwargs):
    """
    Transactions will not be auto-processed into the store until new transactions are posted.
    """
    if backend_type not in DatasetBackends.BACKEND_TYPES.values():
        raise ValueError("The backend type specified is not valid.", backend_type)

    if config is None:
        config = {}

    config.update({
        'backend_type': backend_type,
        'auto_process': auto_process
    })

    return make_post_request(config, '/api/v2/data/{}/backends'.format(dataset_id), **kwargs)


def _ingest_entity_set(dataset_id, entity_set, **kwargs):
    if 'entities' not in entity_set:
        raise ValueError('parameter entity_set is not an \'entities\' dict')

    if kwargs.get('debug'):
        kwargs['debug'] = False
        print("Debug ingest")
        responses = []
        for idx, entity in enumerate(entity_set['entities'], start=1):
            single_entity = {'entities': [entity]}
            print(single_entity)
            responses.append(_ingest_entity_set(dataset_id, single_entity, **kwargs))
            print("{} / {} ingested".format(idx, len(entity_set['entities'])))
        return responses

    response = make_post_request(
        entity_set, 'datasets/add-data/{}'.format(dataset_id), **kwargs)
    if 'location' in response.headers:
        job_id = response.headers['location']
        response = wait_for_job(job_id, **kwargs)

    return response


def _clear_dataset(dataset_id, **kwargs):
    response = make_post_request(
        None, 'datasets/clear/{}'.format(dataset_id), **kwargs)

    return response


def clear_dataset(**kwargs):
    return_message = None

    kwargs['id'] = kwargs.get('id')
    kwargs['regex'] = kwargs.get('regex')
    kwargs['name'] = kwargs.get('name')
    kwargs['all'] = kwargs.get('all')

    responses = []
    if kwargs['id']:
        responses.append(_clear_dataset(kwargs['id'], **kwargs))
        return_message = 'cleared 1 dataset'
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "":
        datasets = list_datasets(**kwargs)
        to_clear = []
        for dataset in datasets:
            if dataset.get('name') is not None and (dataset['name'] == kwargs['name'] or (kwargs['regex'] and re.match(kwargs['regex'], dataset['name']))):
                to_clear.append(dataset)
        if len(to_clear) == 1:
            responses.append(_clear_dataset(to_clear[0]['id'], **kwargs))
            return_message = 'cleared 1 dataset'
        elif kwargs['all']:
            for dataset in to_clear:
                responses.append(_clear_dataset(dataset['id'], **kwargs))
            return_message = "cleared {:d} datasets".format(len(to_clear))
        elif len(to_clear) > 1:
            return_message = "Matching datasets:\n"
            return_message += json.dumps(to_clear)
            return_message += "\n\nName or regular expression matched multiple datasets.  Pass --all to clear all matching datasets."
        else:
            return_message = "No matching datasets found."

    for response in responses:
        if 'location' in response.headers:
            job_id = response.headers['location']
            response = wait_for_job(job_id, **kwargs)

    return return_message


def modify_entity(dataset_id, entity, **kwargs):
    entity['modify'] = True
    return _modify_data(dataset_id, {'entities': [entity]}, **kwargs)


def modify_entities(dataset_id, entities, **kwargs):
    for entity in entities:
        entity['modify'] = True
    return _modify_data(dataset_id, {'entities': entities}, **kwargs)


def _modify_data(dataset_id, entity_set, **kwargs):
    response = make_post_request(
        entity_set, 'datasets/modify-data/{}'.format(dataset_id), **kwargs)
    if 'location' in response.headers:
        job_id = response.headers['location']
        response = wait_for_job(job_id, **kwargs)

    return response


"""
TODO: Use this to clean up the long if statements, but needs to be tested against original logic
def _found_id(resource_obj, kwargs):
    return (resource_obj.get('id') is not None and (resource_obj['id'] == kwargs['id']))


def _found_name(resource_obj, kwargs):
    return ((resource_obj.get('name') is not None) and
            (resource_obj['name'] == kwargs['name']))


def _found_no_name(resource_obj, kwargs):
    return ((resource_obj.get('name') is None) and kwargs.get('no_name', False) is True)


def _regex_matches_name(resource_obj, kwargs):
    return (resource_obj.get('name') is not None and kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name']))


def _complicated_condition_part_1(resource_obj, kwargs):
    return (_found_id(resource_obj, kwargs) or _found_no_name(resource_obj, kwargs))


def _complicated_condition_part_2(resource_obj, kwargs):
    return (_found_name(resource_obj, kwargs) or
            _regex_matches_name(resource_obj, kwargs))


def _complicated_condition(resource_obj, kwargs):
    return _complicated_condition_part_1(resource_obj, kwargs) or _complicated_condition_part_2(resource_obj, kwargs)
"""


def find_resource(**kwargs):
    """
    Get resources that match a search query.

    Sends an HTTP POST to fetch a list of resources that match the given search query.  If no search query parameters are passed, all resources are returned.

    Parameters
    ----------

    **kwargs : key-value
        Target host and user authorization parameters used to make the request.

        id : string
            The ID of the resource to fetch.  If this parameter is passed, at most, one resource will be returned.
        type : string
            Resource type to fetch.  One of: SUBSTRATE, DATASET, ASSET, LENS_TEMPLATE, ORCHESTRATION.
            If this parameter is set, only resources of the specified type will be returned.
        name : string
            Resource name to fetch.  Resource names are not unique.  Multiple resources may be returned.
        regex : string
            Regular expression for filtering search results.  The result names are filtered by the regular expression before being returned.
        mime : string
            Mime type of resources to fetch.  Finds all resources of the specified mime type.
        tags : string
            Finds all resources that contain the specified tags.  Resources are only returned if they contain all specified tags.
        host : string
            The Conduce server's hostname (ex. app.conduce.com)
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce config or, if not
            found, authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    list
        A list of resources matching the search query.  Each resource is a dictionary matching the following format::

            {
               "name": "US Cities",
               "tags": [],
               "create_time": 1506544998452,
               "version": 0,
               "mime": "application/json",
               "modify_time": 1508869186664,
               "revision": 4,
               "type": "DATASET",
               "id": "a262342b-22d2-4368-4698-cf75b62b7cb3",
               "size": 2
             }


    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure.
        See :py:func:`requests.Response.raise_for_status` for more information.

    """
    search_uri = 'conduce/api/v2/resources/searches'

    if kwargs.get('content') is not None:
        search_uri += '?content={}'.format(kwargs.get('content'))

    payload = {}
    if kwargs.get('type') is not None:
        payload.update({'type': kwargs.get('type')})
    if kwargs.get('name') is not None:
        payload.update({'name': kwargs.get('name')})
    if kwargs.get('mime') is not None:
        payload.update({'mime': kwargs.get('mime')})
    if kwargs.get('tags') is not None:
        payload.update({'tags': kwargs.get('tags')})

    kwargs['id'] = kwargs.get('id')
    kwargs['regex'] = kwargs.get('regex')
    kwargs['name'] = kwargs.get('name')

    results = json.loads(make_post_request(payload, search_uri, **kwargs).content)

    if kwargs.get('content') == 'id':
        return results['resource_ids']

    found = []
    if 'resources' in results:
        if kwargs['name'] is None and kwargs['regex'] is None and kwargs['id'] is None and kwargs.get('no_name', False) is False:
            return results['resources']
        else:
            for resource_obj in results['resources']:
                if ((resource_obj.get('id') is not None and resource_obj['id'] == kwargs['id']) or
                    (resource_obj.get('name') is None and kwargs.get('no_name', False) is True) or
                        (resource_obj.get('name') is not None and
                            (resource_obj['name'] == kwargs['name'] or
                                (kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name']))))):
                    found.append(resource_obj)

    return found


def _remove_resource(resource_id, **kwargs):
    return make_delete_request('conduce/api/v2/resources/{}?permanent={}'.format(resource_id, kwargs.get('permanent', False)), **kwargs)


def remove_resource(**kwargs):
    return_message = None

    resource_type = kwargs.get('type')
    if resource_type is None:
        resource_type = "resources"

    kwargs['id'] = kwargs.get('id')
    kwargs['regex'] = kwargs.get('regex')
    kwargs['name'] = kwargs.get('name')
    kwargs['all'] = kwargs.get('all')

    if kwargs['id']:
        return_message = _remove_resource(kwargs['id'], **kwargs)
    elif kwargs['name'] or kwargs['regex'] or kwargs['name'] == "" or kwargs.get('no_name') or kwargs.get('tags'):
        results = find_resource(**kwargs)
        to_remove = []
        for resource_obj in results:
            if (resource_obj.get('name') is not None and
                    (resource_obj['name'] == kwargs['name']) or
                    (resource_obj.get('name') is None and kwargs.get('no_name', False) is True) or
                    (kwargs['regex'] and re.match(kwargs['regex'], resource_obj['name'])) or
                    (kwargs.get('tags') is not None and set(kwargs.get('tags')) < set(resource_obj['tags']))):
                to_remove.append(resource_obj)
        if len(to_remove) == 1:
            _remove_resource(to_remove[0]['id'], **kwargs)
            return_message = 'Removed 1 {}'.format(resource_type)
        elif kwargs['all']:
            for resource_obj in to_remove:
                _remove_resource(resource_obj.get('id'), **kwargs)
            return_message = "Removed {:d} {}".format(
                len(to_remove), resource_type)
        elif len(to_remove) > 1:
            return_message = "Matching {}:\n".format(resource_type)
            return_message += json.dumps(to_remove)
            return_message += "\n\nName or regular expression matched {} {}.  Pass --all to remove all matching {}.".format(
                len(to_remove), resource_type, resource_type)
        else:
            return_message = "No matching {} found.".format(resource_type)
    else:
        return_message = "The query did not match any {}.".format(resource_type)

    return return_message


def remove_substrate(**kwargs):
    return remove_resource(type='SUBSTRATE', **kwargs)


def remove_dataset(**kwargs):
    return remove_resource(type='DATASET', **kwargs)


def remove_template(**kwargs):
    return remove_resource(type='LENS_TEMPLATE', **kwargs)


def remove_asset(**kwargs):
    return remove_resource(type='ASSET', **kwargs)


def remove_orchestration(**kwargs):
    return remove_resource(type='ORCHESTRATION', **kwargs)


def create_substrate(name, substrate_def, **kwargs):
    return create_json_resource('SUBSTRATE', name, substrate_def, **kwargs)


def find_orchestration(**kwargs):
    """
    Find orchestrations matching the given parameters.

    A convenience method that calls :py:func:`find_resource` with the ``type`` argument set to "ORCHESTRATION."

    See :py:func:`find_resource` for more information on the other query parameters.
    """
    return find_resource(type='ORCHESTRATION', **kwargs)


def find_asset(**kwargs):
    """
    Find assets matching the given parameters.

    A convenience method that calls :py:func:`find_resource` with the ``type`` argument set to "ASSET."

    See :py:func:`find_resource` for more information on the other query parameters.
    """
    return find_resource(type='ASSET', **kwargs)


def find_substrate(**kwargs):
    """
    Find substrates matching the given parameters.

    A convenience method that calls :py:func:`find_resource` with the ``type`` argument set to "SUBSTRATE."

    See :py:func:`find_resource` for more information on the other query parameters.
    """
    return find_resource(type='SUBSTRATE', **kwargs)


def find_template(**kwargs):
    """
    Find lens templates matching the given parameters.

    A convenience method that calls :py:func:`find_resource` with the ``type`` argument set to "LENS_TEMPLATE."

    See :py:func:`find_resource` for more information on the other query parameters.
    """
    return find_resource(type='LENS_TEMPLATE', **kwargs)


def find_dataset(**kwargs):
    """
    Find datasets matching the given parameters.

    A convenience method that calls :py:func:`find_resource` with the ``type`` argument set to "DATASET."

    See :py:func:`find_resource` for more information on the other query parameters.
    """
    return find_resource(type='DATASET', **kwargs)


def create_template(name, template_def, **kwargs):
    return create_json_resource('LENS_TEMPLATE', name, template_def, **kwargs)


def get_resource(resource_id, **kwargs):
    fragment = 'conduce/api/v2/resources/{}'.format(resource_id)
    if kwargs.get('raw', False):
        fragment += '?content=raw'

    response = make_get_request(fragment, **kwargs).content
    if not kwargs.get('raw', False):
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
    except Exception:
        pass

    return False


def create_resource(resource_type, resource_name, content, mime_type, **kwargs):
    """
    Create a resource.

    Send a POST request to Conduce to create a new resource.  Resources, like datasets, lenses and assets are the objects used to build Conduce visualizations

    Parameters
    ----------
    resource_type : string
        The type of Conduce resource being created.  Valid JSON resources are: ASSET, DATASET, LENS_TEMPLATE, SUBSTRATE, and ORCHESTRATION.
    resource_name : string
        A string that helps identify the resource
    content : string
        A string representation of the resource.  JSON resources should be passed as a JSON encoded string.
        For text and JSON mime types, the string is passed directly as the resource content.  For other types
        the content string is base64 encoded.
    mime : string
        The mime type of the resource content.
    kwargs : key-value
        **tags**
            A list of strings that help identify the resource.

        See :py:func:`make_post_request` for more information

    Returns
    -------
    dictionary
       Metadata describing the new resource.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:func:`requests.Response.raise_for_status` for more information.
    """
    if not (mime_type.startswith('text/') or mime_type == 'application/json'):
        if not is_base64_encoded(content):
            print("base64 encoding content for {}".format(resource_name))
            content = base64.b64encode(content)
        try:
            content = content.decode('utf-8')
        except Exception:
            pass

    resource_def = {
        'name': resource_name,
        'tags': kwargs.get('tags'),
        'version': kwargs.get('version'),
        'type': resource_type,
        'mime': mime_type,
        'content': content
    }

    return json.loads(make_post_request(resource_def, 'conduce/api/v2/resources', **kwargs).content)


def create_json_resource(resource_type, resource_name, content, **kwargs):
    """
    Create a JSON resource.

    A convenience method for creating JSON resources.  Calls :py:func:`create_resource` with ``mime_type`` set to ``"application/json"``.

    Parameters
    ----------
    resource_type : string
        The type of Conduce resource being created.  Valid JSON resources are: DATASET, LENS_TEMPLATE, SUBSTRATE, and ORCHESTRATION.
    resource_name : string
        A string that helps identify the resource
    content : dictionary
        A dictionary representation of the JSON blob that describes the resource content.  The dictionary
        is converted to a JSON encoded string prior to resource creation.
    kwargs : key-value
        **tags**
            A list of strings that help identify the resource.

        See :py:func:`make_post_request` for more information

    Returns
    -------
    dictionary
       Metadata describing the new resource.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:func:`requests.Response.raise_for_status` for more information.
    """

    return create_resource(
        resource_type,
        resource_name,
        json.dumps(content),
        'application/json',
        **kwargs)


def create_orchestration(name, orchestration_def, **kwargs):
    return create_json_resource('ORCHESTRATION', name, orchestration_def, **kwargs)


def list_api_keys(**kwargs):
    """
    Get this user's API keys.

    Send an HTTP GET request to list this user's API keys.

    Parameters
    ----------
    **kwargs
        See :py:func:`make_get_request`

    Returns
    -------
    requests.Response
        Returns a list of API key dictionaries.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.
    """

    response = make_get_request('apikeys/list', **kwargs)
    return json.loads(response.content)


def create_api_key(**kwargs):
    """
    Add an API key to this user's account.

    Send an HTTP POST request for a new API key.  The API key is added to the account of the user who made the request.

    Parameters
    ----------
    **kwargs
        See :py:func:`make_post_request`

    Returns
    -------
    requests.Response
        Returns the string representation of the new API key.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.
    """
    response = make_post_request(
        {"description": "Generated and used by conduce-python-api"}, 'apikeys/create', **kwargs)
    return json.loads(response.content)['apikey']


def remove_api_key(key, **kwargs):
    """
    Permanently remove an API key from this user's account.

    Send an HTTP POST request to delete the specified API key.  The key may no longer be used for authenticating requests and cannot be restored.

    Parameters
    ----------
    key
        The string representation of the API key to delete
    **kwargs
        See :py:func:`make_post_request`

    Returns
    -------
    Nothing

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure.
        See :py:meth:`requests.Response.raise_for_status` for more information.
    """
    response = make_post_request(
        {"apikey": key}, 'apikeys/delete', **kwargs)
    response.raise_for_status()


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
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce configuration or,
            if not found, authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.

    """
    return _make_request(requests.delete, None, compose_uri(fragment), **kwargs)


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

        parameters : dictionary
            Key/value pairs used to compose an HTTP query string.
        host : string
            The Conduce server's hostname (ex. app.conduce.com)
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce config or, if not found,
            authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure.
        See :py:meth:`requests.Response.raise_for_status` for more information.

    """
    return _make_request(requests.get, None, compose_uri(fragment), **kwargs)


def make_post_request(payload, fragment, **kwargs):
    """
    Send an HTTP POST request to a Conduce server.

    Sends an HTTP POST request for the specified endpoint to a Conduce server.  POST requests are used to create conduce resources.

    Parameters
    ----------
    payload : dictionary
        # more-complicated-post-requests>`_ for more information.
        A dictionary representation of JSON content used to replace the Conduce resource.  See the
        `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/

    fragment : string
        The URI fragment of the requested endpoint. See https://app.conduce.com/docs for a list of endpoints.

    **kwargs : key-value
        Target host and user authorization parameters used to make the request.

        host : string
            The Conduce server's hostname (ex. app.conduce.com)
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce config or, if not found,
            authenticate via password.  Ignored if `api_key` is provided.
    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.

    """
    return _make_request(requests.post, payload, compose_uri(fragment), **kwargs)


def make_put_request(payload, fragment, **kwargs):
    """
    Send an HTTP PUT request to a Conduce server.

    Sends an HTTP PUT request for the specified endpoint to a Conduce server.  PUT requests are used to replace/update Conduce resources.

    Parameters
    ----------
    payload : dictionary
        # more-complicated-post-requests>`_ for more information.
        A dictionary representation of JSON content used to replace the Conduce resource.  See the
        `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/

    fragment : string
        The URI fragment of the requested endpoint. See https://app.conduce.com/docs for a list of endpoints.

    **kwargs : key-value
        Target host and user authorization parameters used to make the request.

        host : string
            The Conduce server's hostname (ex. app.conduce.com)
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce config or, if not found,
            authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.

    """
    return _make_request(requests.put, payload, compose_uri(fragment), **kwargs)


def make_patch_request(payload, fragment, **kwargs):
    """
    Send an HTTP PATCH request to a Conduce server.

    Sends an HTTP PATCH request for the specified endpoint to a Conduce server.  PATCH requests are used to modify Conduce resources.

    Parameters
    ----------
    payload : dictionary
        # more-complicated-post-requests>`_ for more information.
        A dictionary representation of JSON content used to replace the Conduce resource.  See the
        `requests library documentation <http://docs.python-requests.org/en/master/user/quickstart/

    fragment : string
        The URI fragment of the requested endpoint. See https://app.conduce.com/docs for a list of endpoints.

    **kwargs : key-value
        Target host and user authorization parameters used to make the request.

        host : string
            The Conduce server's hostname (ex. app.conduce.com)
        api_key : string
            The user's API key (UUID).  The user should provide `api_key` or `user` but not both.  If the user provides both, `api_key` takes precedent.
        user : string
            The user's email address.  Used to look up an API key from the Conduce configuration or,
            if not found, authenticate via password.  Ignored if `api_key` is provided.

    Returns
    -------
    requests.Response
        The HTTP response from the server.

    Raises
    ------
    requests.HTTPError
        Requests that result in an error raise an exception with information about the failure. See
        :py:meth:`requests.Response.raise_for_status` for more information.

    """
    return _make_request(requests.patch, payload, compose_uri(fragment), **kwargs)


@retry(retry_on_exception=_retry_on_retryable_error, wait_exponential_multiplier=WAIT_EXPONENTIAL_MULTIPLIER, stop_max_attempt_number=NUM_RETRIES)
def _make_request(request_func, payload, uri, **kwargs):
    USER_CONFIG = {}

    def cfg(USER_CONFIG, key):
        if USER_CONFIG == {}:
            USER_CONFIG.update(config.get_full_config())
        return USER_CONFIG[key]

    if 'host' in kwargs and kwargs['host']:
        host = kwargs['host']
    else:
        host = cfg(USER_CONFIG, 'default-host')

    if 'password' in kwargs and kwargs['password']:
        password = kwargs['password']
    else:
        password = None

    if 'no_verify' in kwargs and kwargs['no_verify']:
        verify = False
    else:
        verify = True

    if 'api_key' in kwargs and kwargs['api_key']:
        auth = session.api_key_header(kwargs['api_key'])
    else:
        if 'user' in kwargs and kwargs['user']:
            user = kwargs['user']
        else:
            user = cfg(USER_CONFIG, 'default-user')
        auth = session.get_session(host, user, password, verify)

    headers = {}
    url = 'https://{}/{}'.format(host, uri)
    if 'Authorization' in auth:
        if 'headers' in kwargs and kwargs['headers']:
            headers = kwargs['headers']
            headers.update(auth)
        else:
            headers = auth

        response = request_func(url, json=payload, headers=headers, verify=verify, params=kwargs.get('parameters'))
    else:
        response = request_func(url, json=payload, cookies=auth, headers=headers, verify=verify, params=kwargs.get('parameters'))

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
        print("JSON encoding content for {}".format(resource_id))
        content = json.dumps(content)
    elif not (mime_type.startswith('text/') or mime_type == 'application/json'):
        if not is_base64_encoded(content):
            print("base64 encoding content for {}".format(resource_id))
            content = base64.b64encode(content)

    return _modify_resource_content(resource_id, content, mime_type, **kwargs)


def _modify_resource_content(resource_id, content, mime_type, **kwargs):
    resource = get_resource(resource_id, **kwargs)
    resource['content'] = content
    resource['mime'] = mime_type
    update_resource(resource, **kwargs)


def set_tags(resource_id, tags, **kwargs):
    resource = get_resource(resource_id, **kwargs)
    resource['tags'] = tags
    update_resource(resource, **kwargs)


def add_tags(resource_id, tags, **kwargs):
    resource = get_resource(resource_id, **kwargs)
    resource['tags'] += tags
    update_resource(resource, **kwargs)


def remove_tags(resource_id, tags, **kwargs):
    resource = get_resource(resource_id, **kwargs)
    resource['tags'] = [tag for tag in resource['tags'] if tag not in tags]
    update_resource(resource, **kwargs)


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
