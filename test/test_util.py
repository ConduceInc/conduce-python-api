import unittest
import mock

from conduce import util
import datetime


GOOD_POINT_ENTITY = {
    'id': 'fake ID',
    'kind': 'fake kind',
    'point': 'fake point'
}
GOOD_POINT_SAMPLE = {
    'id': 'fake ID',
    'kind': 'fake kind',
    'time': datetime.datetime.today(),
    'point': 'fake point'
}


class ResultMock:
    content = "{\"apikey\": \"fake json content\"}"


class CustomHTTPException:
    return_value = 409
    msg = "Not found"


class Test(unittest.TestCase):
    def test__convert_coordinates__length_not_two(self):
        fake_point = {
            "x": 1,
            "y": 2,
            "z": 0
        }
        with self.assertRaisesRegex(KeyError, 'A point should only have two dimensions.'):
            util._convert_coordinates(fake_point)

    def test__convert_coordinates__unrecognized_keys(self):
        fake_point = {
            "a": 1,
            "b": 2,
        }
        with self.assertRaisesRegex(KeyError, 'Invalid coordinate.'):
            util._convert_coordinates(fake_point)

    def test__convert_coordinates_xy(self):
        fake_point = {
            "x": 1,
            "y": 2
        }
        expected_point = {
            "x": 1,
            "y": 2,
            "z": 0
        }
        self.assertEqual(util._convert_coordinates(fake_point), expected_point)

    def test__convert_coordinates_latlon(self):
        fake_point = {
            "lon": 1,
            "lat": 2
        }
        expected_point = {
            "x": 1,
            "y": 2,
            "z": 0
        }
        self.assertEqual(util._convert_coordinates(fake_point), expected_point)

    def test__convert_geometries__no_location_returns_empty_list(self):
        self.assertEqual(util._convert_geometries({}), [])

    @mock.patch('conduce.util._convert_coordinates', return_value='path coordinates')
    def test__convert_geometries__invalid_point_and_path(self, mock_convert_coordinates):
        fake_path_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "point": 'invalid point definition',
            "path": [{
                "x": 1,
                "y": 2
            }, {
                "x": 3,
                "y": 4
            }, {
                "x": 5,
                "y": 6
            }]
        }

        with self.assertRaisesRegex(KeyError, 'A sample may only contain one of point, path or polygon.'):
            util._convert_geometries(fake_path_sample)

    @mock.patch('conduce.util._convert_coordinates', return_value='path coordinates')
    def test__convert_geometries__invalid_point_and_polygon(self, mock_convert_coordinates):
        fake_path_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "point": 'invalid point definition',
            "polygon": [{
                "x": 1,
                "y": 2
            }, {
                "x": 3,
                "y": 4
            }, {
                "x": 5,
                "y": 6
            }]
        }

        with self.assertRaisesRegex(KeyError, 'A sample may only contain one of point, path or polygon.'):
            util._convert_geometries(fake_path_sample)

    @mock.patch('conduce.util._convert_coordinates', return_value='path coordinates')
    def test__convert_geometries__invalid_path_and_polygon(self, mock_convert_coordinates):
        fake_path_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "polygon": 'invalid polygon definition',
            "path": [{
                "x": 1,
                "y": 2
            }, {
                "x": 3,
                "y": 4
            }, {
                "x": 5,
                "y": 6
            }]
        }

        with self.assertRaisesRegex(KeyError, 'A sample may only contain one of point, path or polygon.'):
            util._convert_geometries(fake_path_sample)

    @mock.patch('conduce.util._convert_coordinates', return_value='point coordinates')
    def test__convert_geometries__point_location(self, mock_convert_coordinates):
        self.assertEqual(util._convert_geometries({'point': 'fake point'}), ['point coordinates'])
        mock_convert_coordinates.assert_called_once_with('fake point')

    @mock.patch('conduce.util._convert_coordinates', return_value='path coordinates')
    def test__convert_geometries__path_too_short(self, mock_convert_coordinates):
        fake_path_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "path": [{
                "x": 1,
                "y": 2
            }]
        }
        with self.assertRaisesRegex(KeyError, 'Paths must have at least two points.'):
            util._convert_geometries(fake_path_sample)

    @mock.patch('conduce.util._convert_coordinates', return_value='path coordinates')
    def test__convert_geometries__path_location(self, mock_convert_coordinates):
        fake_path_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "path": [{
                "x": 1,
                "y": 2
            }, {
                "x": 3,
                "y": 4
            }, {
                "x": 5,
                "y": 6
            }]
        }
        self.assertEqual(util._convert_geometries(fake_path_sample), ['path coordinates', 'path coordinates', 'path coordinates'])
        self.assertEqual(len(mock_convert_coordinates.call_args_list), 3)
        for idx, call_args in enumerate(mock_convert_coordinates.call_args_list):
            self.assertEqual(call_args, mock.call(fake_path_sample['path'][idx]))

    @mock.patch('conduce.util._convert_coordinates', return_value='polygon coordinates')
    def test__convert_geometries__polygon_too_short(self, mock_convert_coordinates):
        fake_polygon_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "polygon": [{
                "x": 1,
                "y": 2
            }]
        }
        with self.assertRaisesRegex(KeyError, 'Polygons must have at least three points.'):
            util._convert_geometries(fake_polygon_sample)

    @mock.patch('conduce.util._convert_coordinates', return_value='polygon coordinates')
    def test__convert_geometries__polygon_location(self, mock_convert_coordinates):
        fake_polygon_sample = {
            "id": 1,
            "kind": "fake",
            "time": datetime.datetime.now(),
            "polygon": [{
                "x": 1,
                "y": 2
            }, {
                "x": 3,
                "y": 4
            }, {
                "x": 5,
                "y": 6
            }]
        }
        self.assertEqual(util._convert_geometries(fake_polygon_sample), ['polygon coordinates', 'polygon coordinates', 'polygon coordinates'])
        self.assertEqual(len(mock_convert_coordinates.call_args_list), 3)
        for idx, call_args in enumerate(mock_convert_coordinates.call_args_list):
            self.assertEqual(call_args, mock.call(fake_polygon_sample['polygon'][idx]))

    def test_samples_to_entity_set__no_id(self):
        NO_ID_SAMPLE = {
            'kind': 'fake kind',
            'time': datetime.datetime.today(),
            'point': 'fake point'
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Samples must include an ID.'):
            util.samples_to_entity_set(fake_sample_list)

    def test_samples_to_entity_set__no_kind(self):
        NO_ID_SAMPLE = {
            'id': 'fake ID',
            'time': datetime.datetime.today(),
            'point': 'fake point'
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Samples must include a kind field.'):
            util.samples_to_entity_set(fake_sample_list)

    def test_samples_to_entity_set__no_time(self):
        NO_ID_SAMPLE = {
            'id': 'fake ID',
            'kind': 'fake kind',
            'point': 'fake point'
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Samples must include a time field.'):
            util.samples_to_entity_set(fake_sample_list)

    def test_samples_to_entity_set__invalid_id(self):
        NO_ID_SAMPLE = {
            'id': '',
            'kind': 'fake kind',
            'time': datetime.datetime.today(),
            'point': 'fake point'
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Invalid ID.'):
            util.samples_to_entity_set(fake_sample_list)

    def test_samples_to_entity_set__invalid_kind(self):
        NO_ID_SAMPLE = {
            'id': 'fake ID',
            'kind': '',
            'time': datetime.datetime.today(),
            'point': 'fake point'
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Invalid kind.'):
            util.samples_to_entity_set(fake_sample_list)

    def test_samples_to_entity_set__invalid_time(self):
        NO_ID_SAMPLE = {
            'id': 'fake ID',
            'kind': 'fake kind',
            'point': 'fake point',
            'time': None
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Invalid time.'):
            util.samples_to_entity_set(fake_sample_list)

    def test_samples_to_entity_set__time_not_datetime(self):
        NO_ID_SAMPLE = {
            'id': 'fake ID',
            'kind': 'fake kind',
            'point': 'fake point',
            'time': 'invalid time',
        }

        fake_sample_list = [NO_ID_SAMPLE]
        with self.assertRaisesRegex(TypeError, 'Error processing sample at index 0. Time must be a datetime object.'):
            util.samples_to_entity_set(fake_sample_list)

    @mock.patch('conduce.util._convert_geometries', return_value=[])
    def test_samples_to_entity_set__invalid_location(self, mock_convert_geometries):

        fake_sample_list = [GOOD_POINT_SAMPLE]
        with self.assertRaisesRegex(ValueError, 'Error processing sample at index 0. Samples must define a location \(point, path, or polygon\).'):
            util.samples_to_entity_set(fake_sample_list)

    @mock.patch('conduce.util.datetime_to_timestamp_ms', return_value="fake sample time")
    @mock.patch('conduce.util.get_attributes', return_value="fake attributes")
    @mock.patch('conduce.util._convert_geometries', return_value="fake converted geometries")
    def test_samples_to_entity_set(self, mock_convert_geometries, mock_get_attributes, mock_datetime_to_timestamp):

        fake_sample_list = [GOOD_POINT_SAMPLE]
        expected_entity_set = {'entities': [{
            'identity': GOOD_POINT_SAMPLE['id'],
            'kind': GOOD_POINT_SAMPLE['kind'],
            'timestamp_ms': 'fake sample time',
            'endtime_ms': 'fake sample time',
            'path': 'fake converted geometries',
            'attrs': 'fake attributes',
        }]}
        self.assertEqual(util.samples_to_entity_set(fake_sample_list), expected_entity_set)
        mock_convert_geometries.assert_called_once_with(GOOD_POINT_SAMPLE)
        mock_get_attributes.assert_called_once_with(['_kind'], GOOD_POINT_SAMPLE)
        mock_datetime_to_timestamp.assert_called_with(GOOD_POINT_SAMPLE['time'])
        self.assertEqual(len(mock_datetime_to_timestamp.call_args_list), 2)

    def test_entities_to_entity_set__no_id(self):
        NO_ID_entity = {
            'kind': 'fake kind',
            'point': 'fake point'
        }

        fake_entity_list = [NO_ID_entity]
        with self.assertRaisesRegex(ValueError, 'Error processing entity at index 0. Entities must include an ID.'):
            util.entities_to_entity_set(fake_entity_list)

    def test_entities_to_entity_set__no_kind(self):
        NO_ID_entity = {
            'id': 'fake ID',
            'point': 'fake point'
        }

        fake_entity_list = [NO_ID_entity]
        with self.assertRaisesRegex(ValueError, 'Error processing entity at index 0. Entities must include a kind field.'):
            util.entities_to_entity_set(fake_entity_list)

    def test_entities_to_entity_set__invalid_id(self):
        NO_ID_entity = {
            'id': '',
            'kind': 'fake kind',
            'point': 'fake point'
        }

        fake_entity_list = [NO_ID_entity]
        with self.assertRaisesRegex(ValueError, 'Error processing entity at index 0. Invalid ID.'):
            util.entities_to_entity_set(fake_entity_list)

    def test_entities_to_entity_set__invalid_kind(self):
        NO_ID_entity = {
            'id': 'fake ID',
            'kind': '',
            'point': 'fake point'
        }

        fake_entity_list = [NO_ID_entity]
        with self.assertRaisesRegex(ValueError, 'Error processing entity at index 0. Invalid kind.'):
            util.entities_to_entity_set(fake_entity_list)

    def test_entities_to_entity_set__has_time(self):
        NO_ID_entity = {
            'id': 'fake ID',
            'kind': 'fake kind',
            'point': 'fake point',
            'time': 'fake time'
        }

        fake_entity_list = [NO_ID_entity]
        with self.assertRaisesRegex(KeyError, 'Error processing entity at index 0. Timeless entities should not set time.'):
            util.entities_to_entity_set(fake_entity_list)

    @mock.patch('conduce.util._convert_geometries', return_value=[])
    def test_entities_to_entity_set__invalid_location(self, mock_convert_geometries):
        fake_entity_list = [GOOD_POINT_ENTITY]
        with self.assertRaisesRegex(ValueError, 'Error processing entity at index 0. Entities must define a location \(point, path, or polygon\).'):
            util.entities_to_entity_set(fake_entity_list)

    @mock.patch('conduce.util.get_default', return_value="fake default")
    @mock.patch('conduce.util.get_attributes', return_value="fake attributes")
    @mock.patch('conduce.util._convert_geometries', return_value="fake converted geometries")
    def test_entities_to_entity_set(self, mock_convert_geometries, mock_get_attributes, mock_get_default):

        fake_sample_list = [GOOD_POINT_ENTITY]
        expected_entity_set = {'entities': [{
            'identity': GOOD_POINT_ENTITY['id'],
            'kind': GOOD_POINT_ENTITY['kind'],
            'timestamp_ms': 'fake default',
            'endtime_ms': 'fake default',
            'path': 'fake converted geometries',
            'attrs': 'fake attributes',
        }]}
        self.assertEqual(util.entities_to_entity_set(fake_sample_list), expected_entity_set)
        mock_convert_geometries.assert_called_once_with(GOOD_POINT_ENTITY)
        mock_get_attributes.assert_called_once_with(['_kind'], GOOD_POINT_ENTITY)
        self.assertEqual(mock_get_default.call_args_list, ([mock.call('timestamp_ms'), mock.call('endtime_ms')]))

    @mock.patch('dateutil.parser.parse', return_value="fake datetime object")
    def test_parse_samples(self, mock_dateutil_parser_parse):
        fake_json_samples = [{'id': 'fake ID 1', 'time': 'fake time string'}, {'id': 'fake ID 2'}]
        fake_parsed_samples = [{'id': 'fake ID 1', 'time': 'fake datetime object'}, {'id': 'fake ID 2'}]

        self.assertEqual(util.parse_samples(fake_json_samples), fake_parsed_samples)

        mock_dateutil_parser_parse.assert_called_once_with('fake time string')

    @mock.patch('builtins.open', return_value="fake file stream")
    @mock.patch('json.load', return_value="fake JSON")
    @mock.patch('conduce.util.parse_samples', return_value="deserialized samples")
    def test_json_to_samples(self, mock_parse_samples, mock_json_load, mock_open):
        fake_file = "fake file path"

        self.assertEqual(util.json_to_samples(fake_file), 'fake JSON')

        mock_json_load.assert_called_once_with(
            mock_parse_samples, "fake file stream")


if __name__ == '__main__':
    unittest.main()
