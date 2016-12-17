import csv
import json
import os
import uuid
import re
from dateutil import parser
import copy


def string_to_timestamp_ms(datetime_string, ignoretz=True):
    EPOCH = parser.parse("1970-01-01T00:00:00.000+0000", ignoretz=ignoretz)
    timestamp = parser.parse(datetime_string, ignoretz=ignoretz)
    return int((timestamp - EPOCH).total_seconds() * 1000)


def csv_to_json(infile, outfile=None, toStdout=False):
    if hasattr(infile, 'read'):
        reader = csv.DictReader(infile)
        out = json.dumps( [ row for row in reader ] )
    else:
        with open(infile, "r") as f:
            reader = csv.DictReader(f)
            out = json.dumps( [ row for row in reader ] )
    if out is None:
        raise "No JSON output. Try again."
    else:
        if toStdout is True:
            print out
            print
        if not outfile is None:
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
            if not '.' in value:
                score += 300
    except:
        pass
    try:
        uuid.UUID(value)
        score += 500
    except:
        pass
    if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", value.lower()):
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

    try:
        float(value)
        return score
    except:
        pass

    return 0


def get_default(field):
    if field == 'identity':
        return uuid.uuid4()
    elif field == 'timestamp_ms':
        return string_to_timestamp_ms('2000-01-01T00:00:00')
    elif field == 'endtime_ms':
        return string_to_timestamp_ms('2020-01-01T00:00:00')
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
    if not key_map[field]['key']:
        return get_default(field)
    return raw_entity[key_map[field]['key']]


def get_attributes(attribute_keys, raw_entity):
    attributes = []
    for key in attribute_keys:
        attribute = {'key':key}
        try:
            float_val = float(raw_entity[key])
            if float.is_integer(float_val):
                attribute['type'] = 'INT64'
                attribute['int64_value'] = float_val
            else:
                attribute['type'] = 'DOUBLE'
                attribute['double_value'] = float_val
        except:
            attribute['type'] = 'STRING'
            attribute['str_value'] = raw_entity[key]

        attributes.append(attribute)

    return attributes


def csv_to_entities(infile, outfile=None, toStdout=False):
    return dict_to_entities(csv_to_json(infile))


def score_fields(raw_entities, keys):
    #TODO: Use up to 100 values to score fields
    key_scores = {}
    for key in keys:
        key_scores[key] = {}
        key_scores[key]['identity_score'] = get_id_score(key, raw_entities[0][key])
        key_scores[key]['kind_score'] = get_kind_score(key, raw_entities[0][key])
        key_scores[key]['timestamp_ms_score'] = get_timestamp_score(key, raw_entities[0][key])
        key_scores[key]['endtime_ms_score'] = get_endtime_score(key, raw_entities[0][key])
        key_scores[key]['x_score'] = get_x_score(key, raw_entities[0][key])
        key_scores[key]['y_score'] = get_y_score(key, raw_entities[0][key])
        key_scores[key]['z_score'] = get_z_score(key, raw_entities[0][key])
    return key_scores


def map_keys(key_scores, keys, attribute_keys):
    key_map = {}
    for score in key_scores[keys[0]].keys():
        max_score = 0
        max_key = None
        for key in keys:
            if key_scores[key][score] > max_score:
                max_score = key_scores[key][score]
                max_key = key

        key_map[score[:-6]] = {'key':max_key,'score':max_score}
        if max_key in attribute_keys:
            attribute_keys.remove(max_key)

    #TODO: Filter to single key match with highest score

    return key_map

def generate_entities(raw_entities, key_map, attribute_keys):
    entities = []
    for raw_entity in raw_entities:
        entity = {
            'identity': get_field_value(raw_entity, key_map, 'identity'),
            'kind': get_field_value(raw_entity, key_map, 'kind'),
            'timestamp_ms': get_field_value(raw_entity, key_map, 'timestamp_ms'),
            'endtime_ms': get_field_value(raw_entity, key_map, 'endtime_ms'),
            'path': [{
                'x': float(get_field_value(raw_entity, key_map, 'x')),
                'y': float(get_field_value(raw_entity, key_map, 'y')),
                'z': float(get_field_value(raw_entity, key_map, 'z')),
                }],
            'attrs': get_attributes(attribute_keys, raw_entity),
        }
        entities.append(entity)

    return entities

def dict_to_entities(raw_entities):
    keys = raw_entities[0].keys()
    attribute_keys = copy.deepcopy(keys)
    fields = ['identity','kind','x','y','z','timestamp_ms','endtime_ms']

    key_scores = score_fields(raw_entities, keys)
    key_map = map_keys(key_scores, keys, attribute_keys)
    entities = generate_entities(raw_entities, key_map, attribute_keys)

    return {'entities':entities}


if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Convert a CSV file to JSON using the first row as the keys.')
    arg_parser.add_argument('filename', help='The file to be sorted')
    arg_parser.add_argument('-f', '--field', help='The field to sort on', default='Date Completed')
    arg_parser.add_argument('-o', '--outfile', help='The file to be saved')
    arg_parser.add_argument('-p', '--stdout', help='The file to be saved', action='store_true')

    args = arg_parser.parse_args()

    if args.stdout is None:
        outfile = os.path.splitext(args.filename)[0] + '.js'
    else:
        outfile = args.outfile

    if outfile is None:
        args.stdout = True

    entities = csv_to_entities(args.filename, outfile, args.stdout)
    import jsbeautifier
    print jsbeautifier.beautify(json.dumps(entities))
