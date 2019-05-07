from __future__ import print_function
import sys
sys.path.append('..')

import api
import util
import acl
import json


def create_world_cities(args):
    kwargs = vars(args)
    kwargs['tags'] = ['conduce', 'getting-started']
    print("Creating dataset")
    dataset_meta = api.create_dataset('world-cities-data', **kwargs)
    print("Ingesting data from CSV")
    util.ingest_file(dataset_meta['id'], csv='simplemaps-worldcities-basic.csv', kind='city', answer_yes=True, generate_ids=True, **kwargs)
    api.set_public_permissions(dataset_meta['id'], True, False, False, **kwargs)

    with open('world-cities-lens.json', 'rb') as content_stream:
        print("Creating dot lens")
        content = json.load(content_stream)
        content['dataset_id'] = dataset_meta['id']
        lens_meta = api.create_template('world-cities', content, **kwargs)
        api.set_public_permissions(lens_meta['id'], True, False, False, **kwargs)

    with open('world-cities-heat.json', 'rb') as content_stream:
        print("Creating heatmap lens")
        content = json.load(content_stream)
        content['dataset_id'] = dataset_meta['id']
        lens_meta = api.create_template('world-cities-heat', content, **kwargs)
        api.set_public_permissions(lens_meta['id'], True, False, False, **kwargs)

    print("Done.")


def main():
    import argparse

    arg_parser = argparse.ArgumentParser(description='Add the world-cities lens to an environment', formatter_class=argparse.RawTextHelpFormatter)

    arg_parser.add_argument('--user', help='The user whose is making the request')
    arg_parser.add_argument('--host', help='The server on which the command will run')
    arg_parser.add_argument('--api-key', help='The API key used to authenticate')
    arg_parser.add_argument('--no-verify', action='store_true', help='If passed, the SSL certificate of the host will not be verified')

    args = arg_parser.parse_args()

    create_world_cities(args)


if __name__ == '__main__':
    main()
