import conduce.api
import requests
import time
import random
from datetime import datetime


def get_lightning_data():
    req = requests.get("http://wwlln.net/new/map/data/current.json")
    if not req.ok:
        print "Failed to get lightning data:", req.status_code, req.text
        return None
    try:
        return req.json()
    except Exception as exc:
        print "Exception reading data from wwlln:", exc
        return None


def filter_lightning_data(ld, maxInputTime):
    ldout = {}
    items = ld.items()
    items.sort(key=lambda x: x[1]["unixTime"])
    for lid, linfo in items:
        if linfo["unixTime"] <= maxInputTime:
            continue
        ldout[lid] = linfo
    return ldout


def format_data_into_entities(ld):
    entities = [None]*len(ld)
    for i, (lid, linfo) in enumerate(ld.iteritems()):
        entities[i] = {
            "id": lid,
            "kind": "lightning",
            "time": datetime.utcfromtimestamp(linfo["unixTime"]),
            "point": {"x": linfo["long"], "y": linfo["lat"]},
        }
    return entities


def ingest_new_strikes(dataset_id, samples, host):
    try:
        conduce.api.ingest_samples(dataset_id, samples, host=host)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code < 500:
            print "Client error, dropping new data"
            print(e.response)
        else:
            print "Server error"
            print(e.response)
            time.sleep(30)
            ingest_new_strikes(dataset_id, samples, host)


def get_dataset(dataset_name, host):
    datasets = conduce.api.find_dataset(name=dataset_name, host=host)
    if len(datasets) == 0:
        dataset = conduce.api.create_dataset(dataset_name, host=host)
    else:
        dataset = datasets[0]

    return dataset


def main(event, context):
    DATASET_NAME = "wwln_lightning_kvl_test"
    ITER_TIME = 60
    datasets = {}
    #datasets['app.conduce.com'] = get_dataset(DATASET_NAME, 'app.conduce.com')
    datasets['dev-app.conduce.com'] = get_dataset(DATASET_NAME, 'dev-app.conduce.com')
    print("Using datasets")
    print([dataset['id'] for dataset in datasets.values()])
    maxInputTime = 0
    while True:
        raw_ld = get_lightning_data()
        if not raw_ld:
            print "No data received"
            time.sleep(ITER_TIME*0.25)
            continue
        ld = filter_lightning_data(raw_ld, maxInputTime)
        if not ld:
            print "No entities to add"
            time.sleep(ITER_TIME)
            continue
        ents = format_data_into_entities(ld)

        for host, dataset in datasets.iteritems():
            ingest_new_strikes(dataset['id'], ents, host)

        maxInputTime = max(ld.itervalues(), key=lambda x: x["unixTime"])["unixTime"]
        print "Added %d entities" % len(ents)
        time.sleep(ITER_TIME)


if __name__ == "__main__":
    main(None, None)
