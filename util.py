from __future__ import print_function
from __future__ import absolute_import
import csv
import json
import os
import uuid
import re
from dateutil import parser
import copy
from . import api
import pytz
import math
import sys


def get_dataset_id(dataset_name, **kwargs):
    datasets = api.list_datasets(**kwargs)
    for dataset in datasets:
        if dataset['name'] == dataset_name:
            return dataset['id']

    return None


def walk_up_find(search_path, start_dir=os.getcwd()):
    cwd = start_dir
    while True:
        fullpath = os.path.join(cwd, search_path)
        if os.path.exists(fullpath):
            return fullpath
        if cwd == '/' or cwd == '' or cwd == ' ':
            break
        cwd = os.path.dirname(cwd)

    print(search_path, "not found")
    return None


def format_mac_address(mac_address):
    return re.sub('[:-]', '', mac_address).upper().strip()


def datetime_to_timestamp_ms(dt):
    tz_naive = dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None
    EPOCH = parser.parse("1970-01-01T00:00:00.000+0000", ignoretz=tz_naive)
    return int((dt - EPOCH).total_seconds() * 1000)


def string_to_timestamp_ms(datetime_string, ignoretz=True, tz=None):
    try:
        return int(datetime_string)
    except Exception as e:
        pass

    try:
        return float(datetime_string) * 1000
    except Exception as e:
        pass

    if tz is not None:
        ignoretz = False

    try:
        timestamp = parser.parse(datetime_string, ignoretz=ignoretz)
        if tz is not None:
            timestamp = timestamp.replace(tzinfo=pytz.timezone(tz))
        return datetime_to_timestamp_ms(timestamp)
    except ValueError as e:
        print('Could not parse datetime string:', datetime_string)
        raise e


def get_csv_reader(infile, delimiter):
    if len(delimiter) > 1:
        try:
            dialect = csv.Sniffer().sniff(infile.readline(), delimiters=delimiter)
            infile.seek(0)
            return csv.DictReader(infile, dialect=dialect)
        except Exception as e:
            print('{} (using default)'.format(str(e)))
            infile.seek(0)
            return csv.DictReader(infile)
    else:
        return csv.DictReader(infile, delimiter=delimiter)


def csv_to_json(infile, outfile=None, toStdout=False, **kwargs):
    delimiter = ';,'
    if 'delimiter' in kwargs:
        delimiter = kwargs['delimiter']

    if hasattr(infile, 'read'):
        reader = get_csv_reader(infile, delimiter)
        out = json.dumps([row for row in reader])
    else:
        with open(infile, "r") as f:
            reader = get_csv_reader(f, delimiter)
            out = json.dumps([row for row in reader])
    if out is None:
        raise RuntimeError("No JSON output. Try again.")
    else:
        if toStdout is True:
            print(out)
            print()
        if outfile is not None:
            with open(outfile, "w") as output_file:
                json.dump(out, output_file)

    return json.loads(out)


def get_id_score(key, value):
    key = key.lower()
    score = 0
    if key == 'identity' or key == 'id':
        score += 1000
    if key.startswith('id_') or key.startswith('id '):
        score += 100
    if key.endswith(' id') or key.endswith('_id'):
        score += 100
    try:
        if float.is_integer(float(value)):
            score += 100
            if '.' not in value:
                score += 300
    except:
        pass
    try:
        uuid.UUID(value)
        score += 500
    except:
        pass
    if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", unicode(value.lower())):
        score += 400

    return score


def get_kind_score(key, value):
    key = key.lower()
    score = 0
    if key == 'kind' or key == 'type' or key == 'category':
        score += 1000

    return score


def get_timestamp_score(key, value):
    key = key.lower()
    score = 0
    if key == 'timestamp_ms':
        score += 1000
    if key.startswith('timestamp'):
        score += 800
    if 'time' in key:
        score += 500
    if key.startswith('start'):
        score += 200

    try:
        float(value)
        return score
    except:
        pass

    return 0


def get_endtime_score(key, value):
    key = key.lower()
    score = 0
    if key == 'endtime_ms':
        score += 1000
    if key.startswith('endtime'):
        score += 800
    if 'time' in key and 'end' in key:
        score += 500
    if key.startswith('end'):
        score += 200

    try:
        float(value)
        return score
    except:
        pass

    return 0


def get_x_score(key, value):
    key = key.lower()
    score = 0
    if key == 'x' or key == 'longitude' or key == 'lon' or key == 'lng':
        score += 1000
    if 'longitude' in key:
        score += 500

    try:
        float(value)
        return score
    except:
        pass

    return 0


def get_y_score(key, value):
    key = key.lower()
    score = 0
    if key == 'y' or key == 'latitude' or key == 'lat':
        score += 1000
    if 'latitude' in key:
        score += 500

    try:
        float(value)
        return score
    except:
        pass

    return 0


def get_z_score(key, value):
    key = key.lower()
    score = 0
    if key == 'z' or key == 'height' or key == 'depth' or key == 'altitude':
        score += 1000
    if key == 'alt':
        score += 100

    try:
        float(value)
        return score
    except:
        pass

    return 0


def get_default(field):
    if field == 'identity':
        return str(uuid.uuid4())
    elif field == 'timestamp_ms':
        return -(2**48 - 1)
    elif field == 'endtime_ms':
        return 2**48 - 1
    elif field == 'kind':
        return 'default'
    elif field == 'x':
        return 0
    elif field == 'y':
        return 0
    elif field == 'z':
        return 0
    return ''


def get_field_value(raw_entity, key_map, field):
    if key_map[field].get('override_value') is not None:
        return key_map[field].get('override_value')

    if not key_map[field].get('key'):
        return get_default(field)

    return raw_entity[key_map[field].get('key')]


def build_attribute(key, value):
    attribute = {'key': key}
    try:
        float_val = float(value)
        if math.isinf(float_val) or math.isnan(float_val):
            raise RuntimeError('This value should be parsed as a string')
        if float.is_integer(float_val):
            attribute['type'] = 'INT64'
            attribute['int64_value'] = int(float_val)
        else:
            attribute['type'] = 'DOUBLE'
            attribute['double_value'] = float_val
    except:
        attribute['type'] = 'STRING'
        attribute['str_value'] = unicode(value)

    return attribute


def get_attributes(attribute_keys, raw_entity):
    attributes = []
    for key in attribute_keys:
        attributes.append(build_attribute(key, raw_entity[key]))

    return attributes


def score_fields(raw_entities, keys, **kwargs):
    # TODO: Use up to 100 values to score fields
    key_scores = {}
    for key in keys:
        key_scores[key] = {}
        if kwargs.get('generate_ids', False):
            key_scores[key]['identity_score'] = 0
        else:
            key_scores[key]['identity_score'] = get_id_score(key, raw_entities[0][key])
        key_scores[key]['kind_score'] = get_kind_score(key, raw_entities[0][key])
        key_scores[key]['timestamp_ms_score'] = get_timestamp_score(key, raw_entities[0][key])
        key_scores[key]['endtime_ms_score'] = get_endtime_score(key, raw_entities[0][key])
        key_scores[key]['x_score'] = get_x_score(key, raw_entities[0][key])
        key_scores[key]['y_score'] = get_y_score(key, raw_entities[0][key])
        key_scores[key]['z_score'] = get_z_score(key, raw_entities[0][key])
    return key_scores


def map_keys(key_scores, keys):
    key_map = {}
    for score in key_scores[keys[0]].keys():
        max_score = 0
        max_key = None
        for key in keys:
            if key_scores[key][score] > max_score:
                max_score = key_scores[key][score]
                max_key = key

        key_map[score[:-6]] = {'key': max_key, 'score': max_score}

    # TODO: Filter to single key match with highest score

    return key_map


def generate_entities(raw_entities, key_map, **kwargs):
    critical_keys = [d['key'] for d in key_map.values()]
    entities = []
    for raw_entity in raw_entities:
        attribute_keys = [key for key in raw_entity.keys() if key not in critical_keys]
        timestamp = string_to_timestamp_ms(get_field_value(raw_entity, key_map, 'timestamp_ms'))
        endtime = string_to_timestamp_ms(get_field_value(raw_entity, key_map, 'endtime_ms')) if key_map['endtime_ms']['key'] is not None else timestamp

        entity = {
            'identity': get_field_value(raw_entity, key_map, 'identity'),
            'kind': get_field_value(raw_entity, key_map, 'kind'),
            'timestamp_ms': timestamp,
            'endtime_ms': endtime,
            'path': [{
                'x': float(get_field_value(raw_entity, key_map, 'x')),
                'y': float(get_field_value(raw_entity, key_map, 'y')),
                'z': float(get_field_value(raw_entity, key_map, 'z')),
            }],
            'attrs': get_attributes(attribute_keys, raw_entity),
        }

        if kwargs.get('infinite', False):
            entity['timestamp_ms'] = string_to_timestamp_ms(get_default('timestamp_ms'))
            entity['endtime_ms'] = string_to_timestamp_ms(get_default('endtime_ms'))

        entities.append(entity)

    return entities


def dict_to_entities(raw_entities, **kwargs):
    keys = raw_entities[0].keys()
    fields = ['identity', 'kind', 'x', 'y', 'z', 'timestamp_ms', 'endtime_ms']

    key_scores = score_fields(raw_entities, keys, **kwargs)
    key_map = map_keys(key_scores, keys)
    if kwargs.get('kind'):
        key_map['kind'].update({'override_value': kwargs.get('kind')})
    if not kwargs.get('answer_yes'):
        print(json.dumps(key_map, indent=2))
        answer = raw_input("Continue with this mapping? [Y/n]: ")
        if 'y' not in answer.lower():
            sys.exit()

    entities = generate_entities(raw_entities, key_map, **kwargs)

    return {'entities': entities}


def csv_to_entities(infile, **kwargs):
    return dict_to_entities(csv_to_json(infile), **kwargs)


def ingest_json(dataset_id, json_file, **kwargs):
    api._ingest_entity_set(dataset_id, dict_to_entities(json.load(open(json_file))), **kwargs)


def ingest_csv(dataset_id, csv_file, **kwargs):
    api._ingest_entity_set(dataset_id, csv_to_entities(kwargs['csv'], **kwargs), **kwargs)


def ingest_file(dataset_id, **kwargs):
    if 'json' in kwargs and kwargs['json']:
        return ingest_json(dataset_id, kwargs['json'], **kwargs)
    elif 'csv' in kwargs and kwargs['csv']:
        return ingest_csv(dataset_id, kwargs['csv'], **kwargs)
    else:
        raise NotImplementedError('Unrecognized file format')


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Convert a CSV file to JSON using the first row as the keys.')
    arg_parser.add_argument('filename', help='The file to be sorted')
    arg_parser.add_argument('-f', '--field', help='The field to sort on', default='Date Completed')
    arg_parser.add_argument('-o', '--outfile', help='The file to be saved')
    arg_parser.add_argument('-p', '--stdout', help='Dump output to stdout', action='store_true')
    arg_parser.add_argument('-y', '--answer-yes', help='Skip prompt to verify key mapping', action='store_true')
    arg_parser.add_argument('--generate-ids', help='Set this flag if the data does not contain an ID field', action='store_true')
    arg_parser.add_argument('--kind', help='Use this value as the kind for all entities')

    args = arg_parser.parse_args()

    """
    if args.stdout is None:
        outfile = os.path.splitext(args.filename)[0] + '.js'
    else:
        outfile = args.outfile

    if outfile is None:
        args.stdout = True
    """

    entities = csv_to_entities(args.filename, **vars(args))
    print(json.dumps(entities, indent=2))
    print(len(json.dumps(entities)))
