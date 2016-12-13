import requests
import session
import config


def list_orchestrations(args):
    return list_saved('orchestrations', args)


def list_substrates(args):
    return list_saved('substrates', args)


def list_from_args(args):
    if args.object_to_list == 'datasets':
        return list_datasets(args)

    return list_saved(args.object_to_list, args)


def list_datasets(args):
    return make_get_request("conduce/api/datasets/listv2", args)


def list_saved(thing_to_list, args):
    return make_get_request("conduce/api/%s/saved" % thing_to_list, args)


def make_get_request(uri, args):
    import jsbeautifier

    if args.host:
        host = args.host
    else:
        host = config['host']
    if args.user:
        user = args.user
    else:
        user = config['user']

    if args.api_key:
        auth = session.api_key_header(args.api_key)
    else:
        auth = session.get_session(host, user)

    if 'Authorization' in auth:
        response = requests.get('https://%s/%s' % (host, uri), headers=auth)
    else:
        response = requests.get(url, cookies=auth)
    response.raise_for_status()
    return jsbeautifier.beautify(response.content)


if __name__ == '__main__':
    import argparse

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

    parser_config_list_orchestrations = subparsers.add_parser('list-orchestrations', help='List orchestrations owned by user')
    parser_config_list_orchestrations.add_argument('--user', help='The user whose orchestrations will be listed')
    parser_config_list_orchestrations.add_argument('--host', help='The server from which orchestrations will be listed')
    parser_config_list_orchestrations.add_argument('--api-key', help='The API key used to authenticate')
    parser_config_list_orchestrations.set_defaults(func=list_orchestrations)

    parser_config_list_orchestrations = subparsers.add_parser('list-substrates', help='List substrates owned by user')
    parser_config_list_orchestrations.add_argument('--user', help='The user whose substrates will be listed')
    parser_config_list_orchestrations.add_argument('--host', help='The server from which substrates will be listed')
    parser_config_list_orchestrations.add_argument('--api-key', help='The API key used to authenticate')
    parser_config_list_orchestrations.set_defaults(func=list_orchestrations)

    parser_config_list_orchestrations = subparsers.add_parser('list', help='List "objects" owned by user')
    parser_config_list_orchestrations.add_argument('object_to_list', help='Conduce object to list')
    parser_config_list_orchestrations.add_argument('--user', help='The user whose objects will be listed')
    parser_config_list_orchestrations.add_argument('--host', help='The server from which objects will be listed')
    parser_config_list_orchestrations.add_argument('--api-key', help='The API key used to authenticate')
    parser_config_list_orchestrations.set_defaults(func=list_from_args)

    args = arg_parser.parse_args()

    config = config.get_full_config()

    result = args.func(args)
    if result:
        print result
