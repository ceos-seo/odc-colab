# ODC-Colab
ODC-Colab is a CEOS initiative to demonstrate [Open Data
Cube](https://www.opendatacube.org/) notebooks running on Google Colab. This is
done through a Python module with methods that perform an automated setup of an
ODC environment through simple method calls.

This repository includes several example notebooks in the `./notebooks`
directory. We suggest starting with
[01.01.Getting\_Started\_ODC\_and\_Colab.ipynb](https://github.com/ceos-seo/odc-colab/blob/master/notebooks/01.01.Getting_Started_ODC_and_Colab.ipynb)
if unfamiliar with ODC or Colab notebooks.

The example notebooks make use of Google Earth Engine data. They will will
require some user interaction for Google authentication, and the user needs to
be registered as an Earth Engine developer. If not, you may submit an
[application to Google](https://signup.earthengine.google.com/). These
notebooks make use of the CEOS ODC-GEE project which can be found here:
[https://github.com/ceos-seo/odc-gee](https://github.com/ceos-seo/odc-gee).

**Note:** The `gee-notebooks` use a global Landsat 8 dataset obtained from GEE
using [ODC-GEE real-time indexing
capabilities](https://github.com/ceos-seo/odc-gee#real-time-indexing).
Landsat 7, Sentinel-1 and Sentinel-2 products are also defined for use, but
unused in the current notebooks. Other GEE datasets may also be used by
including an asset parameter in the `dc.load` as shown in the README of the
ODC-GEE project.

## Usage
You will need to add some code to the top of your notebook to use the Python
module. There are two different example options for environments shown, but
these are not the only uses of the module. More options are available and can
be found by reading the included docstrings in the `odc_colab.py` source file.
### Local database environment
This environment is for installing ODC with a local database.

The following block downloads the Python module and then runs the setup with a
default local database configuration that includes CEOS ODC utilities:

	!wget -nc https://raw.githubusercontent.com/ceos-seo/odc-colab/master/odc_colab.py
	from odc_colab import odc_colab_init
	odc_colab_init()

The previous block of code will create an environment, but the index will be
empty so needs to be populated. This can be done by importing a database dump
of an existing ODC index:

	from odc_colab import populate_db
	populate_db(path=<database_dump_location>.tar.xz)

The `populate_db()` command without parameters will download
`database/db_dump.tar.xz` from this repository to use for populating the
database.

##### Converting existing notebooks (advanced)
If you have existing notebooks you want to convert for use with this Colab
configuration, a diff file is included to make converting from existing Jupyter
notebooks to Colab notebooks simple. This can be done using the GNU `patch`
tool: `patch <jupyter_notebook> default.diff`.

This will also add a Colab button to the top of the notebook. This button can
take a GitHub URI for the notebook and automatically open it in Colab from
there. You will have to replace the `<URI_PLACEHOLDER>` with your notebook's
URI first, or you can optionally remove that block from your notebook.

**NOTE:** The patch only adds the default top blocks specified earlier. You may
have to specify to install ODC-GEE if wanting a similar environment as the
example notebooks, or you may have to provide a database dump to populate the
index.

### Remote database environment
This environment is for installing ODC with a remote database.

The following block downloads the Python module, sets an environment variable
to allow remote connections, and initializes the ODC environment with CEOS ODC
utilities included:

Substitutions:
* `hostname`: the hostname of the target database.
* `username`: the username of the target database.
* `password`: Optional; the password for the connecting username (default: None).
* `dbname`: Optional; the database name to connect to (default: datacube).
* `port`: Optional; the port number to connect to (default: 5432).

```
!wget -nc https://raw.githubusercontent.com/ceos-seo/odc-colab/master/odc_colab.py
from odc_colab import build_datacube_db_url, odc_colab_init
odc_colab_init(install_postgresql=False, use_defaults=False,
               DATACUBE_DB_URL=build_datacube_db_url(<hostname>, <username>, password=<password>,
		                                     dbname=<dbname>, port=<port>)
```
