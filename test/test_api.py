import unittest
import mock

from conduce import api


class ResultMock_201:
    status_code = 201

    def raise_for_status(response):
        return None


class ResultMock_202:
    status_code = 202

    def raise_for_status(response):
        return None


class ResultMock:
    content = "{\"apikey\": \"fake json content\"}"


class CustomHTTPException:
    return_value = 409
    msg = "Not found"


class Test(unittest.TestCase):
    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_search_dataset_backend(self, mock_make_post_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        expected_response = {'apikey': 'fake json content'}
        self.assertEqual(api.search_dataset_backend(fake_dataset_id, fake_backend_id, 'fake-query', **fake_kwargs), expected_response)

        expected_fragment = '/api/v2/data/{}/backends/{}/searches'.format(fake_dataset_id, fake_backend_id)
        mock_make_post_request.assert_called_once_with('fake-query', expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_delete_request', return_value=ResultMock())
    def test_delete_dataset_backend(self, mock_make_delete_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.remove_dataset_backend(fake_dataset_id, fake_backend_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        mock_make_delete_request.assert_called_once_with(expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_get_dataset_backend_metadata(self, mock_make_get_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.get_dataset_backend_metadata(fake_dataset_id, fake_backend_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        mock_make_get_request.assert_called_once_with(expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_list_dataset_backends(self, mock_make_get_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.list_dataset_backends(fake_dataset_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends'.format(fake_dataset_id)
        mock_make_get_request.assert_called_once_with(expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_patch_request', return_value=ResultMock())
    def test_disable_auto_processing(self, mock_make_patch_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.disable_auto_processing(fake_dataset_id, fake_backend_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        expected_payload = [
            {
                "path": "/auto_process",
                "value": False,
                "op": "add"
            }
        ]
        mock_make_patch_request.assert_called_once_with(expected_payload, expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_patch_request', return_value=ResultMock())
    def test_enable_auto_processing__disable(self, mock_make_patch_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.enable_auto_processing(fake_dataset_id, fake_backend_id, enable=False, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        expected_payload = [
            {
                "path": "/auto_process",
                "value": False,
                "op": "add"
            }
        ]
        mock_make_patch_request.assert_called_once_with(expected_payload, expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_patch_request', return_value=ResultMock())
    def test_enable_auto_processing__default(self, mock_make_patch_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.enable_auto_processing(fake_dataset_id, fake_backend_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        expected_payload = [
            {
                "path": "/auto_process",
                "value": True,
                "op": "add"
            }
        ]
        mock_make_patch_request.assert_called_once_with(expected_payload, expected_fragment, **fake_kwargs)

    @mock.patch('conduce.api.make_patch_request', return_value=ResultMock())
    def test_process_transactions__parameters_set(self, mock_make_patch_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2', 'all': True, 'transaction': 'fake-transaction',
                       'min': 'fake-min', 'max': 'fake-max', 'default': 'fake-default'}

        api.process_transactions(fake_dataset_id, fake_backend_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        expected_parameters = {
            'all': bool(fake_kwargs.get('all')),
            'tx': fake_kwargs.get('transaction'),
            'min': fake_kwargs.get('min'),
            'max': fake_kwargs.get('max'),
            'default': fake_kwargs.get('default'),
        }

        mock_make_patch_request.assert_called_once_with({}, expected_fragment, parameters=expected_parameters, **fake_kwargs)

    @mock.patch('conduce.api.make_patch_request', return_value=ResultMock())
    def test_process_transactions(self, mock_make_patch_request):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}

        api.process_transactions(fake_dataset_id, fake_backend_id, **fake_kwargs)

        expected_fragment = '/api/v2/data/{}/backends/{}'.format(fake_dataset_id, fake_backend_id)
        expected_parameters = {
            'tx': fake_kwargs.get('transaction'),
            'min': fake_kwargs.get('min'),
            'max': fake_kwargs.get('max'),
            'default': fake_kwargs.get('default'),
        }

        mock_make_patch_request.assert_called_once_with({}, expected_fragment, parameters=expected_parameters, **fake_kwargs)

    @mock.patch('conduce.api._create_dataset_backend', return_value=ResultMock())
    def test_add_simple_store(self, mock__create_dataset_backend):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        fake_dataset_id = 'fake-id'
        fake_auto_process = 'fake-auto_process'
        api.add_simple_store(fake_dataset_id, fake_auto_process, **fake_kwargs)
        mock__create_dataset_backend.assert_called_once_with(fake_dataset_id, api.DatasetBackends.simple,
                                                             fake_auto_process, None, **fake_kwargs)

    @mock.patch('conduce.api._create_dataset_backend', return_value=ResultMock())
    def test_add_tile_store(self, mock__create_dataset_backend):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        fake_dataset_id = 'fake-id'
        fake_auto_process = 'fake-auto_process'
        api.add_tile_store(fake_dataset_id, fake_auto_process, **fake_kwargs)
        mock__create_dataset_backend.assert_called_once_with(fake_dataset_id, api.DatasetBackends.tile,
                                                             fake_auto_process, None, **fake_kwargs)

    @mock.patch('conduce.api._create_dataset_backend', return_value=ResultMock())
    def test_add_capped_tile_store(self, mock__create_dataset_backend):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        fake_dataset_id = 'fake-id'
        fake_auto_process = 'fake-auto_process'
        fake_temporal = 'fake-temporal'
        fake_spatial = 'fake-spatial'
        api.add_capped_tile_store(fake_dataset_id, fake_auto_process, fake_temporal, fake_spatial, **fake_kwargs)

        expected_config = {
            'minimum_temporal_level': 'fake-temporal',
            'minimum_spatial_level': 'fake-spatial',
        }
        mock__create_dataset_backend.assert_called_once_with(fake_dataset_id, api.DatasetBackends.capped_tile,
                                                             fake_auto_process, expected_config, **fake_kwargs)

    @mock.patch('conduce.api._create_dataset_backend', return_value=ResultMock())
    def test_add_elasticsearch_store(self, mock__create_dataset_backend):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        fake_dataset_id = 'fake-id'
        fake_auto_process = 'fake-auto_process'
        api.add_elasticsearch_store(fake_dataset_id, fake_auto_process, **fake_kwargs)
        mock__create_dataset_backend.assert_called_once_with(fake_dataset_id, api.DatasetBackends.elasticsearch,
                                                             fake_auto_process, None, **fake_kwargs)

    @mock.patch('conduce.api._create_dataset_backend', return_value=ResultMock())
    def test_add_histogram_store(self, mock__create_dataset_backend):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        fake_dataset_id = 'fake-id'
        fake_auto_process = 'fake-auto_process'
        api.add_histogram_store(fake_dataset_id, fake_auto_process, **fake_kwargs)
        mock__create_dataset_backend.assert_called_once_with(fake_dataset_id, api.DatasetBackends.histogram,
                                                             fake_auto_process, None, **fake_kwargs)

    def test__create_dataset_backend__invalid_backend(self):
        with self.assertRaisesRegex(ValueError, 'The backend type specified is not valid.'):
            api._create_dataset_backend('fake-id', 'invalid-backend-type', 'irrelevant', 'irrelevant')

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test__create_dataset_backend__simple(self, mock_make_post_request):
        api._create_dataset_backend('fake-id', api.DatasetBackends.simple, None, None)
        expected_payload = {
            'backend_type': 'SimpleStore',
            'auto_process': None,
        }
        mock_make_post_request.assert_called_once_with(expected_payload, '/api/v2/data/fake-id/backends')

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test__create_dataset_backend__kwargs_passthrough(self, mock_make_post_request):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        api._create_dataset_backend('fake-id', api.DatasetBackends.simple, None, None, **fake_kwargs)
        expected_payload = {
            'backend_type': 'SimpleStore',
            'auto_process': None,
        }
        mock_make_post_request.assert_called_once_with(expected_payload, '/api/v2/data/fake-id/backends', **fake_kwargs)

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test__create_dataset_backend__auto_process(self, mock_make_post_request):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        api._create_dataset_backend('fake-id', api.DatasetBackends.simple, 'fake-auto-process', None, **fake_kwargs)
        expected_payload = {
            'backend_type': 'SimpleStore',
            'auto_process': 'fake-auto-process',
        }
        mock_make_post_request.assert_called_once_with(expected_payload, '/api/v2/data/fake-id/backends', **fake_kwargs)

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test__create_dataset_backend__custom_config(self, mock_make_post_request):
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        fake_config = {'config1': 'config1', 'config2': 'config2'}
        api._create_dataset_backend('fake-id', api.DatasetBackends.simple, None, fake_config, **fake_kwargs)
        expected_payload = {
            'backend_type': 'SimpleStore',
            'auto_process': None,
            'config1': 'config1',
            'config2': 'config2'
        }
        mock_make_post_request.assert_called_once_with(expected_payload, '/api/v2/data/fake-id/backends', **fake_kwargs)

    @mock.patch('conduce.api.make_delete_request', return_value=ResultMock())
    def test_delete_transactions(self, mock_make_get_request):
        fake_id = 'fake-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        expected_uri = '/api/v2/data/{}/transactions'.format(fake_id)
        api.delete_transactions(fake_id, **fake_kwargs)
        mock_make_get_request.assert_called_once_with(expected_uri, **fake_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_get_transactions(self, mock_make_get_request):
        fake_id = 'fake-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        expected_parameters = {
            'min': fake_kwargs.get('min', -1),
            'max': fake_kwargs.get('max'),
            'value': fake_kwargs.get('value'),
            'rows': fake_kwargs.get('rows'),
            'page_state': fake_kwargs.get('page_state', ''),
        }
        expected_uri = '/api/v2/data/{}/transactions'.format(fake_id)
        api.get_transactions(fake_id, **fake_kwargs)
        mock_make_get_request.assert_called_once_with(expected_uri, parameters=expected_parameters, **fake_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_get_transactions_with_parameters(self, mock_make_get_request):
        fake_id = 'fake-id'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2', 'min': 'fake-min', 'max': 'fake-max',
                       'value': 'fake-value', 'rows': 'fake-rows', 'page_state': 'fake-page-state', 'count': 'fake-count'
                       }
        expected_parameters = {
            'min': fake_kwargs.get('min', -1),
            'max': fake_kwargs.get('max'),
            'value': fake_kwargs.get('value'),
            'rows': fake_kwargs.get('rows'),
            'page_state': fake_kwargs.get('page_state', ''),
            'count': bool(fake_kwargs.get('count', False)),
        }

        expected_uri = '/api/v2/data/{}/transactions'.format(fake_id)
        api.get_transactions(fake_id, **fake_kwargs)
        mock_make_get_request.assert_called_once_with(expected_uri, parameters=expected_parameters, **fake_kwargs)

    @mock.patch('conduce.api.post_transaction', return_value=ResultMock())
    def test_append_transaction(self, mock_post_transaction):
        fake_id = 'fake id'
        fake_set = 'fake entities'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        api.append_transaction(fake_id, fake_set, **fake_kwargs)
        mock_post_transaction.assert_called_once_with(fake_id, fake_set, operation='APPEND', **fake_kwargs)

    @mock.patch('conduce.api.post_transaction', return_value=ResultMock())
    def test_insert_transaction(self, mock_post_transaction):
        fake_id = 'fake id'
        fake_set = 'fake entities'
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        api.insert_transaction(fake_id, fake_set, **fake_kwargs)
        mock_post_transaction.assert_called_once_with(fake_id, fake_set, operation='INSERT', **fake_kwargs)

    def test_post_transaction__invalid_entity_set(self):
        with self.assertRaisesRegex(ValueError, "Parameter entity_set is not an 'entities' dict."):
            api.post_transaction('id', {'invalid_set': 'set'})

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock_201())
    def test_post_transaction__default_operation(self, mock_make_post_request):
        fake_id = 'fake_id'
        fake_entities = {'entities': 'fake entities'}
        fake_kwargs = {'arg1': 'arg1', 'arg2': 'arg2'}
        self.assertIsInstance(api.post_transaction(fake_id, fake_entities, **fake_kwargs), ResultMock_201)

        expected_payload = {
            'data': fake_entities,
            'op': 'INSERT'
        }
        expected_uri = '/api/v2/data/fake_id/transactions?process=False'
        mock_make_post_request.assert_called_once_with(expected_payload, expected_uri, **fake_kwargs)

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock_201())
    def test_post_transaction__process_true(self, mock_make_post_request):
        fake_id = 'fake_id'
        fake_entities = {'entities': 'fake entities'}
        fake_kwargs = {'arg1': 'arg1', 'process': True}
        self.assertIsInstance(api.post_transaction(fake_id, fake_entities, **fake_kwargs), ResultMock_201)

        expected_payload = {
            'data': fake_entities,
            'op': 'INSERT'
        }
        expected_uri = '/api/v2/data/fake_id/transactions?process=True'
        mock_make_post_request.assert_called_once_with(expected_payload, expected_uri, **fake_kwargs)

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock_201())
    def test_post_transaction__kwargs_operation(self, mock_make_post_request):
        fake_id = 'fake_id'
        fake_entities = {'entities': 'fake entities'}
        fake_kwargs = {'arg1': 'arg1', 'operation': 'fake_op'}
        self.assertIsInstance(api.post_transaction(fake_id, fake_entities, **fake_kwargs), ResultMock_201)

        expected_payload = {
            'data': fake_entities,
            'op': 'fake_op'
        }
        expected_uri = '/api/v2/data/fake_id/transactions?process=False'
        mock_make_post_request.assert_called_once_with(expected_payload, expected_uri, **fake_kwargs)

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock_201())
    def test_post_transaction__debug(self, mock_make_post_request):
        fake_id = 'fake_id'
        fake_entities = ['fake entity 1', 'fake entity 2', 'fake entity 3']
        fake_entity_set = {'entities': fake_entities}
        fake_kwargs = {'arg1': 'arg1', 'debug': True}
        self.assertIsInstance(api.post_transaction(fake_id, fake_entity_set, **fake_kwargs), list)

        expected_uri = '/api/v2/data/fake_id/transactions?process=True'
        for idx, call_args in enumerate(mock_make_post_request.call_args_list):
            expected_payload = {
                'data': {'entities': [fake_entities[idx]]},
                'op': 'INSERT'
            }
            fake_kwargs = {'arg1': 'arg1', 'debug': False, 'process': True}
            self.assertEqual(call_args, mock.call(expected_payload, expected_uri, **fake_kwargs))
            expected_uri = '/api/v2/data/fake_id/transactions?process=True'

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_create_resource_mime_type_json(self, mock_make_post_request):
        test_resource_type = "test_resource_type"
        test_resource_name = "test_resource_name"
        test_content = "test_content_valid_json"
        json_mime_type = "application/json"
        test_kwargs = {'kwarg1': "arg1_value"}

        api.create_resource(test_resource_type, test_resource_name,
                            test_content, json_mime_type, **test_kwargs)

        expected_resource_def = {
            'name': "test_resource_name",
            'tags': None,
            'version': None,
            'type': test_resource_type,
            'mime': json_mime_type,
            'content': test_content
        }
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources', **test_kwargs)

    @mock.patch('conduce.api.is_base64_encoded', return_value=True)
    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_create_resource_mime_type_binary_already_base64_encoded(self, mock_make_post_request, mock_is_base64_encoded):
        test_resource_type = "test_resource_type"
        test_resource_name = "test_resource_name"
        test_content = "test_content"
        test_mime_type = "test_binary_mime_type"
        test_kwargs = {'kwarg1': "arg1_value"}

        api.create_resource(test_resource_type, test_resource_name,
                            test_content, test_mime_type, **test_kwargs)

        expected_resource_def = {
            'name': "test_resource_name",
            'tags': None,
            'version': None,
            'type': test_resource_type,
            'mime': test_mime_type,
            'content': test_content
        }
        mock_is_base64_encoded.assert_called_once_with(test_content)
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources', **test_kwargs)

    @mock.patch('base64.b64encode', return_value='base64-encoded-gobbly-gook')
    @mock.patch('conduce.api.is_base64_encoded', return_value=False)
    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_create_resource_mime_type_binary_not_base64_encoded(self, mock_make_post_request, mock_is_base64_encoded, mock_b64encode):
        test_resource_type = "test_resource_type"
        test_resource_name = "test_resource_name"
        test_content = "test_content"
        test_mime_type = "test_binary_mime_type"
        test_kwargs = {'kwarg1': "arg1_value"}

        api.create_resource(test_resource_type, test_resource_name,
                            test_content, test_mime_type, **test_kwargs)
        expected_resource_def = {
            'name': "test_resource_name",
            'tags': None,
            'version': None,
            'type': test_resource_type,
            'mime': test_mime_type,
            'content': 'base64-encoded-gobbly-gook'
        }
        mock_is_base64_encoded.assert_called_once_with(test_content)
        mock_b64encode.assert_called_once_with(test_content)
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources', **test_kwargs)

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_find_resource(self, mock_make_post_request):
        test_resource_type = "test_resource_type"
        test_content = "test_content_valid_json"
        json_mime_type = "application/json"
        test_kwargs = {'kwarg1': "arg1_value"}

        api.find_resource(type='test_resource_type', mime=json_mime_type, tag=None, content=test_content, **test_kwargs)
        expected_resource_def = {
            'type': test_resource_type,
            'mime': "application/json",
        }
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources/searches?content=test_content_valid_json',
            id=None, tag=None, mime='application/json', content=test_content, name=None, regex=None,
            type='test_resource_type', **test_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_list_api_keys(self, mock_make_get_request):
        test_kwargs = {'kwarg1': "arg1_value"}

        result = api.list_api_keys(**test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'apikeys/list', **test_kwargs)
        self.assertEqual(result['apikey'], 'fake json content')

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_create_api_key(self, mock_make_post_request):
        test_kwargs = {'kwarg1': "arg1_value"}
        result = api.create_api_key(**test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {"description": "Generated and used by conduce-python-api"}, 'apikeys/create', **test_kwargs)
        self.assertEqual(result, 'fake json content')

    @mock.patch('conduce.api.make_post_request')
    def test_remove_api_key(self, mock_make_post_request):
        test_api_key = "Test_API"
        test_kwargs = {'kwarg1': "arg1_value"}
        result = api.remove_api_key(test_api_key, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'apikey': test_api_key}, 'apikeys/delete', **test_kwargs)
        self.assertEqual(result, None)

    @mock.patch('conduce.api.make_post_request', return_value=False)
    def test_account_exists(self, mock_make_post_request):
        test_email = "email@conduce.com"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.account_exists(test_email, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'email': 'email@conduce.com'}, 'user/public/email-available', **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_create_account(self, mock_make_post_request):
        test_email = "email@conduce.com"
        test_name = "Test Name"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.create_account(test_name, test_email, **test_kwargs)
        expected_resource_def = {
            'name': test_name,
            'email': test_email
        }
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'admin/create-user', **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_create_team(self, mock_make_post_request):
        team_name = "Conduce"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.create_team(team_name, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'name': team_name}, 'team-create', **test_kwargs)

    @mock.patch('conduce.api.make_get_request')
    def test_list_teams(self, mock_make_get_request):
        test_kwargs = {'kwarg1': "arg1_value"}
        api.list_teams(**test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'user/list-teams', **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_add_user_to_team(self, mock_make_post_request):
        team_id = 1234
        test_email = "email@conduce.com"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.add_user_to_team(team_id, test_email, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'invitee': {'email': test_email}}, 'team/{}/invite'.format(team_id), **test_kwargs)

    @mock.patch('conduce.api.make_get_request')
    def test_list_team_members(self, mock_make_get_request):
        team_id = 1234
        test_kwargs = {'kwarg1': "arg1_value"}
        api.list_team_members(team_id, **test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'team/{}/users'.format(team_id), **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_create_group(self, mock_make_post_request):
        team_id = 1234
        test_group_name = "Conduce Team"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.create_group(team_id, test_group_name, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'name': test_group_name}, 'team/{}/group-create'.format(team_id), **test_kwargs)

    @mock.patch('conduce.api.make_get_request')
    def test_list_groups(self, mock_make_get_request):
        team_id = 1234
        test_kwargs = {'kwarg1': "arg1_value"}
        api.list_groups(team_id, **test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'team/{}/group-list'.format(team_id), **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_add_user_to_group(self, mock_make_post_request):
        team_id = 1234
        test_group_id = 123
        test_user_id = 456
        test_kwargs = {'kwarg1': "arg1_value"}
        api.add_user_to_group(team_id, test_group_id, test_user_id, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'id': test_user_id}, 'team/{}/group/{}/add-user'.format(team_id, test_group_id), **test_kwargs)

    @mock.patch('conduce.api.make_get_request')
    def test_list_group_members(self, mock_make_get_request):
        team_id = 1234
        test_group_id = 123
        test_kwargs = {'kwarg1': "arg1_value"}
        api.list_group_members(team_id, test_group_id, **test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'team/{}/group/{}/users'.format(team_id, test_group_id), **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_set_owner(self, mock_make_post_request):
        team_id = 1234
        test_resource_id = "resource_id_123"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.set_owner(team_id, test_resource_id, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {}, 'acl/{}/transfer-to-team/{}'.format(test_resource_id, team_id), **test_kwargs)

    @mock.patch('conduce.api.make_get_request')
    def test_list_permissions(self, mock_make_get_request):
        test_resource_id = "resource_id_123"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.list_permissions(test_resource_id, **test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'acl/{}/view'.format(test_resource_id), **test_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_get_entity(self, mock_make_get_request):
        test_dataset_id = "dataset_id_123"
        test_entity_id = "entity_id_123"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.get_entity(test_dataset_id, test_entity_id, **test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'datasets/entity/{}/{}'.format(test_dataset_id, test_entity_id), **test_kwargs)

    @mock.patch('conduce.api.make_get_request', return_value=ResultMock())
    def test_get_dataset_metadata(self, mock_make_get_request):
        test_dataset_id = "dataset_id_123"
        test_kwargs = {'kwarg1': "arg1_value"}
        api.get_dataset_metadata(test_dataset_id, **test_kwargs)
        mock_make_get_request.assert_called_once_with(
            'datasets/metadata/{}'.format(test_dataset_id), **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_grant_permissions(self, mock_make_post_request):
        test_target_string = "public"
        test_resource_id = "resource_id_123"
        test_kwargs = {'kwarg1': "arg1_value"}
        read = "Yes"
        write = "Yes"
        share = "Yes"
        api.grant_permissions(test_target_string, test_resource_id, read, write, share, **test_kwargs)
        expected_resource_def = {
            'share': share,
            'write': write,
            'read': read,
            'target': test_target_string
        }
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'acl/{}/grant'.format(test_resource_id), **test_kwargs)

    @mock.patch('conduce.api.make_post_request')
    def test_revoke_permissions(self, mock_make_post_request):
        test_target_string = "public"
        test_resource_id = "resource_id_123"
        test_kwargs = {'kwarg1': "arg1_value"}
        read = "Yes"
        write = "Yes"
        share = "Yes"
        api.revoke_permissions(test_target_string, test_resource_id, read, write, share, **test_kwargs)
        expected_resource_def = {
            'share': share,
            'write': write,
            'read': read,
            'target': test_target_string
        }
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'acl/{}/revoke'.format(test_resource_id), **test_kwargs)

    @mock.patch('conduce.api.make_put_request', return_value=ResultMock())
    def test_update_resource(self, mock_make_put_request):
        test_resource_def = {
            'revision': 1,
            'id': "resource_id_123"
        }
        test_kwargs = {'kwarg1': "arg1_value"}
        api.update_resource(test_resource_def, **test_kwargs)
        expected_resource_def = {
            'revision': 2,
            'id': "resource_id_123"
        }
        mock_make_put_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources/{}'.format(test_resource_def['id']), **test_kwargs)

    @mock.patch('requests.get')
    @mock.patch('conduce.api.compose_uri', return_value='fake-uri')
    @mock.patch('conduce.api._make_request')
    def test_make_get_request(self, mock__make_request, mock_compose_uri, mock_requests_get):
        test_kwargs = {'kwarg1': "arg1_value"}
        api.make_get_request('uri-fragment', **test_kwargs)
        mock__make_request.assert_called_once_with(
            mock_requests_get, None, 'fake-uri', **test_kwargs)

    @mock.patch('requests.delete')
    @mock.patch('conduce.api.compose_uri', return_value='fake-uri')
    @mock.patch('conduce.api._make_request')
    def test_make_delete_request(self, mock__make_request, mock_compose_uri, mock_requests_delete):
        test_kwargs = {'kwarg1': "arg1_value"}
        api.make_delete_request('uri-fragment', **test_kwargs)
        mock__make_request.assert_called_once_with(
            mock_requests_delete, None, 'fake-uri', **test_kwargs)

    @mock.patch('requests.post')
    @mock.patch('conduce.api.compose_uri', return_value='fake-uri')
    @mock.patch('conduce.api._make_request')
    def test_make_post_request(self, mock__make_request, mock_compose_uri, mock_requests_post):
        test_kwargs = {'kwarg1': "arg1_value"}
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        api.make_post_request(test_payload, 'uri-fragment', **test_kwargs)
        mock__make_request.assert_called_once_with(
            mock_requests_post, test_payload, 'fake-uri', **test_kwargs)

    @mock.patch('requests.put')
    @mock.patch('conduce.api.compose_uri', return_value='fake-uri')
    @mock.patch('conduce.api._make_request')
    def test_make_put_request(self, mock__make_request, mock_compose_uri, mock_requests_put):
        test_kwargs = {'kwarg1': "arg1_value"}
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        api.make_put_request(test_payload, 'uri-fragment', **test_kwargs)
        mock__make_request.assert_called_once_with(
            mock_requests_put, test_payload, 'fake-uri', **test_kwargs)

    @mock.patch('requests.patch')
    @mock.patch('conduce.api.compose_uri', return_value='fake-uri')
    @mock.patch('conduce.api._make_request')
    def test_make_patch_request(self, mock__make_request, mock_compose_uri, mock_requests_patch):
        test_kwargs = {'kwarg1': "arg1_value"}
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        api.make_patch_request(test_payload, 'uri-fragment', **test_kwargs)
        mock__make_request.assert_called_once_with(
            mock_requests_patch, test_payload, 'fake-uri', **test_kwargs)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___no_user_args(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri)
        mock_get_full_config.assert_called_once()
        mock_get_session.assert_called_once_with('default-fake-host', 'default-fake-user', None, True)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params=None, verify=True)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___no_verify(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, no_verify=True)
        mock_get_session.assert_called_once_with('default-fake-host', 'default-fake-user', None, False)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params=None, verify=False)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_user(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, user='fake-user')
        mock_get_full_config.assert_called_once()
        mock_get_session.assert_called_once_with('default-fake-host', 'fake-user', None, True)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params=None, verify=True)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_params(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, parameters='fake-params')
        mock_get_full_config.assert_called_once()
        mock_get_session.assert_called_once_with('default-fake-host', 'default-fake-user', None, True)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params='fake-params', verify=True)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_host(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, host='fake-host')
        mock_get_full_config.assert_called_once()
        mock_get_session.assert_called_once_with('fake-host', 'default-fake-user', None, True)
        mock_request_func.assert_called_once_with('https://fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params=None, verify=True)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_password(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, password='fake-password')
        mock_get_full_config.assert_called_once()
        mock_get_session.assert_called_once_with('default-fake-host', 'default-fake-user', 'fake-password', True)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params=None, verify=True)

    @mock.patch('conduce.session.api_key_header', return_value={'Authorization': 'Bearer fake-api-key'})
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_api_key(self, mock_get_full_config, mock_api_key_header):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        test_api_key = 'fake-api-key'
        api._make_request(mock_request_func, test_payload, test_uri, api_key=test_api_key)
        mock_get_full_config.assert_called_once()
        mock_api_key_header.assert_called_once_with(test_api_key)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, headers={'Authorization': 'Bearer fake-api-key'}, params=None, verify=True)

    @mock.patch('conduce.session.api_key_header', return_value={'Authorization': 'Bearer fake-api-key'})
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_api_key_and_headers(self, mock_get_full_config, mock_api_key_header):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        test_api_key = 'fake-api-key'
        test_headers = {'header_a': 1, 'header_b': 2, 'header_c': 3}
        test_combined_headers = {'header_a': 1, 'header_b': 2, 'header_c': 3, 'Authorization': 'Bearer fake-api-key'}
        api._make_request(mock_request_func, test_payload, test_uri, api_key=test_api_key, headers=test_headers)
        mock_get_full_config.assert_called_once()
        mock_api_key_header.assert_called_once_with(test_api_key)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, headers=test_combined_headers, params=None, verify=True)

    @mock.patch('conduce.session.api_key_header', return_value={'Authorization': 'Bearer fake-api-key'})
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___api_key_host_no_get_config(self, mock_get_full_config, mock_api_key_header):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        test_api_key = 'fake-api-key'
        api._make_request(mock_request_func, test_payload, test_uri, api_key=test_api_key, host='fake-host')
        mock_get_full_config.assert_not_called()
        mock_api_key_header.assert_called_once_with(test_api_key)
        mock_request_func.assert_called_once_with('https://fake-host/{}'.format(test_uri),
                                                  json=test_payload, headers={'Authorization': 'Bearer fake-api-key'}, params=None, verify=True)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___user_host_no_get_config(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, user='fake-user', host='fake-host')
        mock_get_full_config.assert_not_called()
        mock_get_session.assert_called_once_with('fake-host', 'fake-user', None, True)
        mock_request_func.assert_called_once_with('https://fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, params=None, verify=True)


if __name__ == '__main__':
    unittest.main()
