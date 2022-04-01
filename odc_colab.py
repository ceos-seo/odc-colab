# pylint: disable=broad-except,unused-argument,import-outside-toplevel,too-many-arguments,too-many-branches
''' Tools for setting up ODC in a Colab environment. '''
import pwd
import sys
from os import environ, getuid, listdir, remove
import subprocess
import warnings

assert 'google.colab' in sys.modules, 'Not in a Google Colab environment.'
assert pwd.getpwuid(getuid()).pw_name == 'root', 'Not running as root.'


def build_datacube_db_url(hostname, username, password=None, dbname='datacube', port=5432):
    ''' Build a PostgreSQL URL for connecting to a networked ODC database.

    Args:
        hostname (str): The hostname of the target database.
        username (str): The username of the target database.
        password (str): Optional;  the password for the connecting username.
        dbname (str): Optional; the database name to connect to.
        port (int): Optional; the port to connect to.

    Returns the URL string.
    '''
    return (f'postgresql://{username}{":"+password if password is not None else ""}'
            f'@{hostname}:{port}/{dbname}')

def _shell_cmd(cmd):
    ''' Executes a list of shell arguments.

    Args:
        cmd (list): A list of arguments being supplied to the shell.

    Returns the output of the command.
    '''
    return subprocess.check_output(
        cmd,
        stderr=subprocess.STDOUT,
        universal_newlines=True, # Python 3.7 would prefer text=True
        )

def _pip_install(module, *args, verbose=False):
    ''' Installs a Python module using pip.

    Args:
        module (str): The name of the module to install.
        verbose (bool): Optional; flag to set verbosity for install.

    Returns the result of the pip command.
    '''
    return _shell_cmd([sys.executable, "-m", "pip", "install"]+list(args)+[module])

def _apt_install(package, verbose=False):
    ''' Install a system package using apt-get.

    Args:
        package (str): The package name to install.
        verbose (bool): Optional; flag to set verbosity for install.

    Returns the result of the apt-get command.
    '''
    try:
        _shell_cmd(["apt-get", "update"])
    except subprocess.CalledProcessError:
        warnings.warn(message=f'Unable to complete `apt-get update` before installing "{package}".  Attempting to install anyway.', stacklevel=2)
    return _shell_cmd(["apt-get", "install", package])

def _git_install(url, module_name=None, verbose=False):
    ''' Checks if a git module exists.

    Args:
        url (str): The URL location of the git module.
        module_name (str): Optional; the name of the module.
        verbose (bool): Optional; flag to set verbosity for install.

    Returns the result of installing the git module.
    '''
    cmd = ["git", "clone", url]
    if module_name:
        cmd.append(module_name)
    return _shell_cmd(cmd)

def _module_found(module):
    ''' Checks if module is loadable.

    Args:
        module (str): The module name to check.
    '''
    if module in sys.modules:
        return True # Already loaded
    import importlib
    spam_spec = importlib.util.find_spec(module)
    return spam_spec is not None

def _package_found(package):
    ''' Checks if package is installed.

    Args:
        package (str): The package name to check.
    '''
    try:
        return bool(_shell_cmd(["dpkg", "-l"]).count(package))
    except Exception as error:
        warnings.warn(message=f'Unable to check dpkg for "{package}" package.  Assuming it is not present.', stacklevel=2)
    return False

def _check_pip_install(module, *args, verbose=False):
    ''' Installs a Python package if it is not found.

    Args:
        module (str): The name of the module to check.
        verbose (bool): Optional; flag to set verbosity for install.
    '''
    if _module_found(module):
        if verbose:
            print(f'Found {module} module, skipping install.')
    else:
        print(f'Module {module} was not found; installing it...')
        shell_result = _pip_install(module, *args)
        if verbose:
            print(shell_result)

def _check_apt_install(package, verbose=False):
    ''' Installs a system package if it is not found.

    Args:
        package (str): The name of the package to check.
        verbose (bool): Optional; flag to set verbosity for install.
    '''
    if _package_found(package):
        if verbose:
            print(f'Found {package} package, skipping install.')
    else:
        print(f'Package {package} was not found; installing it...')
        shell_result = _apt_install(package)
        if verbose:
            print(shell_result)

def _check_git_install(module, url, verbose=False):
    ''' Installs a git module if it is not found.

    Args:
        module (str): The name of the git module.
        url (str): The git URL of module.
        verbose (bool): Optional; flag to set verbosity for install.
    '''
    if _module_found(module):
        if verbose:
            print(f'Found {module} module, skipping install.')
    else:
        print(f'Module {module} was not found; cloning {url} to CWD...')
        shell_result = _git_install(url, module_name=module)
        if verbose:
            print(shell_result)

def _dc_config_present(use_defaults):
    ''' Checks if the datacube configuration exists.

    Args:
        use_defaults (bool): A flag to use a default local database configuration or not.

    Returns:
        False if the configuration does not exist.
        True if the configuration does exist.
    '''
    # See https://opendatacube.readthedocs.io/en/latest/ops/config.html
    from os import path
    if use_defaults:
        datacube_conf = ("""
[default]
db_database: datacube

# A blank host will use a local socket. Specify a hostname (such as localhost) to use TCP.
db_hostname:
""").lstrip().rstrip()
        with open('./datacube.conf', 'w') as _file:
            _file.write(datacube_conf)
        return True
    if 'DATACUBE_DB_URL' in environ:
        return True
    if 'DATACUBE_CONFIG_PATH' in environ:
        if path.exists(environ['DATACUBE_CONFIG_PATH']):
            return True
    if (path.exists('/etc/datacube.conf') or
            path.exists('~/.datacube.conf') or
            path.exists('datacube.conf')):
        return True
    return False

def _psql_running():
    ''' Checks if a PostgreSQL configuration is present.

    Returns:
        False if the configuration does not exist.
        True if the configuration does exist.
    '''
    from os import path
    if path.exists('/var/run/postgresql/10-main.pid'):
        return True
    return False

def odc_colab_init(
        verbose=False,
        install_datacube=True,
        install_ceos_utils=True,
        install_postgresql=True,
        install_odc_gee=False,
        use_defaults=True,
        **kwargs
        ):
    '''
    Configures Colab environment for Open Data Cube

    This function sets several environment variables and
    installs the datacube module and the CEOS datacube_utiltities
    module if necessary.  Additional enviroment variables
    can be passed as kwargs.  They are set before installing
    modules, in case anything specific to the install is needed.

    The ODC DB Credentials can be provided by either setting
    DATACUBE_CONFIG_PATH to point to a configuration file, or
    DATACUBE_DB_URL with the connection information in the format
    postgresql://user:password@host:port/database

    build_datacube_db_url is provided to help create connection string.

    NOTE: This function will install CEOS utils to the CURRENT
    WORKING DIRECTORY if it can't load the module.  If using a
    notebook which changes system path before importing modules,
    the path should be changed (or the module imported) BEFORE
    calling this function, lest it install a duplicate copy.
    If this happens by mistake, the directory can simply be deleted.

    Args:
        verbose (bool): Optional; flag to set verbosity for install.
        install_datacube (bool): Optional; flag to install an ODC environment.
        install_ceos_utils (bool): Optional; flag to install CEOS ODC utilities.
        install_postgresql (bool): Optional; flag to install postgresql.
        install_odc_gee (bool): Optional; flag to install CEOS ODC-GEE tools.
        use_defaults (bool): Optional;
            flag to install environment with default local database configuration.
        install_odc_gee (bool): Optional; install the CEOS ODC-GEE toolset.
    '''
    # Set environment variables
    env = {
        # default values here (may be overridden by user input)
        'AWS_NO_SIGN_REQUEST': 'YES',
        'CURL_CA_BUNDLE': '/etc/ssl/certs/ca-certificates.crt',
    }
    # If user supplied DATACUBE_CONFIG_PATH, we don't want to set DATACUBE_DB_URL
    if 'DATACUBE_CONFIG_PATH' in kwargs:
        del env['DATACUBE_DB_URL']
    env.update(kwargs) # Merge default and user-supplied vars
    if len(env) > 0:
        if verbose:
            print('Setting environment variables:')
        for key, var in env.items():
            if verbose:
                print(f'\t{key}={var}')
            environ[key] = var

    if not _dc_config_present(use_defaults):
        # Python version on Colab has buffer issue with warnings, causing extra junk to leak.
        # Just using a print for now.
        print("Warning:", end='')
        #from warnings import warn
        print("""
There does not appear to be an Open Data Cube environment configured, so
instantiating a Datacube may fail.  An environment configuration can be
specified in one of the following ways:
    - Pass the DATACUBE_DB_URL arg to this function, with a valid connection
    string containing credentials for a (possibly remote) ODC database instance.
    This file includes a build_datacube_db_url() function to help generate one.
    - Pass the DATACUBE_CONFIG_PATH arg to this function, containing a (string)
    path pointing to a valid config file.
    - Put a valid config file at any of the default search locations.
More information on ODC environment configuration can be found at:
  https://opendatacube.readthedocs.io/en/latest/ops/config.html
""")
    # Upgrade pip to do proper dependency resolution
    _pip_install('pip', '--upgrade', verbose=verbose)
    if install_datacube:
        _pip_install('datacube==1.8.3', verbose=verbose)

    if install_ceos_utils:
        _check_git_install('utils',
                           'https://github.com/ceos-seo/data_cube_utilities.git',
                           verbose=verbose)
        _pip_install('xarray>=0.16.1', '--upgrade', verbose=verbose)
        _shell_cmd(['mkdir', '-p', '/content/output'])
        _shell_cmd(['mkdir', '-p', '/content/geotiffs'])

    if install_postgresql:
        _check_apt_install('postgresql', verbose=verbose)
        if not _psql_running():
            try:
                _shell_cmd(["service", "postgresql", "start"])
                _shell_cmd(["sudo", "-u", "postgres",
                            "createuser", "-s", "root"])
                if install_datacube:
                    _shell_cmd(["sudo", "-u", "postgres",
                                "createdb", "-O", "root", "datacube"])
                    #_shell_cmd(["datacube", "system", "init"])
            except Exception as error:
                print(error)

    if install_odc_gee:
        _check_git_install('odc-gee',
                           'https://github.com/ceos-seo/odc-gee.git',
                           verbose=verbose)
        _check_pip_install('odc-gee', '-e', verbose=verbose)
        _shell_cmd(["ln", "-sf", "/content/odc-gee/odc_gee",
                    "/usr/local/lib/python3.6/dist-packages/odc_gee"])
        _shell_cmd(["ln", "-sf", "/content/odc-gee/odc_gee",
                    "/usr/local/lib/python3.7/dist-packages/odc_gee"])
        _patch_schema()
        _shell_cmd(["datacube", "system", "init"])

def _patch_schema():
    from importlib.util import find_spec
    from pathlib import Path
    from types import SimpleNamespace
    from urllib import request

    # Download file if it doesn't exist
    patch_url = 'https://raw.githubusercontent.com/ceos-seo/odc-colab/master/patches/schema.diff'
    patch_file = f'./{patch_url.split("/")[-1]}'
    dummy_response = SimpleNamespace(code=0)
    resp = request.urlopen(patch_url) if not Path(patch_file).exists() else dummy_response
    if resp.code in range(200, 300):
        with open(patch_file, 'wb') as _file:
            _file.write(resp.read())

    # Patch file if unlocked
    if not Path(patch_file).with_suffix('.lock').exists():
        odc_loc = '/usr/local/lib/python3.7/dist-packages/datacube'
        _shell_cmd(["patch", f"{odc_loc}/model/schema/dataset-type-schema.yaml",
                    patch_file])
        Path(patch_file).with_suffix('.lock').touch()

def _combine_split_files(path):
    from pathlib import Path
    part_files = list(filter(lambda f: '.part' in f, listdir(path)))
    if part_files:
        part_files.sort()
        path = Path(path).joinpath(part_files[0].split('.')[0][:-3])
        with open(path, 'wb') as combined_file:
            for part_file in part_files:
                with open(path.parent.joinpath(part_file), 'rb') as _file:
                    combined_file.write(_file.read())
    return path

def _download_db(*args, **kwargs):
    from urllib import request
    url = 'https://raw.githubusercontent.com/ceos-seo/odc-colab/master/database/db_dump.tar.xz'
    print('No database file supplied. Downloading default index.')
    resp = request.urlopen(url)
    if resp.code < 300:
        tar_file = f'./{url.split("/")[-1]}'
        with open(tar_file, 'wb') as _file:
            _file.write(resp.read())
    return tar_file

def populate_db(path=None):
    ''' Populates the datacube database from a compressed SQL dump.

    Args:
        path (str): The path to a tar file to load or a directory of a split tar file.
        earthengine (bool): Flag to download Google Earth Engine Landsat 8 index.

    Raises OSError if tar file is not found.
    '''
    import tarfile
    import tempfile
    from pathlib import Path
    from shutil import move

    if not path:
        path = _download_db()

    path = Path(path).absolute()
    if path.exists():
        if not path.with_suffix('').with_suffix('').with_suffix('.lock').exists():
            path.with_suffix('').with_suffix('').with_suffix('.lock').touch()
            path = _combine_split_files(path) if path.is_dir() else path
            with tarfile.open(str(path), 'r:xz') as tar:
                tar.extractall(path=path.parent)
            sql_files = list(filter(lambda f: '.sql' in f,
                                    listdir(path.parent)))
            for sql_file in sql_files:
                with open(path.parent.joinpath(sql_file), 'r') as old_file:
                    with open(tempfile.mkstemp()[-1], 'w') as new_file:
                        line = old_file.readline()
                        while line:
                            new_file.write(line.replace('$$PATH$$', str(path.parent)))
                            line = old_file.readline()
                remove(old_file.name)
                move(new_file.name, old_file.name)
                _shell_cmd(["psql", "-f", old_file.name,
                            "-d", "datacube"])
            cleanup = [remove(_dir) for _dir in listdir('./')\
                       if '.dat' in _dir or '.sql' in _dir]
            if cleanup:
                print('Cleaned up extracted database files.')
        else:
            print('Lockfile exists, skipping population.')
    else:
        raise OSError('Tar file does not exist.')
