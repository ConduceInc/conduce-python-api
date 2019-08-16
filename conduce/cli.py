from __future__ import print_function
from __future__ import absolute_import
from builtins import str
import requests
import json
import base64
import tempfile
import os
import sys
from subprocess import call
import mimetypes

from . import config
from . import api
from . import util
from . import asset
from . import ingest


def isstr(arg):
    return isinstance(arg, ("".__class__, u"".__class__))


def print_response(response):
    responseStr = response
    try:
        if isinstance(response, bytes):
            responseStr = response.decode()
    except Exception:
        pass
    # if isinstance(response, str):
    if isstr(responseStr):
        try:
            print(json.dumps(json.loads(responseStr), indent=2))
        except Exception:
            print(responseStr)
    else:
        try:
            print(json.dumps(responseStr, indent=2))
        except Exception:
            print(responseStr)


def list_from_args(args):
    object_to_list = args.object_to_list
    del vars(args)['object_to_list']

    if object_to_list.lower() == "lenses" or object_to_list.lower() == "templates":
        object_to_list = "LENS_TEMPLATE"

    return api.list_resources(object_to_list.upper().rstrip('S'), **vars(args))


def create_resource(args):
    resource_type = args.type.upper()
    resource_name = args.name
    content_path = args.content

    del vars(args)['name']
    del vars(args)['type']
    del vars(args)['content']

    with open(content_path, 'rb') as content_stream:
        if resource_type.lower() == 'asset':
            mime_type = mimetypes.guess_type(content_path)[0]
        else:
            mime_type = 'application/json'
        content = content_stream.read()

        return api.create_resource(resource_type, resource_name, content, mime_type, **vars(args))


def copy_resource(args):
    if args.type is not None:
        resource_type = args.type

        if resource_type.lower() == "lenses" or resource_type.lower() == "templates":
            resource_type = "LENS_TEMPLATE"

        args.type = resource_type.upper().rstrip('S')

    resources = api.find_resource(content='full', **vars(args))

    if len(resources) > 1:
        print("Found multiple resources:")
        print(json.dumps(resources, indent=2))
        print("Please select a single resource and try again.")
        return

    if len(resources) == 0:
        print("Resource not found, please update your query and try again.")

    resource_name = args.resource_name
    del vars(args)['resource_name']
    del vars(args)['name']
    del vars(args)['type']
    del vars(args)['id']
    del vars(args)['regex']

    resource_type = resources[0]['type']
    content = resources[0]['content']
    mime_type = resources[0]['mime']

    return api.create_resource(resource_type, resource_name, content, mime_type, **vars(args))


def get_dataset_metadata(args):
    if args.id is not None:
        metadata = api.get_dataset_metadata(args.id, **vars(args))
        return [metadata]
    else:
        datasets = api.find_dataset(**vars(args))

        metadatas = []
        for dataset in datasets:
            metadata = api.get_dataset_metadata(dataset['id'], **vars(args))
            metadatas.append(metadata)
        return metadatas


def format_resource_type(resource_type):
    if resource_type.lower() == "lenses" or resource_type.lower() == "templates":
        resource_type = "LENS_TEMPLATE"

    return resource_type.upper().rstrip('S')


def find_resource(args):
    if args.type is not None:
        args.type = format_resource_type(args.type)

    resources = api.find_resource(**vars(args))
    if args.decode:
        if args.content == 'full':
            for resource in resources:
                if resource.get('mime', 'invalid-mime') == 'application/json':
                    if 'content' in resource:
                        try:
                            resource['content'] = json.loads(resource['content'])
                        except Exception:
                            print('Could not decode content for {}'.format(resource['id']))
                elif not resource.get('mime', 'invalid-mime').startswith('text/'):
                    resource['content'] = base64.b64decode(resource['content'])

    if args.one_line:
        return list(map((lambda x: "{}: {}".format(x.get('name', ''), x.get('id'))), resources))

    return resources


def rename_resource(args):
    if args.type is not None:
        args.type = format_resource_type(args.type)

    resources = api.find_resource(**vars(args))
    if len(resources) == 0:
        print('No resource found')
        return
    if len(resources) != 1:
        print('Resources must be renamed one-at-a-time')
        return

    api.make_patch_request([{"path": "/name", "value": args.new_name, "op": "add"}],
                           '/api/v2/resources/{}'.format(resources[0]['id']), host=args.host, user=args.user, api_key=args.api_key)

    if args.verbose:
        return api.find_resource(id=resources[0]['id'], host=args.host, user=args.user, api_key=args.api_key)
    else:
        return


def open_in_editor(content):
    EDITOR = os.environ.get('EDITOR', 'vim')
    with tempfile.NamedTemporaryFile(suffix='.tmp') as resource_file:
        resource_file.write(str(content))
        resource_file.flush()
        call([EDITOR, resource_file.name])

        with open(resource_file.name, 'r') as edited_resource_file:
            return edited_resource_file.read()


def edit_resource(args):
    if args.type is not None:
        resource_type = args.type

        if resource_type.lower() == "lenses" or resource_type.lower() == "templates":
            resource_type = "LENS_TEMPLATE"

        args.type = resource_type.upper().rstrip('S')

    if args.file:
        mime_type = mimetypes.guess_type(args.file)[0]
        resources = api.find_resource(**vars(args))
        for resource in resources:
            if resource.get('mime', 'invalid-mime') != mime_type:
                resources.remove(resource)
        if len(resources) == 1:
            with open(args.file, 'r') as edited_resource_file:
                edited_resource_content = edited_resource_file.read()
                print("Updating resource")
                resource['content'] = json.dumps(json.loads(edited_resource_content))
                api.update_resource(resource, **vars(args))
        elif len(resources) > 1:
            print("Multiple resources found, please specify a single resource")
            print(resources)
            print("Aborting...")
            return
        else:
            print("No text editable resources found")
            return

    else:
        args.content = 'full'
        resources = api.find_resource(**vars(args))
        for resource in resources:
            if resource.get('mime', 'invalid-mime') == 'application/json':
                resource['content'] = json.dumps(json.loads(resource['content']), indent=2)
            elif not resource.get('mime', 'invalid-mime').startswith('text/'):
                resources.remove(resource)

        if len(resources) == 0:
            print("No text editable resources found")
            return

        for resource in resources:
            EDITOR = os.environ.get('EDITOR', 'vim')
            with tempfile.NamedTemporaryFile(suffix='.tmp', mode='wt') as resource_file:
                resource_file.write(str(resource['content']))
                resource_file.flush()
                call([EDITOR, resource_file.name])

                with open(resource_file.name, 'r') as edited_resource_file:
                    edited_resource_content = edited_resource_file.read()

                    if edited_resource_content != str(resource['content']):
                        print("Updating modified resource")
                        resource['content'] = json.dumps(json.loads(edited_resource_content))
                        api.update_resource(resource, **vars(args))


def edit_entity(args):
    dataset_id = args.dataset_id
    entity_id = args.id
    del vars(args)['dataset_id']
    del vars(args)['id']
    entity_history = api.get_entity(dataset_id, entity_id, **vars(args))

    subject = None
    if args.date is None:
        subject = entity_history[-1]
    else:
        for entity in entity_history:
            if entity['timestamp_ms'] == util.string_to_timestamp_ms(args.date):
                subject = entity

    if subject is not None:
        edited_entity = open_in_editor(json.dumps(subject, indent=2))
        if edited_entity != str(subject):
            return api.modify_entity(dataset_id, json.loads(edited_entity), **vars(args))

    return "No entity found"


def list_datasets(args):
    return api.list_datasets(**vars(args))


def create_dataset(args):
    response = api.create_dataset(args.name, **vars(args))

    if args.json or args.csv:
        print(json.dumps(response, indent=2))
        response = ingest.ingest_file(response['id'], **vars(args))
    elif args.raw:
        response = ingest_entities(response['id'], args)

    return response


def read_entity_set_from_samples_file(args):
    sample_list = None
    if args.csv:
        sample_list = util.parse_samples(util.csv_to_json(args.csv))
    if args.json:
        sample_list = util.json_to_samples(args.json)

    return util.samples_to_entity_set(sample_list)


def append_transaction(args):
    entity_set = read_entity_set_from_samples_file(args)
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    process = not args.hold
    del vars(args)['hold']

    response = api.append_transaction(dataset_id, entity_set, process=process, **vars(args))
    return response


def insert_transaction(args):
    entity_set = read_entity_set_from_samples_file(args)
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    process = not args.hold
    del vars(args)['hold']

    response = api.insert_transaction(dataset_id, entity_set, process=process, **vars(args))
    return response


def get_dataset_transactions(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    return api.get_transactions(dataset_id, **vars(args))


def strip_none(original):
    return {k: v for k, v in original.items() if v is not None}


def request_kwargs(**kwargs):
    return strip_none({
        'host': kwargs.get('host'),
        'user': kwargs.get('user'),
        'api_key': kwargs.get('api_key'),
        'no_verify': kwargs.get('no_verify'),
        'password': kwargs.get('password'),
    })


def process_transactions(args):
    if len(args.backend_ids) == 0 and not args.all_backends:
        raise ValueError('You must provide a list of backend IDs or pass --all-backends')

    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    backend_ids = args.backend_ids
    del vars(args)['backend_ids']
    all_backends = args.all_backends
    del vars(args)['all_backends']
    async_processing = args.async_processing
    del vars(args)['async_processing']

    if all_backends:
        backend_ids = api.list_dataset_backends(dataset_id, **request_kwargs(**vars(args)))

    if async_processing or args.transaction or args.all:
        for backend_id in backend_ids:
            response = api.process_transactions(dataset_id, backend_id, **vars(args))
            print('Processing... check backend {} status at {}'.format(backend_id, response.headers['location']))
    else:
        min_tx = args.min
        del vars(args)['min']
        max_tx = args.max
        del vars(args)['max']
        del vars(args)['all']
        del vars(args)['transaction']

        max_transaction = max_tx or api.get_transactions(dataset_id, count=True, **vars(args))['count']
        for backend_id in backend_ids:
            min_transaction = min_tx or api.get_dataset_backend_metadata(dataset_id, backend_id, **vars(args))['transactions']
            idx = 1
            while min_transaction + idx <= max_transaction:
                print("Processing transaction {} of {} on {}...".format(min_transaction + idx, max_transaction, backend_id))
                response = api.process_transactions(dataset_id, backend_id, transaction=(min_transaction + idx), **vars(args))
                api.wait_for_job(response.headers['location'])
                idx += 1


def enable_auto_processing(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    backend_id = args.backend_id
    del vars(args)['backend_id']
    enable = not args.disable
    del vars(args)['disable']

    return api.enable_auto_processing(dataset_id, backend_id, enable=enable, **vars(args))


def set_default_backend(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    backend_id = args.backend_id
    del vars(args)['backend_id']
    return api.set_default_backend(dataset_id, backend_id, **vars(args))


def remove_dataset_backends(args):
    if len(args.backend_ids) == 0 and not args.all:
        raise ValueError('You must provide a list of backend IDs or pass --all')

    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    backend_ids = args.backend_ids
    del vars(args)['backend_ids']
    remove_all = args.all
    del vars(args)['all']
    force = args.force
    del vars(args)['force']

    if remove_all:
        backend_ids = api.list_dataset_backends(dataset_id, **vars(args))
        if not force:
            answer = input("Removing {} backends! Are you sure (Y/n): ".format(len(backend_ids)))
            if answer is not 'Y':
                return

    for backend_id in backend_ids:
        location = api.remove_dataset_backend(dataset_id, backend_id, **vars(args)).headers['location']
        print('Removing {}: check status at {}'.format(backend_id, location))


def list_dataset_backends(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    backends = args.backend_ids
    del vars(args)['backend_ids']
    verbose = args.verbose
    del vars(args)['verbose']

    if len(backends) == 0:
        backends = api.list_dataset_backends(dataset_id, **vars(args))
    else:
        verbose = True

    if verbose:
        metadata = {}
        for backend_id in backends:
            metadata.update({backend_id: api.get_dataset_backend_metadata(dataset_id, backend_id, **vars(args))})
        return metadata

    return backends


def add_simple_store(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    auto_process = not args.manual_processing
    del vars(args)['manual_processing']
    return api.add_simple_store(dataset_id, auto_process, **vars(args))


def add_tile_store(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    auto_process = not args.manual_processing
    del vars(args)['manual_processing']
    return api.add_tile_store(dataset_id, auto_process, **vars(args))


def add_elasticsearch_store(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    auto_process = not args.manual_processing
    del vars(args)['manual_processing']
    return api.add_elasticsearch_store(dataset_id, auto_process, **vars(args))


def add_histogram_store(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    auto_process = not args.manual_processing
    del vars(args)['manual_processing']
    return api.add_histogram_store(dataset_id, auto_process, **vars(args))


def add_capped_tile_store(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    min_spatial = args.min_spatial
    del vars(args)['min_spatial']
    min_temporal = args.min_temporal
    del vars(args)['min_temporal']
    auto_process = not args.manual_processing
    del vars(args)['manual_processing']
    return api.add_capped_tile_store(dataset_id, auto_process, min_spatial, min_temporal, **vars(args))


def get_backend_status(args):
    dataset_ids = args.dataset_ids
    del vars(args)['dataset_ids']

    for dataset_id in dataset_ids:
        print("{}:".format(dataset_id))
        max_transaction = api.get_transactions(dataset_id, count=True, **request_kwargs(**vars(args)))['count']
        backend_ids = api.list_dataset_backends(dataset_id, **request_kwargs(**vars(args)))

        metadata = {}
        for backend_id in backend_ids:
            metadata = api.get_dataset_backend_metadata(dataset_id, backend_id, **vars(args))
            print("  {}::{}: processed {} of {} transactions".format(
                metadata.get('configuration', {}).get('backend_type', 'LegacyTileStore'),
                backend_id, metadata.get('transactions', 'NaN'), max_transaction))


def ingest_data(args):
    if args.raw:
        del vars(args)['dataset_id']
        return ingest_entities(args.dataset_id, args)
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    return ingest.ingest_file(dataset_id, **vars(args))


def ingest_entities(dataset_id, args):
    with open(args.raw) as json_file:
        entities = json.load(json_file)
        del vars(args)['raw']
        return api._ingest_entity_set(dataset_id, entities, **vars(args))


def create_team(args):
    return api.create_team(args.name, **vars(args))


def list_teams(args):
    return api.list_teams(**vars(args))


def list_team_members(args):
    team_id = args.team_id
    del vars(args)['team_id']

    return api.list_team_members(team_id, **vars(args))


def add_team_user(args):
    team_id = args.team_id
    del vars(args)['team_id']
    email = args.email
    del vars(args)['email']

    return api.add_user_to_team(team_id, email, **vars(args))


def create_group(args):
    team_id = args.team_id
    del vars(args)['team_id']
    name = args.name
    del vars(args)['name']

    return api.create_group(team_id, name, **vars(args))


def list_groups(args):
    team_id = args.team_id
    del vars(args)['team_id']

    return api.list_groups(team_id, **vars(args))


def list_group_members(args):
    team_id = args.team_id
    del vars(args)['team_id']
    group_id = args.group_id
    del vars(args)['group_id']

    return api.list_group_members(team_id, group_id, **vars(args))


def add_group_user(args):
    team_id = args.team_id
    del vars(args)['team_id']
    group_id = args.group_id
    del vars(args)['group_id']
    user_id = args.user_id
    del vars(args)['user_id']

    return api.add_user_to_group(team_id, group_id, user_id, **vars(args))


def set_generic_data(args):
    if args.csv:
        from . import util
        data = util.csv_to_json(args.csv)
    elif args.json:
        with open(args.json) as json_file:
            data = json.load(json_file)

    dataset_id = args.dataset_id
    key = args.key
    del vars(args)['dataset_id']
    del vars(args)['key']

    return api.set_generic_data(dataset_id, key, json.dumps(data), **vars(args))


def get_generic_data(args):
    dataset_id = args.dataset_id
    key = args.key
    del vars(args)['dataset_id']
    del vars(args)['key']
    return json.dumps(api.get_generic_data(dataset_id, key, **vars(args)))


def remove_resource(args):
    if args.type is not None:
        args.type = format_resource_type(args.type)

    return api.remove_resource(**vars(args))


def tag_resource(args):
    tags = vars(args).pop('tags')
    set_tags = vars(args).pop('set')
    remove_tags = vars(args).pop('remove')

    if args.type is not None:
        args.type = format_resource_type(args.type)

    resources = api.find_resource(**vars(args))

    print(resources)
    for resource in resources:
        if set_tags:
            api.set_tags(resource['id'], tags, **vars(args))
        elif remove_tags:
            api.remove_tags(resource['id'], tags, **vars(args))
        else:
            api.add_tags(resource['id'], tags, **vars(args))


def remove_dataset(args):
    return api.remove_dataset(permanent=args.hard, **vars(args))


def clear_dataset(args):
    return api.clear_dataset(**vars(args))


def list_api_keys(args):
    return api.list_api_keys(**vars(args))


def create_api_key(args):
    return api.create_api_key(**vars(args))


def create_tileset(args):
    if args.tile_json:
        raise "TileJSON not currently supported by the CLI"

    if args.style_url.split('mapbox://styles/')[1] < 2:
        raise ValueError('Style URL must be a Mapbox style URL')

    content = {
        'url': args.style_url,
        'style': args.style_url.split('mapbox://styles/')[1],
        'accessToken': args.access_token,
    }

    return api.create_json_resource('TILESET', args.name, content, version=2, **vars(args))


def remove_api_key(args):
    key = args.key
    del vars(args)['key']
    return api.remove_api_key(key, **vars(args))


def set_api_key(args):
    if args.new:
        args.key = api.create_api_key(**vars(args))
    if args.key is None:
        raise ValueError('An API must either be provided with the --key argument or you must generate a new key with --new')
    config.set_api_key(args)
    return "API key set for {} on {}".format(args.user, args.host)


def set_owner(args):
    team_id = args.team_id
    del vars(args)['team_id']
    resource_id = args.resource_id
    del vars(args)['resource_id']

    api.set_owner(team_id, resource_id, **vars(args))


def list_permissions(args):
    resource_id = args.resource_id
    del vars(args)['resource_id']

    return api.list_permissions(resource_id, **vars(args))


def parse_permissions(permissions):
    permissions_dict = {'read': False, 'write': False, 'share': False}
    if 'r' in permissions:
        permissions_dict['read'] = True
    if 'w' in permissions:
        permissions_dict['write'] = True
    if 's' in permissions:
        permissions_dict['share'] = True

    return permissions_dict


def set_public_permissions(args):
    id_list = args.resource_id.split(',')
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    for id in id_list:
        api.set_public_permissions(id, p['read'], p['write'], p['share'], **vars(args))


def set_team_permissions(args):
    id_list = args.resource_id.split(',')
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    for id in id_list:
        api.set_team_permissions(id, p['read'], p['write'], p['share'], **vars(args))


def set_group_permissions(args):
    group_id = args.group_id
    del vars(args)['group_id']
    id_list = args.resource_id.split(',')
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    for id in id_list:
        api.set_group_permissions(group_id, id, p['read'], p['write'], p['share'], **vars(args))


def set_user_permissions(args):
    user_id = args.user_id
    del vars(args)['user_id']
    id_list = args.resource_id.split(',')
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    for id in id_list:
        api.set_user_permissions(user_id, id, p['read'], p['write'], p['share'], **vars(args))


def send_get_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_get_request(uri, **vars(args))


def send_post_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_post_request(json.loads(args.data), uri, **vars(args))


def send_patch_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_patch_request(json.loads(args.data), uri, **vars(args))


def send_delete_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_delete_request(uri, **vars(args))


def account_exists(args):
    email = args.email
    del vars(args)['email']

    return api.account_exists(email, **vars(args))


def create_account(args):
    name = args.name
    del vars(args)['name']
    email = args.email
    del vars(args)['email']

    return api.create_account(name, email, **vars(args))


def get_entity(args):
    datasets = api.find_dataset(id=args.dataset_id, name=args.dataset_name, regex=args.dataset_regex, host=args.host, user=args.user, api_key=args.api_key)
    entities = []
    for dataset in datasets:
        entities.append(api.get_entity(dataset['id'], args.entity_id, host=args.host, user=args.user, api_key=args.api_key))
    return entities


def dump_data(args):
    uri = 'datasets/raw-lens/{}/{}/{}/{}/{}/{}/{}/{}/{}'.format(
        args.dataset_id, args.x_min, args.x_max, args.y_min, args.y_max, args.z_min, args.z_max, args.t_min, args.t_max)
    return api.make_get_request(uri, **vars(args))


def upload_image(args):
    path = os.path.expanduser(args.path)
    del vars(args)['path']

    return asset.initialize_binary_asset(path, **vars(args))


def main():
    import argparse
    import pkg_resources

    class ConduceCommandLineParser(argparse.ArgumentParser):
        def error(self, message):
            self.print_help()
            sys.exit(2)

    if sys.argv[0] != 'conduce.py':
        version = pkg_resources.require("conduce")[0].version
    else:
        version = 'version-dev'

    arg_parser = ConduceCommandLineParser(description='Conduce command line interface {}'.format(version), formatter_class=argparse.RawTextHelpFormatter)
    api_cmd_parser = ConduceCommandLineParser(add_help=False)
    api_cmd_parser.add_argument('--user', help='The user whose is making the request')
    api_cmd_parser.add_argument('--host', help='The server on which the command will run')
    api_cmd_parser.add_argument('--api-key', help='The API key used to authenticate')
    api_cmd_parser.add_argument('--no-verify', action='store_true', help='If passed, the SSL certificate of the host will not be verified')

    subparsers = arg_parser.add_subparsers(help='help for subcommands', dest='see subcommands')
    subparsers.required = True

    parser_config = subparsers.add_parser('config', help='Conduce configuration settings')
    parser_config_subparsers = parser_config.add_subparsers(help='config subcommands', dest='see subcommands')
    parser_config_subparsers.required = True

    parser_config_set = parser_config_subparsers.add_parser('set', help='Set Conduce configuration setting')
    parser_config_set_subparsers = parser_config_set.add_subparsers(help='set subcommands', dest='see subcommands')
    parser_config_set_subparsers.required = True

    parser_config_set_default_user = parser_config_set_subparsers.add_parser('default-user', help='get the default user for executing commands')
    parser_config_set_default_user.add_argument('default_user', help='user name')
    parser_config_set_default_user.set_defaults(func=config.set_default_user)

    parser_config_set_default_host = parser_config_set_subparsers.add_parser('default-host', help='get the default server to send commands to')
    parser_config_set_default_host.add_argument('default_host', help='host')
    parser_config_set_default_host.set_defaults(func=config.set_default_host)

    parser_config_set_api_key = parser_config_set_subparsers.add_parser('api-key', help='Set a Conduce API key')
    parser_config_set_api_key.add_argument('--user', help='The user to which the API key belongs')
    parser_config_set_api_key.add_argument('--host', help='The server on which the API key is valid')
    parser_config_set_api_key.add_argument('--password', help='The password of the user making the request')
    parser_config_set_api_key.add_argument('--key', help='The API key')
    parser_config_set_api_key.add_argument('--new', help='Generate a new API key', action='store_true')
    parser_config_set_api_key.add_argument('--no-verify', action='store_true',
                                           help='If passed, the SSL certificate of the host will not be verified when creating a new key')
    parser_config_set_api_key.set_defaults(func=set_api_key)

    parser_config_get = parser_config_subparsers.add_parser('get', help='Get Conduce configuration setting')
    parser_config_get_subparsers = parser_config_get.add_subparsers(help='get subcommands', dest='see subcommands')
    parser_config_get_subparsers.required = True

    parser_config_get_default_user = parser_config_get_subparsers.add_parser('default-user', help='get the default user for executing commands')
    parser_config_get_default_user.set_defaults(func=config.get_default_user)

    parser_config_get_default_host = parser_config_get_subparsers.add_parser('default-host', help='get the default server to send commands to')
    parser_config_get_default_host.set_defaults(func=config.get_default_host)

    parser_config_get_api_key = parser_config_get_subparsers.add_parser('api-key', help='Get a Conduce API key')
    parser_config_get_api_key.add_argument('--user', help='The user to which the API key belongs')
    parser_config_get_api_key.add_argument('--host', help='The server on which the API key is valid')
    parser_config_get_api_key.set_defaults(func=config.get_api_key_config)

    parser_config_list = subparsers.add_parser('list', parents=[api_cmd_parser], help='List resources by type')
    parser_config_list.add_argument('object_to_list', help='Conduce object to list')

    parser_config_list.set_defaults(func=list_from_args)

    parser_find = subparsers.add_parser('find', parents=[api_cmd_parser], help='Find resources that match the given parameters')
    parser_find.add_argument('--type', help='Conduce resource type to find')
    parser_find.add_argument('--name', help='The name of the resource to find')
    parser_find.add_argument('--id', help='The ID of the resource to find')
    parser_find.add_argument('--regex', help='An expression on which to filter results')
    parser_find.add_argument('--content', help='Content to retrieve: id,full,meta')
    parser_find.add_argument('--decode', action='store_true', help='Decode base64 and JSON for full content requests')
    parser_find.add_argument('--no-name', action='store_true', help='Match resources with no name')
    parser_find.add_argument('-1', '--one-line', action='store_true', help='Return only names and IDs')
    parser_find.add_argument('--tags', type=str, nargs='+', help='Match resources with the specified tag')
    parser_find.set_defaults(func=find_resource)

    parser_dataset = subparsers.add_parser('dataset', help='Conduce dataset operations')
    parser_dataset_subparsers = parser_dataset.add_subparsers(help='dataset subcommands', dest='see subcommands')
    parser_dataset_subparsers.required = True

    parser_dataset_get_metadata = parser_dataset_subparsers.add_parser(
        'metadata', parents=[api_cmd_parser], help='List dataset metadata for resources that match the given parameters')
    parser_dataset_get_metadata.add_argument('--name', help='The name of the dataset to query')
    parser_dataset_get_metadata.add_argument('--id', help='The ID of the dataset to query')
    parser_dataset_get_metadata.add_argument('--regex', help='An expression to match datasets and query')
    parser_dataset_get_metadata.set_defaults(func=get_dataset_metadata)

    dataset_post_transaction_parser = ConduceCommandLineParser(add_help=False)
    dataset_post_transaction_parser.add_argument(
        '--json', help='Optional: A JSON file that can parsed into Conduce entities')
    dataset_post_transaction_parser.add_argument(
        '--csv', help='Optional: A CSV file that can be parsed as Conduce data')
    dataset_post_transaction_parser.add_argument(
        '--raw', help='Optional: A well formatted Conduce entities JSON file. Ignores --kind, --generate-ids and --answer-yes')
    dataset_post_transaction_parser.add_argument(
        '--generate-ids', help='Set this flag if the data does not contain an ID field', action='store_true')
    dataset_post_transaction_parser.add_argument(
        '--kind', help='Use this value as the kind for all entities')
    dataset_post_transaction_parser.add_argument(
        '--answer-yes', help='Set this flag to answer yes at all prompts', action='store_true')
    dataset_post_transaction_parser.add_argument(
        '--debug', help='Get better information about errors', action='store_true')

    parser_dataset_create = parser_dataset_subparsers.add_parser(
        'create', parents=[api_cmd_parser, dataset_post_transaction_parser], help='Create a new dataset with optional data')
    parser_dataset_create.add_argument('name', help='The name to be given to the new dataset')
    parser_dataset_create.add_argument('backends', nargs='*', help='Backends with which to create the dataset')
    parser_dataset_create.set_defaults(func=create_dataset)

    parser_dataset_append = parser_dataset_subparsers.add_parser(
        'append', parents=[api_cmd_parser, dataset_post_transaction_parser], help='Append records to a dataset')
    parser_dataset_append.add_argument(
        'dataset_id', help='Unique identifier of the dataset to which data will be appended')
    parser_dataset_append.add_argument(
        '--hold', action='store_true', help='Prevent this transactions from being processed immediately')
    parser_dataset_append.set_defaults(func=append_transaction)

    parser_dataset_insert = parser_dataset_subparsers.add_parser(
        'insert', parents=[api_cmd_parser, dataset_post_transaction_parser], help='Insert records into a dataset')
    parser_dataset_insert.add_argument(
        'dataset_id', help='Unique identifier of the dataset in which data will be inserted')
    parser_dataset_insert.add_argument(
        '--hold', action='store_true', help='Prevent this transactions from being processed immediately')
    parser_dataset_insert.set_defaults(func=insert_transaction)

    parser_dataset_transactions = parser_dataset_subparsers.add_parser(
        'transactions', parents=[api_cmd_parser], help='Print a sequence of dataset transactions for debugging')
    parser_dataset_transactions.add_argument('dataset_id', help='Unique identifier of the dataset to query')
    parser_dataset_transactions.add_argument('--min', default=-1, help='The oldest transaction in the returned sequence')
    parser_dataset_transactions.add_argument('--max', help='The newest transaction in the returned sequence')
    parser_dataset_transactions.add_argument('--value', help='The index of a single transaction to query')
    parser_dataset_transactions.add_argument('--rows', help='The number of transactions to return')
    parser_dataset_transactions.add_argument('--page_state', help='The page state to continue searching from')
    parser_dataset_transactions.add_argument('--count', action='store_true', help='Return only the number of transactions in the log')
    parser_dataset_transactions.set_defaults(func=get_dataset_transactions)

    parser_dataset_enable_auto_processing = parser_dataset_subparsers.add_parser(
        'auto-process', parents=[api_cmd_parser], help='Configure backend to enable/disable automatic transaction processing')
    parser_dataset_enable_auto_processing.add_argument('dataset_id', help='Unique identifier of the dataset to configure')
    parser_dataset_enable_auto_processing.add_argument('backend_id', help='ID of backend to configure')
    parser_dataset_enable_auto_processing.add_argument('--disable', action='store_true', help='Disable auto processing on the specified backend')
    parser_dataset_enable_auto_processing.set_defaults(func=enable_auto_processing)

    parser_dataset_set_default_backend = parser_dataset_subparsers.add_parser(
        'set-default-backend', parents=[api_cmd_parser], help='Set backend to receive lens queries')
    parser_dataset_set_default_backend.add_argument('dataset_id', help='Unique identifier of the dataset to configure')
    parser_dataset_set_default_backend.add_argument('backend_id', help='ID of default backend')
    parser_dataset_set_default_backend.set_defaults(func=set_default_backend)

    parser_dataset_process_transactions = parser_dataset_subparsers.add_parser(
        'process', parents=[api_cmd_parser], help='Process a sequence of transactions on the specified backends')
    parser_dataset_process_transactions.add_argument(
        'dataset_id', help='Unique identifier of the dataset to process')
    parser_dataset_process_transactions.add_argument(
        'backend_ids', nargs='*', help='IDs of backends to process')
    parser_dataset_process_transactions.add_argument(
        '--all-backends', action='store_true', help='Process specified transactions on all backends')
    parser_dataset_process_transactions.add_argument(
        '--async-processing', action='store_true', help='Process transactions on the backend as a batch job')
    parser_dataset_process_transactions.add_argument(
        '--all', action='store_true', help='Process all outstanding transactions (determined per backend)')
    parser_dataset_process_transactions.add_argument(
        '--min', type=int, help='The oldest transaction to be processed')
    parser_dataset_process_transactions.add_argument(
        '--max', type=int, help='The newest transaction to be processed')
    parser_dataset_process_transactions.add_argument(
        '--transaction', type=int, help='The index of a single transaction to process')
    parser_dataset_process_transactions.set_defaults(func=process_transactions)

    parser_dataset_list_backends = parser_dataset_subparsers.add_parser(
        'list-backends', parents=[api_cmd_parser], help='List backends attached to the dataset')
    parser_dataset_list_backends.add_argument(
        'dataset_id', help='Unique identifier of the dataset to list')
    parser_dataset_list_backends.add_argument(
        'backend_ids', nargs='*', help='One or more backend IDs to list')
    parser_dataset_list_backends.add_argument(
        '-v', '--verbose', action='store_true', help='List metadata for all backends')
    parser_dataset_list_backends.set_defaults(func=list_dataset_backends)

    parser_dataset_list_backends = parser_dataset_subparsers.add_parser(
        'remove-backend', parents=[api_cmd_parser], help='Remove backends from the dataset')
    parser_dataset_list_backends.add_argument('dataset_id', help='Unique identifier of the dataset to list')
    parser_dataset_list_backends.add_argument('backend_ids', nargs='*', help='IDs of backends to remove')
    parser_dataset_list_backends.add_argument('--all', action='store_true', help='Remove all backends, overrides list of backend IDs')
    parser_dataset_list_backends.add_argument('-f', '--force', action='store_true',
                                              help='When --all specified, skip prompt and remove backends without prejudice.')
    parser_dataset_list_backends.set_defaults(func=remove_dataset_backends)

    parser_dataset_add_backend = parser_dataset_subparsers.add_parser(
        'add-backend', parents=[api_cmd_parser], help='Add a backend to the dataset')
    parser_dataset_add_backend_subparsers = parser_dataset_add_backend.add_subparsers(help='Available backends', dest='see subcommands')
    parser_dataset_add_backend_subparsers.required = True

    dataset_add_backend_parser = ConduceCommandLineParser(add_help=False)
    dataset_add_backend_parser.add_argument('dataset_id', help='Unique identifier of the dataset to change')
    dataset_add_backend_parser.add_argument('--manual-processing', action='store_true', help='Disable automatic processing of transactions')

    parser_dataset_add_simple_store = parser_dataset_add_backend_subparsers.add_parser(
        'simple', parents=[api_cmd_parser, dataset_add_backend_parser], help='Add a simple store to the dataset')
    parser_dataset_add_simple_store.set_defaults(func=add_simple_store)

    parser_dataset_add_tile_store = parser_dataset_add_backend_subparsers.add_parser(
        'tile', parents=[api_cmd_parser, dataset_add_backend_parser], help='Add a tile store to the dataset')
    parser_dataset_add_tile_store.set_defaults(func=add_tile_store)

    parser_dataset_add_elasticsearch_store = parser_dataset_add_backend_subparsers.add_parser(
        'elasticsearch', parents=[api_cmd_parser, dataset_add_backend_parser], help='Add a elasticsearch store to the dataset')
    parser_dataset_add_elasticsearch_store.set_defaults(func=add_elasticsearch_store)

    parser_dataset_add_capped_tile_store = parser_dataset_add_backend_subparsers.add_parser(
        'capped-tile', parents=[api_cmd_parser, dataset_add_backend_parser], help='Add a capped_tile store to the dataset')
    parser_dataset_add_capped_tile_store.add_argument(
        '--min-spatial', type=int, default=0, help='The lowest spatial resolution supported by the store (default: 0)')
    parser_dataset_add_capped_tile_store.add_argument(
        '--min-temporal', type=int, default=0, help='The lowest temporal resolution supported by the store (default: 0)')
    parser_dataset_add_capped_tile_store.set_defaults(func=add_capped_tile_store)

    parser_dataset_add_histogram_store = parser_dataset_add_backend_subparsers.add_parser(
        'histogram', parents=[api_cmd_parser, dataset_add_backend_parser], help='Add a histogram store to the dataset')
    parser_dataset_add_histogram_store.set_defaults(func=add_histogram_store)

    parser_dataset_backend_status = parser_dataset_subparsers.add_parser(
        'backend-status', parents=[api_cmd_parser], help='Retrieve transaction processing progress for backends')
    parser_dataset_backend_status.add_argument('dataset_ids', nargs='*', help='Unique identifier of the dataset to configure')
    parser_dataset_backend_status.set_defaults(func=get_backend_status)

    parser_create_resource = subparsers.add_parser('create', parents=[api_cmd_parser], help='Create a new resource')
    parser_create_resource.add_argument('name', help='The name of the resource to create')
    parser_create_resource.add_argument('type', help='Conduce resource type to create')
    parser_create_resource.add_argument('--content', help='The content of the new resource')
    parser_create_resource.set_defaults(func=create_resource)

    parser_edit_resource = subparsers.add_parser('edit', parents=[api_cmd_parser], help='Edit resources that match the given parameters')
    parser_edit_resource.add_argument('--type', help='Conduce resource type to edit')
    parser_edit_resource.add_argument('--name', help='The name of the resource to edit')
    parser_edit_resource.add_argument('--id', help='The ID of the resource to edit')
    parser_edit_resource.add_argument('--regex', help='An expression matching resources to edit')
    parser_edit_resource.add_argument('--file', help='Replace the resource content with the file contents')
    parser_edit_resource.set_defaults(func=edit_resource)

    parser_rename_resource = subparsers.add_parser('rename', parents=[api_cmd_parser], help='Rename the resource that matches the given parameters')
    parser_rename_resource.add_argument('new_name', help='The resource\'s new name')
    parser_rename_resource.add_argument('--type', help='Conduce resource type to rename')
    parser_rename_resource.add_argument('--name', help='The name of the resource to rename')
    parser_rename_resource.add_argument('--id', help='The ID of the resource to rename')
    parser_rename_resource.add_argument('--regex', help='An expression matching resources to rename')
    parser_rename_resource.add_argument('-v', '--verbose', action='store_true', help='Find and print metadata for resource after rename')
    parser_rename_resource.set_defaults(func=rename_resource)

    parser_copy_resource = subparsers.add_parser('copy', parents=[api_cmd_parser], help='Copy resource that matches the given parameters')
    parser_copy_resource.add_argument('resource_name', help='Name of newly copied resource')
    parser_copy_resource.add_argument('--type', help='Conduce resource type to copy')
    parser_copy_resource.add_argument('--name', help='The name of the resource to copy')
    parser_copy_resource.add_argument('--id', help='The ID of the resource to edit')
    parser_copy_resource.add_argument('--regex', help='An expression matching a single resource to copy')
    parser_copy_resource.set_defaults(func=copy_resource)

    parser_edit_entity_entity = subparsers.add_parser('edit-entity', parents=[api_cmd_parser], help='Edit a dataset entity that match the given parameters')
    parser_edit_entity_entity.add_argument('--id', help='The ID of the entity to edit')
    parser_edit_entity_entity.add_argument('--dataset-id', help='The ID of the dataset that contains the entity')
    parser_edit_entity_entity.add_argument('--date', help='The date at which the entity occurred (optional, if not specified the newest will be selected.)')
    parser_edit_entity_entity.set_defaults(func=edit_entity)

    parser_list_api_keys = subparsers.add_parser('list-api-keys', parents=[api_cmd_parser], help='List API keys for your account')
    parser_list_api_keys.set_defaults(func=list_api_keys)

    parser_create_api_key = subparsers.add_parser('create-api-key', parents=[api_cmd_parser], help='Create an API key for your account')
    parser_create_api_key.add_argument('--password', help='The password of the user making the request')
    parser_create_api_key.set_defaults(func=create_api_key)

    parser_remove_api_key = subparsers.add_parser('remove-api-key', parents=[api_cmd_parser], help='Delete an API key')
    parser_remove_api_key.add_argument('key', help='The key to delete')
    parser_remove_api_key.set_defaults(func=remove_api_key)

    parser_create_dataset = subparsers.add_parser('create-dataset', parents=[api_cmd_parser], help='Create a Conduce dataset')
    parser_create_dataset.add_argument('name', help='The name to be given to the new dataset')
    parser_create_dataset.add_argument('--json', help='Optional: A JSON file that can parsed into Conduce entities')
    parser_create_dataset.add_argument('--csv', help='Optional: A CSV file that can be parsed as Conduce data')
    parser_create_dataset.add_argument('--raw', help='Optional: A well formatted Conduce entities JSON file. Ignores --kind, --generate-ids and --answer-yes')
    parser_create_dataset.add_argument('--generate-ids', help='Set this flag if the data does not contain an ID field', action='store_true')
    parser_create_dataset.add_argument('--kind', help='Use this value as the kind for all entities')
    parser_create_dataset.add_argument('--answer-yes', help='Set this flag to answer yes at all prompts', action='store_true')
    parser_create_dataset.add_argument('--debug', help='Get better information about errors', action='store_true')
    parser_create_dataset.set_defaults(func=create_dataset)

    parser_create_tileset = subparsers.add_parser('create-tileset', parents=[api_cmd_parser], help='Create a Conduce tileset')
    parser_create_tileset.add_argument('name', help='The name to be given to the new tileset')
    parser_create_tileset.add_argument('--style-url', help='The Mapbox URL used to access the style <mapbox://styles/...>')
    parser_create_tileset.add_argument('--access-token', help='Mapbox access token. Use for user owned private map styles.')
    parser_create_tileset.add_argument('--tile-json', help='A valid TileJSON file')
    parser_create_tileset.set_defaults(func=create_tileset)

    parser_ingest_data = subparsers.add_parser('ingest-data', parents=[api_cmd_parser], help='Ingest data to a Conduce dataset')
    parser_ingest_data.add_argument('dataset_id', help='The ID of the dataset to receive the entities')
    parser_ingest_data.add_argument('--json', help='A JSON file that can parsed into Conduce entities')
    parser_ingest_data.add_argument('--csv', help='A CSV file that can be parsed as Conduce data')
    parser_ingest_data.add_argument('--raw', help='A well formatted Conduce entities JSON file. Ignores --kind, --generate-ids and --answer-yes')
    parser_ingest_data.add_argument('--generate-ids', help='Set this flag if the data does not contain an ID field', action='store_true')
    parser_ingest_data.add_argument('--kind', help='Use this value as the kind for all entities')
    parser_ingest_data.add_argument('--answer-yes', help='Set this flag to answer yes at all prompts', action='store_true')
    parser_ingest_data.add_argument('--debug', help='Get better information about errors', action='store_true')
    parser_ingest_data.set_defaults(func=ingest_data)

    parser_dump_data = subparsers.add_parser('dump-data', parents=[api_cmd_parser], help='dump all data from a Conduce dataset')
    parser_dump_data.add_argument('dataset_id', help='The ID of the dataset to dump')
    parser_dump_data.add_argument('--x-min', help='Optional', default=-180)
    parser_dump_data.add_argument('--x-max', help='Optional', default=180)
    parser_dump_data.add_argument('--y-min', help='Optional', default=-90)
    parser_dump_data.add_argument('--y-max', help='Optional', default=90)
    parser_dump_data.add_argument('--z-min', help='Optional', default=-1)
    parser_dump_data.add_argument('--z-max', help='Optional', default=1)
    parser_dump_data.add_argument('--t-min', help='Optional', default=-281474976710655)
    parser_dump_data.add_argument('--t-max', help='Optional', default=281474976710655)
    parser_dump_data.set_defaults(func=dump_data)

    parser_get_entity = subparsers.add_parser('get-entity', parents=[api_cmd_parser], help='Get the latest state of a Conduce entity')
    parser_get_entity.add_argument('entity_id', help='The ID of the entity to retrieve')
    parser_get_entity.add_argument('--dataset-name', help='The name of the dataset to query')
    parser_get_entity.add_argument('--dataset-id', help='The ID of the dataset to query')
    parser_get_entity.add_argument('--dataset-regex', help='An expression to match datasets and query')
    parser_get_entity.set_defaults(func=get_entity)

    parser_team = subparsers.add_parser('team', help='Conduce team operations')
    parser_team_subparsers = parser_team.add_subparsers(help='team subcommands', dest='see subcommands')
    parser_team_subparsers.required = True

    parser_create_team = parser_team_subparsers.add_parser('create', parents=[api_cmd_parser], help='Create a Conduce team')
    parser_create_team.add_argument('name', help='The name to be given to the new team')
    parser_create_team.set_defaults(func=create_team)

    parser_list_teams = parser_team_subparsers.add_parser('list', parents=[api_cmd_parser], help='List Conduce teams')
    parser_list_teams.set_defaults(func=list_teams)

    parser_list_team_members = parser_team_subparsers.add_parser('list-members', parents=[api_cmd_parser], help='List members of team')
    parser_list_team_members.add_argument('team_id', help='The team to list')
    parser_list_team_members.set_defaults(func=list_team_members)

    parser_add_team_user = parser_team_subparsers.add_parser('add-user', parents=[api_cmd_parser], help='add user to team')
    parser_add_team_user.add_argument('team_id', help='The UUID of the team to which the user will be added')
    parser_add_team_user.add_argument('email', help='Email address of the Conduce user being added')
    parser_add_team_user.set_defaults(func=add_team_user)

    parser_group = subparsers.add_parser('group', help='Conduce group operations')
    parser_group_subparsers = parser_group.add_subparsers(help='group subcommands', dest='see subcommands')
    parser_group_subparsers.required = True

    parser_create_group = parser_group_subparsers.add_parser('create', parents=[api_cmd_parser], help='Create a Conduce group')
    parser_create_group.add_argument('team_id', help='The UUID of the team to which the group belongs')
    parser_create_group.add_argument('name', help='The name to be given to the new group')
    parser_create_group.set_defaults(func=create_group)

    parser_list_groups = parser_group_subparsers.add_parser('list', parents=[api_cmd_parser], help='List Conduce groups')
    parser_list_groups.add_argument('team_id', help='The UUID of the team to which the group belongs')
    parser_list_groups.set_defaults(func=list_groups)

    parser_list_group_members = parser_group_subparsers.add_parser('list-members', parents=[api_cmd_parser], help='List members of group')
    parser_list_group_members.add_argument('team_id', help='The UUID of the team to which the group belongs')
    parser_list_group_members.add_argument('group_id', help='The group to list')
    parser_list_group_members.set_defaults(func=list_group_members)

    parser_add_group_user = parser_group_subparsers.add_parser('add-user', parents=[api_cmd_parser], help='Add user to group')
    parser_add_group_user.add_argument('team_id', help='The UUID of the team to which the group belongs')
    parser_add_group_user.add_argument('group_id', help='The UUID of the group to which the user will be added')
    parser_add_group_user.add_argument('user_id', help='The UUID of the user being added')
    parser_add_group_user.set_defaults(func=add_group_user)

    parser_account_exists = subparsers.add_parser('account-exists', parents=[api_cmd_parser], help='Check if an account exists for a given email address')
    parser_account_exists.add_argument('email', help='The email address to check')
    parser_account_exists.set_defaults(func=account_exists)

    parser_create_account = subparsers.add_parser('create-account', parents=[api_cmd_parser], help='Create a new user by name and email')
    parser_create_account.add_argument('name', help='The user\'s name as it will be displayed in Conduce')
    parser_create_account.add_argument('email', help='The email address associated with the new user')
    parser_create_account.set_defaults(func=create_account)

    parser_set_generic_data = subparsers.add_parser('set-generic-data', parents=[api_cmd_parser], help='Add generic data to Conduce dataset')
    parser_set_generic_data.add_argument('dataset_id', help='The ID of the dataset to send data to')
    parser_set_generic_data.add_argument('key', help='Unique name with which to lookup data')
    parser_set_generic_data.add_argument('--json', help='The data to be consumed')
    parser_set_generic_data.add_argument('--csv', help='The data to be consumed')
    parser_set_generic_data.set_defaults(func=set_generic_data)

    parser_get_generic_data = subparsers.add_parser('get-generic-data', parents=[api_cmd_parser], help='Retrieve generic data from Conduce dataset')
    parser_get_generic_data.add_argument('dataset_id', help='The ID of the dataset to get the data from')
    parser_get_generic_data.add_argument('key', help='Unique ID of entity to retrieve data from')
    parser_get_generic_data.set_defaults(func=get_generic_data)

    parser_clear_dataset = subparsers.add_parser('clear-dataset', parents=[api_cmd_parser], help='Remove all records from a Conduce dataset')
    parser_clear_dataset.add_argument('--id', help='The ID of the dataset to be cleared')
    parser_clear_dataset.add_argument('--name', help='The name of the dataset to be cleared')
    parser_clear_dataset.add_argument('--regex', help='clear datasets that match the regular expression')
    parser_clear_dataset.add_argument('--all', help='clear all matching datasets', action='store_true')
    parser_clear_dataset.set_defaults(func=clear_dataset)

    parser_remove_dataset = subparsers.add_parser('remove-dataset', parents=[api_cmd_parser], help='Remove a dataset from Conduce (soft delete)')
    parser_remove_dataset.add_argument('--id', help='The ID of the dataset to be removed')
    parser_remove_dataset.add_argument('--name', help='The name of the dataset to be removed')
    parser_remove_dataset.add_argument('--regex', help='Remove datasets that match the regular expression')
    parser_remove_dataset.add_argument('--hard', action='store_true', help='Permanently destroy (hard delete) the dataset')
    parser_remove_dataset.add_argument('--all', help='Remove all matching datasets', action='store_true')
    parser_remove_dataset.set_defaults(func=remove_dataset)

    parser_remove = subparsers.add_parser('remove', parents=[api_cmd_parser], help='Remove a resource from Conduce')
    parser_remove.add_argument('--id', help='The ID of the resource to be removed')
    parser_remove.add_argument('--type', help='Conduce resource type to remove')
    parser_remove.add_argument('--name', help='The name of the resource to be removed')
    parser_remove.add_argument('--regex', help='Remove resources that match the regular expression')
    parser_remove.add_argument('--no-name', action='store_true', help='Match resources with no name')
    parser_remove.add_argument('--tags', nargs='+', help='Match resources with specified tag')
    parser_remove.add_argument('--all', help='Remove all matching resources', action='store_true')
    parser_remove.set_defaults(func=remove_resource)

    parser_tag = subparsers.add_parser('tag', parents=[api_cmd_parser], help='Add tag to resources that match the given parameters')
    parser_tag.add_argument('tags', nargs='+', help='The tag or tags to be applied to the matched resource(s) (separated by spaces)')
    parser_tag.add_argument('--id', help='The ID of the resource to be tagged')
    parser_tag.add_argument('--type', help='Conduce resource type to tag')
    parser_tag.add_argument('--name', help='The name of the resource to be tagged')
    parser_tag.add_argument('--regex', help='tag resources that match the regular expression')
    parser_tag.add_argument('--no-name', action='store_true', help='Match resources with no name')
    parser_tag.add_argument('--remove', action='store_true', help='Remove tags instead of adding')
    parser_tag.add_argument('--set', action='store_true', help='Set the list of tags to the specified')
    parser_tag.set_defaults(func=tag_resource)

    parser_permissions = subparsers.add_parser('permissions', help='Conduce permissions operations')
    parser_permissions_subparsers = parser_permissions.add_subparsers(help='permissions subcommands', dest='see subcommands')
    parser_permissions_subparsers.required = True

    parser_set_owner = parser_permissions_subparsers.add_parser('set-owner', parents=[api_cmd_parser], help='Set the owner of this resource')
    parser_set_owner.add_argument('team_id', help='The UUID of the team to which the user belongs')
    parser_set_owner.add_argument('resource_id', help='The UUID of the resource being modified')
    parser_set_owner.set_defaults(func=set_owner)

    parser_list_permissions = parser_permissions_subparsers.add_parser('list', parents=[api_cmd_parser], help='List permissions of a resource')
    parser_list_permissions.add_argument('resource_id', help='The UUID of the resource to be listed')
    parser_list_permissions.set_defaults(func=list_permissions)

    parser_set_permissions = parser_permissions_subparsers.add_parser('set', parents=[api_cmd_parser], help='Set permissions of a resource')
    parser_set_permissions.add_argument('permissions', help='The permissions to enable [r|w|s]')
    parser_set_permissions.add_argument('resource_id', type=str, help='The UUID of the resource to be updated (or comma separated list)')
    parser_set_permissions_subparsers = parser_set_permissions.add_subparsers(help='set permissions subcommands', dest='see subcommands')
    parser_set_permissions.required = True

    parser_set_public_permissions = parser_set_permissions_subparsers.add_parser(
        'public', parents=[api_cmd_parser], help='Set public permissions of a resource')
    parser_set_public_permissions.set_defaults(func=set_public_permissions)

    parser_set_team_permissions = parser_set_permissions_subparsers.add_parser('team', parents=[api_cmd_parser], help='Set team permissions of a resource')
    parser_set_team_permissions.set_defaults(func=set_team_permissions)

    parser_set_group_permissions = parser_set_permissions_subparsers.add_parser('group', parents=[api_cmd_parser], help='Set group permissions of a resource')
    parser_set_group_permissions.add_argument('group_id', help='The group UUID')
    parser_set_group_permissions.set_defaults(func=set_group_permissions)

    parser_set_user_permissions = parser_set_permissions_subparsers.add_parser('user', parents=[api_cmd_parser], help='Set user permissions of a resource')
    parser_set_user_permissions.add_argument('user_id', help='The user UUID')
    parser_set_user_permissions.set_defaults(func=set_user_permissions)

    parser_upload_image = subparsers.add_parser('upload-image', parents=[api_cmd_parser], help='Ingest data to a Conduce dataset')
    parser_upload_image.add_argument('path', help='The local path to the image file.')
    parser_upload_image.add_argument('--name', help='String to help identify the Conduce resource')
    parser_upload_image.add_argument('--id', help='UUID of the Conduce resource (only for modifying existing resources)')
    parser_upload_image.add_argument('--modify',
                                     help='Modify existing resource if it exists (this is the default behavior if --id is specified)',
                                     action='store_true')
    parser_upload_image.set_defaults(func=upload_image)

    parser_get = subparsers.add_parser('get', parents=[api_cmd_parser], help='Make an arbitrary get request')
    parser_get.add_argument('uri', help='The URI of the resource being requested')
    parser_get.set_defaults(func=send_get_request)

    parser_post = subparsers.add_parser('post', parents=[api_cmd_parser], help='Make an arbitrary post request')
    parser_post.add_argument('uri', help='The URI of the resource being requested')
    parser_post.add_argument('data', help='The data being posted')
    parser_post.set_defaults(func=send_post_request)

    parser_patch = subparsers.add_parser('patch', parents=[api_cmd_parser], help='Make an arbitrary patch request')
    parser_patch.add_argument('uri', help='The URI of the resource being requested')
    parser_patch.add_argument('data', help='The data being posted')
    parser_patch.set_defaults(func=send_patch_request)

    parser_patch = subparsers.add_parser('delete', parents=[api_cmd_parser], help='Make an arbitrary delete request')
    parser_patch.add_argument('uri', help='The URI of the resource being requested')
    parser_patch.set_defaults(func=send_delete_request)

    args = arg_parser.parse_args()
    args.cli = True

    try:
        result = args.func(args)
        if result:
            if hasattr(result, 'headers'):
                print(result.headers)
            if hasattr(result, 'content'):
                print_response(result.content)
            else:
                print_response(result)
    except requests.exceptions.HTTPError as e:
        print(e)
        print(e.response.text)


if __name__ == '__main__':
    main()
