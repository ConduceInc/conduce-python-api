import json

from . import api
from . import util


def get_dataset_id(dataset_name, **kwargs):
    datasets = api.list_datasets(**kwargs)
    for dataset in datasets:
        if dataset['name'] == dataset_name:
            return dataset['id']

    return None


def ingest_json(dataset_id, json_file, **kwargs):
    api._ingest_entity_set(dataset_id, util.dict_to_entities(json.load(open(json_file))), **kwargs)


def ingest_csv(dataset_id, csv_file, **kwargs):
    api._ingest_entity_set(dataset_id, util.csv_to_entities(kwargs['csv'], **kwargs), **kwargs)


def ingest_file(dataset_id, **kwargs):
    if 'json' in kwargs and kwargs['json']:
        return ingest_json(dataset_id, kwargs['json'], **kwargs)
    elif 'csv' in kwargs and kwargs['csv']:
        return ingest_csv(dataset_id, kwargs['csv'], **kwargs)
    else:
        raise NotImplementedError('Unrecognized file format')
