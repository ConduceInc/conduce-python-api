import unittest
import mock
import json
import requests

from conduce import api
from requests.exceptions import HTTPError

class ResultMock:
    content = "{\"apikey\": \"fake json content\"}"
	
class CustomHTTPException:
    return_value = 409
    msg = "Not found"
	
class Test(unittest.TestCase):
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
        test_resource_name = "test_resource_name"
        test_content = "test_content_valid_json"
        json_mime_type = "application/json"
        test_kwargs = {'kwarg1': "arg1_value"}

        api.find_resource(type='test_resource_type', mime = json_mime_type, tag=None, content=test_content, **test_kwargs)
        expected_resource_def = {
              'type': test_resource_type,
              'mime': "application/json",
            }
        mock_make_post_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources/searches?content=test_content_valid_json',id=None, tag=None, mime='application/json',  content=test_content,  name=None, regex=None, type='test_resource_type', **test_kwargs)

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
            'id' : "resource_id_123"
        }
        test_kwargs = {'kwarg1': "arg1_value"}
        res = api.update_resource(test_resource_def, **test_kwargs)
        expected_resource_def = {
            'revision': 2, 
            'id' : "resource_id_123"
        }
        mock_make_put_request.assert_called_once_with(
            expected_resource_def, 'conduce/api/v2/resources/{}'.format(test_resource_def['id']), **test_kwargs)
			
if __name__ == '__main__':
    unittest.main()
