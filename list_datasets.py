import httplib,urllib,json

def list_datasets(host, api_key):
    connection = httplib.HTTPSConnection(host)

    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Bearer ' + api_key
    }

    connection.request("GET", "/conduce/api/datasets/listv2", "", headers)
    response = connection.getresponse()
    response_stuff = response.status, response.reason, response.read()
    connection.close()
    return response_stuff


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='List Conduce datasets')
    arg_parser.add_argument('--host', help='The field to sort on', default='dev-app.conduce.com')
    arg_parser.add_argument('--api-key', help='API authentication')

    args = arg_parser.parse_args()

    if args.api_key is None:
        print "An API key is required"
        exit(1)

    print list_datasets(args.host, args.api_key)
