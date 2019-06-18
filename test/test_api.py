import unittest
import mock
import json

from conduce import api


class ResultMock:
    content = "{\"blah\": \"fake json content\"}"


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


if __name__ == '__main__':
    unittest.main()
