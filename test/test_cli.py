import unittest
import mock

from conduce import cli

# Python 2 compatibility
try:
    import __builtin__ as builtins
except Exception:
    import builtins
assert(hasattr(builtins, 'input'))
###


class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


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


listed_backends = ['listed-backend-{}'.format(x) for x in range(0, 9)]


class Test(unittest.TestCase):
    @mock.patch.object(builtins, 'input', return_value='n')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.remove_dataset_backend', return_value=None)
    def test_remove_dataset_backends__remove_all_answer_no(self, mock_api_remove_dataset_backend, mock_api_list_dataset_backends, mock_input):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], all=True, force=False, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        expected_calls = []
        mock_api_remove_dataset_backend.assert_has_calls(expected_calls)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch.object(builtins, 'input', return_value='Y')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.remove_dataset_backend', return_value=None)
    def test_remove_dataset_backends__remove_all_answer_yes(self, mock_api_remove_dataset_backend, mock_api_list_dataset_backends, mock_input):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], all=True, force=False, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], **vars(fake_passed_args)))
        mock_api_remove_dataset_backend.assert_has_calls(expected_calls)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.remove_dataset_backend', return_value=None)
    def test_remove_dataset_backends__remove_all_forced(self, mock_api_remove_dataset_backend, mock_api_list_dataset_backends):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], all=True, force=True, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], **vars(fake_passed_args)))
        mock_api_remove_dataset_backend.assert_has_calls(expected_calls)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.remove_dataset_backend', return_value=None)
    def test_remove_dataset_backends__remove_all_forced_override_list(self, mock_api_remove_dataset_backend, mock_api_list_dataset_backends):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=fake_backend_ids, all=True, force=True, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], **vars(fake_passed_args)))
        mock_api_remove_dataset_backend.assert_has_calls(expected_calls)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.remove_dataset_backend', return_value=None)
    def test_remove_dataset_backends__backend_list(self, mock_api_remove_dataset_backend):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=fake_backend_ids, all=False, force=False, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        expected_calls = []
        for idx, id in enumerate(fake_backend_ids):
            expected_calls.append(mock.call(fake_dataset_id, fake_backend_ids[idx], **vars(fake_passed_args)))
        mock_api_remove_dataset_backend.assert_has_calls(expected_calls)

    @mock.patch('conduce.api.remove_dataset_backend', return_value=None)
    def test_remove_dataset_backends__one_backend(self, mock_api_remove_dataset_backend):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[fake_backend_id], all=False, force=False, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        mock_api_remove_dataset_backend.assert_called_once_with(fake_dataset_id, fake_backend_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value='backend metadata')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    def test_list_dataset_backends__verbose(self, mock_api_list_dataset_backends, mock_api_get_dataset_backend_metadata):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, verbose=True, **vars(fake_passed_args))

        self.assertEqual(cli.list_dataset_backends(fake_args), ['backend metadata'] * 9)

        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], **vars(fake_passed_args)))
        mock_api_get_dataset_backend_metadata.assert_has_calls(expected_calls)

    @mock.patch('conduce.api.list_dataset_backends', return_value='list of backends')
    def test_list_dataset_backends__default(self, mock_api_list_dataset_backends):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, verbose=False, **vars(fake_passed_args))

        self.assertEqual(cli.list_dataset_backends(fake_args), 'list of backends')

        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))


if __name__ == '__main__':
    unittest.main()
