from __future__ import print_function
from __future__ import absolute_import
import mimetypes
from . import api
from . import util
import os


def initialize_binary_asset(path, **kwargs):
    with open(util.walk_up_find(path, 'rb')) as image_stream:
        mime = mimetypes.guess_type(path)[0]
        image = image_stream.read()

        name = kwargs.get('name', os.path.basename(path))
        if 'name' in kwargs:
            del kwargs['name']
        return initialize_asset(name, image, mime, **kwargs)


def initialize_asset(name, data, mime_type, **kwargs):
    asset_id = kwargs.get('id')
    found = []

    if asset_id is not None:
        api.modify_asset_content(asset_id, data, mime_type, **kwargs)
        print('Updated asset {} {}'.format(name, asset_id))
        return asset_id

    if kwargs.get('modify'):
        found = api.find_asset(name=name, **kwargs)

    if len(found) == 0:
        asset_id = api.create_asset(name, data, mime_type, **kwargs)['id']
        print('Created asset {} {}'.format(name, asset_id))
    else:
        asset_id = found[0]['id']
        print('Found asset {} {}'.format(name, asset_id))
        api.modify_asset_content(asset_id, data, mime_type, **kwargs)
        print('Updated asset {} {}'.format(name, asset_id))

    return asset_id
