import httplib,urllib,json

import csv
import json
import os

def create_dataset(host, api_key, name):
    connection = httplib.HTTPSConnection(host)

    if host is None:
        raise "A hostname is required"
    if api_key is None:
        raise "An API key is required"
    if name is None:
        raise "A dataset name is required"

    bearer = 'Bearer %s' % api_key
    headers = {'Content-type': 'application/json', 'Authorization': bearer}
    substrate =  {
            'x_min': -180.0, 'x_max': 180.0, 'y_min': -90.0, 'y_max': 90.0,
            'z_min': -1.0, 'z_max': 1.0, 't_min': -100000, 't_max': 1956529423000,
            'tile_levels': 1, 'x_tiles': 2, 'y_tiles': 2, 'z_tiles': 1, 't_tiles': 30, 'time_levels': 1
            }
    request = {'name': name}
    params = json.dumps(request)
    connection.request("POST", "/conduce/api/datasets/createv2", params, headers)
    response = connection.getresponse()
    response_content = response.read()
    connection.close()
    return response.status, response.reason, response_content


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Create a Conduce dataset')
    arg_parser.add_argument('--host', help='The field to sort on', default='dev-app.conduce.com')
    arg_parser.add_argument('--api-key', help='API authentication')
    arg_parser.add_argument('-n', '--name', help='Name of new dataset')

    args = arg_parser.parse_args()

    if args.api_key is None:
        print "An API key is required"
        exit(1)

    if args.name is None:
        print "Please specify a dataset name"
        exit(1)

    print create_dataset(args.host, args.api_key, args.name)
