import requests
import session
import config
import json
import api


def list_orchestrations(args):
    return api.list_saved('orchestrations', **vars(args))


def list_substrates(args):
    return api.list_saved('substrates', **vars(args))


def list_from_args(args):
    if args.object_to_list == 'datasets':
        return api.list_datasets(**vars(args))

    return api.list_saved(args.object_to_list, **vars(args))


def list_datasets(args):
    return api.list_datasets(**vars(args))


def create_dataset(args):
    return api.create_dataset(**vars(args))


if __name__ == '__main__':
    import argparse, jsbeautifier

    arg_parser = argparse.ArgumentParser(description='Conduce command line utility')
    subparsers = arg_parser.add_subparsers(help='help for subcommands')

    parser_config = subparsers.add_parser('config', help='Conduce configuration settings')
    parser_config_subparsers = parser_config.add_subparsers(help='config subcommands')

    parser_config_set = parser_config_subparsers.add_parser('set', help='Set Conduce configuration setting')
    parser_config_set.add_argument('--default-user', help='Set the default user for executing commands')
    parser_config_set.add_argument('--default-host', help='Set the default server to send commands to')
    parser_config_set.add_argument('--api-key', help='Set the default API key')
    parser_config_set.set_defaults(func=config.set_config)
    parser_config_set_subparsers = parser_config_set.add_subparsers(help='set subcommands')

    parser_config_set_api_key = parser_config_set_subparsers.add_parser('api-key', help='Set a Conduce API key')
    parser_config_set_api_key.add_argument('--user', help='The user to which the API key belongs')
    parser_config_set_api_key.add_argument('--host', help='The server on which the API key is valid')
    parser_config_set_api_key.add_argument('--key', help='The API key')
    parser_config_set_api_key.set_defaults(func=config.set_api_key)

    parser_config_get = parser_config_subparsers.add_parser('get', help='Get Conduce configuration setting')
    parser_config_get.add_argument('--default-user', help='Get the default user for executing commands', action='store_true')
    parser_config_get.add_argument('--default-host', help='Get the default server to send commands to', action='store_true')
    parser_config_get.set_defaults(func=config.get_config)
    parser_config_get_subparsers = parser_config_get.add_subparsers(help='get subcommands')

    parser_config_get_api_key = parser_config_get_subparsers.add_parser('api-key', help='Get a Conduce API key')
    parser_config_get_api_key.add_argument('--user', help='The user to which the API key belongs')
    parser_config_get_api_key.add_argument('--host', help='The server on which the API key is valid')
    parser_config_get_api_key.set_defaults(func=config.get_api_key_config)

    parser_list_orchestrations = subparsers.add_parser('list-orchestrations', help='List orchestrations owned by user')
    parser_list_orchestrations.add_argument('--user', help='The user whose orchestrations will be listed')
    parser_list_orchestrations.add_argument('--host', help='The server from which orchestrations will be listed')
    parser_list_orchestrations.add_argument('--api-key', help='The API key used to authenticate')
    parser_list_orchestrations.set_defaults(func=list_orchestrations)

    parser_list_substrates = subparsers.add_parser('list-substrates', help='List substrates owned by user')
    parser_list_substrates.add_argument('--user', help='The user whose substrates will be listed')
    parser_list_substrates.add_argument('--host', help='The server from which substrates will be listed')
    parser_list_substrates.add_argument('--api-key', help='The API key used to authenticate')
    parser_list_substrates.set_defaults(func=list_orchestrations)

    parser_config_list = subparsers.add_parser('list', help='List "objects" owned by user')
    parser_config_list.add_argument('object_to_list', help='Conduce object to list')
    parser_config_list.add_argument('--user', help='The user whose objects will be listed')
    parser_config_list.add_argument('--host', help='The server from which objects will be listed')
    parser_config_list.add_argument('--api-key', help='The API key used to authenticate')
    parser_config_list.set_defaults(func=list_from_args)

    parser_create_dataset = subparsers.add_parser('create-dataset', help='Create a Conduce dataset')
    parser_create_dataset.add_argument('name', help='The name to be given to the new dataset')
    parser_create_dataset.add_argument('--user', help='The user who owns the new dataset')
    parser_create_dataset.add_argument('--host', help='The server on which the dataset will be created')
    parser_create_dataset.add_argument('--api-key', help='The API key used to authenticate')
    parser_create_dataset.add_argument('--json', help='Optional: A well formatted Conduce entities JSON file')
    parser_create_dataset.add_argument('--csv', help='Optional: A CSV file that can be parsed as Conduce data')
    parser_create_dataset.set_defaults(func=create_dataset)

    args = arg_parser.parse_args()

    config = config.get_full_config()

    result = args.func(args)
    if result:
        if hasattr(result, 'content'):
            print jsbeautifier.beautify(result.content)
        else:
            print jsbeautifier.beautify(result)
