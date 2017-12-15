import time
import itertools
import math
import requests
import json
import pprint
import conduce.api
import datetime
r = 1
headers = {'Authorization':'Bearer gauDIMLRRx62adtZGWbZGOAe8p3M8kAovRe6onsOTXo',
            'Content-type':'application/json'}
ents = []
while True:
    cur_time = int(round(time.time() * 1000))
    time.sleep(1)
    r = cur_time%5+1
    print r
    ent = {'id': 1,
            'time': datetime.datetime.now(),
            'kind':'test',
            'point':{'x':r*math.cos(cur_time),'y':r*math.sin(cur_time)}
            }
    ents.append(ent)
    if len(ents) > 10:
        pprint.pprint(ents)
        conduce.api.ingest_samples('bb24c0f0-69d4-47f7-9342-9cf70dd145ea',ents)
        ents = []
