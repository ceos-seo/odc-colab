# pylint: disable=broad-except,unused-argument,import-outside-toplevel
''' Tools for setting up ODC in a Colab environment. '''
import sys
from os import environ

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
    import subprocess
    return subprocess.check_output(
        cmd,
        stderr=subprocess.STDOUT,
        universal_newlines=True, # Python 3.7 would prefer text=True
        )

def _pip_install(module, verbose=False):
    ''' Installs a Python module using pip.

    Args:
        module (str): The name of the module to install.
        verbose (bool): Optional; flag to set verbosity for install.

    Returns the result of the pip command.
    '''
    return _shell_cmd([sys.executable, "-m", "pip", "install", module])

def _apt_install(package, verbose=False):
    ''' Install a system package using apt-get.

    Args:
        package (str): The package name to install.
        verbose (bool): Optional; flag to set verbosity for install.

    Returns the result of the apt-get command.
    '''
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
    return bool(_shell_cmd(["dpkg", "-l"]).count(package))

def _check_pip_install(module, verbose=False):
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
        shell_result = _pip_install(module)
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
        use_defaults (bool): A flag to use a default configuration or not.

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

def _psql_config_present():
    ''' Checks if a PostgreSQL configuration is present.

    Returns:
        False if the configuration does not exist.
        True if the configuration does exist.
    '''
    from os import path
    import pwd
    pw_names = [pw.pw_name for pw in pwd.getpwall()]
    if (path.exists('/var/lib/postgresql/10/main/postgresql.conf') and
            path.exists('/var/lib/postgresql/10/main/pg_hba.conf') and
            'postgres' in pw_names):
        return True
    return False

def odc_colab_init(
        verbose=False,
        install_datacube=True,
        install_ceos_utils=True,
        install_postgresql=True,
        use_defaults=False,
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
        use_defaults (bool): Optional; flag to install environment with default configuration.
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


    if install_datacube:
        _check_pip_install('datacube', verbose)

    if install_ceos_utils:
        _check_git_install('utils',
                           'https://github.com/ceos-seo/data_cube_utilities.git',
                           verbose)
        _check_pip_install('hdmedians', verbose)

    if install_postgresql:
        import shutil
        psql_lib = '/var/lib/postgresql/10/main'
        _check_apt_install('postgresql', verbose)
        if not _psql_config_present():
            try:
                shutil.copy(f'{psql_lib}/postgresql.auto.conf', f'{psql_lib}/postgresql.conf')
                shutil.chown(f'{psql_lib}/postgresql.conf', 'postgres', 'postgres')
                pg_hba = ("""
# Allow any user on the local system to connect to any database with
# any database user name using Unix-domain sockets (the default for local
# connections).
#
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
""").lstrip().rstrip()

                with open(f'{psql_lib}/pg_hba.conf', 'w') as _file:
                    _file.write(pg_hba)
                shutil.chown(f'{psql_lib}/pg_hba.conf', 'postgres', 'postgres')
                _shell_cmd(["sudo", "-u", "postgres",
                            "/usr/lib/postgresql/10/bin/pg_ctl",
                            "-D", psql_lib,
                            "-l", "/var/log/postgresql/logfile",
                            "start"])
                _shell_cmd(["sudo", "-u", "postgres",
                            "createuser", "-s", "root"])
                if install_datacube:
                    _shell_cmd(["sudo", "-u", "postgres",
                                "createdb", "-O", "root", "datacube"])
                    #_shell_cmd(["datacube", "system", "init"])
            except Exception as error:
                print(error)

# TODO: Change this for GitHub usage.
# DB dump file will be compressed and split to keep under 100MB.
def populate_db(tar_file):
    ''' Populates the datacube database from a compressed SQL dump.

    Args:
        tar_file (str): The path to a tar file to load.

    Raises OSError if tar file is not found.
    '''
    import tarfile
    from pathlib import Path
    path = Path(tar_file)
    if path.exists():
        with tarfile.open(path.name, 'r') as tar:
            tar.extractall()
        for suffix in path.suffixes:
            path = path.with_suffix('')
        _shell_cmd(["psql", "-f", f"{path}",
                    "-d", "datacube"])
    else:
        raise OSError('Tar file does not exist.')
