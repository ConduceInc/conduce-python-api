import httplib,urllib
import requests
import json
import time

def add_entities_dict(host, api_key, dataset_id, entities):
    return add_entities(host, api_key, dataset_id, get_entities_json(entities))


def add_entities(host, api_key, dataset_id, entities_json):
    authStr = 'Bearer ' + api_key
    URI = '/conduce/api/datasets/add_datav2/' + dataset_id
    payload = entities_json
    headers = {
        'Authorization': authStr,
        'Content-type': 'application/json',
        'Content-Length': len(payload)
    }

    connection = httplib.HTTPSConnection(host)
    connection.request("POST", URI, payload, headers)
    response = connection.getresponse()
    response_content = response.read()
    response_stuff = response.status, response.reason, response_content
    connection.close()

    job_loc = response.getheader('location')
    if job_loc:
        jobURL = "https://%s/conduce/api%s" % (host, job_loc)
        return wait_for_job( authStr, jobURL )
    else:
        print "Error: Response contains no job location."
        print response_stuff
    return False

def wait_for_job(authStr, jobURL):
    headers = { 'Authorization': authStr }

    finished = False
    while not finished:
        time.sleep(0.5)
        response = requests.get(jobURL, headers=headers)
        if int(response.status_code / 100) != 2:
            print "Error code %s: %s" % (response.status_code, response.text)
            return False;

        if response.ok:
            msg = response.json()
            if 'response' in msg:
                print "Job completed successfully."
                finished = True
        else:
            print resp, resp.content
            break
    return True

def get_entities_json(entities):
    if(isinstance(entities, list)):
        conduce_entities = {}
        conduce_entities["entities"] = entities
    elif(isinstance(entities, dict)):
        if "entities" in entities:
            conduce_entities = entities
        else:
            raise Exception('Dictionary must contain "entities" key')
    else:
        raise Exception('Invalid argument')
    return json.dumps(conduce_entities, separators=(',',':'))

if __name__ == '__main__':
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Add data to a Conduce dataset')
    arg_parser.add_argument('--host', help='The field to sort on', default='dev-app.conduce.com')
    arg_parser.add_argument('--api-key', help='API authentication')
    arg_parser.add_argument('-d', '--dataset-id', help='ID of dataset being updated')
    arg_parser.add_argument('-i', '--data-file', help='Properly formatted Conduce entities JSON file')

    args = arg_parser.parse_args()

    if args.api_key is None:
        print "An API key is required"
        exit(1)

    if args.name is None:
        print "Please specify a dataset name"
        exit(1)

    if args.dataset_id is None:
        print "Please specify a dataset ID"
        exit(1)

    if args.data_file is None:
        print "Please specify a data file"
        exit(1)

    with open(args.data_file, "r") as input_file:
        if add_entities(args.host, args.api_key, args.dataset_id, json.dumps(input_file)):
            print "Data added successfully"
            exit_code = 0
        else:
            print "Data add failed"
            exit_code = 1
        exit(exit_code)

    raise "An error occurred opening", args.data_file
