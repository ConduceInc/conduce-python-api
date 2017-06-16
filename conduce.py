import requests
import session
import config
import json
import api


def list_from_args(args):
    object_to_list = args.object_to_list
    del vars(args)['object_to_list']

    return api.list_object(object_to_list, **vars(args))


def list_datasets(args):
    return api.list_datasets(**vars(args))


def create_dataset(args):
    return api.create_dataset(args.name, **vars(args))


def set_generic_data(args):
    if args.csv:
        import util
        data = util.csv_to_json(args.csv)
    elif args.json:
        data = args.json

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


def remove_dataset(args):
    return api.remove_dataset(**vars(args))


def set_api_key(args):
    if args.new == True:
        args.key = api.create_api_key(**vars(args))
    if args.key == None:
        raise ValueError('An API must either be provided with the --key argument or you must generate a new key with --new')
    config.set_api_key(args)
    return "API key set for {} on {}".format(args.user, args.host)


def send_get_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_get_request(uri, **vars(args))


def send_post_request(args):
    uri = args.uri
    del vars(args)['uri']

    return api.make_post_request(json.loads(args.data), uri, **vars(args))


def main():
    import argparse

    arg_parser = argparse.ArgumentParser(description='Conduce command line utility')
    # TODO: figure out how to propagate these arguments to subcommands
    #arg_parser.add_argument('--user', help='The user whose objects will be listed')
    #arg_parser.add_argument('--host', help='The server from which objects will be listed')
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

    parser_config_list = subparsers.add_parser('list', help='List "objects" owned by user')
    parser_config_list.add_argument('object_to_list', help='Conduce object to list')
    parser_config_list.add_argument('--user', help='The user whose objects will be listed')
    parser_config_list.add_argument('--host', help='The server from which objects will be listed')
    parser_config_list.add_argument('--api-key', help='The API key used to authenticate')
    parser_config_list.set_defaults(func=list_from_args)

    parser_create_dataset = subparsers.add_parser('create-dataset', help='Create a Conduce dataset')
    parser_create_dataset.add_argument('name', help='The name to be given to the new dataset')
    parser_create_dataset.add_argument('--api-key', help='The API key used to authenticate')
    parser_create_dataset.add_argument('--json', help='Optional: A well formatted Conduce entities JSON file')
    parser_create_dataset.add_argument('--csv', help='Optional: A CSV file that can be parsed as Conduce data')
    parser_create_dataset.set_defaults(func=create_dataset)

    parser_set_generic_data = subparsers.add_parser('set-generic-data', help='Add generic data to Conduce dataset')
    parser_set_generic_data.add_argument('--json', help='The data to be consumed')
    parser_set_generic_data.add_argument('--csv', help='The data to be consumed')
    parser_set_generic_data.add_argument('--user', help='The user who owns the data')
    parser_set_generic_data.add_argument('--host', help='The server to receive the data')
    parser_set_generic_data.add_argument('--api-key', help='The API key used to authenticate to the server')
    parser_set_generic_data.add_argument('--dataset-id', help='The ID of the dataset to send data to')
    parser_set_generic_data.add_argument('--key', help='Unique name with which to lookup data')
    parser_set_generic_data.set_defaults(func=set_generic_data)

    parser_get_generic_data = subparsers.add_parser('get-generic-data', help='Retrieve generic data from Conduce dataset')
    parser_get_generic_data.add_argument('--user', help='The user who owns the data')
    parser_get_generic_data.add_argument('--host', help='The server on which the data resides')
    parser_get_generic_data.add_argument('--api-key', help='The API key used to authenticate to the server')
    parser_get_generic_data.add_argument('--dataset-id', help='The ID of the dataset to get the data from')
    parser_get_generic_data.add_argument('--key', help='Unique ID of entity to retrieve data from')
    parser_get_generic_data.set_defaults(func=get_generic_data)

    parser_get_generic_data = subparsers.add_parser('remove-dataset', help='Remove a dataset from Conduce')
    parser_get_generic_data.add_argument('--user', help='The user who owns the data')
    parser_get_generic_data.add_argument('--host', help='The server on which the data resides')
    parser_get_generic_data.add_argument('--api-key', help='The API key used to authenticate to the server')
    parser_get_generic_data.add_argument('--id', help='The ID of the dataset to be removed')
    parser_get_generic_data.add_argument('--name', help='The name of the dataset to be removed')
    parser_get_generic_data.add_argument('--regex', help='Remove datasets that match the regular expression')
    parser_get_generic_data.add_argument('--all', help='Remove all matching datasets', action='store_true')
    parser_get_generic_data.set_defaults(func=remove_dataset)

    parser_get = subparsers.add_parser('get', help='Make an arbitrary get request')
    parser_get.add_argument('uri', help='The URI of the resource being requested')
    parser_get.add_argument('--user', help='The user to which the API key belongs')
    parser_get.add_argument('--host', help='The server on which the API key is valid')
    parser_get.set_defaults(func=send_get_request)

    parser_post = subparsers.add_parser('post', help='Make an arbitrary post request')
    parser_post.add_argument('uri', help='The URI of the resource being requested')
    parser_post.add_argument('data', help='The data being posted')
    parser_post.add_argument('--user', help='The user to which the API key belongs')
    parser_post.add_argument('--host', help='The server on which the API key is valid')
    parser_post.set_defaults(func=send_post_request)

    args = arg_parser.parse_args()

    user_config = config.get_full_config()

    try:
        result = args.func(args)
        if result:
            if hasattr(result, 'headers'):
                print result.headers
            if hasattr(result, 'content'):
                try:
                    print json.dumps(json.loads(result.content), indent=2)
                except:
                    print result.content
            else:
                try:
                    print json.dumps(json.loads(result), indent=2)
                except:
                    print result
    except requests.exceptions.HTTPError as e:
        print e
        print e.response.text

if __name__ == '__main__':
    main()
