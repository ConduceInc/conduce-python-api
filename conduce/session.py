from __future__ import print_function
from __future__ import absolute_import
import requests
import getpass
import os
import pickle
from . import config


def api_key_header(api_key):
    if not api_key:
        return None

    return {'Authorization': 'Bearer {}'.format(api_key)}


def get_session(host, email, password, verify=True):
    if password is None:
        api_key = config.get_api_key(email, host)
        if api_key:
            return api_key_header(api_key)

    cookies = None
    cookie_file_dir = os.path.join(os.path.expanduser('~'), '.conduce', host, email)
    if not os.path.exists(cookie_file_dir):
        os.makedirs(cookie_file_dir)
    cookie_file_path = os.path.join(cookie_file_dir, 'session-cookie')

    try:
        with open(cookie_file_path, 'rb') as cookie_file:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(cookie_file))
    except:
        pass

    if cookies is None or not validate_session(host, cookies, verify):
        if password is None:
            print()
            print("host: {}".format(host))
            print("user: {}".format(email))
            password = getpass.getpass()

        cookies = login(host, email, password, verify)
        with open(cookie_file_path, 'wb') as cookie_file:
            pickle.dump(requests.utils.dict_from_cookiejar(cookies), cookie_file)

    return cookies


def validate_session(host, cookies, verify):
    response = requests.get("https://{}/conduce/api/v1/user/validate-session".format(host), cookies=cookies, verify=verify)
    if response.status_code == 401:
        print("Session expired")
        cookies = None
    elif response.status_code != requests.codes.ok:
        response.raise_for_status()
    return cookies


def login(host, email, password, verify):
    if email is None:
        raise Exception('No user provided for login')
    if password is None:
        raise Exception('No password provided for login')

    response = requests.post("https://{}/conduce/api/v1/user/login".format(host), json={
        "email": email,
        "password": password,
        "keep": False,
    }, verify=verify)
    response.raise_for_status()
    return response.cookies


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Get Conduce session')
    arg_parser.add_argument('--host', help='The field to sort on', default='dev-app.conduce.com')
    arg_parser.add_argument('--user', help='Email address of user making request')
    arg_parser.add_argument('--password', help='The password of the user making the request')
    arg_parser.add_argument('--api-key', help='API key used to authenticate')
    arg_parser.add_argument('--no-verify', action='store_true', help='If passed, the SSL certificate of the host will not be verified')

    args = arg_parser.parse_args()

    email = args.user
    if email is None:
        email = "dhl-dev@conduce.com"

    if args.no_verify:
        verify = False
    else:
        verify = True

    print(get_session(args.host, email, args.password, verify))
