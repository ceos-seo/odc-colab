# ODC-Colab
ODC-Colab is a project designed to make Open Data Cube notebooks run on Google
Colab. This is done through a Python module with methods for performing an
automated setup of an ODC environment.

## Usage
To use the Python module you will need to add some code to the top of your
notebook.

The following block downloads the module and then runs the setup with default
configuration:

	!wget https://raw.githubusercontent.com/ceos-seo/odc-colab/master/odc_colab.py
	from odc_colab import odc_colab_init
	odc_colab_init(use_defaults=True)

This block of code will populate the new ODC database with a default index:

	!wget https://raw.githubusercontent.com/ceos-seo/odc-colab/master/database/db_dump.tar.xz
	from odc_colab import populate_db
	populate_db('db_dump.tar.xz')

### Converting existing notebooks
A diff file is included to make converting from Jupyter notebooks to Colab
notebooks simple. This can be done using the `patch` command: `patch
<jupyter_notebook> notebook_patch.diff`.

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
