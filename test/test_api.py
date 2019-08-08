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
        self.assertEquals(result['apikey'], 'fake json content')

    @mock.patch('conduce.api.make_post_request', return_value=ResultMock())
    def test_create_api_key(self, mock_make_post_request):
        test_kwargs = {'kwarg1': "arg1_value"}
        result = api.create_api_key(**test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {"description": "Generated and used by conduce-python-api"}, 'apikeys/create', **test_kwargs)
        self.assertEquals(result, 'fake json content')

    @mock.patch('conduce.api.make_post_request')
    def test_remove_api_key(self, mock_make_post_request):
        test_api_key = "Test_API"
        test_kwargs = {'kwarg1': "arg1_value"}
        result = api.remove_api_key(test_api_key, **test_kwargs)
        mock_make_post_request.assert_called_once_with(
            {'apikey': test_api_key}, 'apikeys/delete', **test_kwargs)
        self.assertEquals(result, None)

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
                                                  json=test_payload, cookies='fake-auth', headers={}, verify=True)

    @mock.patch('conduce.session.get_session', return_value='fake-auth')
    @mock.patch('conduce.config.get_full_config', return_value={'default-host': 'default-fake-host', 'default-user': 'default-fake-user'})
    def test__make_request___no_verify(self, mock_get_full_config, mock_get_session):
        mock_request_func = mock.MagicMock()
        test_payload = {'a': 1, 'b': 2, 'c': 3}
        test_uri = '/fake-uri'
        api._make_request(mock_request_func, test_payload, test_uri, no_verify=True)
        mock_get_session.assert_called_once_with('default-fake-host', 'default-fake-user', None, False)
        mock_request_func.assert_called_once_with('https://default-fake-host/{}'.format(test_uri),
                                                  json=test_payload, cookies='fake-auth', headers={}, verify=False)

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
                                                  json=test_payload, cookies='fake-auth', headers={}, verify=True)

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
                                                  json=test_payload, cookies='fake-auth', headers={}, verify=True)

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
                                                  json=test_payload, cookies='fake-auth', headers={}, verify=True)

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
                                                  json=test_payload, headers={'Authorization': 'Bearer fake-api-key'}, verify=True)

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
                                                  json=test_payload, headers=test_combined_headers, verify=True)

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
                                                  json=test_payload, headers={'Authorization': 'Bearer fake-api-key'}, verify=True)

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
                                                  json=test_payload, cookies='fake-auth', headers={}, verify=True)


if __name__ == '__main__':
    unittest.main()
