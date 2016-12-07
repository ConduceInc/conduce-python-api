import httplib,urllib
import requests
import json
import time

def get_entity(host, api_key, dataset_id, entity_id):
    authStr = 'Bearer ' + api_key
    URI = '/conduce/api/datasets/entity/' + dataset_id + '/' + entity_id
    headers = {
        'Authorization': authStr,
        'Content-type': 'application/json',
    }

    connection = httplib.HTTPSConnection(host)
    connection.request("GET", URI, None, headers)
    response = connection.getresponse()
    response_content = response.read()
    response_stuff = response.status, response.reason, response_content
    connection.close()

    return response_content


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Add data to a Conduce dataset')
    arg_parser.add_argument('--host', help='The field to sort on', default='dev-app.conduce.com')
    arg_parser.add_argument('--api-key', help='API authentication')
    arg_parser.add_argument('-d', '--dataset-id', help='ID of dataset being updated')
    arg_parser.add_argument('-k', '--key', help='ID of entity to retrieve')

    args = arg_parser.parse_args()

    if args.api_key is None:
        print "An API key is required"
        exit(1)

    if args.dataset_id is None:
        print "Please specify a dataset ID"
        exit(1)

    if args.key is None:
        print "Please specify an entity ID"
        exit(1)

    print get_entity(args.host, args.api_key, args.dataset_id, args.key)
