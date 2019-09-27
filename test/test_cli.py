import unittest
import mock

from conduce import cli

# Python 2 compatibility
try:
    import __builtin__ as builtins
except Exception:
    import builtins
assert(hasattr(builtins, 'input'))
assert(hasattr(builtins, 'open'))
###


class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class MockResponse_201:
    status_code = 201

    def raise_for_status(response):
        return None


class MockResponse_202:
    status_code = 202

    def raise_for_status(response):
        return None


class MockResponse:
    content = "{\"apikey\": \"fake json content\"}"
    headers = {"location": "fake location"}


class CustomHTTPException:
    return_value = 409
    msg = "Not found"


listed_backends = ['listed-backend-{}'.format(x) for x in range(0, 9)]


class Test(unittest.TestCase):
    @mock.patch('conduce.api.get_transactions', return_value={'count': 'all-the-transactions'})
    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value={'transactions': 43, 'configuration': {'backend_type': 'fake-backend-type'}})
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    def test_get_backend_status(
        self,
        mock_api_list_dataset_backends,
        mock_api_get_dataset_backend_metadata,
        mock_api_get_transactions,
    ):
        fake_dataset_ids = ['fake-dataset-id-1', 'fake-dataset-id-2', 'fake-dataset-id-3']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_ids=fake_dataset_ids, **vars(fake_passed_args))

        cli.get_backend_status(fake_args)

        expected_list_dataset_backend_calls = []
        expected_get_transaction_count_calls = []
        expected_get_metadata_calls = []

        for dataset_id in fake_dataset_ids:
            expected_get_transaction_count_calls.append(
                mock.call(dataset_id, count=True, **vars(fake_passed_args)))
            expected_list_dataset_backend_calls.append(
                mock.call(dataset_id, **vars(fake_passed_args)))
            for bid in listed_backends:
                expected_get_metadata_calls.append(
                    mock.call(dataset_id, bid, **vars(fake_passed_args)))

        mock_api_list_dataset_backends.assert_has_calls(expected_list_dataset_backend_calls)
        mock_api_get_transactions.assert_has_calls(expected_get_transaction_count_calls)
        mock_api_get_dataset_backend_metadata.assert_has_calls(expected_get_metadata_calls)

    @mock.patch('conduce.api.create_dataset', return_value={'id': 'fake-dataset-id'})
    @mock.patch('conduce.ingest.ingest_file')
    @mock.patch('conduce.cli.ingest_entities')
    def test_create_dataset__raw(
            self,
            mock_ingest_entities,
            mock_ingest_file,
            mock_api_create_dataset,
    ):
        fake_dataset_name = 'fake-dataset-name'
        fake_backend_types = []
        fake_json = 'fake-json'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(name=fake_dataset_name, backends=fake_backend_types, csv=None, raw=fake_json, json=None, **vars(fake_passed_args))

        cli.create_dataset(fake_args)
        mock_ingest_file.assert_not_called()
        mock_ingest_entities.assert_called_once_with('fake-dataset-id', fake_args)
        mock_api_create_dataset.assert_called_once_with(fake_dataset_name, backend_types=fake_backend_types, **vars(fake_passed_args))

    @mock.patch('conduce.api.create_dataset', return_value={'id': 'fake-dataset-id'})
    @mock.patch('conduce.ingest.ingest_file')
    @mock.patch('conduce.cli.ingest_entities')
    def test_create_dataset__json(
            self,
            mock_ingest_entities,
            mock_ingest_file,
            mock_api_create_dataset,
    ):
        fake_dataset_name = 'fake-dataset-name'
        fake_backend_types = []
        fake_json = 'fake-json'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(name=fake_dataset_name, backends=fake_backend_types, csv=None, json=fake_json, raw=None, **vars(fake_passed_args))

        cli.create_dataset(fake_args)
        mock_ingest_entities.assert_not_called()
        mock_ingest_file.assert_called_once_with('fake-dataset-id', **vars(fake_args))
        mock_api_create_dataset.assert_called_once_with(fake_dataset_name, backend_types=fake_backend_types, **vars(fake_passed_args))

    @mock.patch('conduce.api.create_dataset', return_value={'id': 'fake-dataset-id'})
    @mock.patch('conduce.ingest.ingest_file')
    @mock.patch('conduce.cli.ingest_entities')
    def test_create_dataset__csv(
            self,
            mock_ingest_entities,
            mock_ingest_file,
            mock_api_create_dataset,
    ):
        fake_dataset_name = 'fake-dataset-name'
        fake_backend_types = []
        fake_csv = 'fake-csv'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(name=fake_dataset_name, backends=fake_backend_types, json=None, csv=fake_csv, raw=None, **vars(fake_passed_args))

        cli.create_dataset(fake_args)
        mock_ingest_entities.assert_not_called()
        mock_ingest_file.assert_called_once_with('fake-dataset-id', **vars(fake_args))
        mock_api_create_dataset.assert_called_once_with(fake_dataset_name, backend_types=fake_backend_types, **vars(fake_passed_args))

    @mock.patch('conduce.api.create_dataset')
    @mock.patch('conduce.ingest.ingest_file')
    @mock.patch('conduce.cli.ingest_entities')
    def test_create_dataset__backends(
            self,
            mock_ingest_entities,
            mock_ingest_file,
            mock_api_create_dataset,
    ):
        fake_dataset_name = 'fake-dataset-name'
        fake_backend_types = ['simple', 'histogram', 'capped-tile']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(name=fake_dataset_name, backends=fake_backend_types, json=None, csv=None, raw=None, **vars(fake_passed_args))

        cli.create_dataset(fake_args)
        mock_ingest_entities.assert_not_called()
        mock_ingest_file.assert_not_called()
        mock_api_create_dataset.assert_called_once_with(
            fake_dataset_name,
            backend_types=['SimpleStore', 'HistogramStore', 'CappedTileStore'],
            **vars(fake_passed_args))

    @mock.patch('conduce.api.create_dataset')
    @mock.patch('conduce.ingest.ingest_file')
    @mock.patch('conduce.cli.ingest_entities')
    def test_create_dataset__raises_key_error(
            self,
            mock_ingest_entities,
            mock_ingest_file,
            mock_api_create_dataset,
    ):
        fake_dataset_name = 'fake-dataset-name'
        fake_backend_types = ['fake_backend_types']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(name=fake_dataset_name, backends=fake_backend_types, json=None, csv=None, raw=None, **vars(fake_passed_args))

        with self.assertRaises(KeyError):
            cli.create_dataset(fake_args)
        mock_ingest_entities.assert_not_called()
        mock_ingest_file.assert_not_called()
        mock_api_create_dataset.assert_not_called()

    @mock.patch('conduce.api.create_dataset')
    @mock.patch('conduce.ingest.ingest_file')
    @mock.patch('conduce.cli.ingest_entities')
    def test_create_dataset__default(
            self,
            mock_ingest_entities,
            mock_ingest_file,
            mock_api_create_dataset,
    ):
        fake_dataset_name = 'fake-dataset-name'
        fake_backend_types = []
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(name=fake_dataset_name, backends=fake_backend_types, json=None, csv=None, raw=None, **vars(fake_passed_args))

        cli.create_dataset(fake_args)
        mock_ingest_entities.assert_not_called()
        mock_ingest_file.assert_not_called()
        mock_api_create_dataset.assert_called_once_with(fake_dataset_name, backend_types=fake_backend_types, **vars(fake_passed_args))

    @mock.patch('conduce.api.enable_auto_processing', return_value=MockResponse())
    def test_enable_auto_processing__disable_True(self, mock_api_enable_auto_processing):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, disable=True, backend_id=fake_backend_id, **vars(fake_passed_args))

        cli.enable_auto_processing(fake_args)

        mock_api_enable_auto_processing.assert_called_once_with(fake_dataset_id, fake_backend_id, enable=False, **vars(fake_passed_args))

    @mock.patch('conduce.api.enable_auto_processing', return_value=MockResponse())
    def test_enable_auto_processing__disable_False(self, mock_api_enable_auto_processing):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, disable=False, backend_id=fake_backend_id, **vars(fake_passed_args))

        cli.enable_auto_processing(fake_args)

        mock_api_enable_auto_processing.assert_called_once_with(fake_dataset_id, fake_backend_id, enable=True, **vars(fake_passed_args))

    @mock.patch('conduce.api.set_default_backend', return_value=MockResponse())
    def test_set_default_backend(self, mock_api_set_default_backend):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_id=fake_backend_id, **vars(fake_passed_args))

        cli.set_default_backend(fake_args)

        mock_api_set_default_backend.assert_called_once_with(fake_dataset_id, fake_backend_id, **vars(fake_passed_args))

    def test_process_transactions__raises_value_error(self):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], all_backends=False, timeout=None, **vars(fake_passed_args))
        with self.assertRaisesRegex(ValueError, 'You must provide a list of backend IDs or pass --all-backends'):
            cli.process_transactions(fake_args)

    @mock.patch('conduce.api.wait_for_job')
    @mock.patch('conduce.api.get_transactions', return_value={'count': 48})
    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value={'transactions': 43})
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__all_backends(
            self, mock_api_process_transactions,
            mock_api_list_dataset_backends,
            mock_api_get_dataset_backend_metadata,
            mock_api_get_transactions,
            mock_api_wait_for_job,
    ):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(all=False, min=None, max=None, dataset_id=fake_dataset_id, backend_ids=[],
                             transaction=None, async_processing=False, all_backends=True, timeout=None, **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        expected_waits = []
        for idx, id in enumerate(listed_backends):
            for tx_idx in range(44, 48):
                expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], transaction=tx_idx, **vars(fake_passed_args)))
                expected_waits.append(mock.call('fake location', timeout=None, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_wait_for_job.assert_has_calls(expected_waits)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.wait_for_job')
    @mock.patch('conduce.api.get_transactions', return_value={'count': 48})
    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value={'transactions': 43})
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__all_backends_override_list(
            self,
            mock_api_process_transactions,
            mock_api_list_dataset_backends,
            mock_api_get_dataset_backend_metadata,
            mock_api_get_transactions,
            mock_api_wait_for_job,
    ):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=fake_backend_ids, transaction=None,
                             async_processing=False, all=False, min=None, max=None, all_backends=True, timeout=None, **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        expected_waits = []
        for idx, id in enumerate(listed_backends):
            for tx_idx in range(44, 48):
                expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], transaction=tx_idx, **vars(fake_passed_args)))
                expected_waits.append(mock.call('fake location', timeout=None, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_wait_for_job.assert_has_calls(expected_waits)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.wait_for_job')
    @mock.patch('conduce.api.get_transactions', return_value={'count': 48})
    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value={'transactions': 43})
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__one_transaction(
        self,
        mock_api_process_transactions,
        mock_api_get_dataset_backend_metadata,
            mock_api_get_transactions,
            mock_api_wait_for_job,
    ):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(
            all=False,
            min=None,
            max=None,
            dataset_id=fake_dataset_id,
            backend_ids=fake_backend_ids,
            transaction='fake-tx-id',
            async_processing=False,
            all_backends=False,
            timeout=10,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        expected_waits = []
        for idx, id in enumerate(fake_backend_ids):
            expected_calls.append(mock.call(fake_dataset_id, fake_backend_ids[idx], transaction='fake-tx-id', **vars(fake_passed_args)))
            expected_waits.append(mock.call('fake location', timeout=10, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_wait_for_job.assert_has_calls(expected_waits)

    @mock.patch('conduce.api.wait_for_job')
    @mock.patch('conduce.api.get_transactions', return_value={'count': 48})
    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value={'transactions': 43})
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__backend_list(
        self,
        mock_api_process_transactions,
        mock_api_get_dataset_backend_metadata,
            mock_api_get_transactions,
            mock_api_wait_for_job,
    ):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(
            all=False,
            min=None,
            max=None,
            dataset_id=fake_dataset_id,
            backend_ids=fake_backend_ids,
            transaction=None,
            async_processing=False,
            all_backends=False,
            timeout=10,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        expected_waits = []
        for idx, id in enumerate(fake_backend_ids):
            for tx_idx in range(44, 48):
                expected_calls.append(mock.call(fake_dataset_id, fake_backend_ids[idx], transaction=tx_idx, **vars(fake_passed_args)))
                expected_waits.append(mock.call('fake location', timeout=10, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_wait_for_job.assert_has_calls(expected_waits)

    @mock.patch('conduce.api.wait_for_job')
    @mock.patch('conduce.api.get_transactions', return_value={'count': 48})
    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value={'transactions': 43})
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__one_backend(
            self,
            mock_api_process_transactions,
            mock_api_get_dataset_backend_metadata,
            mock_api_get_transactions,
            mock_api_wait_for_job,
    ):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(
            dataset_id=fake_dataset_id,
            backend_ids=[fake_backend_id],
            transaction=None,
            all=False,
            min=None,
            max=None,
            async_processing=False,
            all_backends=False,
            timeout=None,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        expected_waits = []
        for idx in range(44, 48):
            expected_calls.append(mock.call(fake_dataset_id, fake_backend_id, transaction=idx, **vars(fake_passed_args)))
            expected_waits.append(mock.call('fake location', timeout=None, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_wait_for_job.assert_has_calls(expected_waits)

    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__all_backends_async(self, mock_api_process_transactions, mock_api_list_dataset_backends):
        fake_dataset_id = 'fake-dataset-id'
        fake_request_args = FakeArgs(host='fake-host', user='fake-user')
        fake_passed_args = FakeArgs(all=True, **vars(fake_request_args))
        fake_args = FakeArgs(
            dataset_id=fake_dataset_id,
            backend_ids=[],
            async_processing=True,
            transaction=None,
            all_backends=True,
            timeout=None,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], transaction=None, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_request_args))

    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__all_backends_override_list_async(self, mock_api_process_transactions, mock_api_list_dataset_backends):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_request_args = FakeArgs(host='fake-host', user='fake-user')
        fake_passed_args = FakeArgs(all=True, **vars(fake_request_args))
        fake_args = FakeArgs(
            dataset_id=fake_dataset_id,
            backend_ids=fake_backend_ids,
            async_processing=True,
            transaction=None,
            all_backends=True,
            timeout=None,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], transaction=None, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_request_args))

    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__backend_list_async(self, mock_api_process_transactions):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_ids = ['fake-backend-id-1', 'fake-backend-id-2', 'fake-backend-id-3']
        fake_passed_args = FakeArgs(all=True, host='fake-host', user='fake-user')
        fake_args = FakeArgs(
            dataset_id=fake_dataset_id,
            backend_ids=fake_backend_ids,
            async_processing=True,
            transaction=None,
            all_backends=False,
            timeout=None,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        expected_calls = []
        for idx, id in enumerate(fake_backend_ids):
            expected_calls.append(mock.call(fake_dataset_id, fake_backend_ids[idx], transaction=None, **vars(fake_passed_args)))
        mock_api_process_transactions.assert_has_calls(expected_calls)

    @mock.patch('conduce.api.process_transactions', return_value=MockResponse())
    def test_process_transactions__one_backend_async(self, mock_api_process_transactions):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(all=False, host='fake-host', user='fake-user')
        fake_args = FakeArgs(
            dataset_id=fake_dataset_id,
            backend_ids=[fake_backend_id],
            async_processing=True,
            transaction=None,
            all_backends=False,
            timeout=None,
            **vars(fake_passed_args))

        cli.process_transactions(fake_args)

        mock_api_process_transactions.assert_called_once_with(fake_dataset_id, fake_backend_id, transaction=None, **vars(fake_passed_args))

    @mock.patch('json.load', return_value='fake-json')
    @mock.patch.object(builtins, 'open', return_value="fake file stream")
    @mock.patch('conduce.util.csv_to_json', return_value='fake-csv-to-json')
    @mock.patch('conduce.util.parse_samples', return_value='fake-parsed-samples')
    @mock.patch('conduce.util.json_to_samples', return_value='fake-samples')
    @mock.patch('conduce.util.samples_to_entity_set', return_value='fake-entity-set')
    def test_read_entity_set_from_samples_file__raw(self, mock_samples_to_entity_set,
                                                    mock_json_to_samples, mock_parse_samples, mock_csv_to_json, mock_open, mock_json_load):
        fake_args = FakeArgs(raw='fake-entity-set', csv=None, json=None)
        self.assertEqual(cli.read_entity_set_from_samples_file(fake_args), 'fake-json')
        mock_csv_to_json.assert_not_called()
        mock_parse_samples.assert_not_called()
        mock_json_to_samples.assert_not_called()
        mock_samples_to_entity_set.assert_not_called()
        mock_open.called_once_with('fake-entity-set')
        mock_json_load.called_once_with('fake file stream')

    @mock.patch('conduce.util.csv_to_json', return_value='fake-csv-to-json')
    @mock.patch('conduce.util.parse_samples', return_value='fake-parsed-samples')
    @mock.patch('conduce.util.json_to_samples', return_value='fake-samples')
    @mock.patch('conduce.util.samples_to_entity_set', return_value='fake-entity-set')
    def test_read_entity_set_from_samples_file__json(self, mock_samples_to_entity_set,
                                                     mock_json_to_samples, mock_parse_samples, mock_csv_to_json):
        fake_args = FakeArgs(json='fake-json', csv=None, raw=None)
        self.assertEqual(cli.read_entity_set_from_samples_file(fake_args), 'fake-entity-set')
        mock_csv_to_json.assert_not_called()
        mock_parse_samples.assert_not_called()
        mock_json_to_samples.assert_called_once_with('fake-json')
        mock_samples_to_entity_set.called_once_with('fake-parsed-samples')

    @mock.patch('conduce.util.csv_to_json', return_value='fake-csv-to-json')
    @mock.patch('conduce.util.parse_samples', return_value='fake-parsed-samples')
    @mock.patch('conduce.util.json_to_samples', return_value='fake-samples')
    @mock.patch('conduce.util.samples_to_entity_set', return_value='fake-entity-set')
    def test_read_entity_set_from_samples_file__csv(self, mock_samples_to_entity_set,
                                                    mock_json_to_samples, mock_parse_samples, mock_csv_to_json):
        fake_args = FakeArgs(csv='fake-csv', json=None, raw=None)
        self.assertEqual(cli.read_entity_set_from_samples_file(fake_args), 'fake-entity-set')
        mock_csv_to_json.assert_called_once_with('fake-csv')
        mock_parse_samples.assert_called_once_with('fake-csv-to-json')
        mock_json_to_samples.assert_not_called()
        mock_samples_to_entity_set.called_once_with('fake-parsed-samples')

    @mock.patch('conduce.cli.read_entity_set_from_samples_file', return_value='fake-entity-set')
    @mock.patch('conduce.api.append_transaction', return_value=MockResponse())
    def test_append_transaction_hold(self, mock_api_append_transaction, mock_read_entity_set_from_samples_file):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, hold=True, **vars(fake_passed_args))

        cli.append_transaction(fake_args)

        mock_api_append_transaction.assert_called_once_with(fake_dataset_id, 'fake-entity-set', process=False, **vars(fake_passed_args))
        mock_read_entity_set_from_samples_file.assert_called_once_with(fake_args)

    @mock.patch('conduce.cli.read_entity_set_from_samples_file', return_value='fake-entity-set')
    @mock.patch('conduce.api.insert_transaction', return_value=MockResponse())
    def test_insert_transaction_hold(self, mock_api_insert_transaction, mock_read_entity_set_from_samples_file):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, hold=True, **vars(fake_passed_args))

        cli.insert_transaction(fake_args)

        mock_api_insert_transaction.assert_called_once_with(fake_dataset_id, 'fake-entity-set', process=False, **vars(fake_passed_args))
        mock_read_entity_set_from_samples_file.assert_called_once_with(fake_args)

    @mock.patch('conduce.cli.read_entity_set_from_samples_file', return_value='fake-entity-set')
    @mock.patch('conduce.api.insert_transaction', return_value=MockResponse())
    def test_insert_transaction(self, mock_api_insert_transaction, mock_read_entity_set_from_samples_file):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, hold=False, **vars(fake_passed_args))

        cli.insert_transaction(fake_args)

        mock_api_insert_transaction.assert_called_once_with(fake_dataset_id, 'fake-entity-set', process=True, **vars(fake_passed_args))
        mock_read_entity_set_from_samples_file.assert_called_once_with(fake_args)

    @mock.patch('conduce.api.get_transactions', return_value=MockResponse())
    def test_get_dataset_transactions_set_value(self, mock_api_get_transactions):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(value=13, host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, min=1, max=15, **vars(fake_passed_args))

        cli.get_dataset_transactions(fake_args)

        mock_api_get_transactions.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.get_transactions', return_value=MockResponse())
    def test_get_dataset_transactions_set_min_max(self, mock_api_get_transactions):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(min=1, max=15, value=None, host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, **vars(fake_passed_args))

        cli.get_dataset_transactions(fake_args)

        mock_api_get_transactions.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.get_transactions', return_value=MockResponse())
    def test_get_dataset_transactions_default(self, mock_api_get_transactions):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(min=-1, max=None, value=None, host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, **vars(fake_passed_args))

        cli.get_dataset_transactions(fake_args)

        mock_api_get_transactions.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch.object(builtins, 'input', return_value='n')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.remove_dataset_backend', return_value=MockResponse())
    def test_remove_dataset_backends__remove_all_answer_no(self, mock_api_remove_dataset_backend, mock_api_list_dataset_backends, mock_input):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], all=True, force=False, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        mock_api_remove_dataset_backend.assert_not_called()
        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch.object(builtins, 'input', return_value='Y')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    @mock.patch('conduce.api.remove_dataset_backend', return_value=MockResponse())
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
    @mock.patch('conduce.api.remove_dataset_backend', return_value=MockResponse())
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
    @mock.patch('conduce.api.remove_dataset_backend', return_value=MockResponse())
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

    @mock.patch('conduce.api.remove_dataset_backend', return_value=MockResponse())
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

    def test_remove_dataset_backends__raises_value_error(self):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], all=False, force=False, **vars(fake_passed_args))
        with self.assertRaisesRegex(ValueError, 'You must provide a list of backend IDs or pass --all'):
            cli.remove_dataset_backends(fake_args)

    @mock.patch('conduce.api.remove_dataset_backend', return_value=MockResponse())
    def test_remove_dataset_backends__one_backend(self, mock_api_remove_dataset_backend):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[fake_backend_id], all=False, force=False, **vars(fake_passed_args))

        cli.remove_dataset_backends(fake_args)

        mock_api_remove_dataset_backend.assert_called_once_with(fake_dataset_id, fake_backend_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value='backend metadata')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    def test_list_dataset_backends__backend_id(self, mock_api_list_dataset_backends, mock_api_get_dataset_backend_metadata):
        fake_dataset_id = 'fake-dataset-id'
        fake_backend_id = 'fake-backend-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[fake_backend_id], verbose=None, **vars(fake_passed_args))

        self.assertEqual(cli.list_dataset_backends(fake_args), {fake_backend_id: 'backend metadata'})
        mock_api_get_dataset_backend_metadata.assert_called_once_with(
            fake_dataset_id, fake_backend_id, **vars(fake_passed_args))
        mock_api_list_dataset_backends.assert_not_called()

    @mock.patch('conduce.api.get_dataset_backend_metadata', return_value='backend metadata')
    @mock.patch('conduce.api.list_dataset_backends', return_value=listed_backends)
    def test_list_dataset_backends__verbose(self, mock_api_list_dataset_backends, mock_api_get_dataset_backend_metadata):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], verbose=True, **vars(fake_passed_args))

        self.assertEqual(cli.list_dataset_backends(fake_args), dict((bid, 'backend metadata') for bid in listed_backends))

        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

        expected_calls = []
        for idx, id in enumerate(listed_backends):
            expected_calls.append(mock.call(fake_dataset_id, listed_backends[idx], **vars(fake_passed_args)))
        mock_api_get_dataset_backend_metadata.assert_has_calls(expected_calls)

    @mock.patch('conduce.api.list_dataset_backends', return_value='list of backends')
    def test_list_dataset_backends__default(self, mock_api_list_dataset_backends):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_args = FakeArgs(dataset_id=fake_dataset_id, backend_ids=[], verbose=False, **vars(fake_passed_args))

        self.assertEqual(cli.list_dataset_backends(fake_args), 'list of backends')

        mock_api_list_dataset_backends.assert_called_once_with(fake_dataset_id, **vars(fake_passed_args))

    @mock.patch('conduce.api.add_simple_store', return_value=MockResponse())
    def test_add_simple_store__default(self, mock_api_add_simple_store):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_manual_processing = False
        fake_args = FakeArgs(dataset_id=fake_dataset_id, manual_processing=fake_manual_processing, **vars(fake_passed_args))

        cli.add_simple_store(fake_args)

        mock_api_add_simple_store.assert_called_once_with(fake_dataset_id, not fake_manual_processing, **vars(fake_passed_args))

    @mock.patch('conduce.api.add_tile_store', return_value=MockResponse())
    def test_add_tile_store__default(self, mock_api_add_tile_store):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_manual_processing = False
        fake_args = FakeArgs(dataset_id=fake_dataset_id, manual_processing=fake_manual_processing, **vars(fake_passed_args))

        cli.add_tile_store(fake_args)

        mock_api_add_tile_store.assert_called_once_with(fake_dataset_id, not fake_manual_processing, **vars(fake_passed_args))

    @mock.patch('conduce.api.add_elasticsearch_store', return_value=MockResponse())
    def test_add_elasticsearch_store__default(self, mock_api_add_elasticsearch_store):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_manual_processing = True
        fake_args = FakeArgs(dataset_id=fake_dataset_id, manual_processing=fake_manual_processing, **vars(fake_passed_args))

        cli.add_elasticsearch_store(fake_args)

        mock_api_add_elasticsearch_store.assert_called_once_with(fake_dataset_id, not fake_manual_processing, **vars(fake_passed_args))

    @mock.patch('conduce.api.add_histogram_store', return_value=MockResponse())
    def test_add_histogram_store__default(self, mock_api_add_histogram_store):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_manual_processing = False
        fake_args = FakeArgs(dataset_id=fake_dataset_id, manual_processing=fake_manual_processing, **vars(fake_passed_args))

        cli.add_histogram_store(fake_args)

        mock_api_add_histogram_store.assert_called_once_with(fake_dataset_id, not fake_manual_processing, **vars(fake_passed_args))

    @mock.patch('conduce.api.add_capped_tile_store', return_value=MockResponse())
    def test_add_capped_tile_store__default(self, mock_api_add_capped_tile_store):
        fake_dataset_id = 'fake-dataset-id'
        fake_passed_args = FakeArgs(host='fake-host', user='fake-user')
        fake_manual_processing = True
        fake_min_spatial = 'fake-min-spatial'
        fake_min_temporal = 'fake-min-temporal'
        fake_args = FakeArgs(dataset_id=fake_dataset_id,
                             min_spatial=fake_min_spatial,
                             min_temporal=fake_min_temporal,
                             manual_processing=fake_manual_processing,
                             **vars(fake_passed_args))

        cli.add_capped_tile_store(fake_args)

        mock_api_add_capped_tile_store.assert_called_once_with(
            fake_dataset_id,
            fake_min_spatial,
            fake_min_temporal,
            not fake_manual_processing,
            **vars(fake_passed_args))


if __name__ == '__main__':
    unittest.main()
