import conduce.api
import requests
import time
import random
from datetime import datetime

ITER_TIME = 60
DATASET_NAME = "wwln_lightning"


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
    # HACK really
    ldout = {}
    ##count = 0
    items = ld.items()
    # NOTE: The sort order is increasing time.  With the limits
    # on count, this is just adding old data slowly.  The sort
    # should have reverse=True & no count limit if this is to
    # cecome a real daemon.
    # But for the demo, I want to see data streaming in
    # so I stream in small parts of it so there is a continuous
    # supply of new data coming in during the demo.
    items.sort(key=lambda x: x[1]["unixTime"])
    for lid, linfo in items:
        # American lightning is the Best!
        if linfo["lat"] < 18 or linfo["lat"] > 50:
            continue
        if linfo["long"] > -65 or linfo["long"] < -125:
            continue
        if linfo["unixTime"] <= maxInputTime:
            continue
        ##count += 1
        ldout[lid] = linfo
        # if count >= 40:
        # break
    return ldout


def format_data_into_entities(ld):
    entities = [None]*len(ld)
    for i, (lid, linfo) in enumerate(ld.iteritems()):
        entities[i] = {
            "id": lid,
            "kind": "lightning",
            "time": datetime.utcfromtimestamp(linfo["unixTime"]),
            "point": {"x": linfo["long"], "y": linfo["lat"]},
            "strength": random.randint(0, 9001)
        }
    return entities


def main(event, context):
    datasets = conduce.api.find_dataset(name=DATASET_NAME, host='app.conduce.com')
    if len(datasets) == 0:
        dataset = conduce.api.create_dataset(DATASET_NAME, host='app.conduce.com')
    else:
        dataset = datasets[0]
    print "Using dataset", dataset['id']
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
        conduce.api.ingest_samples(dataset['id'], ents, host='app.conduce.com')
        # only update maxtime if the post worked - right now this has happened
        # because of deployments taking the server down for a short time
        maxInputTime = max(ld.itervalues(), key=lambda x: x["unixTime"])["unixTime"]
        print "Added %d entities" % len(ents)
        time.sleep(ITER_TIME)


if __name__ == "__main__":
    main(None, None)
