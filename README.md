# ODC-Colab
ODC-Colab is a CEOS initiative to make Open Data Cube notebooks run on Google
Colab. This is done through a Python module with methods that perform an
automated setup of an ODC environment through simple method calls.

This repository includes an example implementation of the CEOS ODC
notebooks repository:
[https://github.com/ceos-seo/data_cube_notebooks](https://github.com/ceos-seo/data_cube_notebooks).

These notebooks can be found in the `notebooks/DCAL` folder.

## Usage
You will need to add some code to the top of your notebook to use the Python
module. There are two different example options for environments shown, but
these are not the only uses of the module. More options are available and can
be found by reading the included docstrings in the `odc_colab.py` source file.
### Local database environment
This environment is for installing ODC with a local database.

The following block downloads the Python module and then runs the setup with a
default local database configuration that includes CEOS ODC utilities:

	!wget https://raw.githubusercontent.com/ceos-seo/odc-colab/master/odc_colab.py
	from odc_colab import odc_colab_init
	odc_colab_init(use_defaults=True)

The previous block of code will create an environment, but the index will be
empty so needs to be populated. This can be done with by uploading a database
dump of an existing index and running the following code:

	from odc_colab import populate_db
	populate_db('<database_dump_location>.tar.xz')

Not specifying a file will default to downloading `database/db_dump.tar.xz`
from this repository and using that to populate the database: `populate_db()`.

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
!wget https://raw.githubusercontent.com/ceos-seo/odc-colab/master/odc_colab.py
from odc_colab import build_datacube_db_url, odc_colab_init
odc_colab_init(install_postgresql=False, use_defaults=False,
               DATACUBE_DB_URL=build_datacube_db_url(<hostname>, <username>, password=<password>,
		                                     dbname=<dbname>, port=<port>)
```

### Converting existing notebooks (advanced)
A diff file is included to make converting from existing Jupyter notebooks to
Colab notebooks simple. This can be done using the GNU `patch` tool: `patch
<jupyter_notebook> notebook_patch.diff`.

This will also add a Colab button to the top of the notebook. This button can
take a GitHub URI for the notebook and automatically open it in Colab from
there. You will have to replace the `<URI_PLACEHOLDER>` with your notebook's
URI first, or you can optionally remove that block from your notebook.

**NOTE:** The patch only adds the top blocks specified earlier. Other code in
the notebook may need to be edited in order for the notebook to run to
completion in Colab.

## Developers
Example notebooks are included in the repository to showcase usage in Colab.
These notebooks are populated using a script which pulls the latest DCAL
notebooks from the [ceos-seo notebooks project on
GitHub](https://github.com/ceos-seo/data_cube_notebooks.git).

To run the script: `./scripts/update_notebooks`

This uses the patch file mentioned above and replaces other items in the
notebook in order for it to run to completion.
