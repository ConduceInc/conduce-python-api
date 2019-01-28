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


def filter_lightning_data(lightning_strikes, maxInputTime):
    items = lightning_strikes.items()
    filtered_strikes = {}
    items.sort(key=lambda x: x[1]["unixTime"])
    for strike_id, strike_info in items:
        if strike_info["unixTime"] <= maxInputTime:
            continue
        filtered_strikes[strike_id] = strike_info
    return filtered_strikes


def format_data_into_entities(lightning_strikes):
    samples = [None]*len(lightning_strikes)
    for i, (strike_id, strike_info) in enumerate(lightning_strikes.iteritems()):
        samples[i] = {
            "id": strike_id,
            "kind": "lightning",
            "time": datetime.utcfromtimestamp(strike_info["unixTime"]),
            "point": {"x": strike_info["long"], "y": strike_info["lat"]},
        }
    return samples


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
        strikes = get_lightning_data()
        if not strikes:
            print "No data received"
            time.sleep(ITER_TIME*0.25)
            continue
        filtered_strikes = filter_lightning_data(strikes, maxInputTime)
        if not filtered_strikes:
            print "No entities to add"
            time.sleep(ITER_TIME)
            continue
        samples = format_data_into_entities(filtered_strikes)

        for host, dataset in datasets.iteritems():
            ingest_new_strikes(dataset['id'], samples, host)

        maxInputTime = max(filtered_strikes.itervalues(), key=lambda x: x["unixTime"])["unixTime"]
        print "Added %d entities" % len(samples)
        time.sleep(ITER_TIME)


if __name__ == "__main__":
    main(None, None)
