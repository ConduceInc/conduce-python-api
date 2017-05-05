import yaml, os


config_file_path = os.path.join(os.path.expanduser('~'), '.conduceconfig')


def open_config():
    config = None
    if not os.path.isfile(config_file_path):
        with open(config_file_path, 'w') as config_file:
            print 'creating new configuration'
            new_config = {'default-host':'dev-app.conduce.com'}
            yaml.dump(new_config, config_file, default_flow_style=False)

    with open(config_file_path, 'r') as config_file:
        config = yaml.load(config_file)
        if not config:
            config = {}

    return config


def save_config(config):
    with open(config_file_path, 'w') as config_file:
        yaml.dump(config, config_file, default_flow_style=False)


def set_default_user(args):
    config = open_config()

    if args.default_user:
        config['default-user'] = args.default_user
        print config['default-user']

    save_config(config)


def set_default_host(args):
    config = open_config()

    if args.default_host:
        config['default-host'] = args.default_host
        print config['default-host']

    save_config(config)


def get_full_config():
    return open_config()


def get_env_from_host(host):
    if 'stg' == host:
        return 'stg-app'
    elif 'dev' == host:
        return 'dev-app'
    elif 'prd' == host:
        return 'prd-app'

    return host.split('.')[0]


def set_api_key(args):
    config = open_config()

    if not args.user:
        args.user = config['default-user']
    if not args.host:
        raise Exception('No host specified for API key')
    if not args.key:
        raise Exception('No API key specified')

    if not args.user in config:
        config[args.user] = {'api-keys':{'dev-app':"", 'stg-app':"", 'prd-app':""}}
    config[args.user]['api-keys'][get_env_from_host(args.host)] = args.key

    save_config(config)


def get_api_key_config(args):
    config = open_config()
    if not args.user:
        args.user = config['default-user']
    if not args.host:
        args.host = config['default-host']


    if get_env_from_host(args.host) in config[args.user]['api-keys']:
        key = config[args.user]['api-keys'][get_env_from_host(args.host)]
        return '{{ "user": "{}", "host": "{}", "api-key": "{}" }}'.format(args.user, args.host, key)


def get_api_key(user, host):
    config = open_config()
    if get_env_from_host(host) in config[user]['api-keys']:
        return config[user]['api-keys'][get_env_from_host(host)]


def get_default_user(args):
    config = open_config()
    if not config:
        return "Error opening configuration file"

    return  config['default-user']


def get_default_host(args):
    config = open_config()
    if not config:
        return "Error opening configuration file"

    return  config['default-host']


def config(command):
    if command[0] == 'set':
        set_config(command[1:])
    elif command[0] == 'get':
        get_config(command[1:])
    else:
        raise Exception("Invalid command", command[0])


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Conduce configuration settings')
    arg_parser.add_argument('command', nargs='+', help='Command to execute')

    args = arg_parser.parse_args()

    config(command)
