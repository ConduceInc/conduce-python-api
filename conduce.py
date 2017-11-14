import requests
import session
import config
import json
import api
import util
import base64


def list_from_args(args):
    object_to_list = args.object_to_list
    del vars(args)['object_to_list']

    if object_to_list.lower() == "lenses" or object_to_list.lower() == "templates":
        object_to_list = "LENS_TEMPLATE"

    return api.list_resources(object_to_list.upper().rstrip('S'), **vars(args))


def find_resource(args):
    if args.type is not None:
        resource_type = args.type

        if resource_type.lower() == "lenses" or resource_type.lower() == "templates":
            resource_type = "LENS_TEMPLATE"

        args.type = resource_type.upper().rstrip('S')

    resources = api.find_resource(**vars(args))
    if args.decode:
        if args.content == 'full':
            for resource in resources:
                if resource.get('mime', 'invalid-mime') == 'application/json':
                    resource['content'] = json.loads(resource['content'])
                elif not resource.get('mime', 'invalid-mime').startswith('text/'):
                    resource['content'] = base64.b64decode(resource['content'])

    return resources


def list_datasets(args):
    return api.list_datasets(**vars(args))


def create_dataset(args):
    response = api.create_dataset(args.name, **vars(args))

    if args.json or args.csv:
        print json.dumps(response, indent=2)
        response = util.ingest_file(response['id'], **vars(args))

    return response


def ingest_data(args):
    dataset_id = args.dataset_id
    del vars(args)['dataset_id']
    return util.ingest_file(dataset_id, **vars(args))


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
        import util
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
    return api.remove_resource(**vars(args))


def remove_dataset(args):
    return api.remove_dataset(**vars(args))


def clear_dataset(args):
    return api.clear_dataset(**vars(args))


def list_api_keys(args):
    return api.list_api_keys(**vars(args))


def create_api_key(args):
    return api.create_api_key(**vars(args))


def remove_api_key(args):
    key = args.key
    del vars(args)['key']
    return api.remove_api_key(key, **vars(args))


def set_api_key(args):
    if args.new == True:
        args.key = api.create_api_key(**vars(args))
    if args.key == None:
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
    resource_id = args.resource_id
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    api.set_public_permissions(resource_id, p['read'], p['write'], p['share'], **vars(args))


def set_team_permissions(args):
    resource_id = args.resource_id
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    api.set_team_permissions(resource_id, p['read'], p['write'], p['share'], **vars(args))


def set_group_permissions(args):
    group_id = args.group_id
    del vars(args)['group_id']
    resource_id = args.resource_id
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    api.set_group_permissions(group_id, resource_id, p['read'], p['write'], p['share'], **vars(args))


def set_user_permissions(args):
    user_id = args.user_id
    del vars(args)['user_id']
    resource_id = args.resource_id
    del vars(args)['resource_id']

    p = parse_permissions(args.permissions)

    api.set_user_permissions(user_id, resource_id, p['read'], p['write'], p['share'], **vars(args))


def send_get_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_get_request(uri, **vars(args))


def send_post_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_post_request(json.loads(args.data), uri, **vars(args))


def account_exists(args):
    email = args.email
    del vars(args)['email']

    return api.account_exists(email, **vars(args))


def get_entity(args):
    datasets = api.find_dataset(id=args.dataset_id, name=args.dataset_name, regex=args.dataset_regex, host=args.host, user=args.user, api_key=args.api_key)
    entities = []
    for dataset in datasets:
        entities.append(json.loads(api.get_entity(dataset['id'], args.entity_id, host=args.host, user=args.user, api_key=args.api_key).content))
    return entities


def main():
    import argparse
    import pkg_resources
    version = pkg_resources.require("conduce")[0].version

    arg_parser = argparse.ArgumentParser(description='Conduce command line utility\nv{}'.format(version), formatter_class=argparse.RawTextHelpFormatter)
    api_cmd_parser = argparse.ArgumentParser(add_help=False)
    api_cmd_parser.add_argument('--user', help='The user whose is making the request')
    api_cmd_parser.add_argument('--host', help='The server on which the command will run')
    api_cmd_parser.add_argument('--api-key', help='The API key used to authenticate')

    subparsers = arg_parser.add_subparsers(help='help for subcommands')

    parser_config = subparsers.add_parser('config', help='Conduce configuration settings')
    parser_config_subparsers = parser_config.add_subparsers(help='config subcommands')

    parser_config_set = parser_config_subparsers.add_parser('set', help='Set Conduce configuration setting')
    parser_config_set_subparsers = parser_config_set.add_subparsers(help='set subcommands')

    parser_config_set_default_user = parser_config_set_subparsers.add_parser('default-user', help='get the default user for executing commands')
    parser_config_set_default_user.add_argument('default_user', help='user name')
    parser_config_set_default_user.set_defaults(func=config.set_default_user)

    parser_config_set_default_host = parser_config_set_subparsers.add_parser('default-host', help='get the default server to send commands to')
    parser_config_set_default_host.add_argument('default_host', help='host')
    parser_config_set_default_host.set_defaults(func=config.set_default_host)

    parser_config_set_api_key = parser_config_set_subparsers.add_parser('api-key', help='Set a Conduce API key')
    parser_config_set_api_key.add_argument('--user', help='The user to which the API key belongs')
    parser_config_set_api_key.add_argument('--host', help='The server on which the API key is valid')
    parser_config_set_api_key.add_argument('--key', help='The API key')
    parser_config_set_api_key.add_argument('--new', help='Generate a new API key', action='store_true')
    parser_config_set_api_key.set_defaults(func=set_api_key)

    parser_config_get = parser_config_subparsers.add_parser('get', help='Get Conduce configuration setting')
    parser_config_get_subparsers = parser_config_get.add_subparsers(help='get subcommands')

    parser_config_get_default_user = parser_config_get_subparsers.add_parser('default-user', help='get the default user for executing commands')
    parser_config_get_default_user.set_defaults(func=config.get_default_user)

    parser_config_get_default_host = parser_config_get_subparsers.add_parser('default-host', help='get the default server to send commands to')
    parser_config_get_default_host.set_defaults(func=config.get_default_host)

    parser_config_get_api_key = parser_config_get_subparsers.add_parser('api-key', help='Get a Conduce API key')
    parser_config_get_api_key.add_argument('--user', help='The user to which the API key belongs')
    parser_config_get_api_key.add_argument('--host', help='The server on which the API key is valid')
    parser_config_get_api_key.set_defaults(func=config.get_api_key_config)

    parser_config_list = subparsers.add_parser('list',  parents=[api_cmd_parser], help='List resources by type')
    parser_config_list.add_argument('object_to_list', help='Conduce object to list')

    parser_config_list.set_defaults(func=list_from_args)

    parser_config_find = subparsers.add_parser('find',  parents=[api_cmd_parser], help='Find resources that match the given parameters')
    parser_config_find.add_argument('--type', help='Conduce reourse type to find')
    parser_config_find.add_argument('--name', help='The name of the dataset to query')
    parser_config_find.add_argument('--id', help='The ID of the dataset to query')
    parser_config_find.add_argument('--regex', help='An expression to match datasets and query')
    parser_config_find.add_argument('--content', help='Content to retreive: id,full,meta')
    parser_config_find.add_argument('--decode', action='store_true', help='Decode base64 and JSON for full content requests')
    parser_config_find.set_defaults(func=find_resource)

    parser_list_api_keys = subparsers.add_parser('list-api-keys', parents=[api_cmd_parser], help='List API keys for your account')
    parser_list_api_keys.set_defaults(func=list_api_keys)

    parser_create_api_key = subparsers.add_parser('create-api-key', parents=[api_cmd_parser], help='Create an API key for your account')
    parser_create_api_key.set_defaults(func=create_api_key)

    parser_remove_api_key = subparsers.add_parser('remove-api-key', parents=[api_cmd_parser], help='Delete an API key')
    parser_remove_api_key.add_argument('key', help='The key to delete')
    parser_remove_api_key.set_defaults(func=remove_api_key)

    parser_create_dataset = subparsers.add_parser('create-dataset', parents=[api_cmd_parser], help='Create a Conduce dataset')
    parser_create_dataset.add_argument('name', help='The name to be given to the new dataset')
    parser_create_dataset.add_argument('--json', help='Optional: A well formatted Conduce entities JSON file')
    parser_create_dataset.add_argument('--csv', help='Optional: A CSV file that can be parsed as Conduce data')
    parser_create_dataset.add_argument('--generate-ids', help='Set this flag if the data does not contain an ID field', action='store_true')
    parser_create_dataset.add_argument('--kind', help='Use this value as the kind for all entities')
    parser_create_dataset.add_argument('--answer-yes', help='Set this flag to answer yes at all prompts', action='store_true')
    parser_create_dataset.add_argument('--debug', help='Get better information about errors', action='store_true')
    parser_create_dataset.set_defaults(func=create_dataset)

    parser_ingest_data = subparsers.add_parser('ingest-data', parents=[api_cmd_parser], help='Ingest data to a Conduce dataset')
    parser_ingest_data.add_argument('dataset_id', help='The ID of the dataset to receive the entities')
    parser_ingest_data.add_argument('--json', help='Optional: A well formatted Conduce entities JSON file')
    parser_ingest_data.add_argument('--csv', help='Optional: A CSV file that can be parsed as Conduce data')
    parser_ingest_data.add_argument('--generate-ids', help='Set this flag if the data does not contain an ID field', action='store_true')
    parser_ingest_data.add_argument('--kind', help='Use this value as the kind for all entities')
    parser_ingest_data.add_argument('--answer-yes', help='Set this flag to answer yes at all prompts', action='store_true')
    parser_ingest_data.add_argument('--debug', help='Get better information about errors', action='store_true')
    parser_ingest_data.set_defaults(func=ingest_data)

    parser_get_entity = subparsers.add_parser('get-entity', parents=[api_cmd_parser], help='Get the latest state of a Conduce entity')
    parser_get_entity.add_argument('entity_id', help='The ID of the entity to retrieve')
    parser_get_entity.add_argument('--dataset-name', help='The name of the dataset to query')
    parser_get_entity.add_argument('--dataset-id', help='The ID of the dataset to query')
    parser_get_entity.add_argument('--dataset-regex', help='An expression to match datasets and query')
    parser_get_entity.set_defaults(func=get_entity)

    parser_team = subparsers.add_parser('team', help='Conduce team operations')
    parser_team_subparsers = parser_team.add_subparsers(help='team subcommands')

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
    parser_group_subparsers = parser_group.add_subparsers(help='group subcommands')

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

    parser_account_exists = subparsers.add_parser('account-exists', parents=[api_cmd_parser], help='')
    parser_account_exists.add_argument('email', help='The email address to check')
    parser_account_exists.set_defaults(func=account_exists)

    parser_set_generic_data = subparsers.add_parser('set-generic-data',  parents=[api_cmd_parser], help='Add generic data to Conduce dataset')
    parser_set_generic_data.add_argument('--json', help='The data to be consumed')
    parser_set_generic_data.add_argument('--csv', help='The data to be consumed')
    parser_set_generic_data.add_argument('--dataset-id', help='The ID of the dataset to send data to')
    parser_set_generic_data.add_argument('--key', help='Unique name with which to lookup data')
    parser_set_generic_data.set_defaults(func=set_generic_data)

    parser_get_generic_data = subparsers.add_parser('get-generic-data', parents=[api_cmd_parser], help='Retrieve generic data from Conduce dataset')
    parser_get_generic_data.add_argument('--dataset-id', help='The ID of the dataset to get the data from')
    parser_get_generic_data.add_argument('--key', help='Unique ID of entity to retrieve data from')
    parser_get_generic_data.set_defaults(func=get_generic_data)

    parser_get_generic_data = subparsers.add_parser('clear-dataset', parents=[api_cmd_parser], help='Remove all records from a Conduce dataset')
    parser_get_generic_data.add_argument('--id', help='The ID of the dataset to be cleared')
    parser_get_generic_data.add_argument('--name', help='The name of the dataset to be cleared')
    parser_get_generic_data.add_argument('--regex', help='clear datasets that match the regular expression')
    parser_get_generic_data.add_argument('--all', help='clear all matching datasets', action='store_true')
    parser_get_generic_data.set_defaults(func=clear_dataset)

    parser_get_generic_data = subparsers.add_parser('remove-dataset', parents=[api_cmd_parser], help='Remove a dataset from Conduce')
    parser_get_generic_data.add_argument('--id', help='The ID of the dataset to be removed')
    parser_get_generic_data.add_argument('--name', help='The name of the dataset to be removed')
    parser_get_generic_data.add_argument('--regex', help='Remove datasets that match the regular expression')
    parser_get_generic_data.add_argument('--all', help='Remove all matching datasets', action='store_true')
    parser_get_generic_data.set_defaults(func=remove_dataset)

    parser_get_generic_data = subparsers.add_parser('remove', parents=[api_cmd_parser], help='Remove a resource from Conduce')
    parser_get_generic_data.add_argument('--id', help='The ID of the resource to be removed')
    parser_get_generic_data.add_argument('--name', help='The name of the resource to be removed')
    parser_get_generic_data.add_argument('--regex', help='Remove resources that match the regular expression')
    parser_get_generic_data.add_argument('--all', help='Remove all matching resources', action='store_true')
    parser_get_generic_data.set_defaults(func=remove_resource)

    parser_permissions = subparsers.add_parser('permissions', help='Conduce permissions operations')
    parser_permissions_subparsers = parser_permissions.add_subparsers(help='permissions subcommands')

    parser_set_owner = parser_permissions_subparsers.add_parser('set-owner', parents=[api_cmd_parser], help='Set the owner of this resource')
    parser_set_owner.add_argument('team_id', help='The UUID of the team to which the user belongs')
    parser_set_owner.add_argument('resource_id', help='The UUID of the resource being modified')
    parser_set_owner.set_defaults(func=set_owner)

    parser_list_permissions = parser_permissions_subparsers.add_parser('list', parents=[api_cmd_parser], help='List permissions of a resource')
    parser_list_permissions.add_argument('resource_id', help='The UUID of the resource to be listed')
    parser_list_permissions.set_defaults(func=list_permissions)

    parser_set_permissions = parser_permissions_subparsers.add_parser('set', parents=[api_cmd_parser], help='Set permissions of a resource')
    parser_set_permissions.add_argument('permissions', help='The permissions to enable [r|w|s]')
    parser_set_permissions.add_argument('resource_id', help='The UUID of the resource to be listed')
    parser_set_permissions_subparsers = parser_set_permissions.add_subparsers(help='set permissions subcommands')

    parser_set_public_permissions = parser_set_permissions_subparsers.add_parser(
        'public', parents=[api_cmd_parser], help='Set public permissions of a resource')
    parser_set_public_permissions.set_defaults(func=set_public_permissions)

    parser_set_team_permissions = parser_set_permissions_subparsers.add_parser('team', parents=[api_cmd_parser], help='Set team permissions of a resource')
    parser_set_team_permissions.set_defaults(func=set_team_permissions)

    parser_set_group_permissions = parser_set_permissions_subparsers.add_parser('group', parents=[api_cmd_parser], help='Set team permissions of a resource')
    parser_set_group_permissions.add_argument('group_id', help='The group UUID')
    parser_set_group_permissions.set_defaults(func=set_group_permissions)

    parser_set_user_permissions = parser_set_permissions_subparsers.add_parser('user', parents=[api_cmd_parser], help='Set team permissions of a resource')
    parser_set_user_permissions.add_argument('user_id', help='The user UUID')
    parser_set_user_permissions.set_defaults(func=set_user_permissions)

    parser_get = subparsers.add_parser('get',  parents=[api_cmd_parser], help='Make an arbitrary get request')
    parser_get.add_argument('uri', help='The URI of the resource being requested')
    parser_get.set_defaults(func=send_get_request)

    parser_post = subparsers.add_parser('post', parents=[api_cmd_parser], help='Make an arbitrary post request')
    parser_post.add_argument('uri', help='The URI of the resource being requested')
    parser_post.add_argument('data', help='The data being posted')
    parser_post.set_defaults(func=send_post_request)

    args = arg_parser.parse_args()

    user_config = config.get_full_config()

    try:
        result = args.func(args)
        if result:
            if hasattr(result, 'headers'):
                print result.headers
            if hasattr(result, 'content'):
                if isinstance(result.content, str):
                    try:
                        print json.dumps(json.loads(result.content), indent=2)
                    except:
                        print result.content
                else:
                    try:
                        print json.dumps(result.content, indent=2)
                    except:
                        print result.content
            else:
                if isinstance(result, str):
                    try:
                        print json.dumps(json.loads(result), indent=2)
                    except:
                        print result
                else:
                    try:
                        print json.dumps(result, indent=2)
                    except:
                        print result
    except requests.exceptions.HTTPError as e:
        print e
        print e.response.text


if __name__ == '__main__':
    main()
