#!/usr/bin/env python
import requests
import json
import time
import urlparse

#this imports conduce.api
import api as func_api

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


DEV_SERVER = "https://dev-app.conduce.com"

#Resources
USER_ASSET = "userassets"
TEMPLATE = "templates"



_LIST_KEYS = {
    USER_ASSET: "asset",
    TEMPLATE: "template",
}


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
    __version = 3.0

    def __init__(self, host="https://app.conduce.com", api_key=None, email=None, password=None, insecure=True):
        """
        Configure an API client that can connect to Conduce servers.
        You may provide either an API key or an email and password.  The API key
        is strongly encouraged since it does not expose a user's credentials, and
        does not provide full access to a user's account if compromised.
        If email/password are provided, you must call the login() function to
        get a cookie before making API calls.

        :param host: optional host, only used if connecting to beta/preview servers
        :param api_key: optional api key.  This is the recommended way to use this client
        :param email: optional email if using login
        :param password: optional pasword if using login
        :rtype: ConduceAPIClient
        """
        #TODO: Integrate this with config.py
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
                print "Warning, ignoring email and password inputs because api key provided"
            email = None
            password = None
        #TODO: Make sure API has valid characters letters, numbers & - & _
        self._api_key = api_key
        self._email = email
        self._password = password
        self._cookies = None
        self._verify = not insecure
        info = urlparse.urlparse(host)
        scheme = info.scheme if info.scheme else "https"
        hostname = info.hostname if info.hostname else info.path
        if hostname.endswith("/"):
            hostname = hostname[:-1]
        #TODO: Regex check host
        self._host = "{}://{}".format(scheme, hostname)
        self._hostname = hostname

    def login(self):
        if self._api_key:
            return
        login_data = json.dumps({'email': self._email, 'password': self._password, 'keep': True})
        headers = {'Content-Type': 'application/json'}
        req = requests.post('%s/conduce/api/v1/user/login' % self._host, data=login_data, headers=headers, verify=self._verify)
        if not req.ok:
            raise ConduceError(req.url, req)
        self._cookies = req.cookies
        #HACK!!!
        req = self.api_get("/apikeys/list")
        apikeys = req.json()
        if len(apikeys) == 0:
            raise NotImplementedError("Create an API key under the {} user to use the OO API".format(self._email))
        self._api_key = apikeys[0]["apikey"]

    def api_get(self, uri):
        url = '%s/conduce/api/v1%s' % (self._host, uri)
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
        url = '%s/conduce/api/v1%s' % (self._host, uri)
        headers = {"Content-Type": content_type}
        if self._api_key:
            headers["Authorization"] = "Bearer %s" % self._api_key
            #headers["AUTHORIZATION"] = "Bearer %s" % self._api_key
        req = requests.post(url, cookies=self._cookies, verify=self._verify, headers=headers, data=data)
        if not req.ok:
            raise ConduceError(url, req)
        return req

    #
    # Impedence matching the functional API
    #
    def _get_creds(self):
        if self._api_key:
            return {"api_key": self._api_key, "host": self._hostname}
        else:
            raise NotImplementedError("The object oriented API does not support the email/password login yet")

    def _check_resp(self, resp):
        if not resp.ok:
            raise ConduceError(resp.url, resp)

    #
    # Gotta support these for now :/
    # These are around so existing scripts using the OO API still work.  I figure
    # it's easier to just support these for now & integrate everything once the v2
    # api is availabe to do tagging
    #
    def create_folder(self, folder_name, exists_ok=False):
        #Returns whether the folder was new
        try:
            self.api_post('/folders/create', {"name": folder_name})
            return True
        except ConduceError as exc:
            if exists_ok and exc.code == 400 and "already exists" in exc.text:
                return False
            raise

    #
    # Resource API
    #
    #TODO: Rework into the API while doing v2 cleanup
    def _find_resource_by_name(self, resource_type, name):
        if resource_type not in _LIST_KEYS:
            raise NotImplementedError("No support for {}, only support: {}".format(resource_name, _LIST_KEYS.keys()))
        key = "{}_list".format(_LIST_KEYS[resource_type])
        search_uri = '{}/search'.format(resource_type)
        resp = func_api.make_post_request({'query':name}, search_uri, **self._get_creds())
        self._check_resp(resp)
        results = resp.json().get(key, {})
        for finfo in results.get("files", []):
            if finfo.get("name") == name:
                return finfo
        return None

    def remove_resource(self, resource_id, resource_type=None):
        resp = func_api._remove_thing_by_id(resource_type, resource_id, **self._get_creds())
        return resp


    #
    # User Assets
    #

    # have to support searching by folder, just copy the old code for now
    def search_userassets(self, folder=None, mime_type=None):
        filters = {}
        if folder is not None:
            filters["folder"] = {"name": folder}
        if mime_type is not None:
            filters["mime-type"] = mime_type
        req = self.api_post("/userassets/search", filters)
        ret = req.json()
        return ret["asset_list"]

    def find_userasset(self, name):
        return self._find_resource_by_name(USER_ASSET, name)

    def delete_asset(self, asset_id):
        return self.remove_resource(asset_id, resource_type=USER_ASSET)

    def create_asset(self, asset_path, mime_type, asset_data):
        #need to support a folder/tag
        # api.create_asset("{}/{}".format(conduce_folder, asset_name), "image/png", data)
        resp = func_api.create_asset(asset_path, asset_data, mime_type, **self._get_creds())
        self._check_resp(resp)
        key = "{}_created".format(_LIST_KEYS[USER_ASSET])
        return resp.json()[key]

    #
    # Templates
    #

    # Same as searchuserasets, just copy the old code for now b/c this
    # searches based on folders - integrate this better one day
    def search_templates(self, folder=None, filename_contains=None):
        filters = {}
        if folder is not None:
            filters["folder"] = {"name": folder}
        if filename_contains is not None:
            filters["query"] = filename_contains
        req = self.api_post("/templates/search", filters)
        ret = req.json()
        return ret["template_list"]

    def find_template(self, name):
        #need to support search_templates(folder=conduce_folder, filename_contains=template["name"])
        return self._find_resource_by_name(TEMPLATE, name)

    def delete_template(self, template_id):
        return self.remove_resource(template_id, resource_type=TEMPLATE)

    def create_template(self, template_path, template_data):
        #support template_info = api.create_template("{}/{}".format(conduce_folder, template["name"]), template)
        resp = func_api.create_template(template_path, template_data, **self._get_creds())
        self._check_resp(resp)
        key = "{}_created".format(_LIST_KEYS[TEMPLATE])
        return resp.json()[key]

    def save_template(self, template_id, template_data):
        resp = func_api.save_template(template_id, template_data, **self._get_creds())
        self._check_resp(resp)
        key = "{}_saved".format(_LIST_KEYS[TEMPLATE])
        return resp.json()[key]


    #
    # Dataset functions
    #

    def create_dataset(self, dataset_name):
        resp = func_api.create_dataset(dataset_name, **self._get_creds())
        self._check_resp(resp)
        return resp.json()["dataset"]

    def list_datasets(self):
        resp = func_api.list_datasets(**self._get_creds())
        self._check_resp(resp)
        return resp.json()

    def get_dataset_id(self, name):
        for ds in self.list_datasets():
            if ds.get("name") == name:
                return ds["id"]
        return None

    def ensure_dataset(self, dataset_name):
        dataset_id = self.get_dataset_id(dataset_name)
        if dataset_id is not None:
            return dataset_id
        return self.create_dataset(dataset_name)

    def add_data_to_dataset(self, dsid, ents):
        func_api.ingest_entities(dsid, ents, **self._get_creds())
        return True

