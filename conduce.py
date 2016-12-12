import requests
import session
import config


def list_orchestrations(args):
    if args.host:
        host = args.host
    else:
        host = config['host']
    if args.user:
        user = args.user
    else:
        user = config['user']

    return list_thing(host, 'orchestrations', session.get_session(host, user))


def list_substrates(args):
    if args.host:
        host = args.host
    else:
        host = config['host']
    if args.user:
        user = args.user
    else:
        user = config['user']

    return list_thing(host, 'substrates', session.get_session(host, user))


def list_from_args(args):
    if args.host:
        host = args.host
    else:
        host = config['host']
    if args.user:
        user = args.user
    else:
        user = config['user']

    return list_thing(host, args.object_to_list, session.get_session(host, user))


def list_thing(host, thing_to_list, cookies):
    import jsbeautifier
    response = requests.get("https://%s/conduce/api/%s/saved" % (host, thing_to_list), cookies=cookies)
    response.raise_for_status()
    return jsbeautifier.beautify(response.content)


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='List Conduce substrates')
    subparsers = arg_parser.add_subparsers(help='help for subcommands')

    parser_config = subparsers.add_parser('config', help='Conduce configuration settings')
    parser_config_subparsers = parser_config.add_subparsers(help='config subcommands')

    parser_config_set = parser_config_subparsers.add_parser('set', help='Set Conduce configuration setting')
    parser_config_set.add_argument('--default-user', help='Set the default user for executing commands')
    parser_config_set.add_argument('--default-host', help='Set the default server to send commands to')
    parser_config_set.set_defaults(func=config.set_config)

    parser_config_get = parser_config_subparsers.add_parser('get', help='Get Conduce configuration setting')
    parser_config_get.add_argument('--default-user', help='Get the default user for executing commands', action='store_true')
    parser_config_get.add_argument('--default-host', help='Get the default server to send commands to', action='store_true')
    parser_config_get.set_defaults(func=config.get_config)

    parser_config_list_orchestrations = subparsers.add_parser('list-orchestrations', help='List orchestrations owned by user')
    parser_config_list_orchestrations.add_argument('--user', help='The user whose orchestrations will be listed')
    parser_config_list_orchestrations.add_argument('--host', help='The server from which orchestrations will be listed')
    parser_config_list_orchestrations.set_defaults(func=list_orchestrations)

    parser_config_list_orchestrations = subparsers.add_parser('list-substrates', help='List substrates owned by user')
    parser_config_list_orchestrations.add_argument('--user', help='The user whose substrates will be listed')
    parser_config_list_orchestrations.add_argument('--host', help='The server from which substrates will be listed')
    parser_config_list_orchestrations.set_defaults(func=list_orchestrations)

    parser_config_list_orchestrations = subparsers.add_parser('list', help='List "objects" owned by user')
    parser_config_list_orchestrations.add_argument('object_to_list', help='Conduce object to list')
    parser_config_list_orchestrations.add_argument('--user', help='The user whose objects will be listed')
    parser_config_list_orchestrations.add_argument('--host', help='The server from which objects will be listed')
    parser_config_list_orchestrations.set_defaults(func=list_from_args)

    args = arg_parser.parse_args()

    config = config.get_full_config()

    result = args.func(args)
    if result:
        print result
