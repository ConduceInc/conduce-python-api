import httplib,urllib
import requests
import json
import time
from get_entity import get_entity

def get_generic_data(host, api_key, dataset_id, entity_id):
    response_content = get_entity(host, api_key, dataset_id, entity_id)

    json_response = json.loads(response_content)
    return json.loads(json_response[0]['attrs'][0]['str_value'])


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

    print get_generic_data(args.host, args.api_key, args.dataset_id, args.key)
