# pylint: disable=import-error,invalid-name,protected-access,too-few-public-methods
""" Module for Google Earth Engine tools. """
from importlib import import_module
from pathlib import Path
import os

from rasterio.errors import RasterioIOError

import datacube

HOME = os.getenv('HOME')
CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS',
                        f'{HOME}/.config/odc-gee/credentials.json')

if not os.environ.get('CURL_CA_BUNDLE'):
    os.environ.update(CURL_CA_BUNDLE='/etc/ssl/certs/ca-certificates.crt')

class Datacube(datacube.Datacube):
    ''' Extended Datacube object for use with Google Earth Engine.

    Attributes:
        credentials: The Earth Engine credentials being used for the API session.
        request: The Request object used in the session.
        ee: A reference to the ee (earthengine-api) module.
    '''
    def __init__(self, *args, credentials=CREDENTIALS, **kwargs):
        self.ee = import_module('ee')
        if Path(credentials).exists():
            os.environ.update(GOOGLE_APPLICATION_CREDENTIALS=credentials)
            self.credentials = self.ee.ServiceAccountCredentials('', key_file=credentials)
            self.ee.Initialize(self.credentials)
            self.request = None
        else:
            self.ee.Authenticate()
            self.ee.Initialize()
            self.credentials = self.ee.data.get_persistent_credentials()
            self.request = import_module('google.auth.transport.requests').Request()
            self._refresh_credentials()
        super().__init__(*args, **kwargs)

    def load(self, *args, **kwargs):
        ''' An overloaded load function from Datacube.

        This load method allows for querying the Earth Engine REST API to search for datasets
        instead of using the standard database query of datacube.Datacube.

        Returns: The queried xarray.Dataset.
        '''
        try:
            return super().load(*args, **kwargs)
        except RasterioIOError as error:
            if error.args[0].find('"UNAUTHENTICATED"') != -1:
                if self._refresh_credentials():
                    return self.load(*args, **kwargs)
                raise error
        except Exception as error:
            raise error

    def _refresh_credentials(self):
        if self.request:
            self.credentials.refresh(self.request)
            os.environ.update(EEDA_BEARER=self.credentials.token)
            return True
        return False
