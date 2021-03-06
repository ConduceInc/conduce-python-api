from __future__ import print_function
from __future__ import absolute_import
from builtins import input
from builtins import str
import csv
import json
import os
import uuid
import re
from dateutil import parser
from datetime import datetime
import pytz
import math
import sys


def time_period_to_zoom_level(time_period):
    LOG_ONE_HALF = math.log(0.5)
    TEMPORAL_ZOOM_LEVEL_0_LENGTH = 365.0 * 24 * 3600 * 1000

    min_temporal_zoom_level = 0

    if time_period != 0:
        min_temporal_zoom_level = math.floor(math.log(time_period / TEMPORAL_ZOOM_LEVEL_0_LENGTH) / LOG_ONE_HALF)

    return min_temporal_zoom_level


def distance_to_zoom_level(distance):
    LOG_ONE_HALF = math.log(0.5)
    SPATIAL_ZOOM_LEVEL_0_LENGTH = 360.0

    min_spatial_zoom_level = 0

    if distance != 0:
        min_spatial_zoom_level = math.floor(math.log(distance / SPATIAL_ZOOM_LEVEL_0_LENGTH) / LOG_ONE_HALF)

    return min_spatial_zoom_level


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
    except Exception:
        pass
    try:
        uuid.UUID(value)
        score += 500
    except Exception:
        pass
    if re.match("[0-9a-f]{2}([-:])[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", str(value.lower())):
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
        string_to_timestamp_ms(value)
        return score
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
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
    except Exception:
        attribute['type'] = 'STRING'
        attribute['str_value'] = str(value)

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
    for score in list(key_scores[keys[0]].keys()):
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
    critical_keys = [d['key'] for d in list(key_map.values())]
    entities = []
    for raw_entity in raw_entities:
        attribute_keys = [key for key in list(raw_entity.keys()) if key not in critical_keys]
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
    keys = list(raw_entities[0].keys())
    fields = ['identity', 'kind', 'x', 'y', 'z', 'timestamp_ms', 'endtime_ms']

    key_scores = score_fields(raw_entities, keys, **kwargs)
    key_map = map_keys(key_scores, keys)
    if kwargs.get('kind'):
        key_map['kind'].update({'override_value': kwargs.get('kind')})
    if not kwargs.get('answer_yes'):
        print(json.dumps(key_map, indent=2))
        answer = input("Continue with this mapping? [Y/n]: ")
        if 'y' not in answer.lower():
            sys.exit()

    entities = generate_entities(raw_entities, key_map, **kwargs)

    return {'entities': entities}


def csv_to_entities(infile, **kwargs):
    return dict_to_entities(csv_to_json(infile), **kwargs)


def _convert_coordinates(point):
    if len(point) != 2:
        raise KeyError('A point should only have two dimensions.', point)
    if 'lat' and 'lon' in point:
        coord = {
            'x': float(point['lon']),
            'y': float(point['lat'])
        }
    elif 'x' and 'y' in point:
        coord = {
            'x': float(point['x']),
            'y': float(point['y'])
        }
    else:
        raise KeyError('Invalid coordinate.', point)

    coord['z'] = 0

    return coord


def _convert_geometries(sample):
    coordinates = []
    if 'point' in sample:
        coordinates = [_convert_coordinates(sample['point'])]
    if 'path' in sample:
        if len(coordinates) > 0:
            raise KeyError('A sample may only contain one of point, path or polygon.', sample)
        if len(sample['path']) < 2:
            raise KeyError('Paths must have at least two points.')
        for point in sample['path']:
            coordinates.append(_convert_coordinates(point))
    if 'polygon' in sample:
        if len(coordinates) > 0:
            raise KeyError('A sample may only contain one of point, path or polygon.', sample)
        if len(sample['polygon']) < 3:
            raise KeyError('Polygons must have at least three points.')
        for point in sample['polygon']:
            coordinates.append(_convert_coordinates(point))

    return coordinates


def samples_to_entity_set(sample_list):
    conduce_keys = ['id', 'kind', 'time', 'point', 'path', 'polygon']
    entities = []
    for idx, sample in enumerate(sample_list):
        if 'id' not in sample:
            raise ValueError('Error processing sample at index {}. Samples must include an ID.'.format(idx), sample)
        if 'kind' not in sample:
            raise ValueError('Error processing sample at index {}. Samples must include a kind field.'.format(idx), sample)
        if 'time' not in sample:
            raise ValueError('Error processing sample at index {}. Samples must include a time field.'.format(idx), sample)

        if sample['id'] is None or len(str(sample['id'])) == 0:
            raise ValueError('Error processing sample at index {}. Invalid ID.'.format(idx), sample)
        if sample['kind'] is None or len(sample['kind']) == 0:
            raise ValueError('Error processing sample at index {}. Invalid kind.'.format(idx), sample)
        if sample['time'] is None:
            raise ValueError('Error processing sample at index {}. Invalid time.'.format(idx), sample)

        if not isinstance(sample['time'], datetime):
            raise TypeError('Error processing sample at index {}. Time must be a datetime object.'.format(idx), sample['time'])

        coordinates = _convert_geometries(sample)
        if coordinates == []:
            raise ValueError('Error processing sample at index {}. Samples must define a location (point, path, or polygon).'.format(idx), sample)

        sample['_kind'] = sample['kind']
        attribute_keys = [key for key in list(sample.keys()) if key not in conduce_keys]
        attributes = get_attributes(attribute_keys, sample)

        entities.append({
            'identity': str(sample['id']),
            'kind': sample['kind'],
            'timestamp_ms': datetime_to_timestamp_ms(sample['time']),
            'endtime_ms': datetime_to_timestamp_ms(sample['time']),
            'path': coordinates,
            'attrs': attributes
        })

    return {'entities': entities}


def entities_to_entity_set(entity_list):
    conduce_keys = ['id', 'kind', 'point', 'path', 'polygon']
    entities = []
    ids = set()
    for idx, ent in enumerate(entity_list):
        if 'id' not in ent:
            raise ValueError('Error processing entity at index {}. Entities must include an ID.'.format(idx), ent)
        if 'kind' not in ent:
            raise ValueError('Error processing entity at index {}. Entities must include a kind field.'.format(idx), ent)

        if ent['id'] is None or len(str(ent['id'])) == 0:
            raise ValueError('Error processing entity at index {}. Invalid ID.'.format(idx), ent)
        if ent['id'] in ids:
            raise ValueError('Error processing entity at index{}. Non-Unique ID'.format(idx), ent)
        if ent['kind'] is None or len(ent['kind']) == 0:
            raise ValueError('Error processing entity at index {}. Invalid kind.'.format(idx), ent)
        if ent.get('time') is not None:
            raise KeyError('Error processing entity at index {}. Timeless entities should not set time.'.format(idx), ent)

        coordinates = _convert_geometries(ent)
        if coordinates == []:
            raise ValueError('Error processing entity at index {}. Entities must define a location (point, path, or polygon).'.format(idx), ent)

        ids.add(ent['id'])
        ent['_kind'] = ent['kind']
        attribute_keys = [key for key in list(ent.keys()) if key not in conduce_keys]
        attributes = get_attributes(attribute_keys, ent)

        entities.append({
            'identity': str(ent['id']),
            'kind': ent['kind'],
            'timestamp_ms': get_default('timestamp_ms'),
            'endtime_ms': get_default('endtime_ms'),
            'path': coordinates,
            'attrs': attributes
        })

    return {'entities': entities}


def parse_sample(sample):
    if 'time' in sample:
        sample['time'] = parser.parse(sample['time'])
    return sample


def parse_samples(samples):
    for sample in samples:
        sample.update(parse_sample(sample))
    return samples


def json_to_samples(json_path):
    return json.load(open(json_path, 'r'), object_hook=parse_sample)


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
