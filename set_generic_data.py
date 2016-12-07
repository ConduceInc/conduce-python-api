import json
import copy
from add_entities import add_entities_dict
from util import csv_to_json

import base64
from dateutil import parser

def set_generic_data(host, api_key, dataset_id, data):
    timestamp = 0
    location = {}
    location["x"] = 0
    location["y"] = 0
    location["z"] = 0

    attributes = [{
        "key": "json_data",
        "type": "STRING",
        #"str_value": base64.b64encode(data),
        "str_value": data,
    }]

    remove_entity = {
        "identity": args.key,
        "kind": 'raw_data',
        "timestamp_ms": timestamp,
        "path": [location],
        "removed": True,
    }

    remove_entities = []
    remove_entities.append(remove_entity)
    add_entities_dict(host, api_key, dataset_id, remove_entities)

    entity = {
        "identity": args.key,
        "kind": 'raw_data',
        "timestamp_ms": timestamp,
        "path": [location],
        "attrs": attributes,
    }

    entities = []
    entities.append(entity)

    return add_entities_dict(host, api_key, dataset_id, entities)



if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Send generic data to Conduce.')
    arg_parser.add_argument('filename', help='The file to be consumed')
    arg_parser.add_argument('--dataset-id', help='The ID of the dataset to send data to')
    arg_parser.add_argument('--api-key', help='The API key used to authenticate to the server')
    arg_parser.add_argument('--host', help='The Conduce server to receive the data')
    arg_parser.add_argument('--key', help='Unique name with which to lookup data')

    args = arg_parser.parse_args()

    if args.api_key is None:
        raise "api-key is a required argument"

    if args.dataset_id is None:
        raise "dataset-id is a required argument"

    if args.host is None:
        args.host = 'dev-app.conduce.com'

    if args.key is None:
        raise "Lookup key is required"

    if args.filename.endswith('.csv'):
        json_data = csv_to_json(args.filename)
        data = json.dumps(json_data);
    else:
        with open(args.filename) as data_file:
            data = data_file.readlines()

    if not data is None:
        print set_generic_data(args.host, args.api_key, args.dataset_id, data)
    else:
        print "Could not parse input file"
