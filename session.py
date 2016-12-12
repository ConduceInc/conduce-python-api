import requests, getpass
import os
import pickle


def get_session(host, email):
    cookies = None
    cookie_file_dir = os.path.join(os.path.expanduser('~'), '.conduce', host, email)
    if not os.path.exists(cookie_file_dir):
        os.makedirs(cookie_file_dir)
    cookie_file_path = os.path.join(cookie_file_dir, 'session-cookie')

    try:
        with open(cookie_file_path, 'r') as cookie_file:
            cookies = requests.utils.cookiejar_from_dict(pickle.load(cookie_file))
    except:
        pass

    if cookies is None or not validate_session(host, cookies):
        print
        print "user: %s" % email
        cookies = login(host, email, getpass.getpass())
        with open(cookie_file_path, 'w') as cookie_file:
            pickle.dump(requests.utils.dict_from_cookiejar(cookies), cookie_file)

    return cookies


def validate_session(host, cookies):
    response = requests.get("https://%s/api/validate-session" % host, cookies=cookies)
    if response.status_code == 401:
        print "Session expired"
        cookies = None
    elif response.status_code != requests.codes.ok:
        response.raise_for_status()
    return cookies


def login(host, email, password):
    if email is None:
        raise Exception('No user provided for login')
    if password is None:
        raise Exception('No password provided for login')

    response = requests.post("https://%s/api/login" % host, json={
        "email": email,
        "password": password,
        "keep": False,
    })
    response.raise_for_status()
    return response.cookies


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='List Conduce substrates')
    arg_parser.add_argument('--host', help='The field to sort on', default='dev-app.conduce.com')
    arg_parser.add_argument('--user', help='Email address of user making request')

    args = arg_parser.parse_args()

    email = args.user
    if email is None:
        email = "dhl-dev@conduce.com"

    print get_session(args.host, email)
