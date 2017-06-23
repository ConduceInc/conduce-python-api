#!/usr/bin/env python
import requests
import json
import time
import urlparse

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


EXAMPLE_CONDUCE_API_KEY="tTPtOvbQrrSzgxR8uymnlpRzZIWEoEhTifJGLN1rZSs"
VM_SERVER = "https://10.254.255.10"
DEV_SERVER = "https://dev-app.conduce.com"

class ConduceError(Exception):
    def __init__(self, url, resp, msg=None):
        self.code = resp.status_code
        self.url = url
        self.text = resp.text
        msg = "Got a error code %s from %s: %s" % (resp.status_code, url, resp.text)
        super(ConduceError, self).__init__(msg)


class ConduceAPIClient(object):
    #Simple Version history:
    # 1.0 Version including all features to migrate using sluice-to-banksy & run a RT daemon
    # 2.0: Use v2 datasets for everything
    # 2.1: Make create dataset sage function & ensure_sage_dataset function
    # 3.0: Integrate with functional api
    __version = 2.1

    def __init__(self, host="https://app.conduce.com", api_key=None, email=None, password=None, insecure=True):
        """
        Configure an API client that can connect to Conduce servers.
        You may provide either an API key or an email and password.  The API key
        is strongly encouraged since it does not use a users credentials, and
        does not provide full access to a user's account if compromised.
        If email/password are provided, you must call the login() function to
        get a cookie.

        :param host: optional host, only used if connecting to beta servers
        :param api_key: optional api key.  This is the recommended way to use this client
        :param email: optional email if using login
        :param password: optional pasword if using login
        :rtype: ConduceAPIClient
        """
        if api_key is None:
            #using email & password
            if email is None and password is None:
                raise ValueError("api_key or email & password required")
            if email is None or password is None:
                raise ValueError("both email and password must be provided")
        else:
            #If an api key is specified, make sure email & password are none
            if email is not None or password is not None:
                #TODO: Use the warning lib
                print "Warning, not using email or password inputs because api key is specified"
            email = None
            password = None
        #TODO: Make sure API has valid characters letters, numbers & - & _
        self._api_key = api_key
        self._email = email
        self._password = password
        self._cookies = None
        #TODO: Regex check host
        self._verify = True
        info = urlparse.urlparse(host)
        scheme = info.scheme if info.scheme else "https"
        hostname = info.hostname if info.hostname else info.path
        if hostname.endswith("/"):
            hostname = hostname[:-1]
        if scheme == 'https':
            if not (hostname.endswith('.conduce.com') or hostname.endswith('.mct.io')):
                self._verify = False
        elif not insecure:
            raise ValueError("If not using https, insecure kwarg must be true")
        self._host = "{}://{}".format(scheme, hostname)

    def login(self):
        if self._api_key:
            return
        login_data = json.dumps({'email': self._email, 'password': self._password, 'keep': True})
        headers = {'Content-Type': 'application/json'}
        req = requests.post('%s/api/login' % self._host, data=login_data, headers=headers, verify=self._verify)
        if not req.ok:
            raise ConduceError(url, req)
        self._cookies = req.cookies

    def api_get(self, uri):
        url = '%s/conduce/api%s' % (self._host, uri)
        headers = {}
        if self._api_key:
            headers["Authorization"] = "Bearer %s" % self._api_key
            #headers["AUTHORIZATION"] = "Bearer %s" % self._api_key
        req = requests.get(url, cookies=self._cookies, headers=headers, verify=self._verify)
        if int(req.status_code / 100) != 2:
            raise ConduceError(url, req)
        return req

    def api_post(self, uri, data_dict):
        return self.api_post_binary(uri, json.dumps(data_dict), "application/json")

    def api_post_binary(self, uri, data, content_type):
        url = '%s/conduce/api%s' % (self._host, uri)
        headers = {"Content-Type": content_type}
        if self._api_key:
            headers["Authorization"] = "Bearer %s" % self._api_key
            #headers["AUTHORIZATION"] = "Bearer %s" % self._api_key
        req = requests.post(url, cookies=self._cookies, verify=self._verify, headers=headers, data=data)
        if not req.ok:
            raise ConduceError(url, req)
        return req

    def search_userassets(self, folder=None, mime_type=None):
        filters = {}
        if folder is not None:
            filters["folder"] = {"name": folder}
        if mime_type is not None:
            filters["mime_type"] = mime_type
        req = self.api_post("/userassets/search", filters)
        ret = req.json()
        return ret["asset_list"]

    def delete_asset(self, asset_id):
        req = self.api_post("/userassets/delete/{}".format(asset_id), None)
        return req.json()

    def create_asset(self, asset_path, mime_type, asset_data):
        req = self.api_post_binary("/userassets/new/{}".format(asset_path), asset_data, mime_type)
        ret = req.json()
        return ret["asset_created"]

    def create_folder(self, folder_name, exists_ok=False):
        #Returns whether the folder was new
        try:
            self.api_post('/templates/new_folder', {"name": folder_name})
            return True
        except ConduceError as exc:
            if exists_ok and exc.code == 400 and "already exists" in exc.text:
                return False
            raise

    def search_templates(self, folder=None, filename_contains=None):
        filters = {}
        if folder is not None:
            filters["folder"] = {"name": folder}
        if filename_contains is not None:
            filters["query"] = filename_contains
        req = self.api_post("/templates/search", filters)
        ret = req.json()
        return ret["template_list"]

    def delete_template(self, template_id):
        req = self.api_post("/templates/delete/{}".format(template_id), None)
        return req.json()

    def create_template(self, template_path, template_data):
        req = self.api_post("/templates/new/{}".format(template_path), template_data)
        ret = req.json()
        return ret["template_created"]




    def list_datasets(self):
        req = self.api_get('/datasets/listv2')
        return req.json()

    def get_dataset_id(self, name):
        for ds in self.list_datasets():
            if ds.get("name") == name:
                return ds["id"]
        return None

    def create_dataset(self, ds):
        resp = self.api_post('/datasets/createv2', ds)
        obj = resp.json()
        return obj["dataset"]

    def create_sage_dataset(self, dataset_name):
        dsreq = {
            "name": dataset_name,
            "backend": "sage"
        }
        return self.create_dataset(dsreq)

    def ensure_sage_dataset(self, dataset_name):
        dataset_id = self.get_dataset_id(dataset_name)
        if dataset_id is not None:
            return dataset_id
        return self.create_sage_dataset(dataset_name)

    def add_data_to_dataset(self, dsid, ents):
        es = {"entities": ents}
        resp = self.api_post('/datasets/add_datav2/%s' % dsid, es)
        #wait for the job to finish
        finished = False
        job_loc = resp.headers['location']
        while not finished:
            resp = self.api_get(job_loc)
            if resp.ok:
                print resp.content
                msg = resp.json()
                if 'response' in msg:
                    finished = True
                    return True
                time.sleep(0.5)
            else:
                print resp, resp.content
                break
        #Shouldn't get here
        return None

    def compact(self, dsid):
        #TODO: Is this V2?
        resp = self.api_post('/datasets/compact/%s' % dsid)
        finished = False
        print resp
        print resp.content
        job_loc = resp.headers['location']
        while not finished:
            resp = self.api_get(job_loc)
            msg = resp.json()
            if 'response' in msg:
                finished = True
                return json.loads(msg['result'])
            else:
                time.sleep(0.5)
        #Shouldn't get here
        return None

